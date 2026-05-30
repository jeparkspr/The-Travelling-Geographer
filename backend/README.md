# Travelling Geographer Backend

FastAPI-based backend for the Travelling Geographer travel destination wishlist and journal app.

## Tech Stack

- Python 3.12
- FastAPI 0.115.0
- SQLAlchemy 2.0 (async)
- PostgreSQL 16 + PostGIS
- Alembic for migrations
- Pillow for image processing
- httpx for async HTTP requests

## Setup

### Prerequisites

- Python 3.12+
- PostgreSQL 16 with PostGIS extension
- asyncpg for async PostgreSQL driver

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

## API Structure

### Destinations
- `GET /api/destinations` - List destinations with filters
- `POST /api/destinations` - Create destination
- `GET /api/destinations/{id}` - Get destination details
- `PUT /api/destinations/{id}` - Update destination
- `DELETE /api/destinations/{id}` - Delete destination
- `POST /api/destinations/clip` - Create from bookmarklet
- `POST /api/destinations/{id}/links` - Add link
- `PUT /api/destinations/{id}/links/{link_id}` - Update link
- `DELETE /api/destinations/{id}/links/{link_id}` - Delete link
- `POST /api/destinations/{id}/links/{link_id}/fetch-image` - Fetch preview image

### Media
- `POST /api/destinations/{id}/media` - Upload media
- `POST /api/destinations/{id}/media/from-url` - Upload media from URL
- `GET /api/destinations/{id}/media` - List media
- `DELETE /api/destinations/media/{id}` - Delete media
- `PUT /api/destinations/{id}/cover/{media_id}` - Set cover image

### Journal Entries
- `POST /api/destinations/{id}/journal` - Create journal entry
- `GET /api/destinations/{id}/journal` - List journal entries
- `GET /api/destinations/{id}/journal/{entry_id}` - Get journal entry
- `PUT /api/destinations/{id}/journal/{entry_id}` - Update journal entry
- `DELETE /api/destinations/{id}/journal/{entry_id}` - Delete journal entry

### Custom Fields
- `GET /api/custom-fields` - List all custom fields
- `POST /api/custom-fields` - Create custom field
- `PUT /api/custom-fields/{id}` - Update custom field
- `DELETE /api/custom-fields/{id}` - Delete custom field

### Geocoding
- `GET /api/geocode?q=...` - Geocode address
- `GET /api/geocode/reverse?lat=...&lon=...` - Reverse geocode

### Search
- `GET /api/search?q=...` - Full-text search

### Admin
- `GET /api/admin/tags` - Get all tags with counts
- `PUT /api/admin/tags/rename` - Rename or merge tags
- `GET /api/admin/filter-options` - Get unique countries/regions for filters
- `GET /api/admin/backup-stream` - Unified backup via SSE (data + media → .tgz)
- `GET /api/admin/backup-download/{token}` - Download completed backup archive
- `POST /api/admin/restore-upload` - Upload .tgz for restore
- `GET /api/admin/restore-stream/{token}` - Restore from archive via SSE
- `GET /api/admin/export-csv` - Export destinations as CSV

### AI
- `GET /api/ai/settings` - Get AI settings (key masked)
- `PUT /api/ai/settings` - Update API key and/or prompt template
- `POST /api/ai/test-connection` - Test Gemini API connection
- `POST /api/ai/populate` - AI-populate destination fields from coordinates

## Database Schema

### Destinations
Main entity storing travel destination information with geographic coordinates.

### Links
URLs associated with destinations (travel guides, booking sites, etc).

### Journal Entries
Travel journal entries for each destination with optional media.

### Media
Images, videos, and documents associated with destinations or journal entries.

### Custom Field Definitions
User-defined fields for destinations (text, number, boolean, date, select, multi-select).

## Features

- Full-text search across destinations and journal entries
- Spatial queries for bounding box filtering
- Media management with automatic thumbnail generation
- Custom field definitions for extensibility
- Data import/export functionality
- Nominatim geocoding integration
- Image preview fetching from URLs

## Configuration

Settings are loaded from environment variables via `pydantic-settings`:

- `DATABASE_URL`: PostgreSQL connection string
- `MEDIA_DIR`: Directory for storing uploaded media
- `NOMINATIM_URL`: Nominatim API endpoint
- `APP_NAME`: Application display name
- `MAX_UPLOAD_SIZE`: Maximum file upload size (bytes)
- `THUMBNAIL_SIZE`: Thumbnail dimensions tuple

## Development

### Running migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Downgrade one migration
alembic downgrade -1
```

### Database Console

```bash
psql postgresql://postgres:postgres@localhost/travelling_geographer
```

## Production

For production deployment:
1. Use a proper ASGI server (Gunicorn + Uvicorn)
2. Configure environment variables for database and storage
3. Run migrations: `alembic upgrade head`
4. Set up reverse proxy (nginx)
5. Enable HTTPS
6. Configure CORS appropriately
