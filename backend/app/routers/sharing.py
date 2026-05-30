"""Sharing endpoints for destinations and boards.

Destination sharing:  POST/GET/DELETE  /destinations/{dest_id}/share
Board sharing:        POST/GET/DELETE  /board/share
User lookup:          GET              /users/shareable
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.destination import Destination
from app.models.user import User, BoardShare, DestinationShare
from app.schemas.sharing import (
    DestinationShareCreate,
    DestinationShareRead,
    BoardShareCreate,
    BoardShareRead,
)
from app.services.auth import get_current_user, is_admin
from app.services.permissions import (
    require_destination_access,
    get_user_tier_for_destination,
    TIER_ORDER,
)

router = APIRouter(tags=["sharing"])


# ─── Destination Sharing ───────────────────────────────────────────────────────

@router.get("/destinations/{dest_id}/share", response_model=List[DestinationShareRead])
async def list_destination_shares(
    dest_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[DestinationShareRead]:
    """List all users a destination is shared with. Requires at least 'manage' tier."""
    await require_destination_access(dest_id, "manage", db, current_user)

    result = await db.execute(
        select(DestinationShare, User)
        .join(User, DestinationShare.shared_with_id == User.id)
        .where(DestinationShare.destination_id == dest_id)
        .order_by(User.display_name)
    )
    rows = result.all()

    return [
        DestinationShareRead(
            id=share.id,
            destination_id=share.destination_id,
            shared_with_id=share.shared_with_id,
            shared_with_name=user.display_name,
            shared_with_email=user.email,
            permission_tier=share.permission_tier,
            created_at=share.created_at,
        )
        for share, user in rows
    ]


@router.post("/destinations/{dest_id}/share", response_model=DestinationShareRead, status_code=status.HTTP_201_CREATED)
async def share_destination(
    dest_id: str,
    share_data: DestinationShareCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DestinationShareRead:
    """Share a destination with another user. Requires 'manage' tier."""
    destination = await require_destination_access(dest_id, "manage", db, current_user)

    # Validate tier
    if share_data.permission_tier not in TIER_ORDER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid permission tier. Must be one of: {', '.join(TIER_ORDER.keys())}",
        )

    # Cannot share with yourself
    if share_data.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot share a destination with yourself",
        )

    # Verify target user exists
    target_result = await db.execute(
        select(User).where(User.id == share_data.user_id, User.is_active == True)  # noqa: E712
    )
    target_user = target_result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check if already shared — update tier if so
    existing_result = await db.execute(
        select(DestinationShare).where(
            DestinationShare.destination_id == dest_id,
            DestinationShare.shared_with_id == share_data.user_id,
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        existing.permission_tier = share_data.permission_tier
        await db.commit()
        await db.refresh(existing)
        share = existing
    else:
        share = DestinationShare(
            destination_id=dest_id,
            shared_with_id=share_data.user_id,
            permission_tier=share_data.permission_tier,
        )
        db.add(share)
        await db.commit()
        await db.refresh(share)

    return DestinationShareRead(
        id=share.id,
        destination_id=share.destination_id,
        shared_with_id=share.shared_with_id,
        shared_with_name=target_user.display_name,
        shared_with_email=target_user.email,
        permission_tier=share.permission_tier,
        created_at=share.created_at,
    )


@router.delete("/destinations/{dest_id}/share/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_destination_share(
    dest_id: str,
    share_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a destination share. Requires 'manage' tier."""
    await require_destination_access(dest_id, "manage", db, current_user)

    result = await db.execute(
        select(DestinationShare).where(
            DestinationShare.id == share_id,
            DestinationShare.destination_id == dest_id,
        )
    )
    share = result.scalar_one_or_none()
    if not share:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share not found")

    await db.delete(share)
    await db.commit()


# ─── Board Sharing ─────────────────────────────────────────────────────────────

@router.get("/board/share", response_model=List[BoardShareRead])
async def list_board_shares(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[BoardShareRead]:
    """List all board shares the current user has created (shared their board with others)."""
    result = await db.execute(
        select(BoardShare, User)
        .join(User, BoardShare.shared_with_id == User.id)
        .where(BoardShare.owner_id == current_user.id)
        .order_by(User.display_name)
    )
    rows = result.all()

    return [
        BoardShareRead(
            id=share.id,
            owner_id=share.owner_id,
            owner_name=current_user.display_name,
            shared_with_id=share.shared_with_id,
            shared_with_name=user.display_name,
            shared_with_email=user.email,
            permission_tier=share.permission_tier,
            created_at=share.created_at,
        )
        for share, user in rows
    ]


@router.post("/board/share", response_model=BoardShareRead, status_code=status.HTTP_201_CREATED)
async def share_board(
    share_data: BoardShareCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BoardShareRead:
    """Share the current user's entire board with another user."""
    # Validate tier
    if share_data.permission_tier not in TIER_ORDER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid permission tier. Must be one of: {', '.join(TIER_ORDER.keys())}",
        )

    # Cannot share with yourself
    if share_data.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot share your board with yourself",
        )

    # Verify target user exists
    target_result = await db.execute(
        select(User).where(User.id == share_data.user_id, User.is_active == True)  # noqa: E712
    )
    target_user = target_result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check if already shared — update tier if so
    existing_result = await db.execute(
        select(BoardShare).where(
            BoardShare.owner_id == current_user.id,
            BoardShare.shared_with_id == share_data.user_id,
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        existing.permission_tier = share_data.permission_tier
        await db.commit()
        await db.refresh(existing)
        share = existing
    else:
        share = BoardShare(
            owner_id=current_user.id,
            shared_with_id=share_data.user_id,
            permission_tier=share_data.permission_tier,
        )
        db.add(share)
        await db.commit()
        await db.refresh(share)

    return BoardShareRead(
        id=share.id,
        owner_id=share.owner_id,
        owner_name=current_user.display_name,
        shared_with_id=share.shared_with_id,
        shared_with_name=target_user.display_name,
        shared_with_email=target_user.email,
        permission_tier=share.permission_tier,
        created_at=share.created_at,
    )


@router.delete("/board/share/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_board_share(
    share_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a board share. Only the board owner can remove it."""
    result = await db.execute(
        select(BoardShare).where(
            BoardShare.id == share_id,
            BoardShare.owner_id == current_user.id,
        )
    )
    share = result.scalar_one_or_none()
    if not share:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board share not found")

    await db.delete(share)
    await db.commit()


# Note: GET /users/shareable lives in the users router to avoid
# being shadowed by the /users/{user_id} catch-all route.
