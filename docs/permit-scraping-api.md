# Permit Scraping API Documentation

## Overview

The Permit Scraping API endpoint (`/api/permits/scrape`) provides automated data collection from Texas permit data sources including Austin, Houston, and Dallas. The API normalizes data from different sources (Socrata, CSV feeds) into a consistent format and stores it in the `permits_gold` table.

## API Endpoint

**POST** `/api/permits/scrape?source={source}`

### Parameters

- `source` (required): Data source to scrape
  - `austin` - Austin Building Permits (Socrata API)
  - `houston` - Houston Permits (CSV feed) 
  - `dallas` - Dallas Building Permits (Socrata API)

### Response Format

```json
{
  "ok": true,
  "source": "austin",
  "fetched": 1500,
  "upserts": 1450,
  "errors": 50,
  "timestamp": "2025-08-16T07:20:13.227Z"
}
```

### Error Response

```json
{
  "ok": false,
  "error": "Unknown source: invalid_source",
  "timestamp": "2025-08-16T07:20:13.227Z"
}
```

## Data Sources

### 1. Austin Building Permits
- **Source**: Austin Open Data (Socrata)
- **URL**: `https://data.austintexas.gov/resource/3syk-w9eu.json`
- **Format**: JSON API
- **Fields**: permit_number, status_current, description, total_valuation, original_address1, issued_date, latitude, longitude

### 2. Houston Building Permits  
- **Source**: Houston Planning Department
- **URL**: `https://www.houstontx.gov/planning/DevelopReview/permits_issued.csv`
- **Format**: CSV file
- **Fields**: permit_number, permit_type, status, description, valuation, address, issued_date, latitude, longitude

### 3. Dallas Building Permits
- **Source**: Dallas Open Data (Socrata)
- **URL**: `https://www.dallasopendata.com/resource/e7gq-4sah.json`
- **Format**: JSON API
- **Fields**: permit_number, permit_type, permit_status, work_description, estimated_cost, address, issued_date, latitude, longitude

## Normalized Data Structure

All sources are normalized to this common structure:

```typescript
type Normalized = {
  source: string              // Source identifier (austin_socrata, houston_csv, dallas_socrata)
  source_record_id: string    // Original record ID from source
  jurisdiction: string        // City name (Austin, Houston, Dallas)
  county?: string            // County name (Travis, Harris, Dallas)
  permit_no?: string         // Permit number
  permit_type?: string       // Type of permit
  category?: string          // Permit category
  status?: string            // Current status
  description?: string       // Project description
  value?: number             // Project valuation
  address?: string           // Project address
  city?: string              // City name
  state?: string             // State (TX)
  zipcode?: string           // ZIP code
  latitude?: number          // Latitude coordinate
  longitude?: number         // Longitude coordinate
  applied_date?: string      // Application date (ISO string)
  issued_date?: string       // Issue date (ISO string)
  scraped_at?: string        // Scraping timestamp (ISO string)
}
```

## Database Integration

### Table: `permits_gold`

The API uses the `upsert_permit(jsonb)` PostgreSQL function to insert/update permit data with conflict resolution based on `(jurisdiction, permit_id)`.

Key features:
- **Conflict Resolution**: Updates existing records, inserts new ones
- **Data Normalization**: Work type classification using built-in functions
- **Geospatial Support**: Automatic geometry generation from lat/lng
- **Audit Trail**: Tracks created_at, updated_at, scraped_at timestamps

### SQL Function

```sql
-- Usage example
SELECT upsert_permit('{
  "source": "austin_socrata",
  "jurisdiction": "Austin",
  "permit_no": "2024-001234",
  "description": "New construction",
  "value": 350000,
  "address": "123 Main St",
  "latitude": 30.2672,
  "longitude": -97.7431,
  "issued_date": "2024-01-15T00:00:00.000Z"
}'::jsonb);
```

## Usage Examples

### Scrape Austin permits
```bash
curl -X POST "https://your-domain.com/api/permits/scrape?source=austin"
```

### Scrape Houston permits
```bash
curl -X POST "https://your-domain.com/api/permits/scrape?source=houston"
```

### Scrape Dallas permits
```bash
curl -X POST "https://your-domain.com/api/permits/scrape?source=dallas"
```

## Environment Variables

The API requires these environment variables:

```bash
# Required for Supabase integration
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Optional API tokens for rate limiting/authentication
AUSTIN_SOCRATA_TOKEN=your_austin_token
DALLAS_SOCRATA_TOKEN=your_dallas_token
```

## Error Handling

The API handles various error scenarios:

1. **Unknown Source**: Returns 400 with error message
2. **Network Failures**: Returns 500 with fetch error details  
3. **Database Errors**: Logs individual record failures, continues processing
4. **Data Validation**: Handles missing/invalid fields gracefully

## Rate Limiting

- Austin/Dallas (Socrata): 1000 requests/hour recommended
- Houston (CSV): No specific limits, but cache-friendly
- API fetches 2000 records per request by default

## Security

- Uses Supabase service role key for privileged database access
- Service role key bypasses RLS policies for automated data ingestion
- API keys for external sources are optional but recommended

## Monitoring

The API provides detailed response metrics:
- `fetched`: Number of records retrieved from source
- `upserts`: Number of successful database operations
- `errors`: Number of failed operations
- `timestamp`: Processing completion time

Monitor logs for individual record processing errors and overall performance metrics.