# Supabase Sink Integration for Harris County Permits

This implementation adds Supabase batch upsert functionality to the Harris County permit scraper.

## Features

- **SupabaseSink class** (`permit_leads/sinks/supabase_sink.py`):
  - Batch upserts with configurable chunk size (default: 500 records)
  - Idempotent operations via conflict resolution on `event_id` column
  - Environment-based configuration using `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`
  - Comprehensive logging of success/failure counts per batch
  - Proper JSON serialization of datetime objects
  - Health check functionality
  - Raises exceptions on non-200 responses

- **Harris County integration**:
  - Automatically writes to Supabase in addition to existing CSV/SQLite outputs
  - Only activated for `tx-harris` jurisdiction
  - Graceful fallback when Supabase is unavailable
  - Maintains full backward compatibility

## Usage

### Setup Environment Variables
```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
```

### Run Harris County Scraper
```bash
# Basic usage - writes to CSV, SQLite, and Supabase
python -m permit_leads scrape --jurisdiction tx-harris --days 7

# With custom formats and verbose logging
python -m permit_leads scrape --jurisdiction tx-harris --days 3 --formats csv sqlite jsonl --verbose

# Using the wrapper script
./scripts/scrape-harris.cjs --since=3d
```

## Database Table

The implementation expects a `permits_raw_harris` table in Supabase with an `event_id` column for conflict resolution.

## Error Handling

- Missing environment variables: Logs warning and skips Supabase output
- Supabase unavailable: Logs error but allows other outputs to succeed
- Non-200 responses: Raises exception as specified
- Batch failures: Logs detailed per-batch and total counts

## Example Output

```
INFO:permit_leads.sinks.supabase_sink:Starting upsert of 1250 records in 3 chunks of 500
INFO:permit_leads.sinks.supabase_sink:Processing chunk 1/3 (500 records)
INFO:permit_leads.sinks.supabase_sink:Successfully upserted 500 records to permits_raw_harris
INFO:permit_leads.sinks.supabase_sink:Chunk 1 complete: 500 success, 0 failed
INFO:permit_leads.sinks.supabase_sink:Processing chunk 2/3 (500 records)
INFO:permit_leads.sinks.supabase_sink:Successfully upserted 500 records to permits_raw_harris
INFO:permit_leads.sinks.supabase_sink:Chunk 2 complete: 500 success, 0 failed
INFO:permit_leads.sinks.supabase_sink:Processing chunk 3/3 (250 records)
INFO:permit_leads.sinks.supabase_sink:Successfully upserted 250 records to permits_raw_harris
INFO:permit_leads.sinks.supabase_sink:Chunk 3 complete: 250 success, 0 failed
INFO:permit_leads.sinks.supabase_sink:Upsert complete: 1250 success, 0 failed
INFO:permit_leads.main:Supabase upsert completed: 1250 success, 0 failed
```

## Implementation Notes

- Uses supabase-py v2 (already in requirements.txt)
- Minimal changes to existing codebase
- Only affects Harris County scraper (`tx-harris` jurisdiction)
- Existing functionality (CSV/SQLite) unchanged
- Comprehensive test coverage included