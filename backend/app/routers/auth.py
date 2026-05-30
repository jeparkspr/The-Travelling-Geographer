"""Authentication endpoints: login, register, refresh, logout, me."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, RefreshToken
from app.schemas.user import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    TokenResponse,
    RefreshRequest,
    CurrentUser,
    UserRead,
)
from app.services.auth import (
    hash_password,
    validate_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    store_refresh_token,
    validate_refresh_token,
    revoke_all_user_tokens,
    get_current_user,
    has_any_users,
    is_admin,
    hash_token,
)
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


def _build_token_response(access: str, refresh: str) -> TokenResponse:
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate with email + password, receive JWT tokens.

    Always returns 200 so the browser does not log console errors for
    expected failures like wrong credentials.  The ``success`` field
    indicates whether authentication succeeded.
    """
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user is None or not user.password_hash:
        return LoginResponse(success=False, detail="Invalid credentials")

    if not verify_password(body.password, user.password_hash):
        return LoginResponse(success=False, detail="Invalid credentials")

    if not user.is_active:
        return LoginResponse(success=False, detail="Account disabled")

    if not user.is_approved:
        return LoginResponse(success=False, detail="Account pending approval")

    # Issue tokens
    access = create_access_token(user.id)
    refresh = create_refresh_token()
    await store_refresh_token(db, user.id, refresh)

    # Update last_login
    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    return LoginResponse(
        success=True,
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Self-register a new account.

    Registration is only allowed if the app has already been set up (has at
    least one user — the admin created via /setup). New users get the
    default 'Viewer' role and are auto-approved for now.
    """
    # Block registration if no admin exists yet (must use /setup first)
    if not await has_any_users(db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="App not set up yet. Use the setup wizard.",
        )

    # Validate password complexity
    pwd_errors = validate_password(body.password)
    if pwd_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet complexity requirements: " + " ".join(pwd_errors),
        )

    # Check duplicate email
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    # Create user with default User role
    from app.models.user import Role, UserRole

    user_role_result = await db.execute(select(Role).where(Role.name == "User"))
    user_role = user_role_result.scalar_one_or_none()

    user = User(
        email=body.email,
        display_name=body.display_name,
        password_hash=hash_password(body.password),
        is_active=True,
        is_approved=True,
    )
    db.add(user)
    await db.flush()

    if user_role:
        db.add(UserRole(user_id=user.id, role_id=user_role.id))

    # Issue tokens
    access = create_access_token(user.id)
    refresh = create_refresh_token()
    await store_refresh_token(db, user.id, refresh)
    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    return _build_token_response(access, refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a valid refresh token for a new access + refresh token pair."""
    rt = await validate_refresh_token(db, body.refresh_token)

    # Revoke old token (rotation)
    rt.revoked = True

    # Look up user
    result = await db.execute(select(User).where(User.id == rt.user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    # Issue new pair
    access = create_access_token(user.id)
    new_refresh = create_refresh_token()
    await store_refresh_token(db, user.id, new_refresh)
    await db.commit()

    return _build_token_response(access, new_refresh)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Revoke the given refresh token."""
    h = hash_token(body.refresh_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == h))
    rt = result.scalar_one_or_none()
    if rt:
        rt.revoked = True
        await db.commit()


@router.get("/me", response_model=CurrentUser)
async def me(user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    role_names = [ur.role.name for ur in (user.roles or [])]
    permissions = {}
    for ur in (user.roles or []):
        for perm in ("can_manage_users", "can_manage_settings"):
            if getattr(ur.role, perm, False):
                permissions[perm] = True
    if is_admin(user):
        permissions["is_admin"] = True

    return CurrentUser(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        is_active=user.is_active,
        roles=role_names,
        permissions=permissions,
    )
