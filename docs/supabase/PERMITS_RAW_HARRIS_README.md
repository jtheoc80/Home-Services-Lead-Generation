# Harris County Permits Raw Ingest Table

This directory contains SQL scripts for setting up a raw ingest table for Harris County building permits.

## Overview

The `permits_raw_harris` table is designed for high-performance ingestion of raw permit data from Harris County's building permit system. This table serves as the first stage in the data pipeline before processing and enrichment.

## Files

- **`permits_raw_harris_setup.sql`** - Creates the raw ingest table with proper indexes
- **`test_permits_raw_harris.sql`** - Test queries to verify table setup and functionality

## Table Schema

### `public.permits_raw_harris`

| Column | Type | Description |
|--------|------|-------------|
| `event_id` | `bigint` | Primary key - Unique permit event identifier from Harris County |
| `permit_number` | `text` | Official permit number assigned by Harris County |
| `permit_name` | `text` | Descriptive name/title of the permit |
| `app_type` | `text` | Application type (building, electrical, plumbing, etc.) |
| `issue_date` | `timestamptz` | Date the permit was issued |
| `project_number` | `text` | Internal project number if applicable |
| `full_address` | `text` | Complete address of the permitted work |
| `street_number` | `numeric` | Numeric portion of street address |
| `street_name` | `text` | Street name portion of address |
| `status` | `text` | Current permit status (issued, expired, completed, etc.) |
| `raw` | `jsonb` | Original raw permit data in JSONB format for reference |
| `created_at` | `timestamptz` | Timestamp when record was inserted (default: now()) |

## Indexes

- **Primary Key**: `event_id`
- **Fast Date Index**: `idx_permits_harris_issue_date` on `issue_date DESC` - Optimized for recent-first queries
- **Status Index**: `idx_permits_harris_status` on `status` - For filtering by permit status
- **Permit Number Index**: `idx_permits_harris_permit_number` on `permit_number` - For lookup by permit number
- **Created At Index**: `idx_permits_harris_created_at` on `created_at DESC` - For ingestion monitoring

## Security

**Row Level Security (RLS) is DISABLED** on this table by design:

- This table is intended for **service-role ingest only**
- End users should not directly access raw permit data
- Data flows from this table to processed/enriched tables with proper RLS
- Only backend services with service-role keys should write to this table

## Usage

### Setup

1. Run the setup script in Supabase SQL Editor:
   ```sql
   -- Copy and paste contents of permits_raw_harris_setup.sql
   ```

2. Verify setup with test script:
   ```sql
   -- Copy and paste contents of test_permits_raw_harris.sql
   ```

### Data Ingestion

Use the service role key to insert permit data:

```sql
INSERT INTO public.permits_raw_harris (
    event_id,
    permit_number,
    permit_name,
    app_type,
    issue_date,
    full_address,
    status,
    raw
) VALUES (
    $1, $2, $3, $4, $5, $6, $7, $8
);
```

### Query Patterns

```sql
-- Get recent permits (uses fast index)
SELECT * FROM public.permits_raw_harris 
WHERE issue_date >= '2024-01-01'::timestamptz 
ORDER BY issue_date DESC 
LIMIT 100;

-- Find by permit number
SELECT * FROM public.permits_raw_harris 
WHERE permit_number = 'BP2024-001234';

-- Filter by status
SELECT * FROM public.permits_raw_harris 
WHERE status = 'Issued'
ORDER BY issue_date DESC;
```

## Integration with Lead Processing Pipeline

This raw table feeds into the broader lead generation pipeline:

1. **Raw Ingest** → `permits_raw_harris` (this table)
2. **Processing** → Extract and normalize permit data
3. **Enrichment** → Add geocoding, parcel data, trade classification
4. **Scoring** → Apply ML scoring for lead quality
5. **Output** → `public.leads` table for contractor dashboard

## Monitoring

Monitor ingest performance with:

```sql
-- Check ingest volume by day
SELECT 
    DATE(created_at) as ingest_date,
    COUNT(*) as permits_ingested
FROM public.permits_raw_harris 
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY ingest_date DESC;

-- Check permit date distribution
SELECT 
    DATE(issue_date) as permit_date,
    COUNT(*) as permit_count
FROM public.permits_raw_harris 
WHERE issue_date >= NOW() - INTERVAL '30 days'
GROUP BY DATE(issue_date)
ORDER BY permit_date DESC;
```