# Travelling Geographer - Quick Start Guide

## Docker Compose Setup (Recommended)

```bash
# From project root
docker compose up -d

# Check logs
docker compose logs -f app
```

The application will be available at `http://localhost:8080`. Migrations run automatically on startup.

## Local Development Setup

### Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL 16 with PostGIS extension

### Step 1: Database

```bash
# Option A: Use Docker for just the database
docker compose up db -d

# Option B: Local PostgreSQL
createdb travelling_geographer
psql travelling_geographer -c "CREATE EXTENSION postgis;"
```

### Step 2: Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env if using non-default PostgreSQL settings

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

Backend will be available at: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Step 3: Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend will be available at `http://localhost:5173` with hot module reloading.

## Testing the API

### Using cURL

```bash
# List destinations
curl http://localhost:8000/api/destinations

# Create destination
curl -X POST http://localhost:8000/api/destinations \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tokyo",
    "country": "Japan",
    "latitude": 35.6762,
    "longitude": 139.6503,
    "status": "suggested"
  }'

# Search
curl "http://localhost:8000/api/search?q=tokyo"

# Geocode
curl "http://localhost:8000/api/geocode?q=Paris"
```

### Using FastAPI Interactive Docs

Navigate to `http://localhost:8000/docs` and use the Swagger UI to test endpoints directly.

## Common Operations

### Upload Media
```bash
curl -X POST http://localhost:8000/api/destinations/{dest_id}/media \
  -F "files=@photo.jpg"
```

### Upload Media from URL
```bash
curl -X POST http://localhost:8000/api/destinations/{dest_id}/media/from-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/image.jpg", "set_as_cover": true}'
```

### Create Journal Entry
```bash
curl -X POST http://localhost:8000/api/destinations/{dest_id}/journal \
  -F "title=Day 1 in Tokyo" \
  -F "body=<p>Amazing experience!</p>" \
  -F "entry_date=2026-06-15" \
  -F "rating=5"
```

### Add Link
```bash
curl -X POST http://localhost:8000/api/destinations/{dest_id}/links \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "title": "Travel Guide",
    "sort_order": 0
  }'
```

### AI Populate
```bash
curl -X POST http://localhost:8000/api/ai/populate \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 35.6762,
    "longitude": 139.6503,
    "location_name": "Tokyo",
    "country": "Japan"
  }'
```

### Export CSV
```bash
curl http://localhost:8000/api/admin/export-csv > destinations.csv
```

### Backup (via browser)
Use the Settings > Backup & Restore tab in the UI. The backup button creates a .tgz archive containing all data and media files with a progress bar.

### Restore (via browser)
Use the Settings > Backup & Restore tab. Select a .tgz backup file and click Restore. Progress is shown via a progress bar.

## Database Schema Overview

```
destinations
  ├─ id (UUID, PK)
  ├─ name
  ├─ description (HTML)
  ├─ status (suggested, researching, want_to_visit, planned, visited, archived)
  ├─ latitude, longitude
  ├─ location (PostGIS geometry)
  ├─ cover_media_id (FK → media)
  ├─ best_season (array: Spring, Summer, Fall, Winter)
  ├─ tags (array)
  ├─ custom_field_values (JSONB)
  └─ timestamps

links (FK → destinations)
  ├─ url, title, description
  └─ sort_order

journal_entries (FK → destinations)
  ├─ title, body (HTML)
  ├─ entry_date, rating

media (FK → destinations OR journal_entries)
  ├─ file_path, file_type, file_size
  └─ thumbnail_path

custom_field_definitions
  ├─ field_name, field_key (unique)
  ├─ field_type (text, number, boolean, date, select, multi_select)
  └─ options (array)

app_settings
  ├─ key (unique), value
  └─ updated_at
```

## Alembic Migrations

```bash
# Check migration status
alembic current

# Apply all migrations
alembic upgrade head

# Downgrade one migration
alembic downgrade -1

# View migration history
alembic history
```

Note: Migrations run automatically when the Docker container starts.

## Troubleshooting

### Port Already in Use
Modify port mappings in `docker-compose.yml`:
```yaml
services:
  app:
    ports:
      - "8081:8000"  # Changed from 8080:8000
```

### Database Connection Error
Check `DATABASE_URL` in `.env`. Format: `postgresql+asyncpg://user:password@localhost/dbname`

### PostGIS Error
```sql
CREATE EXTENSION postgis;
```

### AI Populate Not Working
- Check API key in Settings > AI
- Use Test Connection to verify
- Check container logs: `docker compose logs -f app`
- Model: gemini-2.5-flash (rate limits apply on free tier)

## Documentation Files

- `API_REFERENCE.md` - Detailed API endpoint documentation
- `BACKEND_STRUCTURE.txt` - File structure overview
- `IMPLEMENTATION_SUMMARY.md` - Technical implementation details
- `backend/README.md` - Backend-specific documentation
