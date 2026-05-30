"""First-run setup wizard API.

GET  /setup/status  → {is_setup_complete, has_users}
POST /setup/initialize  → create admin user + seed roles → TokenResponse
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, Role, UserRole
from app.schemas.user import SetupStatus, SetupRequest, TokenResponse
from app.services.auth import (
    hash_password,
    validate_password,
    create_access_token,
    create_refresh_token,
    store_refresh_token,
    has_any_users,
)
from app.config import settings

router = APIRouter(prefix="/setup", tags=["setup"])


async def _seed_roles(db: AsyncSession) -> dict[str, Role]:
    """Ensure the three system roles exist. Returns {name: Role}."""
    role_defs = [
        {"name": "Administrator", "default_tier": "manage", "is_system": True,  "can_manage_users": True,  "can_manage_settings": True},
        {"name": "User",          "default_tier": "edit",   "is_system": True,  "can_manage_users": False, "can_manage_settings": False},
    ]
    roles = {}
    for rd in role_defs:
        result = await db.execute(select(Role).where(Role.name == rd["name"]))
        role = result.scalar_one_or_none()
        if role is None:
            role = Role(**rd)
            db.add(role)
            await db.flush()
        roles[role.name] = role
    return roles


@router.get("/status", response_model=SetupStatus)
async def setup_status(db: AsyncSession = Depends(get_db)):
    """Check whether the app has been set up (i.e. has at least one user)."""
    has_users = await has_any_users(db)
    return SetupStatus(is_setup_complete=has_users, has_users=has_users)


@router.post("/initialize", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def initialize(body: SetupRequest, db: AsyncSession = Depends(get_db)):
    """Create the first admin account and seed system roles.

    This endpoint can only be called once — it will 409 if users already exist.
    """
    if await has_any_users(db):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Setup already completed — users exist.",
        )

    # Validate password complexity
    pwd_errors = validate_password(body.password)
    if pwd_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet complexity requirements: " + " ".join(pwd_errors),
        )

    # Seed roles
    roles = await _seed_roles(db)

    # Create admin user
    admin = User(
        email=body.email,
        display_name=body.display_name,
        password_hash=hash_password(body.password),
        is_active=True,
        is_approved=True,
    )
    db.add(admin)
    await db.flush()

    # Assign Administrator role
    db.add(UserRole(user_id=admin.id, role_id=roles["Administrator"].id))

    # Issue tokens
    access = create_access_token(admin.id)
    refresh = create_refresh_token()
    await store_refresh_token(db, admin.id, refresh)
    admin.last_login = datetime.now(timezone.utc)

    await db.commit()

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
