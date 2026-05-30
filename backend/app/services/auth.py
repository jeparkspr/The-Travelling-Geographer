"""Authentication & authorization helpers.

Provides:
- Password hashing (bcrypt via passlib)
- JWT access / refresh token creation & validation
- FastAPI dependencies: get_current_user, require_role, require_permission
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User, Role, UserRole, RefreshToken

# ---------------------------------------------------------------------------
# Password hashing (bcrypt directly — avoids passlib compat issues)
# ---------------------------------------------------------------------------

import bcrypt as _bcrypt


import re

# Allowed special characters for passwords (security-safe subset)
ALLOWED_SYMBOLS = set("!@#$%^&*()-_=+[]{}|;:',.\"/? ")
ALLOWED_SYMBOLS_DISPLAY = "! @ # $ % ^ & * ( ) - _ = + [ ] { } | ; : ' , . \" / ? space"


def validate_password(password: str) -> list[str]:
    """Validate password complexity. Returns a list of failure reasons (empty = valid)."""
    errors = []
    if len(password) < 12:
        errors.append("Must be at least 12 characters long.")
    if not re.search(r"[A-Z]", password):
        errors.append("Must contain at least one uppercase letter (A–Z).")
    if not re.search(r"[a-z]", password):
        errors.append("Must contain at least one lowercase letter (a–z).")
    if not re.search(r"[0-9]", password):
        errors.append("Must contain at least one number (0–9).")
    if not any(ch in ALLOWED_SYMBOLS for ch in password):
        errors.append("Must contain at least one special character.")
    # Check for disallowed characters
    for ch in password:
        if not (ch.isalnum() or ch in ALLOWED_SYMBOLS):
            errors.append(f"Character '{ch}' is not allowed. Allowed symbols: {ALLOWED_SYMBOLS_DISPLAY}")
            break
    return errors


def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def create_access_token(user_id: str, extra: dict | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "access",
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token() -> str:
    """Return a cryptographically random opaque token (not a JWT)."""
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """SHA-256 hash for storing refresh tokens in DB."""
    return hashlib.sha256(token.encode()).hexdigest()


def decode_access_token(token: str) -> dict:
    """Decode and validate an access JWT. Raises on failure."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("type") != "access":
            raise JWTError("Not an access token")
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Decode the Bearer token and return the active User, or 401."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    result = await db.execute(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.roles).selectinload(UserRole.role))
    )
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    if not user.is_approved:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account pending approval")

    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Like get_current_user but returns None instead of 401 when unauthenticated.
    Useful during the transition period while auth is being added."""
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


def _user_role_names(user: User) -> List[str]:
    """Extract role name list from a loaded User."""
    return [ur.role.name for ur in (user.roles or [])]


def _user_has_permission(user: User, permission: str) -> bool:
    """Check a boolean permission flag across all of the user's roles."""
    for ur in (user.roles or []):
        if getattr(ur.role, permission, False):
            return True
    return False


def is_admin(user: User) -> bool:
    return "Administrator" in _user_role_names(user)


def require_role(*role_names: str):
    """Dependency factory: require the user to have at least one of the given roles."""
    async def _check(user: User = Depends(get_current_user)):
        user_roles = _user_role_names(user)
        if "Admin" in user_roles:
            return user  # Admin bypasses role checks
        if not any(r in user_roles for r in role_names):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user
    return _check


def require_permission(permission: str):
    """Dependency factory: require a specific permission flag (e.g. can_manage_users)."""
    async def _check(user: User = Depends(get_current_user)):
        if is_admin(user):
            return user
        if not _user_has_permission(user, permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user
    return _check


# ---------------------------------------------------------------------------
# Refresh-token DB helpers
# ---------------------------------------------------------------------------

async def store_refresh_token(db: AsyncSession, user_id: str, raw_token: str) -> RefreshToken:
    """Hash and persist a refresh token."""
    rt = RefreshToken(
        user_id=user_id,
        token_hash=hash_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(rt)
    await db.flush()
    return rt


async def validate_refresh_token(db: AsyncSession, raw_token: str) -> RefreshToken:
    """Look up the refresh token, check expiry and revocation."""
    h = hash_token(raw_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == h)
    )
    rt = result.scalar_one_or_none()
    if rt is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    if rt.revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")
    if rt.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")
    return rt


async def revoke_all_user_tokens(db: AsyncSession, user_id: str) -> None:
    """Revoke every refresh token for a user (e.g. on password change)."""
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False,  # noqa: E712
        )
    )
    for rt in result.scalars():
        rt.revoked = True


async def has_any_users(db: AsyncSession) -> bool:
    """Return True if at least one user exists (for setup wizard)."""
    result = await db.execute(select(func.count(User.id)))
    return result.scalar() > 0
