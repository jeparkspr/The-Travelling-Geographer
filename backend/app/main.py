import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from PIL import Image

try:
    import pillow_avif  # noqa: F401
except ImportError:
    pass

from app.config import settings
from app.database import init_db
from app.routers import destinations, media, journal, custom_fields, geocoding, search, tags, ai, sharing
from app.routers import auth as auth_router, setup as setup_router, users as users_router
from app.services.auth import get_current_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    print("Starting up The Travelling Geographer API...")
    await init_db()
    os.makedirs(settings.MEDIA_DIR, exist_ok=True)
    print(f"Media directory ready: {settings.MEDIA_DIR}")

    yield

    # Shutdown
    print("Shutting down The Travelling Geographer API...")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware - allow all origins for LAN app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Public routers (no auth required)
app.include_router(auth_router.router, prefix="/api")
app.include_router(setup_router.router, prefix="/api")

# Protected routers (require authentication)
_auth = [Depends(get_current_user)]
app.include_router(destinations.router, prefix="/api", dependencies=_auth)
app.include_router(media.router, prefix="/api", dependencies=_auth)
app.include_router(journal.router, prefix="/api", dependencies=_auth)
app.include_router(journal.bulk_router, prefix="/api", dependencies=_auth)
app.include_router(custom_fields.router, prefix="/api", dependencies=_auth)
app.include_router(geocoding.router, prefix="/api", dependencies=_auth)
app.include_router(search.router, prefix="/api", dependencies=_auth)
app.include_router(tags.router, prefix="/api", dependencies=_auth)
app.include_router(tags.sse_router, prefix="/api")  # SSE endpoints use query-param auth
app.include_router(ai.router, prefix="/api", dependencies=_auth)
app.include_router(users_router.router, prefix="/api", dependencies=_auth)
app.include_router(sharing.router, prefix="/api", dependencies=_auth)

# On-demand thumbnail generation: if a thumb_ file is missing, generate it
# from the original image. This must be defined BEFORE the StaticFiles mount.
@app.get("/media/{rest_of_path:path}")
async def serve_media_with_thumb_fallback(rest_of_path: str):
    """Serve media files, generating thumbnails on-demand if missing."""
    file_path = os.path.join(settings.MEDIA_DIR, rest_of_path)

    # If the file exists, serve it directly
    if os.path.isfile(file_path):
        return FileResponse(file_path)

    # If it's a missing thumbnail, try to generate it
    basename = os.path.basename(rest_of_path)
    if basename.startswith("thumb_"):
        original_name = basename[6:]  # strip "thumb_" prefix
        dir_path = os.path.join(settings.MEDIA_DIR, os.path.dirname(rest_of_path))
        original_path = os.path.join(dir_path, original_name)

        if os.path.isfile(original_path):
            try:
                img = Image.open(original_path)
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")
                img.thumbnail(settings.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                thumb_path = os.path.join(dir_path, basename)
                img.save(thumb_path, "JPEG", quality=85)
                return FileResponse(thumb_path)
            except Exception as e:
                print(f"On-demand thumbnail generation failed: {e}")

    return Response(status_code=404)

# Serve frontend static files if they exist
frontend_dist = "/app/frontend/dist"
if os.path.exists(frontend_dist):
    # Mount static assets (JS, CSS, images) at /assets
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


# SPA catch-all: serve index.html for any non-API route
# This MUST be the last route defined
@app.get("/{full_path:path}")
async def serve_spa(request: Request, full_path: str):
    """Serve the Vue SPA for any path not matched by API routes."""
    # Check if the requested file exists in the dist root (e.g. favicon.png)
    static_file = os.path.join(frontend_dist, full_path)
    if full_path and os.path.isfile(static_file):
        return FileResponse(static_file)
    # Otherwise serve the SPA index
    index_file = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"detail": "Frontend not built"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
