"""User management endpoints (admin only)."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, Role, UserRole, DestinationShare, BoardShare
from app.models.destination import Destination
from app.models.media import Media
from app.models.journal import JournalEntry
from app.schemas.user import UserCreate, UserUpdate, UserRead, RoleRead
from app.schemas.sharing import ShareableUser
from app.services.auth import (
    get_current_user,
    require_permission,
    hash_password,
    validate_password,
    revoke_all_user_tokens,
)

router = APIRouter(prefix="/users", tags=["users"])


# All endpoints require can_manage_users permission
_require_manage = require_permission("can_manage_users")


def _user_query():
    """Base query that eagerly loads User → UserRole → Role."""
    return select(User).options(
        selectinload(User.roles).selectinload(UserRole.role)
    )


def _is_admin(u: User) -> bool:
    """Check if a user currently has the Admin role."""
    return any(ur.role.name == "Administrator" for ur in (u.roles or []))


async def _count_admins(db: AsyncSession) -> int:
    """Count users who hold the Admin role."""
    result = await db.execute(
        select(func.count())
        .select_from(UserRole)
        .join(Role, UserRole.role_id == Role.id)
        .where(Role.name == "Administrator")
    )
    return result.scalar()


def _serialize_user(u: User) -> UserRead:
    """Convert a User (with loaded roles) to UserRead."""
    return UserRead(
        id=u.id,
        email=u.email,
        display_name=u.display_name,
        is_active=u.is_active,
        is_approved=u.is_approved,
        totp_enabled=u.totp_enabled,
        created_at=u.created_at,
        last_login=u.last_login,
        roles=[RoleRead.model_validate(ur_link.role) for ur_link in (u.roles or [])],
    )


@router.get("", response_model=List[UserRead])
async def list_users(
    _admin: User = Depends(_require_manage),
    db: AsyncSession = Depends(get_db),
):
    """List all users with their roles."""
    result = await db.execute(_user_query().order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [_serialize_user(u) for u in users]


@router.get("/roles", response_model=List[RoleRead])
async def list_roles(
    _admin: User = Depends(_require_manage),
    db: AsyncSession = Depends(get_db),
):
    """List all available roles in hierarchy order (highest first)."""
    ROLE_ORDER = {"Administrator": 0, "User": 1}
    result = await db.execute(select(Role))
    roles = [RoleRead.model_validate(r) for r in result.scalars()]
    roles.sort(key=lambda r: ROLE_ORDER.get(r.name, 99))
    return roles


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    _admin: User = Depends(_require_manage),
    db: AsyncSession = Depends(get_db),
):
    """Admin creates a new user with specified roles."""
    # Validate password complexity
    pwd_errors = validate_password(body.password)
    if pwd_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet complexity requirements: " + " ".join(pwd_errors),
        )

    # Check duplicate
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=body.email,
        display_name=body.display_name,
        password_hash=hash_password(body.password),
        is_active=body.is_active,
        is_approved=body.is_approved,
    )
    db.add(user)
    await db.flush()

    # Assign roles
    for rname in body.role_names:
        role_result = await db.execute(select(Role).where(Role.name == rname))
        role = role_result.scalar_one_or_none()
        if role:
            db.add(UserRole(user_id=user.id, role_id=role.id))

    await db.commit()

    # Re-fetch with eager loading
    result = await db.execute(_user_query().where(User.id == user.id))
    user = result.scalar_one()
    return _serialize_user(user)


@router.get("/shareable", response_model=List[ShareableUser])
async def list_shareable_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ShareableUser]:
    """List all active users (except the current user) for the share picker."""
    result = await db.execute(
        select(User)
        .where(User.is_active == True, User.id != current_user.id)  # noqa: E712
        .order_by(User.display_name)
    )
    users = result.scalars().all()
    return [
        ShareableUser(id=u.id, email=u.email, display_name=u.display_name)
        for u in users
    ]


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: str,
    _admin: User = Depends(_require_manage),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(_user_query().where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _serialize_user(user)


@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: str,
    body: UserUpdate,
    _admin: User = Depends(_require_manage),
    db: AsyncSession = Depends(get_db),
):
    """Update a user's profile, password, roles, or status."""
    result = await db.execute(_user_query().where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if body.email is not None:
        dup = await db.execute(select(User).where(User.email == body.email, User.id != user_id))
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")
        user.email = body.email

    if body.display_name is not None:
        user.display_name = body.display_name

    if body.password is not None:
        pwd_errors = validate_password(body.password)
        if pwd_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password does not meet complexity requirements: " + " ".join(pwd_errors),
            )
        user.password_hash = hash_password(body.password)
        await revoke_all_user_tokens(db, user_id)

    if body.is_active is not None:
        # Prevent deactivating the last admin
        if not body.is_active and _is_admin(user):
            if await _count_admins(db) <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot deactivate the last admin account",
                )
        user.is_active = body.is_active

    if body.is_approved is not None:
        user.is_approved = body.is_approved

    if body.role_names is not None:
        # Prevent removing Admin from the last admin
        if _is_admin(user) and "Administrator" not in body.role_names:
            if await _count_admins(db) <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot remove Admin role from the last admin account",
                )
        # Replace all roles
        for ur_link in list(user.roles or []):
            await db.delete(ur_link)
        await db.flush()
        for rname in body.role_names:
            role_result = await db.execute(select(Role).where(Role.name == rname))
            role = role_result.scalar_one_or_none()
            if role:
                db.add(UserRole(user_id=user.id, role_id=role.id))

    await db.commit()

    # Re-fetch with eager loading
    result = await db.execute(_user_query().where(User.id == user_id))
    user = result.scalar_one()
    return _serialize_user(user)


@router.get("/{user_id}/destination-count")
async def get_user_destination_count(
    user_id: str,
    admin: User = Depends(_require_manage),
    db: AsyncSession = Depends(get_db),
):
    """Get the number of destinations owned by a user (for delete confirmation)."""
    result = await db.execute(
        select(func.count()).select_from(Destination).where(Destination.owner_id == user_id)
    )
    count = result.scalar()
    return {"count": count}


class DeleteUserBody(BaseModel):
    action: str  # "transfer" or "delete"
    transfer_to_user_id: Optional[str] = None


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    body: DeleteUserBody,
    admin: User = Depends(_require_manage),
    db: AsyncSession = Depends(get_db),
):
    """Delete a user, with the choice to transfer or delete their destinations.

    body.action = "transfer": reassign destinations to body.transfer_to_user_id
    body.action = "delete": permanently delete all user's destinations and media
    """
    if user_id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself")

    result = await db.execute(_user_query().where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if _is_admin(user) and await _count_admins(db) <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the last admin account",
        )

    # Handle destinations
    if body.action == "transfer":
        if not body.transfer_to_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="transfer_to_user_id is required when action is 'transfer'",
            )
        if body.transfer_to_user_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot transfer destinations to the user being deleted",
            )
        # Verify target user exists
        target_result = await db.execute(select(User).where(User.id == body.transfer_to_user_id))
        if not target_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer target user not found")

        # Reassign all destinations to the target user
        dest_result = await db.execute(
            select(Destination).where(Destination.owner_id == user_id)
        )
        for dest in dest_result.scalars().all():
            dest.owner_id = body.transfer_to_user_id

        # Clean up destination shares where the deleted user is a collaborator
        await db.execute(
            DestinationShare.__table__.delete().where(
                DestinationShare.shared_with_id == user_id
            )
        )
        # Clean up board shares involving the deleted user (as owner or recipient)
        await db.execute(
            BoardShare.__table__.delete().where(
                (BoardShare.owner_id == user_id) | (BoardShare.shared_with_id == user_id)
            )
        )

        await db.flush()

    elif body.action == "delete":
        # Delete all destinations owned by the user (cascades to media, journals, links, shares)
        dest_result = await db.execute(
            select(Destination).where(Destination.owner_id == user_id)
        )
        for dest in dest_result.scalars().all():
            await db.delete(dest)

        # Clean up shares where deleted user is a collaborator
        await db.execute(
            DestinationShare.__table__.delete().where(
                DestinationShare.shared_with_id == user_id
            )
        )
        await db.execute(
            BoardShare.__table__.delete().where(
                (BoardShare.owner_id == user_id) | (BoardShare.shared_with_id == user_id)
            )
        )

        await db.flush()

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="action must be 'transfer' or 'delete'",
        )

    await db.delete(user)
    await db.commit()
