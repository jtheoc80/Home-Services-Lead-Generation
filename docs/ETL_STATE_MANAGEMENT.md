# ETL State Management for Permit Scraping

This document explains the ETL state management system implemented for tracking last successful scraping runs and preventing data gaps.

## Overview

The ETL state management system tracks the last successful run timestamp for each data source to enable incremental data loading. It prevents data gaps by using a 1-minute buffer when querying for new records.

## Key Components

### 1. ETL State Table

Located in Supabase, the `etl_state` table stores:
- `source` (TEXT PRIMARY KEY): Source identifier (e.g., 'harris_issued_permits')
- `last_run` (TIMESTAMPTZ): Timestamp of last successful extraction
- `created_at` (TIMESTAMPTZ): When this source was first tracked
- `updated_at` (TIMESTAMPTZ): When this source was last updated

### 2. ETLStateManager Class

**File**: `permit_leads/etl_state.py`

Provides methods to:
- `get_last_run(source)`: Get last successful run timestamp
- `update_last_run(source, timestamp)`: Update last successful run
- `get_since_timestamp(source, fallback_days=7)`: Get timestamp for incremental loading with 1-minute buffer

### 3. ETLAwareArcGISAdapter

**File**: `permit_leads/adapters/etl_aware_arcgis_adapter.py`

Enhanced ArcGIS adapter that:
- Automatically manages ETL state for Harris County permits
- Uses source name 'harris_issued_permits' as specified in requirements
- Queries `ISSUEDDATE > last_run - 1 minute` to prevent gaps
- Updates last_run timestamp on successful completion

## How It Works

### Initial Run (No Previous State)
1. ETL state manager checks for existing `last_run` for source
2. If none found, uses fallback timestamp (default: 7 days ago)
3. Queries permits with `ISSUEDDATE > fallback_timestamp`
4. On success, stores current timestamp as `last_run`

### Subsequent Runs (With Previous State)
1. Retrieves `last_run` timestamp from Supabase
2. Subtracts 1 minute to create buffer: `since = last_run - 1 minute`
3. Queries permits with `ISSUEDDATE > since`
4. On success, updates `last_run` to current timestamp

### Gap Prevention
The 1-minute buffer ensures no records are missed between runs:
- If last run was at 10:00:00
- Next run queries for records after 09:59:00
- This accounts for clock differences and ensures overlap

## Usage

### Automatic Usage (Recommended)
The ETL state management is automatically enabled for Harris County when using the region-aware scraper:

```bash
# This automatically uses ETL state management for Harris County
python -m permit_leads scrape --jurisdiction tx-harris
```

### Manual ETL State Management
Use the CLI tool for administrative tasks:

```bash
# Check last run for Harris County
python scripts/etl_state_cli.py check harris_issued_permits

# Update last run to current time
python scripts/etl_state_cli.py update harris_issued_permits

# Update last run to specific time
python scripts/etl_state_cli.py update harris_issued_permits --timestamp "2025-01-15 14:30:00"

# List all sources and their state
python scripts/etl_state_cli.py list

# Reset a source (removes all state)
python scripts/etl_state_cli.py reset harris_issued_permits --confirm
```

## Configuration

### Environment Variables
The system requires Supabase environment variables:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_SERVICE_ROLE`: Service role key with table access

### Graceful Degradation
If Supabase is not available:
- System logs warnings but continues operation
- Falls back to date-based queries using `--days` parameter
- No state tracking occurs (every run processes full date range)

## Database Migration

To set up the ETL state table in Supabase:

```sql
-- Apply the migration
\i backend/app/migrations/005_etl_state_table.sql
```

Or manually create:

```sql
CREATE TABLE IF NOT EXISTS etl_state (
    source TEXT PRIMARY KEY,
    last_run TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Monitoring and Troubleshooting

### Check ETL State
```bash
python scripts/etl_state_cli.py check harris_issued_permits
```

### Verify Integration
```bash
# Run dry-run to see what would be queried
python -m permit_leads scrape --jurisdiction tx-harris --dry-run --verbose
```

### Reset After Issues
If there are data quality issues or missed records:
```bash
# Reset state to force full re-scan
python scripts/etl_state_cli.py reset harris_issued_permits --confirm

# Or set specific timestamp to resume from
python scripts/etl_state_cli.py update harris_issued_permits --timestamp "2025-01-15 10:00:00"
```

## Implementation Details

### Source Name Mapping
- Harris County: `harris_issued_permits` (as specified in requirements)
- Other jurisdictions: `{jurisdiction_slug}_permits`

### Date Field Mapping
- Harris County uses `ISSUEDDATE` field from ArcGIS Feature Service
- Query format: `ISSUEDDATE > TIMESTAMP 'YYYY-MM-DD HH:MM:SS'`

### Error Handling
- Network errors don't update ETL state (preserves last known good state)
- Supabase connection errors are logged but don't block operation
- Invalid timestamps are rejected with helpful error messages

## Benefits

1. **Incremental Loading**: Only processes new/updated records
2. **Gap Prevention**: 1-minute buffer ensures no missed records
3. **Resilience**: Graceful handling of network/database issues
4. **Monitoring**: CLI tools for state inspection and management
5. **Performance**: Reduces load on source systems and processing time