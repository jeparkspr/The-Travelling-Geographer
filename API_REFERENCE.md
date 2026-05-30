# Travelling Geographer - API Reference

## Base URL
`http://localhost:8000/api`

## Destinations

### List Destinations
```
GET /destinations
Query Parameters:
  - status: filtering by suggested|researching|want_to_visit|planned|visited|archived
  - country: filter by country (partial match)
  - region: filter by region (partial match)
  - city: filter by city (partial match)
  - tags: list of tags to filter by (match ANY)
  - priority: low|medium|high|must_do
  - best_season: list of seasons
  - search: full-text search on name+description
  - min_lat, max_lat, min_lng, max_lng: bounding box for map
  - sort_by: field to sort by (updated_at, date_added, rating, etc.)
  - sort_order: asc|desc
  - page: page number (default: 1)
  - page_size: items per page (default: 10, max: 100)

Response: List[DestinationListRead]
```

### Create Destination
```
POST /destinations
Body: DestinationCreate
{
  "name": "Paris",
  "description": "<p>The City of Light</p>",
  "status": "want_to_visit",
  "country": "France",
  "region": "Île-de-France",
  "city": "Paris",
  "latitude": 48.8566,
  "longitude": 2.3522,
  "address": "Paris, France",
  "rating": null,
  "cost_estimate": 2500.00,
  "priority": "high",
  "tags": ["europe", "culture", "museum"],
  "custom_field_values": {},
  "planned_start_date": "2026-06-01",
  "planned_end_date": "2026-06-15"
}

Response: DestinationRead
```

### Get Destination
```
GET /destinations/{id}
Response: DestinationRead (includes links, media count, journal count)
```

### Update Destination
```
PUT /destinations/{id}
Body: DestinationUpdate (all fields optional)
Response: DestinationRead
```

### Delete Destination
```
DELETE /destinations/{id}
Response: 204 No Content (also deletes associated media files)
```

### Create from Bookmarklet
```
POST /destinations/clip
Body: DestinationClip
{
  "url": "https://example.com/travel-guide",
  "title": "Paris Travel Guide",
  "description": "A comprehensive guide to Paris"
}

Response: DestinationRead (auto-geocoded, status=researching)
```

## Links

### Add Link
```
POST /destinations/{dest_id}/links
Body: LinkCreate
{
  "url": "https://booking.com",
  "title": "Hotel Booking",
  "description": "Book accommodation",
  "sort_order": 0
}

Response: LinkRead
```

### Update Link
```
PUT /destinations/{dest_id}/links/{link_id}
Body: LinkUpdate (all optional)
Response: LinkRead
```

### Delete Link
```
DELETE /destinations/{dest_id}/links/{link_id}
Response: 204 No Content
```

### Fetch Preview Image from Link
```
POST /destinations/{dest_id}/links/{link_id}/fetch-image
Response: { "id", "file_name", "file_size", "file_type" }
Creates Media record with the fetched image
```

## Media

### Upload Media
```
POST /destinations/{dest_id}/media
Form Data: files (multipart/form-data)
Supported: images (jpeg, png, gif, webp), videos (mp4, quicktime), pdfs

Response: List[MediaRead]
Features:
  - Auto-generates thumbnails for images
  - Saves to /media/{dest_id}/
  - File size limit: 50MB (configurable)
```

### Upload Media from URL
```
POST /destinations/{dest_id}/media/from-url
Body:
{
  "url": "https://example.com/image.jpg",
  "set_as_cover": true
}

Response: MediaRead
Downloads the image from the URL and saves it as media.
If set_as_cover is true, sets it as the destination's cover image.
```

### List Media
```
GET /destinations/{dest_id}/media
Response: List[MediaRead]
```

### Delete Media
```
DELETE /destinations/media/{id}
Response: 204 No Content (also deletes thumbnail)
```

### Set Cover Image
```
PUT /destinations/{dest_id}/cover/{media_id}
Response: DestinationRead
Sets the specified media as the destination's cover image.
```

## Journal Entries

### Create Journal Entry
```
POST /destinations/{dest_id}/journal
Form Data:
  - title (required): string
  - body (optional): HTML text
  - entry_date (optional): ISO date
  - rating (optional): 1-5
  - files (optional): multipart file upload

Response: JournalEntryRead
```

### List Journal Entries
```
GET /destinations/{dest_id}/journal
Response: List[JournalEntryRead] (ordered by entry_date desc)
```

### Get Journal Entry
```
GET /destinations/{dest_id}/journal/{entry_id}
Response: JournalEntryRead
```

### Update Journal Entry
```
PUT /destinations/{dest_id}/journal/{entry_id}
Body: JournalEntryUpdate (all optional)
Response: JournalEntryRead
```

### Delete Journal Entry
```
DELETE /destinations/{dest_id}/journal/{entry_id}
Response: 204 No Content (also deletes associated media)
```

## Custom Fields

### List Custom Fields
```
GET /custom-fields
Response: List[CustomFieldRead]
```

### Create Custom Field
```
POST /custom-fields
Body: CustomFieldCreate
{
  "field_name": "Visited Duration",
  "field_key": "visited_duration",
  "field_type": "text|number|boolean|date|select|multi_select",
  "options": ["option1", "option2"],  # for select/multi_select
  "sort_order": 0
}

Response: CustomFieldRead
```

### Update Custom Field
```
PUT /custom-fields/{id}
Body: CustomFieldUpdate (all optional)
Response: CustomFieldRead
```

### Delete Custom Field
```
DELETE /custom-fields/{id}
Response: 204 No Content
Also removes the field values from all destinations
```

## Geocoding

### Geocode Address
```
GET /geocode?q=Paris
Response:
{
  "lat": 48.8566,
  "lon": 2.3522,
  "display_name": "Paris, France",
  "country": "France",
  "region": "Île-de-France",
  "city": "Paris"
}
or null if not found
```

### Reverse Geocode
```
GET /geocode/reverse?lat=48.8566&lon=2.3522
Response: Same as geocode response or null
```

## Search

### Full-Text Search
```
GET /search?q=paris+museum
Response: List of results
[
  {
    "id": "uuid",
    "title": "Paris",
    "type": "destination|journal_entry",
    "status": "visited",
    "location": "Paris, France",
    "destination_id": "uuid",
    "destination": "Paris",
    "relevance": 0.8
  }
]
```

## Admin

### Get All Tags with Counts
```
GET /admin/tags
Response:
{
  "europe": 15,
  "culture": 12,
  "museum": 8,
  ...
}
Sorted by count descending
```

### Rename Tag
```
PUT /admin/tags/rename
Body:
{
  "old_name": "europe",
  "new_name": "Europe",
  "merge": false
}

Response: { "status": "ok", "updated": 5 }
If merge=false and the new name already exists, returns 409 Conflict.
Set merge=true to merge both tags into the new name.
```

### Get Filter Options
```
GET /admin/filter-options
Response:
{
  "countries": ["France", "Japan", ...],
  "regions": ["Europe", "Asia", ...]
}
Returns distinct values for filter dropdowns.
```

### Unified Backup (SSE)
```
GET /admin/backup-stream
Response: Server-Sent Events (text/event-stream)

Events:
  - { "type": "progress", "files_done": 3, "total_files": 10, "current_file": "media/uuid/photo.jpg" }
  - { "type": "done", "token": "abc123", "total_files": 10 }
  - { "type": "error", "detail": "..." }

Creates a unified .tgz archive containing data.json (all destinations,
journal entries, media metadata, custom fields, links) and all media files.
```

### Download Backup Archive
```
GET /admin/backup-download/{token}
Response: application/gzip (.tgz file)

Downloads the archive created by backup-stream using the provided token.
```

### Upload Restore Archive
```
POST /admin/restore-upload
Form Data: file (.tgz archive)
Response: { "token": "abc123" }

Uploads the backup archive and returns a token for the restore stream.
```

### Restore from Archive (SSE)
```
GET /admin/restore-stream/{token}
Response: Server-Sent Events (text/event-stream)

Events:
  - { "type": "progress", "files_done": 3, "total_files": 10, "current_file": "Importing destinations..." }
  - { "type": "done", "message": "Restore complete: 5 destinations, 12 journal entries, 8 media files" }
  - { "type": "error", "detail": "..." }

Restores data and media from the uploaded .tgz archive.
Three phases: data import, media file extraction, reconciliation.
```

### Export CSV
```
GET /admin/export-csv
Response: text/csv

Downloads all destinations as a CSV file. Columns include:
ID, Date Added, Name, Status, Country, Region, City, Latitude, Longitude,
Address, Rating, Priority, Cost Estimate, Cost Actual, Best Season, Tags,
Date Researched, Planned Start Date, Planned End Date, Visited Start Date,
Visited End Date, plus any custom field columns.

Multi-value fields (Best Season, Tags) use "; " as separator.
Description is excluded.
```

## AI

### Get AI Settings
```
GET /ai/settings
Response:
{
  "gemini_api_key_set": true,
  "ai_prompt_template": "Provide travel information about..."
}
The API key value is never returned, only whether one is configured.
```

### Update AI Settings
```
PUT /ai/settings
Body:
{
  "gemini_api_key": "AIza...",           // optional
  "ai_prompt_template": "Your prompt..." // optional, empty string resets to default
}
Response: { "status": "ok" }
```

### Test AI Connection
```
POST /ai/test-connection
Response:
{
  "success": true,
  "message": "Connection successful"
}
Tests the stored Gemini API key with a simple request.
```

### AI Populate Destination
```
POST /ai/populate
Body:
{
  "latitude": 48.8566,
  "longitude": 2.3522,
  "location_name": "Eiffel Tower",
  "country": "France"
}

Response:
{
  "name": "Eiffel Tower",
  "country": "France",
  "region": "Europe",
  "city": "Paris",
  "description": "Overview\n\nThe Eiffel Tower is...\n\nSafety\n\n...",
  "tags": ["Iconic Landmark", "Architecture", "Romance"],
  "best_season": ["Spring", "Fall"]
}

Uses Google Gemini (gemini-2.5-flash) to generate destination details
from coordinates. The prompt template is configurable in AI settings.
```

## Data Types

### DestinationCreate/Update
```json
{
  "name": "string (required)",
  "description": "HTML string (optional)",
  "status": "suggested|researching|want_to_visit|planned|visited|archived",
  "country": "string (required)",
  "region": "string (optional)",
  "city": "string (optional)",
  "latitude": "float (required)",
  "longitude": "float (required)",
  "address": "string (optional)",
  "rating": "integer 1-5 (optional)",
  "cost_estimate": "decimal (optional)",
  "cost_actual": "decimal (optional)",
  "priority": "low|medium|high|must_do (optional)",
  "best_season": "array of: Spring|Summer|Fall|Winter (optional)",
  "tags": "array of strings",
  "custom_field_values": "object {}",
  "date_researched": "ISO datetime (optional)",
  "planned_start_date": "ISO date (optional)",
  "planned_end_date": "ISO date (optional)",
  "visited_start_date": "ISO date (optional)",
  "visited_end_date": "ISO date (optional)"
}
```

### DestinationRead (also includes)
```json
{
  "id": "uuid",
  "created_at": "ISO datetime",
  "updated_at": "ISO datetime",
  "date_added": "ISO datetime",
  "links": "List[LinkRead]",
  "media_count": "integer",
  "journal_entry_count": "integer"
}
```

## Status Codes

- `200 OK` - Success
- `201 Created` - Resource created
- `204 No Content` - Deletion successful
- `400 Bad Request` - Invalid input
- `404 Not Found` - Resource not found
- `413 Payload Too Large` - File upload exceeds limit
- `500 Internal Server Error` - Server error

## Error Response
```json
{
  "detail": "Error message"
}
```

## Notes

- All times are in UTC (timezone-aware)
- UUIDs are strings (not objects)
- Decimals for currency fields
- Full-text search uses PostgreSQL's tsvector
- Spatial queries supported for bounding box filtering
- Media files served from `/media/{dest_id}/{filename}`
- Thumbnails auto-generated at 400x400 for images

