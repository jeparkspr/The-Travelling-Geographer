import os
import hashlib
from datetime import datetime
from typing import List
from urllib.parse import urlparse, unquote

import httpx
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from PIL import Image
import io

# Enable AVIF support in Pillow
try:
    import pillow_avif  # noqa: F401
except ImportError:
    pass

from app.database import get_db
from app.models.destination import Destination
from app.models.media import Media
from app.models.user import User
from app.schemas.media import MediaRead
from app.services.auth import get_current_user
from app.services.permissions import require_destination_access
from app.config import settings

router = APIRouter(prefix="/destinations", tags=["media"])


@router.post("/{dest_id}/media", response_model=List[MediaRead], status_code=status.HTTP_201_CREATED)
async def upload_media(
    dest_id: str,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[MediaRead]:
    """Upload media files to a destination. Requires 'contribute' access."""
    destination = await require_destination_access(dest_id, "contribute", db, current_user)

    # Create media directory for destination
    dest_media_dir = os.path.join(settings.MEDIA_DIR, dest_id)
    os.makedirs(dest_media_dir, exist_ok=True)

    created_media = []

    for file in files:
        # Check file size
        content = await file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large (max {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB)"
            )

        # Validate file type
        allowed_types = {
            "image/jpeg", "image/png", "image/gif", "image/webp", "image/avif",
            "video/mp4", "video/quicktime",
            "application/pdf",
        }
        actual_content_type = file.content_type
        if actual_content_type not in allowed_types:
            # Try to detect image type from content using PIL
            try:
                img_check = Image.open(io.BytesIO(content))
                fmt = img_check.format
                type_map = {"JPEG": "image/jpeg", "PNG": "image/png", "GIF": "image/gif", "WEBP": "image/webp", "AVIF": "image/avif", "BMP": "image/bmp"}
                detected = type_map.get(fmt, "")
                if detected in allowed_types or fmt in ("BMP",):
                    # Accept it as an image — convert BMP/unknown to JPEG
                    actual_content_type = detected if detected in allowed_types else "image/jpeg"
                else:
                    raise ValueError("Not a supported image")
            except Exception as pil_err:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File type {file.content_type} not allowed"
                )

        # Save file
        file_name = file.filename or "upload"
        # Sanitize filename
        file_name = "".join(c for c in file_name if c.isalnum() or c in (".", "-", "_"))

        file_path = os.path.join(dest_media_dir, file_name)

        # Convert webp/avif to JPEG before saving
        if actual_content_type in ("image/webp", "image/avif"):
            try:
                img = Image.open(io.BytesIO(content))
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")
                buf = io.BytesIO()
                img.save(buf, "JPEG", quality=90)
                content = buf.getvalue()
                actual_content_type = "image/jpeg"
                base = os.path.splitext(file_name)[0]
                file_name = base + ".jpg"
                file_path = os.path.join(dest_media_dir, file_name)
                with open(file_path, "wb") as f:
                    f.write(content)
            except Exception as e:
                print(f"Image conversion error, saving as-is: {e}")
                with open(file_path, "wb") as f:
                    f.write(content)
        else:
            with open(file_path, "wb") as f:
                f.write(content)

        # Generate thumbnail for images
        if actual_content_type.startswith("image/"):
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

        # Create Media record
        media = Media(
            destination_id=dest_id,
            file_path=file_path,
            file_name=file_name,
            file_type=actual_content_type,
            file_size=len(content),
        )

        db.add(media)
        created_media.append(media)

    await db.commit()

    # Refresh to get IDs
    for media in created_media:
        await db.refresh(media)

    return [MediaRead.model_validate(m) for m in created_media]


@router.get("/{dest_id}/media", response_model=List[MediaRead])
async def list_destination_media(
    dest_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[MediaRead]:
    """List media for a destination. Requires 'view' access."""
    await require_destination_access(dest_id, "view", db, current_user)

    result = await db.execute(
        select(Media).where(Media.destination_id == dest_id)
    )
    media_list = result.scalars().all()

    return [MediaRead.model_validate(m) for m in media_list]


@router.delete("/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(
    media_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete media file and record. Requires 'edit' access on the destination."""
    result = await db.execute(
        select(Media).where(Media.id == media_id)
    )
    media = result.scalar_one_or_none()

    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found")

    # Check permission on the parent destination
    if media.destination_id:
        await require_destination_access(media.destination_id, "edit", db, current_user)

    # Delete file from disk
    if os.path.exists(media.file_path):
        try:
            os.remove(media.file_path)
        except Exception as e:
            print(f"Error deleting file {media.file_path}: {e}")

    # Delete thumbnail if it exists
    thumb_name = f"thumb_{media.file_name}"
    thumb_path = os.path.dirname(media.file_path)
    thumb_full_path = os.path.join(thumb_path, thumb_name)
    if os.path.exists(thumb_full_path):
        try:
            os.remove(thumb_full_path)
        except Exception as e:
            print(f"Error deleting thumbnail {thumb_full_path}: {e}")

    await db.delete(media)
    await db.commit()


class UrlUploadRequest(BaseModel):
    url: str
    set_as_cover: bool = True


@router.post("/{dest_id}/media/from-url", response_model=MediaRead, status_code=status.HTTP_201_CREATED)
async def upload_media_from_url(
    dest_id: str,
    body: UrlUploadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MediaRead:
    """Download an image from a URL, save it as media, and optionally set as cover. Requires 'contribute' access."""
    destination = await require_destination_access(dest_id, "contribute", db, current_user)

    # Download the image with browser-like headers to avoid blocks
    try:
        # Use the image's own origin as referer (some CDNs block cross-origin)
        parsed_url = urlparse(body.url)
        referer = f"{parsed_url.scheme}://{parsed_url.netloc}/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "image/jpeg,image/png,image/webp,image/*;q=0.8,*/*;q=0.5",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": referer,
        }
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            resp = await client.get(body.url, headers=headers)
            # If origin referer fails, retry with google referer
            if resp.status_code in (401, 403):
                headers["Referer"] = "https://www.google.com/"
                resp = await client.get(body.url, headers=headers)
            resp.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to download image from URL: {e}"
        )

    content = resp.content
    content_type = resp.headers.get("content-type", "").split(";")[0].strip()
    # Validate it's an image
    allowed_image_types = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/avif"}
    if content_type not in allowed_image_types:
        # Try to detect from content using PIL
        try:
            img_check = Image.open(io.BytesIO(content))
            fmt = img_check.format
            type_map = {"JPEG": "image/jpeg", "PNG": "image/png", "GIF": "image/gif", "WEBP": "image/webp", "AVIF": "image/avif"}
            content_type = type_map.get(fmt, "")
            if content_type not in allowed_image_types:
                raise ValueError(f"PIL detected format: {fmt}")
        except Exception as pil_err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"URL does not point to a supported image (got {content_type})"
            )

    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image too large (max {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB)"
        )

    # Derive filename from URL
    parsed = urlparse(body.url)
    url_filename = os.path.basename(unquote(parsed.path)) or "image"
    # Sanitize
    url_filename = "".join(c for c in url_filename if c.isalnum() or c in (".", "-", "_"))
    if not url_filename or url_filename == "image":
        # Generate a name from a hash of the URL
        ext_map = {"image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif", "image/webp": ".webp", "image/avif": ".avif"}
        ext = ext_map.get(content_type, ".jpg")
        url_filename = hashlib.md5(body.url.encode()).hexdigest()[:12] + ext

    # Save file
    dest_media_dir = os.path.join(settings.MEDIA_DIR, dest_id)
    os.makedirs(dest_media_dir, exist_ok=True)

    # Convert webp/avif to JPEG before saving
    if content_type in ("image/webp", "image/avif"):
        try:
            img = Image.open(io.BytesIO(content))
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")
            buf = io.BytesIO()
            img.save(buf, "JPEG", quality=90)
            content = buf.getvalue()
            content_type = "image/jpeg"
            # Update filename extension
            base = os.path.splitext(url_filename)[0]
            url_filename = base + ".jpg"
        except Exception as e:
            print(f"Image conversion error, saving as-is: {e}")

    file_path = os.path.join(dest_media_dir, url_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    # Generate thumbnail
    try:
        img = Image.open(file_path)
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")
        img.thumbnail(settings.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
        thumb_name = f"thumb_{url_filename}"
        thumb_path = os.path.join(dest_media_dir, thumb_name)
        img.save(thumb_path, "JPEG", quality=85)
    except Exception as e:
        print(f"Thumbnail generation error: {e}")

    # Create Media record
    media = Media(
        destination_id=dest_id,
        file_path=file_path,
        file_name=url_filename,
        file_type=content_type,
        file_size=len(content),
    )
    db.add(media)
    await db.flush()

    # Optionally set as cover
    if body.set_as_cover:
        destination.cover_media_id = media.id
        destination.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(media)

    return MediaRead.model_validate(media)
