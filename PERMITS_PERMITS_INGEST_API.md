# New Permits Ingest API Implementation

This document describes the new nested permits ingest API implemented at `/api/permits/permits/ingest`.

## API Endpoint

**URL:** `/api/permits/permits/ingest`  
**Method:** `POST`  
**Content-Type:** `application/json`

## Query Parameters

- `source` (optional): Data source to fetch from
  - `austin` (default): Austin Socrata API
  - `dallas`: Dallas Socrata API
- `dry` (optional): Dry run mode
  - `1`: Fetch and normalize data without inserting into database
  - `0` or omitted: Fetch and insert data into database

## Features

### Source Key Mapping

The API maps external source keys to internal source identifiers:

```typescript
const SOURCE_KEY: Record<string, string> = {
  austin: 'austin_socrata',
  dallas: 'dallas_socrata',
}
```

### Fetcher Functions

- `fetchAustin()`: Fetches and normalizes Austin permit data
- `fetchDallas()`: Fetches and normalizes Dallas permit data

Both functions return `Normalized[]` arrays with standardized permit data structure.

### Data Processing

1. **Fetch**: Retrieves raw data from the specified source API
2. **Normalize**: Converts raw data to standardized `Normalized` interface
3. **Count Before**: Queries existing permit count for the source
4. **Upsert** (if not dry run): Inserts/updates permits using `upsert_permit(p)` function
5. **Count After**: Queries permit count after processing
6. **Response**: Returns comprehensive processing results

## Response Format

```json
{
  "ok": true,
  "source": "austin_socrata",
  "fetched": 100,
  "dry": false,
  "upserts": 95,
  "beforeCount": 1000,
  "afterCount": 1095,
  "sample": [
    {
      "source": "austin_socrata",
      "source_record_id": "permit_123",
      "permit_number": "2025-001",
      "issued_date": "2025-01-15T10:00:00Z",
      "work_description": "Residential addition",
      "address": "123 Main St",
      "city": "Austin",
      "county": "Travis",
      "valuation": 50000
    }
  ],
  "errors": []
}
```

## Error Handling

- Returns 400 for unknown source parameters
- Returns 500 for processing errors
- Collects and returns first 5 error messages from failed upserts
- Graceful handling of API fetch failures

## Database Integration

### Upsert Function

Uses `upsert_permit(p)` function with parameter `p` containing the normalized permit data:

```sql
SELECT * FROM upsert_permit('{"source": "austin_socrata", "source_record_id": "123", ...}'::jsonb);
```

### Table Structure

Works with the existing `permits` table structure with fields:
- `source`, `source_record_id` (composite key)
- `permit_number`, `issued_date`, `permit_type`
- `work_description`, `address`, `city`, `county`, `zipcode`
- `latitude`, `longitude`, `valuation`, `square_feet`
- `applicant_name`, `contractor_name`, `owner_name`, `status`
- `raw_data` (JSONB), `created_at`, `updated_at`

## Usage Examples

### Dry Run (Austin)
```bash
curl -X POST "http://localhost:3000/api/permits/permits/ingest?source=austin&dry=1"
```

### Live Ingestion (Dallas)
```bash
curl -X POST "http://localhost:3000/api/permits/permits/ingest?source=dallas"
```

### Default Source (Austin)
```bash
curl -X POST "http://localhost:3000/api/permits/permits/ingest?dry=1"
```

## Configuration

### Environment Variables

- `NEXT_PUBLIC_SUPABASE_URL` or `SUPABASE_URL`: Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase service role key (server-side only)
- `DALLAS_APP_TOKEN` (optional): Dallas Open Data API token for higher rate limits

### Runtime Configuration

```typescript
export const runtime = 'nodejs'          // Important for service role
export const dynamic = 'force-dynamic'
export const revalidate = 0
```

## Testing

Use the provided test files:
- `test_new_permits_api.ts`: Basic API endpoint testing
- `test_comprehensive_permits_api.ts`: Full functionality testing including upsert function

## Migration Notes

This implementation:
- Adds a new API endpoint alongside the existing `/api/permits/ingest`
- Requires the `upsert_permit(p)` function variant (see `sql/upsert_permit_p_version.sql`)
- Maintains compatibility with existing permit data structure
- Uses the same external API endpoints as the original implementation