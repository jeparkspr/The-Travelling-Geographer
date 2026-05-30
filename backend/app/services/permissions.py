"""Central permission checking service implementing the authorization waterfall.

Tier hierarchy (each includes all capabilities below it):
    view < contribute < edit < manage

Waterfall order:
    1. Admin? → manage on all destinations + system privileges
    2. Owner? → manage
    3. destination_share exists? → use that tier
    4. board_share from owner? → use that tier
    5. Role default_tier? → own destinations only
    6. None → deny (403)

When both a destination_share and board_share exist, the higher tier wins.
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.destination import Destination
from app.models.user import User, BoardShare, DestinationShare
from app.services.auth import get_current_user, is_admin

# Tier ordering — higher index = more permissions
TIER_ORDER = {"view": 0, "contribute": 1, "edit": 2, "manage": 3}


def tier_value(tier: str) -> int:
    """Return numeric value for a tier string (higher = more access)."""
    return TIER_ORDER.get(tier, -1)


def tier_at_least(user_tier: str, required_tier: str) -> bool:
    """Check whether user_tier meets or exceeds required_tier."""
    return tier_value(user_tier) >= tier_value(required_tier)


def highest_tier(*tiers: Optional[str]) -> Optional[str]:
    """Return the highest tier from the given values, ignoring None."""
    valid = [t for t in tiers if t and t in TIER_ORDER]
    if not valid:
        return None
    return max(valid, key=tier_value)


async def get_user_tier_for_destination(
    db: AsyncSession,
    user: User,
    destination: Destination,
) -> Optional[str]:
    """Determine the effective permission tier a user has on a destination.

    Returns the tier string or None if access is denied.
    """
    # 1. Admin → manage
    if is_admin(user):
        return "manage"

    # 2. Owner → manage
    if destination.owner_id == user.id:
        return "manage"

    # 3. Check destination_share
    dest_share_result = await db.execute(
        select(DestinationShare.permission_tier).where(
            DestinationShare.destination_id == destination.id,
            DestinationShare.shared_with_id == user.id,
        )
    )
    dest_tier = dest_share_result.scalar_one_or_none()

    # 4. Check board_share (from the destination's owner)
    board_share_result = await db.execute(
        select(BoardShare.permission_tier).where(
            BoardShare.owner_id == destination.owner_id,
            BoardShare.shared_with_id == user.id,
        )
    )
    board_tier = board_share_result.scalar_one_or_none()

    # Use the highest of the two share tiers
    share_tier = highest_tier(dest_tier, board_tier)
    if share_tier:
        return share_tier

    # 5. No sharing relationship → deny
    return None


async def require_destination_access(
    dest_id: str,
    required_tier: str,
    db: AsyncSession,
    user: User,
) -> Destination:
    """Load a destination and verify the user has at least the required tier.

    Returns the Destination if access is granted; raises 403 or 404 otherwise.
    """
    result = await db.execute(
        select(Destination).where(Destination.id == dest_id)
    )
    destination = result.scalar_one_or_none()

    if not destination:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Destination not found",
        )

    user_tier = await get_user_tier_for_destination(db, user, destination)

    if user_tier is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this destination",
        )

    if not tier_at_least(user_tier, required_tier):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Requires at least '{required_tier}' permission (you have '{user_tier}')",
        )

    return destination


def build_accessible_destinations_query(user: User):
    """Build a WHERE clause that filters destinations to those the user can access.

    Returns a list of SQLAlchemy filter conditions to be used with and_/or_.

    For admins: own destinations + shared destinations (not all users').
    For regular users: own destinations + shared via destination_share or board_share.
    """
    user_id = user.id

    # Owned by the user
    owned = Destination.owner_id == user_id

    # Shared via destination_shares
    dest_shared = Destination.id.in_(
        select(DestinationShare.destination_id).where(
            DestinationShare.shared_with_id == user_id
        )
    )

    # Shared via board_shares (all destinations from users who shared their board)
    board_shared = Destination.owner_id.in_(
        select(BoardShare.owner_id).where(
            BoardShare.shared_with_id == user_id
        )
    )

    return or_(owned, dest_shared, board_shared)
