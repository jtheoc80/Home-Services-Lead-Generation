# Harris County Permits Normalization

This document explains the Harris County permits normalization functionality that implements the `normalize_permits_harris()` SQL function.

## Overview

The Harris County permits normalization system provides:

- **Raw Data Table**: `permits_raw_harris` for storing raw Harris County permit data
- **Normalization Function**: `normalize_permits_harris()` for copying and transforming data to unified schema
- **Deduplication**: By `event_id` (keeping latest version)
- **Upsert Logic**: On `source_ref` field for handling updates
- **Unified Schema**: Maps Harris County fields to standard `public.leads` table

## Database Schema

### permits_raw_harris Table

```sql
CREATE TABLE permits_raw_harris (
  id BIGSERIAL PRIMARY KEY,
  event_id TEXT UNIQUE NOT NULL,  -- Harris County's unique event/permit identifier
  permit_number TEXT,
  address TEXT,
  permit_type TEXT,
  work_description TEXT,
  permit_status TEXT,
  issue_date TIMESTAMPTZ,
  application_date TIMESTAMPTZ,
  expiration_date TIMESTAMPTZ,
  applicant_name TEXT,
  property_owner TEXT,
  contractor_name TEXT,
  valuation NUMERIC,
  square_footage NUMERIC,
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  parcel_id TEXT,
  district TEXT,
  sub_type TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  raw_data JSONB
);
```

### New Fields in leads Table

The migration adds these fields to the existing `leads` table:

- `source_ref TEXT` - Reference to original source record (event_id for Harris County)
- `county TEXT` - County name (e.g., "Harris", "Fort Bend")
- `permit_type TEXT` - Specific permit type from source system

## Usage

### 1. Apply Migration

```bash
# Apply the migration
cd backend
python apply_harris_migration.py
```

### 2. Insert Raw Data

Insert Harris County permit data into `permits_raw_harris`:

```sql
INSERT INTO permits_raw_harris (
  event_id, permit_number, address, permit_type, work_description, 
  permit_status, issue_date, applicant_name, property_owner, valuation,
  latitude, longitude, raw_data
) VALUES (
  'HARRIS_2024_001',
  'BP2024001234', 
  '1234 Main St, Houston, TX 77001',
  'Residential Building',
  'Single family residence - new construction with plumbing and electrical',
  'Issued',
  '2024-01-15T10:30:00-06:00',
  'ABC Construction LLC',
  'John Smith',
  450000.0,
  29.7604,
  -95.3698,
  '{"original_source": "Harris County API"}'::jsonb
);
```

### 3. Run Normalization

Execute the normalization function:

```sql
SELECT * FROM normalize_permits_harris();
```

Returns:
```
 processed_count | new_count | updated_count 
-----------------+-----------+---------------
               1 |         1 |             0
```

### 4. Query Normalized Data

```sql
-- Get all Harris County leads
SELECT * FROM leads WHERE county = 'Harris';

-- Get specific permit by source reference
SELECT * FROM leads WHERE source_ref = 'HARRIS_2024_001';
```

## Field Mapping

| Raw Field (permits_raw_harris) | Normalized Field (leads) | Notes |
|--------------------------------|--------------------------|-------|
| event_id | source_ref | Primary key for upserts |
| permit_number | permit_id | Harris County permit number |
| address | address | Normalized (whitespace cleaned) |
| permit_type | work_class, permit_type | Used for both fields |
| work_description | description | Full work description |
| permit_status | status | Current permit status |
| issue_date | issue_date | When permit was issued |
| applicant_name | applicant | Primary applicant |
| contractor_name | applicant | Used if applicant_name empty |
| property_owner | owner | Property owner name |
| valuation | value | Project valuation |
| latitude, longitude | latitude, longitude | GPS coordinates |
| (derived) | county | Always "Harris" |
| (derived) | jurisdiction | Always "Harris County" |
| (derived) | state | Always "TX" |
| (derived) | category | "residential" or "commercial" |
| (derived) | is_residential | Boolean based on category |
| (derived) | trade_tags | Array extracted from description |

## Trade Tag Extraction

The function automatically extracts trade tags from work descriptions:

- **plumbing**: plumb, water, sewer
- **electrical**: electric, electrical, wiring  
- **hvac**: hvac, heating, cooling, air
- **roofing**: roof, roofing
- **general_contractor**: kitchen, bathroom, remodel, renovation

## Category Classification

- **residential**: Contains "residential" in permit_type OR keywords like "single family", "duplex", "house", "home"
- **commercial**: Contains "commercial" in permit_type OR keywords like "office", "retail", "industrial"  
- **other**: Everything else

## Deduplication Logic

1. Groups raw permits by `event_id`
2. Keeps only the latest version (highest `created_at`)
3. Processes each unique `event_id` once

## Upsert Logic

1. Checks if `source_ref` already exists in `leads` table
2. If exists: Updates all fields except `id`, `created_at`
3. If new: Inserts as new record
4. Returns counts of processed, new, and updated records

## Testing

Run the test suite:

```bash
cd backend
python -m pytest tests/test_harris_permit_normalization.py -v
```

Run the demo:

```bash
cd backend
python demo_harris_normalization.py
```

## Files Created/Modified

- `backend/app/migrations/005_harris_permits_normalization.sql` - Main migration
- `backend/tests/test_harris_permit_normalization.py` - Test suite
- `backend/apply_harris_migration.py` - Migration application script
- `backend/demo_harris_normalization.py` - Demo script

## Example Workflow

1. **ETL Process**: Extract Harris County data from API/scraper → Insert into `permits_raw_harris`
2. **Normalization**: Run `SELECT * FROM normalize_permits_harris()` 
3. **Query**: Use standard `leads` table queries for normalized data
4. **Updates**: Re-run normalization to handle permit updates (status changes, etc.)

## Performance Considerations

- Index on `event_id` for deduplication
- Index on `source_ref` for upsert operations  
- JSONB storage for raw data allows flexible source data
- Function processes in batches with progress logging
- Supports incremental updates (only processes new/changed records)

## Error Handling

- Continues processing if individual records fail
- Logs progress every 100 records
- Returns counts for monitoring
- Preserves original data in `raw_data` field