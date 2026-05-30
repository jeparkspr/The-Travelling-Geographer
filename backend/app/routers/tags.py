import asyncio
import csv
import json
import io
import os
import re
import tarfile
import tempfile
import uuid as uuid_mod
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import selectinload

from app.config import settings as app_settings
from app.database import get_db
from app.services.auth import decode_access_token, require_permission, get_current_user
from app.services.permissions import build_accessible_destinations_query
from app.models.destination import Destination, Link
from app.models.journal import JournalEntry
from app.models.media import Media
from app.models.custom_field import CustomFieldDefinition
from app.models.media import Media as MediaModel
from app.models.user import User, UserRole, Role

router = APIRouter(prefix="/admin", tags=["admin"])

# Separate router for SSE/download endpoints that can't use Authorization headers.
# These validate auth via query parameter instead of the router-level dependency.
sse_router = APIRouter(prefix="/admin", tags=["admin"])


async def _require_admin_token(token: str, db: AsyncSession):
    """Decode a query-param JWT and verify the user holds the Administrator role.
    Raises 401 for invalid tokens, 403 for non-admin users."""
    payload = decode_access_token(token)  # raises 401 if invalid
    user_id = payload.get("sub")
    result = await db.execute(
        select(User)
        .options(selectinload(User.roles).selectinload(UserRole.role))
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    is_admin = any(ur.role.name == "Administrator" for ur in (user.roles or []))
    if not is_admin:
        raise HTTPException(status_code=403, detail="Administrator access required")
    return user


class TagRenameRequest(BaseModel):
    old_name: str
    new_name: str
    merge: bool = False


@router.get("/tags")
async def get_all_tags(
    db: AsyncSession = Depends(get_db),
) -> Dict[str, int]:
    """Get all unique tags with counts."""
    result = await db.execute(select(Destination))
    destinations = result.scalars().all()

    tag_counts: Dict[str, int] = {}
    for dest in destinations:
        for tag in dest.tags or []:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    return dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True))


@router.put("/tags/rename")
async def rename_tag(
    request: TagRenameRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Rename a tag across all destinations. If merge=False and new_name already
    exists, return a 409 conflict so the frontend can offer to merge."""
    old_name = request.old_name.strip()
    new_name = request.new_name.strip()

    if not old_name or not new_name:
        raise HTTPException(status_code=400, detail="Tag names cannot be empty")

    if old_name == new_name:
        raise HTTPException(status_code=400, detail="New name is the same as the old name")

    result = await db.execute(select(Destination))
    destinations = result.scalars().all()

    # Check if new_name already exists on any destination
    new_name_exists = any(
        new_name in (dest.tags or []) for dest in destinations
    )

    if new_name_exists and not request.merge:
        raise HTTPException(
            status_code=409,
            detail=f'Tag "{new_name}" already exists. Merge?',
        )

    updated_count = 0
    for dest in destinations:
        if not dest.tags or old_name not in dest.tags:
            continue
        # Remove old tag, add new tag (if not already present), deduplicate
        new_tags = [t for t in dest.tags if t != old_name]
        if new_name not in new_tags:
            new_tags.append(new_name)
        dest.tags = new_tags
        dest.updated_at = datetime.utcnow()
        updated_count += 1

    await db.commit()

    return {
        "old_name": old_name,
        "new_name": new_name,
        "merged": new_name_exists,
        "destinations_updated": updated_count,
    }


class TagDeleteRequest(BaseModel):
    tag_name: str


class TagBulkMergeRequest(BaseModel):
    source_tags: List[str]
    target_tag: str


@router.delete("/tags/{tag_name}")
async def delete_tag(
    tag_name: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a tag from all destinations."""
    tag_name = tag_name.strip()
    if not tag_name:
        raise HTTPException(status_code=400, detail="Tag name cannot be empty")

    result = await db.execute(select(Destination))
    destinations = result.scalars().all()

    updated_count = 0
    for dest in destinations:
        if not dest.tags or tag_name not in dest.tags:
            continue
        dest.tags = [t for t in dest.tags if t != tag_name]
        dest.updated_at = datetime.utcnow()
        updated_count += 1

    await db.commit()

    return {
        "tag_name": tag_name,
        "destinations_updated": updated_count,
    }


@router.post("/tags/delete-unused")
async def delete_unused_tags(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete all tags that have 0 destinations.
    Since tags are stored as arrays on destinations, a tag with 0 destinations
    means it doesn't appear in any destination's tags array — so there's nothing
    to actually remove. This endpoint is a no-op structurally but returns the
    count for confirmation. If orphan tags exist in some other form, this handles them."""
    # Tags are stored inline on destinations, so there's no separate tags table.
    # A "tag with 0 destinations" can only exist if we track tags elsewhere.
    # For now, this is a frontend concern — the backend /tags endpoint only
    # returns tags that exist on at least one destination.
    return {"deleted_count": 0, "message": "No orphan tags found"}


@router.post("/tags/bulk-merge")
async def bulk_merge_tags(
    request: TagBulkMergeRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Merge multiple source tags into a single target tag."""
    target = request.target_tag.strip()
    sources = [s.strip() for s in request.source_tags if s.strip()]

    if not target:
        raise HTTPException(status_code=400, detail="Target tag name cannot be empty")
    if not sources:
        raise HTTPException(status_code=400, detail="No source tags provided")

    # Remove target from sources if present (no need to merge a tag into itself)
    sources = [s for s in sources if s != target]
    if not sources:
        raise HTTPException(status_code=400, detail="Source tags must differ from the target tag")

    result = await db.execute(select(Destination))
    destinations = result.scalars().all()

    updated_count = 0
    for dest in destinations:
        if not dest.tags:
            continue
        has_source = any(t in sources for t in dest.tags)
        if not has_source:
            continue
        # Remove all source tags, add target if not present
        new_tags = [t for t in dest.tags if t not in sources]
        if target not in new_tags:
            new_tags.append(target)
        dest.tags = new_tags
        dest.updated_at = datetime.utcnow()
        updated_count += 1

    await db.commit()

    return {
        "source_tags": sources,
        "target_tag": target,
        "destinations_updated": updated_count,
    }


@router.get("/filter-options")
async def get_filter_options(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get unique countries and regions for filter dropdowns."""
    result = await db.execute(select(Destination))
    destinations = result.scalars().all()

    countries = set()
    regions = set()
    for dest in destinations:
        if dest.country and dest.country.strip():
            countries.add(dest.country.strip())
        if dest.region and dest.region.strip():
            regions.add(dest.region.strip())

    return {
        "countries": sorted(countries),
        "regions": sorted(regions),
    }


# In-memory store for completed backup archives (cleaned up after download)
_backup_store: Dict[str, str] = {}  # token -> temp file path


@sse_router.get("/backup-stream")
async def backup_stream(token: str, db: AsyncSession = Depends(get_db)):
    """SSE endpoint with query-param auth (EventSource cannot send headers)."""
    await _require_admin_token(token, db)  # raises 401/403 if invalid or non-admin
    """SSE endpoint: build a unified .tgz archive (data.json + media) and
    stream progress events.

    Events emitted (one JSON object per ``data:`` line):
    - ``{"type":"progress","phase":"<data|media>","files_done":<int>,"total_files":<int>,"current_file":"<name>"}``
    - ``{"type":"done","token":"<uuid>","total_files":<int>,"size_bytes":<int>}``
    - ``{"type":"error","detail":"<message>"}``
    """
    media_dir = app_settings.MEDIA_DIR

    # --- Fetch all data for the JSON export (must happen before the generator
    # because we need the db session which cannot cross async boundaries) ---
    dest_result = await db.execute(select(Destination))
    destinations = dest_result.scalars().all()

    journal_result = await db.execute(select(JournalEntry))
    journal_entries = journal_result.scalars().all()

    media_result = await db.execute(select(MediaModel))
    media_files = media_result.scalars().all()

    field_result = await db.execute(select(CustomFieldDefinition))
    custom_fields = field_result.scalars().all()

    # Build the export dict
    export_data = {
        "version": "1.0",
        "destinations": [],
        "journal_entries": [],
        "media": [],
        "custom_fields": [],
    }
    for dest in destinations:
        export_data["destinations"].append({
            "id": dest.id,
            "name": dest.name,
            "description": dest.description,
            "status": dest.status,
            "country": dest.country,
            "region": dest.region,
            "city": dest.city,
            "latitude": dest.latitude,
            "longitude": dest.longitude,
            "address": dest.address,
            "rating": dest.rating,
            "cost_estimate": str(dest.cost_estimate) if dest.cost_estimate else None,
            "cost_actual": str(dest.cost_actual) if dest.cost_actual else None,
            "priority": dest.priority,
            "best_season": dest.best_season,
            "tags": dest.tags,
            "custom_field_values": dest.custom_field_values,
            "date_added": dest.date_added.isoformat() if dest.date_added else None,
            "date_researched": dest.date_researched.isoformat() if dest.date_researched else None,
            "planned_start_date": dest.planned_start_date.isoformat() if dest.planned_start_date else None,
            "planned_end_date": dest.planned_end_date.isoformat() if dest.planned_end_date else None,
            "visited_start_date": dest.visited_start_date.isoformat() if dest.visited_start_date else None,
            "visited_end_date": dest.visited_end_date.isoformat() if dest.visited_end_date else None,
            "created_at": dest.created_at.isoformat() if dest.created_at else None,
            "updated_at": dest.updated_at.isoformat() if dest.updated_at else None,
            "cover_media_id": dest.cover_media_id,
            "links": [
                {
                    "id": link.id,
                    "url": link.url,
                    "title": link.title,
                    "sort_order": link.sort_order,
                }
                for link in (dest.links or [])
            ],
        })
    for entry in journal_entries:
        export_data["journal_entries"].append({
            "id": entry.id,
            "destination_id": entry.destination_id,
            "title": entry.title,
            "body": entry.body,
            "entry_date": entry.entry_date.isoformat() if entry.entry_date else None,
            "rating": entry.rating,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
            "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
        })
    for media in media_files:
        export_data["media"].append({
            "id": media.id,
            "destination_id": media.destination_id,
            "journal_entry_id": media.journal_entry_id,
            "file_name": media.file_name,
            "file_type": media.file_type,
            "file_size": media.file_size,
            "caption": media.caption,
            "upload_date": media.upload_date.isoformat() if media.upload_date else None,
        })
    for field in custom_fields:
        export_data["custom_fields"].append({
            "id": field.id,
            "field_name": field.field_name,
            "field_key": field.field_key,
            "field_type": field.field_type,
            "options": field.options,
            "sort_order": field.sort_order,
            "created_at": field.created_at.isoformat() if field.created_at else None,
        })

    # Serialize once so the generator doesn't need db
    data_json_bytes = json.dumps(export_data, indent=2).encode("utf-8")

    async def event_generator():
        try:
            # Collect media file list
            all_media_files: List[tuple] = []  # (full_path, arcname)
            if os.path.exists(media_dir):
                for root, _dirs, files in os.walk(media_dir):
                    for fname in files:
                        full_path = os.path.join(root, fname)
                        arcname = os.path.join("media", os.path.relpath(full_path, media_dir))
                        all_media_files.append((full_path, arcname))

            # total = 1 (data.json) + media files
            total = 1 + len(all_media_files)

            # Create temp file for the archive
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".tgz")
            tmp_path = tmp.name
            tmp.close()

            with tarfile.open(tmp_path, mode="w:gz") as tar:
                # 1. Add data.json
                info = tarfile.TarInfo(name="data.json")
                info.size = len(data_json_bytes)
                tar.addfile(info, io.BytesIO(data_json_bytes))

                evt = {
                    "type": "progress",
                    "phase": "data",
                    "files_done": 1,
                    "total_files": total,
                    "current_file": "data.json",
                }
                yield f"data: {json.dumps(evt)}\n\n"
                await asyncio.sleep(0)

                # 2. Add media files
                for idx, (full_path, arcname) in enumerate(all_media_files, 2):
                    tar.add(full_path, arcname=arcname)
                    if idx % max(1, total // 100) == 0 or idx == total:
                        evt = {
                            "type": "progress",
                            "phase": "media",
                            "files_done": idx,
                            "total_files": total,
                            "current_file": os.path.basename(arcname),
                        }
                        yield f"data: {json.dumps(evt)}\n\n"
                        await asyncio.sleep(0)

            # Store the archive and issue a download token
            token = str(uuid_mod.uuid4())
            _backup_store[token] = tmp_path

            size_bytes = os.path.getsize(tmp_path)
            done_evt = {
                "type": "done",
                "token": token,
                "total_files": total,
                "size_bytes": size_bytes,
            }
            yield f"data: {json.dumps(done_evt)}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'detail': str(exc)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@sse_router.get("/backup-download/{token}")
async def backup_download(token: str, auth_token: str = None, db: AsyncSession = Depends(get_db)):
    """Download a completed backup archive by token (query-param auth, admin only)."""
    if not auth_token:
        raise HTTPException(status_code=401, detail="Missing auth token")
    await _require_admin_token(auth_token, db)  # raises 401/403 if invalid or non-admin
    tmp_path = _backup_store.pop(token, None)
    if not tmp_path or not os.path.exists(tmp_path):
        raise HTTPException(status_code=404, detail="Backup not found or already downloaded")

    filename = f"geographer-backup-{datetime.utcnow().strftime('%Y-%m-%d')}.tgz"

    async def stream_and_cleanup():
        try:
            with open(tmp_path, "rb") as f:
                while chunk := f.read(8192):
                    yield chunk
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    return StreamingResponse(
        stream_and_cleanup(),
        media_type="application/gzip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# Store for uploaded restore files (token -> temp path)
_restore_store: Dict[str, str] = {}


_require_admin = require_permission("can_manage_users")


@router.post("/restore-upload")
async def restore_upload(file: UploadFile = File(...), _admin: User = Depends(_require_admin)):
    """Upload a .tgz backup file (admin only). Returns a token to start the SSE restore."""
    fname = (file.filename or "").lower()
    if not fname.endswith(".tgz"):
        raise HTTPException(status_code=400, detail="File must be a .tgz archive")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".tgz")
    tmp.write(await file.read())
    tmp.close()

    token = str(uuid_mod.uuid4())
    _restore_store[token] = tmp.name
    return {"token": token}


@sse_router.get("/restore-stream/{token}")
async def restore_stream(token: str, auth_token: str = None, db: AsyncSession = Depends(get_db)):
    """SSE endpoint with query-param auth (EventSource cannot send headers)."""
    if not auth_token:
        raise HTTPException(status_code=401, detail="Missing auth token")
    await _require_admin_token(auth_token, db)  # raises 401/403 if invalid or non-admin
    """SSE endpoint: restore from an uploaded .tgz and stream progress.

    Events:
    - ``{"type":"progress","phase":"...","files_done":<int>,"total_files":<int>,"current_file":"..."}``
    - ``{"type":"done","message":"..."}``
    - ``{"type":"error","detail":"..."}``
    """
    import mimetypes
    from decimal import Decimal

    tmp_path = _restore_store.pop(token, None)
    if not tmp_path or not os.path.exists(tmp_path):
        async def not_found():
            yield f"data: {json.dumps({'type': 'error', 'detail': 'Upload not found or expired'})}\n\n"
        return StreamingResponse(not_found(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    media_dir = app_settings.MEDIA_DIR
    os.makedirs(media_dir, exist_ok=True)

    # ---- Pre-parse the archive (needs to happen before generator) ----
    try:
        with tarfile.open(tmp_path, mode="r:gz") as tar:
            members = tar.getmembers()

            # Security check
            for member in members:
                if member.name == "data.json":
                    continue
                prefix = "media/" if member.name.startswith("media/") else ""
                rel = member.name[len(prefix):]
                dest_path = os.path.join(media_dir, rel)
                if not os.path.abspath(dest_path).startswith(os.path.abspath(media_dir)):
                    async def unsafe():
                        yield f"data: {json.dumps({'type': 'error', 'detail': 'Archive contains unsafe file paths'})}\n\n"
                    return StreamingResponse(unsafe(), media_type="text/event-stream",
                                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

            # Extract data.json
            data_json = None
            try:
                f = tar.extractfile(tar.getmember("data.json"))
                if f:
                    data_json = json.loads(f.read().decode("utf-8"))
            except KeyError:
                async def no_data():
                    yield f"data: {json.dumps({'type': 'error', 'detail': 'Archive does not contain data.json'})}\n\n"
                return StreamingResponse(no_data(), media_type="text/event-stream",
                                         headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

            # Collect media members
            media_members = [m for m in members if m.name != "data.json" and not m.isdir()]
    except tarfile.TarError as exc:
        async def bad_tar():
            yield f"data: {json.dumps({'type': 'error', 'detail': f'Invalid archive: {str(exc)}'})}\n\n"
        return StreamingResponse(bad_tar(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    # Total steps: 1 (data import) + media file extraction count + 1 (reconciliation)
    total_steps = 1 + len(media_members) + 1

    async def event_generator():
        try:
            step = 0

            # ---- Step 1: Import data.json ----
            imported_count = {
                "destinations": 0, "journal_entries": 0,
                "custom_fields": 0, "links": 0, "media_records": 0,
            }

            if data_json:
                # Custom fields
                for field_data in data_json.get("custom_fields", []):
                    existing = await db.execute(
                        select(CustomFieldDefinition).where(
                            CustomFieldDefinition.field_key == field_data["field_key"]
                        )
                    )
                    if not existing.scalar_one_or_none():
                        db.add(CustomFieldDefinition(
                            field_name=field_data["field_name"],
                            field_key=field_data["field_key"],
                            field_type=field_data["field_type"],
                            options=field_data.get("options"),
                            sort_order=field_data.get("sort_order", 0),
                        ))
                        imported_count["custom_fields"] += 1
                await db.flush()

                # Destinations
                for dest_data in data_json.get("destinations", []):
                    existing = await db.execute(
                        select(Destination).where(Destination.id == dest_data["id"])
                    )
                    if not existing.scalar_one_or_none():
                        lat = dest_data["latitude"]
                        lon = dest_data["longitude"]
                        cost_estimate = None
                        if dest_data.get("cost_estimate"):
                            try:
                                cost_estimate = Decimal(dest_data["cost_estimate"])
                            except Exception:
                                pass
                        cost_actual = None
                        if dest_data.get("cost_actual"):
                            try:
                                cost_actual = Decimal(dest_data["cost_actual"])
                            except Exception:
                                pass
                        db.add(Destination(
                            id=dest_data["id"],
                            name=dest_data["name"],
                            description=dest_data.get("description"),
                            status=dest_data.get("status", "researching"),
                            country=dest_data["country"],
                            region=dest_data.get("region"),
                            city=dest_data.get("city"),
                            latitude=lat, longitude=lon,
                            location=f"SRID=4326;POINT({lon} {lat})",
                            address=dest_data.get("address"),
                            rating=dest_data.get("rating"),
                            cost_estimate=cost_estimate,
                            cost_actual=cost_actual,
                            priority=dest_data.get("priority"),
                            best_season=dest_data.get("best_season"),
                            tags=dest_data.get("tags", []),
                            custom_field_values=dest_data.get("custom_field_values", {}),
                            cover_media_id=dest_data.get("cover_media_id"),
                        ))
                        imported_count["destinations"] += 1
                await db.flush()

                # Links
                for dest_data in data_json.get("destinations", []):
                    for link_data in dest_data.get("links", []):
                        existing = await db.execute(
                            select(Link).where(Link.id == link_data["id"])
                        )
                        if not existing.scalar_one_or_none():
                            db.add(Link(
                                id=link_data["id"],
                                destination_id=dest_data["id"],
                                url=link_data["url"],
                                title=link_data.get("title"),
                                sort_order=link_data.get("sort_order", 0),
                            ))
                            imported_count["links"] += 1
                await db.flush()

                # Journal entries
                for entry_data in data_json.get("journal_entries", []):
                    existing = await db.execute(
                        select(JournalEntry).where(JournalEntry.id == entry_data["id"])
                    )
                    if not existing.scalar_one_or_none():
                        db.add(JournalEntry(
                            id=entry_data["id"],
                            destination_id=entry_data["destination_id"],
                            title=entry_data["title"],
                            body=entry_data.get("body"),
                            rating=entry_data.get("rating"),
                        ))
                        imported_count["journal_entries"] += 1
                await db.flush()

                # Media records from data.json
                for media_data in data_json.get("media", []):
                    existing = await db.execute(
                        select(MediaModel).where(MediaModel.id == media_data["id"])
                    )
                    if not existing.scalar_one_or_none():
                        dest_id = media_data.get("destination_id", "")
                        file_name = media_data["file_name"]
                        file_path = os.path.join(media_dir, dest_id, file_name) if dest_id else os.path.join(media_dir, file_name)
                        db.add(MediaModel(
                            id=media_data["id"],
                            destination_id=media_data.get("destination_id"),
                            journal_entry_id=media_data.get("journal_entry_id"),
                            file_path=file_path,
                            file_name=file_name,
                            file_type=media_data["file_type"],
                            file_size=media_data.get("file_size", 0),
                            caption=media_data.get("caption"),
                        ))
                        imported_count["media_records"] += 1
                await db.flush()

            step = 1
            yield f"data: {json.dumps({'type': 'progress', 'phase': 'data', 'files_done': step, 'total_files': total_steps, 'current_file': 'data.json'})}\n\n"
            await asyncio.sleep(0)

            # ---- Step 2: Extract media files ----
            with tarfile.open(tmp_path, mode="r:gz") as tar:
                for idx, member in enumerate(media_members):
                    if member.name.startswith("media/"):
                        rel_path = member.name[len("media/"):]
                    else:
                        rel_path = member.name
                    dest_path = os.path.join(media_dir, rel_path)
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    src = tar.extractfile(member)
                    if src:
                        with open(dest_path, "wb") as out:
                            out.write(src.read())

                    step = 2 + idx
                    if (idx + 1) % max(1, len(media_members) // 100) == 0 or idx == len(media_members) - 1:
                        yield f"data: {json.dumps({'type': 'progress', 'phase': 'media', 'files_done': step, 'total_files': total_steps, 'current_file': os.path.basename(rel_path)})}\n\n"
                        await asyncio.sleep(0)

            # ---- Step 3: Reconciliation ----
            # Create missing media records for extracted files
            media_created = 0
            for dest_dir_name in os.listdir(media_dir):
                dest_dir_path = os.path.join(media_dir, dest_dir_name)
                if not os.path.isdir(dest_dir_path):
                    continue
                result = await db.execute(
                    select(Destination).where(Destination.id == dest_dir_name)
                )
                if not result.scalar_one_or_none():
                    continue
                for file_name in os.listdir(dest_dir_path):
                    if file_name.startswith("thumb_"):
                        continue
                    file_path = os.path.join(dest_dir_path, file_name)
                    if not os.path.isfile(file_path):
                        continue
                    existing = await db.execute(
                        select(MediaModel).where(
                            MediaModel.destination_id == dest_dir_name,
                            MediaModel.file_name == file_name,
                        )
                    )
                    if existing.scalar_one_or_none():
                        continue
                    file_size = os.path.getsize(file_path)
                    mime_type, _ = mimetypes.guess_type(file_name)
                    if not mime_type:
                        mime_type = "application/octet-stream"
                    db.add(MediaModel(
                        destination_id=dest_dir_name,
                        file_path=file_path,
                        file_name=file_name,
                        file_type=mime_type,
                        file_size=file_size,
                    ))
                    media_created += 1
            await db.flush()

            # Fix orphaned cover_media_id references
            covers_fixed = 0
            dest_result = await db.execute(
                select(Destination).where(Destination.cover_media_id.isnot(None))
            )
            for dest in dest_result.scalars().all():
                cover_check = await db.execute(
                    select(MediaModel).where(MediaModel.id == dest.cover_media_id)
                )
                if cover_check.scalar_one_or_none():
                    continue
                media_q = await db.execute(
                    select(MediaModel).where(
                        MediaModel.destination_id == dest.id,
                        MediaModel.file_type.like("image/%"),
                    )
                )
                first_image = media_q.scalars().first()
                if first_image:
                    dest.cover_media_id = first_image.id
                    dest.updated_at = datetime.utcnow()
                    covers_fixed += 1

            await db.commit()

            yield f"data: {json.dumps({'type': 'progress', 'phase': 'finalize', 'files_done': total_steps, 'total_files': total_steps, 'current_file': 'Finalizing...'})}\n\n"
            await asyncio.sleep(0)

            # Build summary message
            parts = []
            if imported_count["destinations"]:
                parts.append(f"{imported_count['destinations']} destination(s)")
            if imported_count["journal_entries"]:
                parts.append(f"{imported_count['journal_entries']} journal entry(ies)")
            if imported_count["links"]:
                parts.append(f"{imported_count['links']} link(s)")
            total_media = imported_count["media_records"] + media_created
            if total_media:
                parts.append(f"{total_media} media record(s)")
            if covers_fixed:
                parts.append(f"{covers_fixed} cover photo(s) re-assigned")

            msg = "Restore complete."
            if parts:
                msg += " Imported: " + ", ".join(parts) + "."
            else:
                msg += " No new data to import (everything already exists)."

            yield f"data: {json.dumps({'type': 'done', 'message': msg})}\n\n"

        except Exception as exc:
            try:
                await db.rollback()
            except Exception:
                pass
            yield f"data: {json.dumps({'type': 'error', 'detail': str(exc)})}\n\n"
        finally:
            # Clean up the uploaded temp file
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ---- CSV Export ---------------------------------------------------------------

# All available fixed fields for CSV export, in display order
EXPORT_FIELDS = [
    {"key": "id", "label": "ID"},
    {"key": "date_added", "label": "Date Added"},
    {"key": "name", "label": "Name"},
    {"key": "status", "label": "Status"},
    {"key": "country", "label": "Country"},
    {"key": "region", "label": "Region"},
    {"key": "city", "label": "City"},
    {"key": "latitude", "label": "Latitude"},
    {"key": "longitude", "label": "Longitude"},
    {"key": "address", "label": "Address"},
    {"key": "description", "label": "Description"},
    {"key": "rating", "label": "Rating"},
    {"key": "priority", "label": "Priority"},
    {"key": "cost_estimate", "label": "Cost Estimate"},
    {"key": "cost_actual", "label": "Cost Actual"},
    {"key": "best_season", "label": "Best Season"},
    {"key": "tags", "label": "Tags"},
    {"key": "date_researched", "label": "Date Researched"},
    {"key": "planned_start_date", "label": "Planned Start Date"},
    {"key": "planned_end_date", "label": "Planned End Date"},
    {"key": "visited_start_date", "label": "Visited Start Date"},
    {"key": "visited_end_date", "label": "Visited End Date"},
]


@router.get("/export-fields")
async def get_export_fields(db: AsyncSession = Depends(get_db)):
    """Return the list of available fields for CSV export."""
    # Fetch custom field definitions
    cf_result = await db.execute(
        select(CustomFieldDefinition).order_by(CustomFieldDefinition.sort_order)
    )
    custom_fields = cf_result.scalars().all()

    fields = list(EXPORT_FIELDS)
    for cf in custom_fields:
        fields.append({"key": f"cf_{cf.field_key}", "label": cf.field_name})

    return fields


def _get_field_value(dest, key: str, custom_fields_map: dict) -> str:
    """Extract a single field value from a destination for CSV export."""
    if key == "id":
        return dest.id
    elif key == "date_added":
        return dest.date_added.strftime("%Y-%m-%d") if dest.date_added else ""
    elif key == "name":
        return dest.name or ""
    elif key == "status":
        return dest.status or ""
    elif key == "country":
        return dest.country or ""
    elif key == "region":
        return dest.region or ""
    elif key == "city":
        return dest.city or ""
    elif key == "latitude":
        return dest.latitude
    elif key == "longitude":
        return dest.longitude
    elif key == "address":
        return dest.address or ""
    elif key == "description":
        # Strip HTML tags for CSV
        desc = dest.description or ""
        desc = re.sub(r"<[^>]+>", "", desc)
        return desc.strip()
    elif key == "rating":
        return dest.rating if dest.rating is not None else ""
    elif key == "priority":
        return dest.priority or ""
    elif key == "cost_estimate":
        return str(dest.cost_estimate) if dest.cost_estimate is not None else ""
    elif key == "cost_actual":
        return str(dest.cost_actual) if dest.cost_actual is not None else ""
    elif key == "best_season":
        return "; ".join(dest.best_season) if dest.best_season else ""
    elif key == "tags":
        return "; ".join(dest.tags) if dest.tags else ""
    elif key == "date_researched":
        return dest.date_researched.strftime("%Y-%m-%d") if dest.date_researched else ""
    elif key == "planned_start_date":
        return dest.planned_start_date.strftime("%Y-%m-%d") if dest.planned_start_date else ""
    elif key == "planned_end_date":
        return dest.planned_end_date.strftime("%Y-%m-%d") if dest.planned_end_date else ""
    elif key == "visited_start_date":
        return dest.visited_start_date.strftime("%Y-%m-%d") if dest.visited_start_date else ""
    elif key == "visited_end_date":
        return dest.visited_end_date.strftime("%Y-%m-%d") if dest.visited_end_date else ""
    elif key.startswith("cf_"):
        cf_key = key[3:]
        cf_values = dest.custom_field_values or {}
        return cf_values.get(cf_key, "")
    return ""


@router.get("/export-csv")
async def export_csv(
    db: AsyncSession = Depends(get_db),
    fields: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Export the current user's accessible destinations as a CSV file.
    Includes owned destinations and those shared with the user.
    Optionally filter columns via a comma-separated `fields` query parameter."""
    access_filter = build_accessible_destinations_query(current_user)
    result = await db.execute(
        select(Destination).where(access_filter).order_by(Destination.name)
    )
    destinations = result.scalars().all()

    # Fetch custom field definitions
    cf_result = await db.execute(
        select(CustomFieldDefinition).order_by(CustomFieldDefinition.sort_order)
    )
    custom_fields = cf_result.scalars().all()
    cf_map = {cf.field_key: cf for cf in custom_fields}

    # Build the list of all available fields (preserving order)
    all_fields = list(EXPORT_FIELDS)
    for cf in custom_fields:
        all_fields.append({"key": f"cf_{cf.field_key}", "label": cf.field_name})

    # Filter to requested fields if specified
    if fields:
        requested = [f.strip() for f in fields.split(",") if f.strip()]
        requested_set = set(requested)
        # Preserve the order from all_fields but only include requested ones
        selected = [f for f in all_fields if f["key"] in requested_set]
    else:
        # Default: all fields except description
        selected = [f for f in all_fields if f["key"] != "description"]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([f["label"] for f in selected])

    for dest in destinations:
        row = [_get_field_value(dest, f["key"], cf_map) for f in selected]
        writer.writerow(row)

    csv_content = output.getvalue()
    output.close()

    filename = f"destinations-{datetime.now().strftime('%Y-%m-%d')}.csv"
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
