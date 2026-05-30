# Travelling Geographer - Implementation Summary

## Project Overview

A complete, full-stack travel destination wishlist and journal application. Built with a FastAPI async backend, Vue 3 frontend, PostgreSQL with PostGIS, and Google Gemini AI integration. Deployed via Docker Compose as a self-hosted, single-user application.

## What Was Built

### Backend Core Framework
- **config.py** - Pydantic settings with environment-based configuration
- **database.py** - Async SQLAlchemy setup with AsyncSession factory
- **main.py** - FastAPI app with all routers, CORS, static file serving, lifespan management

### Database Models (6)
1. **destination.py** - Main Destination model with 20+ fields
   - Geographic support via PostGIS Point geometry
   - Status tracking (suggested → researching → planned → visited → archived)
   - Cost estimation and actual tracking
   - Priority and seasonal info (title-case: Spring, Summer, Fall, Winter)
   - Custom field support via JSONB
   - Cover image support (cover_media_id)
   - Full-text search indexes
   - Relationships to Links, Media, JournalEntries

2. **media.py** - Media file management
   - Support for images, videos, documents
   - FK to both Destination and JournalEntry
   - File metadata and thumbnail tracking

3. **journal.py** - Travel journal entries
   - Linked to specific destination
   - Date-based entries with ratings
   - Associated media support

4. **custom_field.py** - User-extensible field definitions
   - Support for text, number, boolean, date, select, multi_select types
   - Sort order configuration

5. **app_settings.py** - Application settings
   - Key-value store for AI configuration
   - Default AI prompt template with 4 sections (Overview, Safety, Food, Best Time to Visit)

### Services (2)
1. **geocoding.py** - Nominatim API integration
   - Forward geocoding (address → coordinates)
   - Reverse geocoding (coordinates → address)
   - Async httpx with proper User-Agent

2. **image_fetcher.py** - Image fetching service
   - og:image extraction from HTML
   - Fallback to img tags
   - JPEG conversion and optimization

### API Routers (8 - 55+ endpoints)

1. **destinations.py** (16 endpoints)
   - LIST with 10+ filters and full-text search
   - CRUD operations
   - Bounding box spatial filtering
   - Link management (add/update/delete)
   - Image preview fetching from links
   - Bookmarklet clip capture
   - Cover image selection

2. **media.py** (5 endpoints)
   - Multi-file upload with validation
   - Upload from URL with optional auto-cover
   - Automatic thumbnail generation
   - List and delete with cleanup

3. **journal.py** (5 endpoints)
   - Journal entry CRUD
   - Inline media uploads
   - Date-based retrieval

4. **custom_fields.py** (4 endpoints)
   - Field definition management
   - Automatic cleanup on deletion

5. **geocoding.py** (2 endpoints)
   - Forward and reverse geocoding proxy

6. **search.py** (1 endpoint)
   - Full-text search across destinations and journal entries
   - Relevance ranking

7. **tags.py** (8 endpoints)
   - Tag aggregation with counts
   - Tag rename and merge
   - Filter options (unique countries/regions)
   - Unified backup via SSE (data + media → .tgz archive)
   - Backup download (token-based)
   - Restore upload + SSE progress stream
   - CSV export of all destinations

8. **ai.py** (4 endpoints)
   - AI settings management (API key, prompt template)
   - Test Gemini API connection
   - AI populate destination from coordinates using Google Gemini (gemini-2.5-flash)
   - JSON response parsing with newline fixing and truncation detection

### Database Migrations (5)
1. **001_initial.py** - Complete initial schema (5 tables, 12 indexes)
2. **002_add_cover_media_id.py** - Cover image support for destinations
3. **003_rename_noted_to_suggested.py** - Rename 'noted' status to 'suggested'
4. **004_add_app_settings.py** - App settings table for AI configuration
5. **005_titlecase_seasons.py** - Convert season values to title-case + update saved prompt

### Frontend (Vue 3)

**Views:**
- **DestinationList.vue** - Card grid with filtering sidebar, pagination
- **DestinationDetail.vue** - Tabbed detail view (Info, Media, Journal, Links)
- **DestinationForm.vue** - Create/edit form with AI populate button, map picker
- **MapView.vue** - Interactive Leaflet map with filtering
- **Settings.vue** - 6-tab settings page (General, Custom Fields, Tags, Backup & Restore, AI, Bookmarklet)

**Components:**
- **MapComponent.vue** - Reusable Leaflet map
- **FilterSidebar.vue** - Multi-criteria filter panel
- **RichTextEditor.vue** - TipTap editor with formatting toolbar
- **LinkManager.vue** - Link CRUD with preview image fetching

**Composables:**
- **useApi.js** - Axios client with all API methods
- **useGeocoding.js** - Geocoding utility

**Stores (Pinia):**
- **destinations.js** - Destinations state and filtering
- **customFields.js** - Custom field definitions
- **settings.js** - UI preferences (show archived, show toasts, filter states)

## Key Features

### AI Integration
- Google Gemini (gemini-2.5-flash) for destination information
- Configurable prompt template with placeholders ({location_name}, {country}, {latitude}, {longitude})
- AI populate button on destination form generates: name, country, region, city, description (4 sections with headings), tags, best seasons
- Plain text to HTML conversion for TipTap editor (headings → `<h3>`, paragraphs → `<p>`)
- JSON response parsing with literal newline fixing, code fence stripping, truncation detection
- API key stored securely in database, never returned to frontend

### Unified Backup & Restore
- Single backup button creates .tgz archive containing data.json + media/ folder
- SSE (Server-Sent Events) for real-time progress during backup and restore
- Two-phase restore: upload file → SSE stream processing with progress bar
- Includes all data: destinations (with links, cover_media_id), journal entries, media metadata, custom fields
- Reconciliation phase fixes orphaned cover references

### CSV Export
- Exports all destinations to CSV (excludes description)
- Columns: ID, Date Added, Name, Status, Country, Region, City, Latitude, Longitude, Address, Rating, Priority, Cost Estimate, Cost Actual, Best Season, Tags, dates, plus custom field columns
- Multi-value fields use "; " separator

### Media Management
- Multi-file upload with drag-and-drop
- Upload from URL (paste or type)
- Automatic thumbnail generation
- Cover image selection per destination
- Images served from /media/{dest_id}/

## Technical Stack

| Component | Technology |
|-----------|------------|
| Backend Framework | FastAPI 0.115.0 |
| ORM | SQLAlchemy 2.0 (async) |
| Database Driver | asyncpg 0.30.0 |
| Database | PostgreSQL 16 + PostGIS |
| Migrations | Alembic 1.13.0 |
| Validation | Pydantic 2.9.0 |
| HTTP Client | httpx 0.27.0 |
| Image Processing | Pillow 11.0.0 |
| Configuration | pydantic-settings 2.5.0 |
| HTML Parsing | BeautifulSoup4 4.12.3 |
| AI | Google Gemini API (gemini-2.5-flash) |
| Frontend Framework | Vue 3 (Composition API) |
| Build Tool | Vite 5 |
| UI Library | PrimeVue 4 (Aura dark theme) |
| Maps | Leaflet + vue-leaflet |
| Rich Text | TipTap |
| State Management | Pinia |
| HTTP Client (FE) | Axios |
| Server | Uvicorn 0.30.0 |
| Deployment | Docker Compose |

## Database Schema

### Tables (6)
1. **destinations** (20+ fields) - Core travel destination data with PostGIS geometry
2. **links** (5 fields) - Resource URLs for destinations
3. **journal_entries** (8 fields) - Travel journal entries
4. **media** (9 fields) - File references with thumbnails
5. **custom_field_definitions** (6 fields) - User-defined field definitions
6. **app_settings** (4 fields) - Key-value application settings

## Deployment

Docker Compose creates two containers:
- **tg-app**: Frontend (built at container build time) + Backend (uvicorn)
- **tg-db**: PostgreSQL 16 with PostGIS

Migrations run automatically on container startup via the Dockerfile CMD.

```bash
docker compose up -d
# App available at http://localhost:8080
```
