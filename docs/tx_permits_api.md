# TX Permits Ingestion API

This document describes the implementation of the public TX permit ingest feature that fetches permit data from Texas cities and stores it in Supabase.

## Database Schema

### `public.permits` Table

Created in `/sql/public_permits_setup.sql` with the following structure:

- **Unique constraint**: `(source, source_record_id)` ensures no duplicates
- **Indexes**: Created for optimal query performance on common fields
- **PostGIS support**: Automatic geometry creation from lat/lng coordinates
- **Triggers**: Auto-update geometry and timestamps

### `upsert_permit(jsonb)` Function

SQL RPC function for normalized, idempotent inserts:
- Takes JSONB permit data
- Performs upsert based on `(source, source_record_id)`
- Returns record ID and action ('inserted' or 'updated')
- Handles data type conversion and validation

## API Endpoint

### `POST /api/permits/ingest`

Located at `/frontend/app/api/permits/ingest/route.ts`

**Features:**
- Dynamic rendering (no caching)
- Uses `SUPABASE_SERVICE_ROLE_KEY` for database operations
- Field mapping for different data sources
- Error handling and reporting

**Request Body:**
```json
{
  "source": "austin" | "houston" | "dallas" | "all"
}
```

**Response:**
```json
{
  "success": true,
  "source": "austin",
  "fetched": 100,
  "processed": 100,
  "inserted": 85,
  "updated": 15,
  "errors": ["error messages if any"],
  "timestamp": "2025-01-15T10:00:00.000Z"
}
```

### `GET /api/permits/ingest`

Health check endpoint that returns API information and usage.

## Data Source Integration

### Austin (Socrata API)
- **URL**: `https://data.austintexas.gov/resource/3syk-w9eu.json`
- **Format**: JSON
- **Field Mapping**: Austin-specific field names to normalized schema

### Houston (ArcGIS API)  
- **URL**: ArcGIS REST service endpoint
- **Format**: GeoJSON features
- **Field Mapping**: Houston-specific field names to normalized schema
- **Coordinates**: Includes X/Y coordinates for spatial data

### Dallas (CSV)
- **URL**: Dallas Open Data CSV endpoint  
- **Format**: CSV download
- **Field Mapping**: Dallas-specific field names to normalized schema
- **Note**: CSV parsing logic needs to be implemented

## Environment Variables

Required variables for Vercel deployment:

```bash
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
```

## Testing

Use the test script at `/test_permits_ingest.ts`:

```bash
# Run tests (requires environment variables)
tsx test_permits_ingest.ts
```

Tests include:
- Database table structure validation
- `upsert_permit` function testing
- API endpoint health check

## Usage Examples

### Manual Testing

```bash
# Health check
curl http://localhost:3000/api/permits/ingest

# Ingest Austin permits
curl -X POST http://localhost:3000/api/permits/ingest \
  -H "Content-Type: application/json" \
  -d '{"source": "austin"}'

# Ingest all sources
curl -X POST http://localhost:3000/api/permits/ingest \
  -H "Content-Type: application/json" \
  -d '{"source": "all"}'
```

### Future Implementation

- **Real dataset URLs**: Replace placeholder URLs with actual endpoints
- **API tokens**: Add authentication for data sources that require it
- **Cron jobs**: Set up scheduled ingestion jobs
- **Dashboard integration**: Wire permit metrics to dashboard widgets
- **CSV parsing**: Implement proper CSV parsing for Dallas data

## Architecture Notes

- **Idempotent**: Multiple runs won't create duplicates
- **Incremental**: Only new/changed records are processed
- **Normalized**: Common schema across all Texas cities
- **Spatial**: PostGIS geometry support for location queries
- **Extensible**: Easy to add new Texas cities/counties