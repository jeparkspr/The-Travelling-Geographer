import os
from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from PIL import Image

from app.database import get_db
from app.models.destination import Destination
from app.models.user import User
from app.models.journal import JournalEntry
from app.models.media import Media
from app.schemas.journal import JournalEntryCreate, JournalEntryUpdate, JournalEntryRead, JournalEntryWithDestination
from app.services.auth import get_current_user
from app.services.permissions import require_destination_access, build_accessible_destinations_query
from app.config import settings

router = APIRouter(prefix="/destinations", tags=["journal"])
bulk_router = APIRouter(prefix="/journal", tags=["journal"])


@router.post("/{dest_id}/journal", response_model=JournalEntryRead, status_code=status.HTTP_201_CREATED)
async def create_journal_entry(
    dest_id: str,
    title: str = Form(...),
    body: str = Form(None),
    entry_date: str = Form(None),
    rating: int = Form(None),
    files: List[UploadFile] = File(default=[]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JournalEntryRead:
    """Create journal entry with optional media uploads. Requires 'contribute' access."""
    destination = await require_destination_access(dest_id, "contribute", db, current_user)

    # Parse entry_date if provided
    entry_date_obj = None
    if entry_date:
        try:
            entry_date_obj = datetime.fromisoformat(entry_date).date()
        except ValueError:
            pass

    entry = JournalEntry(
        destination_id=dest_id,
        title=title,
        body=body,
        entry_date=entry_date_obj,
        rating=rating,
    )

    db.add(entry)
    await db.flush()

    # Handle media uploads
    if files:
        dest_media_dir = os.path.join(settings.MEDIA_DIR, dest_id, "journal")
        os.makedirs(dest_media_dir, exist_ok=True)

        for file in files:
            content = await file.read()

            if len(content) > settings.MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File too large (max {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB)"
                )

            allowed_types = {
                "image/jpeg", "image/png", "image/gif", "image/webp",
                "video/mp4", "video/quicktime",
                "application/pdf",
            }
            if file.content_type not in allowed_types:
                continue

            file_name = file.filename or "upload"
            file_name = "".join(c for c in file_name if c.isalnum() or c in (".", "-", "_"))

            file_path = os.path.join(dest_media_dir, file_name)

            with open(file_path, "wb") as f:
                f.write(content)

            # Generate thumbnail for images
            if file.content_type.startswith("image/"):
                try:
                    img = Image.open(file_path)
                    if img.mode in ("RGBA", "LA", "P"):
                        img = img.convert("RGB")
                    img.thumbnail(settings.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)

                    thumb_name = f"thumb_{file_name}"
                    thumb_path = os.path.join(dest_media_dir, thumb_name)
                    img.save(thumb_path, "JPEG", quality=85)
                except Exception as e:
                    print(f"Thumbnail generation error: {e}")

            media = Media(
                journal_entry_id=entry.id,
                file_path=file_path,
                file_name=file_name,
                file_type=file.content_type,
                file_size=len(content),
            )
            db.add(media)

    await db.commit()
    await db.refresh(entry)

    return JournalEntryRead.model_validate(entry)


@router.get("/{dest_id}/journal", response_model=List[JournalEntryRead])
async def list_journal_entries(
    dest_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[JournalEntryRead]:
    """List journal entries for a destination. Requires 'view' access."""
    await require_destination_access(dest_id, "view", db, current_user)

    result = await db.execute(
        select(JournalEntry)
        .where(JournalEntry.destination_id == dest_id)
        .order_by(JournalEntry.entry_date.desc())
    )
    entries = result.scalars().all()

    return [JournalEntryRead.model_validate(e) for e in entries]


@router.get("/{dest_id}/journal/{entry_id}", response_model=JournalEntryRead)
async def get_journal_entry(
    dest_id: str,
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JournalEntryRead:
    """Get a specific journal entry. Requires 'view' access."""
    await require_destination_access(dest_id, "view", db, current_user)

    result = await db.execute(
        select(JournalEntry).where(
            (JournalEntry.id == entry_id) & (JournalEntry.destination_id == dest_id)
        )
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found")

    return JournalEntryRead.model_validate(entry)


@router.put("/{dest_id}/journal/{entry_id}", response_model=JournalEntryRead)
async def update_journal_entry(
    dest_id: str,
    entry_id: str,
    entry_data: JournalEntryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JournalEntryRead:
    """Update journal entry. Requires 'edit' access."""
    await require_destination_access(dest_id, "edit", db, current_user)
    result = await db.execute(
        select(JournalEntry).where(
            (JournalEntry.id == entry_id) & (JournalEntry.destination_id == dest_id)
        )
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found")

    update_data = entry_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(entry, key, value)

    entry.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(entry)

    return JournalEntryRead.model_validate(entry)


@router.delete("/{dest_id}/journal/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_journal_entry(
    dest_id: str,
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete journal entry and associated media. Requires 'edit' access."""
    await require_destination_access(dest_id, "edit", db, current_user)
    result = await db.execute(
        select(JournalEntry).where(
            (JournalEntry.id == entry_id) & (JournalEntry.destination_id == dest_id)
        )
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found")

    # Delete media files
    if entry.media:
        for media in entry.media:
            if os.path.exists(media.file_path):
                try:
                    os.remove(media.file_path)
                except Exception as e:
                    print(f"Error deleting file {media.file_path}: {e}")

    await db.delete(entry)
    await db.commit()


@bulk_router.get("/all", response_model=List[JournalEntryWithDestination])
async def get_all_journal_entries(
    statuses: str = "planned,visited,archived",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[JournalEntryWithDestination]:
    """Get all journal entries across accessible destinations, optionally filtered by status."""
    status_list = [s.strip() for s in statuses.split(",") if s.strip()]

    accessible_filter = build_accessible_destinations_query(current_user)

    # Step 1: Get accessible destinations with matching statuses
    dest_query = select(Destination.id, Destination.name, Destination.status).where(
        accessible_filter
    )
    if status_list:
        dest_query = dest_query.where(Destination.status.in_(status_list))

    dest_result = await db.execute(dest_query)
    dest_rows = dest_result.all()
    dest_map = {d_id: (d_name, d_status) for d_id, d_name, d_status in dest_rows}
    dest_ids = list(dest_map.keys())

    if not dest_ids:
        return []

    # Step 2: Get journal entries for those destinations (proper ORM load with media)
    entries_result = await db.execute(
        select(JournalEntry)
        .where(JournalEntry.destination_id.in_(dest_ids))
        .options(selectinload(JournalEntry.media))
        .order_by(JournalEntry.entry_date.desc())
    )
    journal_entries = entries_result.scalars().all()

    # Step 3: Build response with destination info
    entries = []
    for entry in journal_entries:
        dest_name, dest_status = dest_map.get(entry.destination_id, ("Unknown", "unknown"))
        entry_dict = JournalEntryRead.model_validate(entry).model_dump()
        entry_dict["destination_name"] = dest_name
        entry_dict["destination_status"] = dest_status
        entries.append(JournalEntryWithDestination(**entry_dict))

    return entries
