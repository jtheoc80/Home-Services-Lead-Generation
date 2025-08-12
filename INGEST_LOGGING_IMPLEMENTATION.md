# Ingest Logging Implementation Summary

This document summarizes the implementation of ingest logging functionality for the Home Services Lead Generation system.

## Problem Statement

Add public.ingest_logs(id bigserial pk, created_at timestamptz default now(), trace_id uuid, stage text, ok boolean, details jsonb) and an API route /api/leads/trace/[id] (protected by X-Debug-Key) that returns all rows for a trace.

In the scraper and API, log a row on every critical step ("fetch_page", "parse", "upsert", "db_insert").

## Implementation Overview

### 1. Database Schema ✅
The `ingest_logs` table was already defined in `docs/supabase/ingest_logs_table.sql`:

```sql
create table if not exists public.ingest_logs (
    id bigserial primary key,
    trace_id uuid not null,
    stage text not null,
    ok boolean not null,
    details jsonb,
    created_at timestamptz not null default now()
);
```

### 2. Ingest Logger Module ✅
Created `backend/app/ingest_logger.py` with:

- **`log_ingest_step(trace_id, stage, ok, details)`** - Core logging function
- **`generate_trace_id()`** - Generate UUID4 trace IDs
- **`get_trace_logs(trace_id)`** - Retrieve logs for a trace
- **`IngestTracer`** - Context manager for automatic trace logging

#### Usage Examples:

```python
# Direct logging
from app.ingest_logger import log_ingest_step
log_ingest_step(trace_id, "fetch_page", True, {"url": "example.com", "records": 50})

# Context manager
from app.ingest_logger import IngestTracer
with IngestTracer() as tracer:
    tracer.log("fetch_page", True, {"url": "example.com"})
    tracer.log("parse", True, {"records_parsed": 45})
```

### 3. API Endpoint ✅
Added `/api/leads/trace/{trace_id}` endpoint in `backend/main.py`:

- **Authentication**: Protected by X-Debug-Key header
- **Response**: JSON with trace_id, logs array, and total_logs count
- **Error handling**: 401 for invalid keys, 500 for database errors

#### Usage:
```bash
curl -H "X-Debug-Key: your-debug-key" \
     http://localhost:8000/api/leads/trace/123e4567-e89b-12d3-a456-426614174000
```

### 4. Scraper Integration ✅
Modified `permit_leads/scrapers/base.py`:

- Added trace logging to `scrape_permits()` method
- Logs "fetch_page" and "parse" stages automatically
- Graceful fallback if logging dependencies unavailable

#### Usage:
```python
scraper = HoustonCityScraper()
permits = scraper.scrape_permits(since=datetime.now(), trace_id=trace_id)
```

### 5. Ingest Process Integration ✅
Modified `backend/app/ingest.py`:

- Added trace logging to `insert_lead()` function for "db_insert" stage
- Added trace logging to CSV ingest methods for "upsert" stage
- All methods accept optional `trace_id` parameter

#### Usage:
```python
# Single lead insert
insert_lead(lead_data, trace_id=trace_id)

# CSV ingest
ingestor = LeadIngestor(db_url)
ingestor.ingest_csv("leads.csv", trace_id=trace_id)
```

### 6. Critical Steps Logged ✅

The implementation logs all required critical steps:

1. **"fetch_page"** - When scraper fetches permit data from source
2. **"parse"** - When raw permit data is parsed into structured format
3. **"upsert"** - When data is bulk inserted/updated via CSV or batch operations
4. **"db_insert"** - When individual records are inserted into database

Each log entry includes:
- `trace_id` - UUID to track the complete flow
- `stage` - One of the critical steps above
- `ok` - Boolean indicating success/failure
- `details` - JSON object with contextual information (URLs, record counts, errors, etc.)
- `created_at` - Automatic timestamp

## Environment Variables

- **`X_DEBUG_KEY`** - Required for trace API endpoint authentication
- **`SUPABASE_URL`** - Database connection for logging
- **`SUPABASE_ANON_KEY`** - Supabase authentication

## Testing

### Unit Tests ✅
- `backend/tests/test_ingest_logging.py` - Comprehensive unit tests
- Covers all functions with mocked database calls
- Tests validation, error handling, and success cases

### Integration Tests ✅
- `test_fastapi_trace.py` - FastAPI endpoint testing
- Tests authentication, successful retrieval, error handling
- Uses mocked responses for isolation

### Demo Scripts ✅
- `demo_ingest_logging.py` - End-to-end demonstration
- `test_ingest_logging.py` - Basic functionality verification

## Running Tests

```bash
# Unit tests
cd backend && python -m pytest tests/test_ingest_logging.py -v

# FastAPI endpoint tests  
python test_fastapi_trace.py

# Demo
python demo_ingest_logging.py
```

## API Response Format

```json
{
  "trace_id": "123e4567-e89b-12d3-a456-426614174000",
  "total_logs": 4,
  "logs": [
    {
      "id": 1,
      "trace_id": "123e4567-e89b-12d3-a456-426614174000", 
      "stage": "fetch_page",
      "ok": true,
      "details": {"url": "example.com", "records": 50},
      "created_at": "2024-01-01T12:00:00Z"
    },
    {
      "id": 2,
      "trace_id": "123e4567-e89b-12d3-a456-426614174000",
      "stage": "parse", 
      "ok": true,
      "details": {"records_parsed": 45, "errors": 5},
      "created_at": "2024-01-01T12:00:01Z"
    }
  ]
}
```

## Error Handling

- Invalid trace IDs return 400 Bad Request
- Missing/invalid debug keys return 401 Unauthorized  
- Database errors return 500 Internal Server Error
- Failed logging operations are logged but don't break the main flow
- Graceful degradation when logging dependencies unavailable

## Security

- Trace endpoint protected by X-Debug-Key header
- Uses constant-time comparison for security
- No sensitive data exposed in logs
- Database access via service role policies

## Performance Considerations

- Async logging to avoid blocking main workflows
- Minimal overhead on critical paths
- Indexed queries on trace_id for fast retrieval
- Graceful fallback when logging fails

This implementation provides complete traceability through the lead ingestion pipeline while maintaining security, performance, and reliability.