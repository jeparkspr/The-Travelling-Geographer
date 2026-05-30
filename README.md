# Travelling Geographer

A self-hosted travel destination wishlist and journal application with interactive maps, media management, and AI-powered destination information.

## Features

- Interactive map and list views with advanced filtering
- Rich text descriptions with TipTap editor
- AI-powered destination population via Google Gemini
- Media management with drag-and-drop upload and URL import
- Travel journal entries with ratings
- Custom fields for extensible destination data
- Unified backup and restore (data + media in a single .tgz archive)
- CSV export of destinations
- Web clipper bookmarklet
- Tag management with rename and merge
- Dark theme UI (PrimeVue Aura)

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic
- **Frontend**: Vue 3 (Composition API), Vite 5, PrimeVue 4, Leaflet, TipTap
- **Database**: PostgreSQL 16 + PostGIS
- **AI**: Google Gemini API (gemini-2.5-flash)
- **Deployment**: Docker Compose

## Prerequisites

- Docker and Docker Compose (version 3.9+)
- For development: Node.js 20+ and Python 3.12+

## Quick Start

1. Clone the repository and navigate to the project root:
   ```bash
   cd travelling-geographer-app
   ```

2. Start the application with Docker Compose:
   ```bash
   docker compose up -d
   ```

3. Wait for the services to build and start (typically 2-5 minutes on first run). Check the logs:
   ```bash
   docker compose logs -f app
   ```

4. Open your browser and visit:
   ```
   http://localhost:8080
   ```

Migrations run automatically on container startup.

## Development Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start just the database via Docker
docker compose up db -d

# Run migrations and start the backend
alembic upgrade head
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173` with hot module reloading.

## AI Setup

The app uses Google Gemini to auto-populate destination information (description, tags, best seasons, etc.) from map coordinates.

1. Get a free API key from [Google AI Studio](https://aistudio.google.com/apikey)
2. In the app, go to Settings > AI
3. Paste your API key and click Save Key
4. Use Test Connection to verify it works
5. The AI Populate button will appear on the destination form next to the map

## API Documentation

When the app is running, interactive API documentation is available at:
```
http://localhost:8080/docs
```

See also `API_REFERENCE.md` for a complete endpoint reference.

## Backup & Restore

### Via the UI (recommended)

Go to Settings > Backup & Restore:
- **Backup**: Click the Backup button to download a .tgz archive containing all data and media files. A progress bar shows the status.
- **Restore**: Select a .tgz backup file and click Restore. Progress is shown in real time.
- **Export CSV**: Click Export CSV to download all destinations as a spreadsheet-compatible file.

### Via command line

```bash
# Database backup
docker compose exec db pg_dump -U postgres travelling_geographer > backup.sql

# Database restore
docker compose exec -T db psql -U postgres travelling_geographer < backup.sql
```

## Architecture Overview

- **Backend**: Python FastAPI application handling API routes, database operations, file uploads, and AI integration
- **Frontend**: Vue 3 + Vite single-page application with PrimeVue components
- **Database**: PostgreSQL 16 with PostGIS extension for geospatial queries
- **Media Storage**: Local Docker volume for user-uploaded images and files
- **AI**: Google Gemini API called server-side via httpx, API key stored in database

## Common Commands

```bash
# View logs
docker compose logs -f app      # App logs
docker compose logs -f db       # Database logs

# Stop the application
docker compose down

# Stop and remove all data
docker compose down -v

# Rebuild the application (after code changes)
docker compose build --no-cache
docker compose up -d

# Access the database directly
docker compose exec db psql -U postgres -d travelling_geographer
```

## Troubleshooting

**Port already in use**: If port 8080 or 5432 is already in use, modify the port mappings in `docker-compose.yml`.

**Database connection issues**: Ensure the database healthcheck passes before the app starts:
```bash
docker compose exec db pg_isready -U postgres -d travelling_geographer
```

**AI populate errors**: Check your API key in Settings > AI, and use Test Connection to verify. Rate limits apply on the free tier of Google Gemini.

**Frontend not building**: Clear node_modules and rebuild:
```bash
rm -rf frontend/node_modules
docker compose build --no-cache
```
