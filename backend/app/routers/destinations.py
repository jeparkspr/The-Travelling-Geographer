import os
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.functions import ST_DWithin, ST_GeomFromText

from app.database import get_db
from app.models.destination import Destination, Link
from app.models.media import Media
from app.models.journal import JournalEntry
from pydantic import BaseModel
from app.schemas.destination import (
    DestinationCreate,
    DestinationUpdate,
    DestinationRead,
    DestinationListRead,
    DestinationClip,
    LinkCreate,
    LinkUpdate,
    LinkRead,
)
from app.services.geocoding import geocode, reverse_geocode
from app.services.image_fetcher import fetch_preview_image
from app.services.auth import get_current_user
from app.services.permissions import (
    build_accessible_destinations_query,
    require_destination_access,
    get_user_tier_for_destination,
)
from app.models.user import User, DestinationShare
from app.config import settings

router = APIRouter(prefix="/destinations", tags=["destinations"])


@router.get("", response_model=List[DestinationListRead])
async def list_destinations(
    status_filter: Optional[str] = Query(None, alias="status"),
    country: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    tags: Optional[List[str]] = Query(None),
    priority: Optional[str] = Query(None),
    best_season: Optional[List[str]] = Query(None),
    search: Optional[str] = Query(None),
    min_lat: Optional[float] = Query(None),
    max_lat: Optional[float] = Query(None),
    min_lng: Optional[float] = Query(None),
    max_lng: Optional[float] = Query(None),
    ownership: Optional[str] = Query(None),  # "mine", "shared", or None (all accessible)
    sort_by: str = Query("updated_at"),
    sort_order: str = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[DestinationListRead]:
    """List destinations with filters and pagination. Scoped to owned + shared."""
    query = select(Destination)

    # Scope to accessible destinations (owned + shared)
    access_filter = build_accessible_destinations_query(current_user)
    query = query.where(access_filter)

    # Optional ownership filter
    if ownership == "mine":
        query = query.where(Destination.owner_id == current_user.id)
    elif ownership == "shared":
        query = query.where(Destination.owner_id != current_user.id)

    # Apply filters
    filters = []

    if status_filter:
        filters.append(Destination.status == status_filter)

    if country:
        filters.append(Destination.country.ilike(f"%{country}%"))

    if region:
        filters.append(Destination.region.ilike(f"%{region}%"))

    if city:
        filters.append(Destination.city.ilike(f"%{city}%"))

    if priority:
        filters.append(Destination.priority == priority)

    if tags:
        # Match ANY tag
        for tag in tags:
            filters.append(Destination.tags.contains([tag]))

    if best_season:
        for season in best_season:
            filters.append(Destination.best_season.contains([season]))

    if search:
        # Full-text search on name and description
        search_vector = func.to_tsvector("english", func.concat_ws(" ", Destination.name, Destination.description))
        search_query = func.plainto_tsquery("english", search)
        filters.append(search_vector.match(search_query))

    # Bounding box filter for map
    if min_lat is not None and max_lat is not None and min_lng is not None and max_lng is not None:
        # Create a bounding box polygon and use spatial intersect
        bbox_wkt = f"POLYGON(({min_lng} {min_lat}, {max_lng} {min_lat}, {max_lng} {max_lat}, {min_lng} {max_lat}, {min_lng} {min_lat}))"
        filters.append(
            func.ST_Intersects(
                Destination.location,
                func.ST_GeomFromText(bbox_wkt, 4326)
            )
        )

    if filters:
        query = query.where(and_(*filters))

    # Sort
    sort_column = getattr(Destination, sort_by, Destination.updated_at)
    if sort_order.lower() == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    destinations = result.scalars().all()

    # Batch-fetch share counts for all destinations in one query
    dest_ids = [d.id for d in destinations]
    share_counts = {}
    if dest_ids:
        sc_result = await db.execute(
            select(
                DestinationShare.destination_id,
                func.count().label("cnt"),
            )
            .where(DestinationShare.destination_id.in_(dest_ids))
            .group_by(DestinationShare.destination_id)
        )
        share_counts = {row.destination_id: row.cnt for row in sc_result}

    # Add media and journal counts, thumbnail, and owner info
    response = []
    for dest in destinations:
        media_list = dest.media if dest.media else []
        media_count = len(media_list)
        journal_count = len(dest.journal_entries) if dest.journal_entries else 0

        # Get thumbnail URL — prefer cover_media_id, fall back to first image
        thumbnail_url = None
        cover_media = None
        if dest.cover_media_id:
            cover_media = next((m for m in media_list if m.id == dest.cover_media_id), None)

        # Use cover media if found, otherwise first image
        thumb_source = cover_media
        if not thumb_source:
            thumb_source = next(
                (m for m in media_list if m.file_type and m.file_type.startswith("image/")),
                None,
            )

        if thumb_source:
            if "/media/" in thumb_source.file_path:
                parts = thumb_source.file_path.split("/media/", 1)[1]
                dir_part = parts.rsplit("/", 1)[0] if "/" in parts else ""
                thumbnail_url = f"/media/{dir_part}/thumb_{thumb_source.file_name}"
            else:
                thumbnail_url = f"/media/{dest.id}/thumb_{thumb_source.file_name}"

        # Determine the user's effective permission tier for this destination
        user_tier = await get_user_tier_for_destination(db, current_user, dest)

        dest_dict = DestinationListRead.model_validate(dest).model_dump()
        dest_dict["media_count"] = media_count
        dest_dict["journal_entry_count"] = journal_count
        dest_dict["thumbnail_url"] = thumbnail_url
        dest_dict["owner_id"] = dest.owner_id
        dest_dict["owner_name"] = dest.owner.display_name if dest.owner else None
        dest_dict["permission_tier"] = user_tier
        dest_dict["shared_with_count"] = share_counts.get(dest.id, 0)
        response.append(DestinationListRead(**dest_dict))

    return response


@router.post("", response_model=DestinationRead, status_code=status.HTTP_201_CREATED)
async def create_destination(
    dest_data: DestinationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DestinationRead:
    """Create a new destination."""
    destination = Destination(
        owner_id=current_user.id,
        name=dest_data.name,
        description=dest_data.description,
        status=dest_data.status,
        country=dest_data.country,
        region=dest_data.region,
        city=dest_data.city,
        latitude=dest_data.latitude,
        longitude=dest_data.longitude,
        location=f"SRID=4326;POINT({dest_data.longitude} {dest_data.latitude})",
        address=dest_data.address,
        rating=dest_data.rating,
        cost_estimate=dest_data.cost_estimate,
        cost_actual=dest_data.cost_actual,
        priority=dest_data.priority,
        best_season=dest_data.best_season,
        tags=dest_data.tags,
        custom_field_values=dest_data.custom_field_values,
        date_researched=dest_data.date_researched,
        planned_start_date=dest_data.planned_start_date,
        planned_end_date=dest_data.planned_end_date,
        visited_start_date=dest_data.visited_start_date,
        visited_end_date=dest_data.visited_end_date,
    )

    db.add(destination)
    await db.commit()
    await db.refresh(destination)

    media_count = len(destination.media) if destination.media else 0
    journal_count = len(destination.journal_entries) if destination.journal_entries else 0

    result = DestinationRead.model_validate(destination).model_dump()
    result["media_count"] = media_count
    result["journal_entry_count"] = journal_count

    return DestinationRead(**result)


@router.get("/{dest_id}", response_model=DestinationRead)
async def get_destination(
    dest_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DestinationRead:
    """Get destination details. Requires at least 'view' access."""
    destination = await require_destination_access(dest_id, "view", db, current_user)
    user_tier = await get_user_tier_for_destination(db, current_user, destination)

    media_count = len(destination.media) if destination.media else 0
    journal_count = len(destination.journal_entries) if destination.journal_entries else 0

    dest_dict = DestinationRead.model_validate(destination).model_dump()
    dest_dict["media_count"] = media_count
    dest_dict["journal_entry_count"] = journal_count
    dest_dict["owner_id"] = destination.owner_id
    dest_dict["owner_name"] = destination.owner.display_name if destination.owner else None
    dest_dict["permission_tier"] = user_tier

    return DestinationRead(**dest_dict)


@router.put("/{dest_id}", response_model=DestinationRead)
async def update_destination(
    dest_id: str,
    dest_data: DestinationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DestinationRead:
    """Update destination. Requires at least 'edit' access."""
    destination = await require_destination_access(dest_id, "edit", db, current_user)

    # Update fields
    update_data = dest_data.model_dump(exclude_unset=True)

    # Handle location update
    latitude = update_data.pop("latitude", None)
    longitude = update_data.pop("longitude", None)

    # Fields that can be explicitly cleared (set to None)
    nullable_fields = {
        "rating", "priority", "cost_estimate", "cost_actual",
        "region", "city", "description", "address",
        "date_researched", "planned_start_date", "planned_end_date",
        "visited_start_date", "visited_end_date", "best_season",
        "cover_media_id",
    }

    for key, value in update_data.items():
        if value is not None:
            setattr(destination, key, value)
        elif key in nullable_fields:
            setattr(destination, key, value)

    if latitude is not None or longitude is not None:
        lat = latitude if latitude is not None else destination.latitude
        lon = longitude if longitude is not None else destination.longitude
        destination.latitude = lat
        destination.longitude = lon
        destination.location = f"SRID=4326;POINT({lon} {lat})"

    destination.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(destination)

    media_count = len(destination.media) if destination.media else 0
    journal_count = len(destination.journal_entries) if destination.journal_entries else 0

    dest_dict = DestinationRead.model_validate(destination).model_dump()
    dest_dict["media_count"] = media_count
    dest_dict["journal_entry_count"] = journal_count

    return DestinationRead(**dest_dict)


@router.put("/{dest_id}/cover/{media_id}", response_model=DestinationRead)
async def set_cover_image(
    dest_id: str,
    media_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DestinationRead:
    """Set a media item as the cover image for a destination. Requires 'edit' access."""
    destination = await require_destination_access(dest_id, "edit", db, current_user)

    # Verify media belongs to this destination
    from app.models.media import Media
    media_result = await db.execute(
        select(Media).where(
            (Media.id == media_id) & (Media.destination_id == dest_id)
        )
    )
    media = media_result.scalar_one_or_none()

    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found for this destination")

    destination.cover_media_id = media_id
    destination.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(destination)

    media_count = len(destination.media) if destination.media else 0
    journal_count = len(destination.journal_entries) if destination.journal_entries else 0

    dest_dict = DestinationRead.model_validate(destination).model_dump()
    dest_dict["media_count"] = media_count
    dest_dict["journal_entry_count"] = journal_count

    return DestinationRead(**dest_dict)


@router.delete("/{dest_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_destination(
    dest_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete destination and associated media files. Requires 'manage' access."""
    destination = await require_destination_access(dest_id, "manage", db, current_user)

    # Delete media files from disk
    if destination.media:
        for media in destination.media:
            if os.path.exists(media.file_path):
                try:
                    os.remove(media.file_path)
                except Exception as e:
                    print(f"Error deleting file {media.file_path}: {e}")

    await db.delete(destination)
    await db.commit()


@router.post("/clip", response_model=DestinationRead, status_code=status.HTTP_201_CREATED)
async def create_from_clip(
    clip_data: DestinationClip,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DestinationRead:
    """Create destination from bookmarklet clip (URL + title + description)."""
    # Try to geocode the title if it looks like a place
    geo_results = await geocode(clip_data.title or clip_data.url)
    geo_data = geo_results[0] if geo_results else None

    if geo_data:
        latitude = geo_data["lat"]
        longitude = geo_data["lon"]
        country = geo_data["country"]
        region = geo_data.get("region", "")
        city = geo_data.get("city", "")
    else:
        # Default coordinates (0,0) with a flag
        latitude = 0.0
        longitude = 0.0
        country = ""
        region = ""
        city = ""

    destination = Destination(
        owner_id=current_user.id,
        name=clip_data.title or "Untitled Destination",
        description=clip_data.description,
        status="suggested",
        country=country,
        region=region,
        city=city,
        latitude=latitude,
        longitude=longitude,
        location=f"SRID=4326;POINT({longitude} {latitude})",
        tags=[],
        custom_field_values={},
    )

    db.add(destination)
    await db.flush()

    # Add the source link
    link = Link(
        destination_id=destination.id,
        url=clip_data.url,
        title=clip_data.title,
        sort_order=0,
    )
    db.add(link)

    await db.commit()
    await db.refresh(destination)

    media_count = 0
    journal_count = 0

    result = DestinationRead.model_validate(destination).model_dump()
    result["media_count"] = media_count
    result["journal_entry_count"] = journal_count

    return DestinationRead(**result)


@router.post("/{dest_id}/links", response_model=LinkRead, status_code=status.HTTP_201_CREATED)
async def add_link(
    dest_id: str,
    link_data: LinkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LinkRead:
    """Add a link to a destination. Requires 'contribute' access."""
    destination = await require_destination_access(dest_id, "contribute", db, current_user)

    link = Link(
        destination_id=dest_id,
        url=link_data.url,
        title=link_data.title,
        sort_order=link_data.sort_order,
    )

    db.add(link)
    await db.commit()
    await db.refresh(link)

    return LinkRead.model_validate(link)


@router.put("/{dest_id}/links/{link_id}", response_model=LinkRead)
async def update_link(
    dest_id: str,
    link_id: str,
    link_data: LinkUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LinkRead:
    """Update a link. Requires 'edit' access."""
    await require_destination_access(dest_id, "edit", db, current_user)

    result = await db.execute(
        select(Link).where(
            and_(Link.id == link_id, Link.destination_id == dest_id)
        )
    )
    link = result.scalar_one_or_none()

    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")

    update_data = link_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(link, key, value)

    await db.commit()
    await db.refresh(link)

    return LinkRead.model_validate(link)


@router.delete("/{dest_id}/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(
    dest_id: str,
    link_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a link. Requires 'edit' access."""
    await require_destination_access(dest_id, "edit", db, current_user)
    result = await db.execute(
        select(Link).where(
            and_(Link.id == link_id, Link.destination_id == dest_id)
        )
    )
    link = result.scalar_one_or_none()

    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")

    await db.delete(link)
    await db.commit()


@router.post("/{dest_id}/links/{link_id}/fetch-image", response_model=dict, status_code=status.HTTP_201_CREATED)
async def fetch_link_image(
    dest_id: str,
    link_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Fetch preview image from a link and create Media record. Requires 'contribute' access."""
    await require_destination_access(dest_id, "contribute", db, current_user)

    result = await db.execute(
        select(Link).where(
            and_(Link.id == link_id, Link.destination_id == dest_id)
        )
    )
    link = result.scalar_one_or_none()

    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")

    # Create media directory for destination
    dest_media_dir = os.path.join(settings.MEDIA_DIR, dest_id)
    os.makedirs(dest_media_dir, exist_ok=True)

    # Fetch image
    image_info = await fetch_preview_image(link.url, dest_media_dir)

    if not image_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not fetch image from URL"
        )

    # Create Media record
    media = Media(
        destination_id=dest_id,
        file_path=image_info["file_path"],
        file_name=image_info["file_name"],
        file_type=image_info["file_type"],
        file_size=image_info["file_size"],
        caption=f"Preview from {link.title or link.url}",
    )

    db.add(media)
    await db.commit()
    await db.refresh(media)

    return {
        "id": media.id,
        "file_name": media.file_name,
        "file_size": media.file_size,
        "file_type": media.file_type,
    }


# ─── Bulk Operations ─────────────────────────────────────────────────────────

class BulkEditBody(BaseModel):
    destination_ids: List[str]
    status: Optional[str] = None
    priority: Optional[str] = None
    tags: Optional[List[str]] = None
    tag_mode: Optional[str] = "add"  # "add" or "replace"


class BulkShareBody(BaseModel):
    destination_ids: List[str]
    user_id: str
    permission_tier: str = "view"


class BulkDeleteBody(BaseModel):
    destination_ids: List[str]


async def _get_accessible_destinations(
    dest_ids: List[str],
    required_tier: str,
    db: AsyncSession,
    current_user: User,
) -> List[Destination]:
    """Load destinations by IDs, checking each is accessible at the required tier.
    Returns only those the user has sufficient access to; skips others."""
    access_filter = build_accessible_destinations_query(current_user)
    result = await db.execute(
        select(Destination).where(
            Destination.id.in_(dest_ids),
            access_filter,
        )
    )
    destinations = result.scalars().all()

    # For edit/manage, verify the user's tier on each destination
    accessible = []
    for dest in destinations:
        tier = await get_user_tier_for_destination(dest, current_user, db)
        from app.services.permissions import tier_at_least
        if tier and tier_at_least(tier, required_tier):
            accessible.append(dest)

    return accessible


@router.post("/bulk/edit")
async def bulk_edit_destinations(
    body: BulkEditBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bulk update status, priority, and/or tags for multiple destinations.
    Requires 'edit' tier on each destination. Skips destinations the user
    cannot edit."""
    if not body.destination_ids:
        raise HTTPException(status_code=400, detail="No destinations specified")

    destinations = await _get_accessible_destinations(
        body.destination_ids, "edit", db, current_user
    )

    updated = 0
    for dest in destinations:
        if body.status is not None:
            dest.status = body.status
        if body.priority is not None:
            dest.priority = body.priority
        if body.tags is not None and len(body.tags) > 0:
            if body.tag_mode == "replace":
                dest.tags = list(body.tags)
            else:
                # Add mode — merge without duplicates, preserving order
                existing = list(dest.tags or [])
                for t in body.tags:
                    if t not in existing:
                        existing.append(t)
                dest.tags = existing
        updated += 1

    await db.commit()
    return {"updated": updated, "total_requested": len(body.destination_ids)}


@router.post("/bulk/share")
async def bulk_share_destinations(
    body: BulkShareBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Share multiple destinations with a user at a given permission tier.
    Requires 'manage' tier on each destination. Updates tier if already shared."""
    if not body.destination_ids:
        raise HTTPException(status_code=400, detail="No destinations specified")

    if body.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot share destinations with yourself")

    from app.services.permissions import TIER_ORDER
    if body.permission_tier not in TIER_ORDER:
        raise HTTPException(status_code=400, detail=f"Invalid tier. Must be one of: {', '.join(TIER_ORDER.keys())}")

    # Verify target user exists
    target_result = await db.execute(
        select(User).where(User.id == body.user_id, User.is_active == True)  # noqa: E712
    )
    if not target_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Target user not found")

    destinations = await _get_accessible_destinations(
        body.destination_ids, "manage", db, current_user
    )

    shared = 0
    for dest in destinations:
        # Check if already shared — update tier if so
        existing_result = await db.execute(
            select(DestinationShare).where(
                DestinationShare.destination_id == dest.id,
                DestinationShare.shared_with_id == body.user_id,
            )
        )
        existing = existing_result.scalar_one_or_none()

        if existing:
            existing.permission_tier = body.permission_tier
        else:
            db.add(DestinationShare(
                destination_id=dest.id,
                shared_with_id=body.user_id,
                permission_tier=body.permission_tier,
            ))
        shared += 1

    await db.commit()
    return {"shared": shared, "total_requested": len(body.destination_ids)}


@router.post("/bulk/delete")
async def bulk_delete_destinations(
    body: BulkDeleteBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete multiple destinations. Requires 'manage' tier on each.
    Also removes media files from disk."""
    if not body.destination_ids:
        raise HTTPException(status_code=400, detail="No destinations specified")

    destinations = await _get_accessible_destinations(
        body.destination_ids, "manage", db, current_user
    )

    deleted = 0
    for dest in destinations:
        # Delete media files from disk
        if dest.media:
            for media in dest.media:
                if os.path.exists(media.file_path):
                    try:
                        os.remove(media.file_path)
                    except Exception:
                        pass
        await db.delete(dest)
        deleted += 1

    await db.commit()
    return {"deleted": deleted, "total_requested": len(body.destination_ids)}
