import os
import httpx
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from PIL import Image
import io

from app.config import settings

# Common headers to avoid being blocked by websites
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/*,*/*;q=0.8",
}

# Skip images whose src contains these substrings (icons, tracking pixels, etc.)
SKIP_PATTERNS = [
    "favicon", "icon", "logo", "badge", "avatar", "emoji",
    "1x1", "pixel", "tracking", "spacer", "blank",
    ".svg", ".gif",
    "data:image/svg",
    "data:image/gif",
]


def _is_likely_content_image(src: str) -> bool:
    """Check if an image src looks like a real content image, not an icon or pixel."""
    src_lower = src.lower()
    return not any(pattern in src_lower for pattern in SKIP_PATTERNS)


def _make_absolute_url(image_url: str, base_url: str) -> str:
    """Convert a relative URL to absolute."""
    if image_url.startswith("//"):
        parsed = urlparse(base_url)
        return f"{parsed.scheme}:{image_url}"
    elif image_url.startswith("/"):
        parsed = urlparse(base_url)
        return f"{parsed.scheme}://{parsed.netloc}{image_url}"
    elif not image_url.startswith("http"):
        return f"{base_url.rstrip('/')}/{image_url}"
    return image_url


async def fetch_preview_image(url: str, media_dir: str) -> Optional[Dict[str, Any]]:
    """
    Fetch and save a preview image from a URL.

    Extracts og:image or twitter:image from HTML meta tags,
    or finds the first suitable content image on the page.
    Saves to media_dir, generates thumbnail, and returns file info.

    Args:
        url: URL to fetch
        media_dir: Directory to save image to

    Returns:
        Dict with file_path, file_name, file_type, file_size or None on failure
    """
    try:
        async with httpx.AsyncClient(headers=HEADERS) as client:
            # Fetch the webpage
            response = await client.get(url, timeout=15.0, follow_redirects=True)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")

            # If the URL itself is an image, download it directly
            if content_type.startswith("image/"):
                return await _save_image(response.content, url, media_dir)

            # Parse HTML to find image
            soup = BeautifulSoup(response.content, "html.parser")

            image_url = None

            # 1. Try og:image first (most reliable)
            og_image = soup.find("meta", property="og:image")
            if og_image and og_image.get("content"):
                image_url = og_image["content"]

            # 2. Try twitter:image
            if not image_url:
                twitter_image = soup.find("meta", attrs={"name": "twitter:image"})
                if not twitter_image:
                    twitter_image = soup.find("meta", property="twitter:image")
                if twitter_image and twitter_image.get("content"):
                    image_url = twitter_image["content"]

            # 3. Try first suitable <img> tag (skip icons/pixels)
            if not image_url:
                for img in soup.find_all("img"):
                    img_src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
                    if not img_src:
                        continue
                    if not _is_likely_content_image(img_src):
                        continue
                    # Accept it — we can't reliably check dimensions from HTML alone
                    image_url = img_src
                    break

            if not image_url:
                print(f"No image found on page: {url}")
                return None

            # Make absolute URL
            image_url = _make_absolute_url(image_url, url)

            # Fetch the image
            img_response = await client.get(image_url, timeout=15.0, follow_redirects=True)
            img_response.raise_for_status()

            return await _save_image(img_response.content, image_url, media_dir)

    except Exception as e:
        print(f"Image fetch error for '{url}': {e}")
        return None


async def _save_image(
    image_bytes: bytes, source_url: str, media_dir: str
) -> Optional[Dict[str, Any]]:
    """Save image bytes to disk and generate a thumbnail."""
    try:
        # Open image with Pillow
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")

        # Skip tiny images (likely icons/pixels that slipped through)
        if img.width < 100 or img.height < 100:
            print(f"Skipping small image ({img.width}x{img.height}) from {source_url}")
            return None

        # Generate filename
        parsed_url = urlparse(source_url)
        original_filename = os.path.basename(parsed_url.path)
        if not original_filename or "." not in original_filename:
            original_filename = "preview.jpg"

        filename_base = os.path.splitext(original_filename)[0]
        # Sanitize
        filename_base = "".join(
            c for c in filename_base if c.isalnum() or c in ("-", "_")
        )
        if not filename_base:
            filename_base = "preview"
        filename = f"{filename_base}.jpg"

        # Save full image
        os.makedirs(media_dir, exist_ok=True)
        save_path = os.path.join(media_dir, filename)
        img.save(save_path, "JPEG", quality=85)

        # Generate thumbnail
        thumb = img.copy()
        thumb.thumbnail(settings.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
        thumb_path = os.path.join(media_dir, f"thumb_{filename}")
        thumb.save(thumb_path, "JPEG", quality=85)

        file_size = os.path.getsize(save_path)

        return {
            "file_path": save_path,
            "file_name": filename,
            "file_type": "image/jpeg",
            "file_size": file_size,
        }

    except Exception as e:
        print(f"Image save error: {e}")
        return None
