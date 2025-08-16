# Texas Counties Supabase Integration

This document describes the Supabase database setup for all Texas counties supported by the LeadLedgerPro system.

## Supported Counties

The following Texas counties are configured for Supabase integration:

- **Harris County** (`tx-harris`) - Houston Metro area
- **Fort Bend County** (`tx-fort-bend`) - Southwest Houston Metro
- **Brazoria County** (`tx-brazoria`) - South Houston Metro  
- **Galveston County** (`tx-galveston`) - Southeast Houston Metro

## Database Tables

Each county requires its own table in your Supabase database with the following schema:

### Harris County Table

```sql
CREATE TABLE permits_raw_harris (
  event_id TEXT PRIMARY KEY,
  permit_number TEXT,
  permit_name TEXT,
  app_type TEXT,
  issue_date TIMESTAMPTZ,
  project_number TEXT,
  full_address TEXT,
  street_number TEXT,
  street_name TEXT,
  status TEXT,
  raw JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_permits_raw_harris_issue_date ON permits_raw_harris(issue_date);
CREATE INDEX idx_permits_raw_harris_status ON permits_raw_harris(status);
CREATE INDEX idx_permits_raw_harris_app_type ON permits_raw_harris(app_type);
```

### Fort Bend County Table

```sql
CREATE TABLE permits_raw_fort_bend (
  event_id TEXT PRIMARY KEY,
  permit_number TEXT,
  permit_name TEXT,
  app_type TEXT,
  issue_date TIMESTAMPTZ,
  project_number TEXT,
  full_address TEXT,
  street_number TEXT,
  street_name TEXT,
  status TEXT,
  raw JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_permits_raw_fort_bend_issue_date ON permits_raw_fort_bend(issue_date);
CREATE INDEX idx_permits_raw_fort_bend_status ON permits_raw_fort_bend(status);
CREATE INDEX idx_permits_raw_fort_bend_app_type ON permits_raw_fort_bend(app_type);
```

### Brazoria County Table

```sql
CREATE TABLE permits_raw_brazoria (
  event_id TEXT PRIMARY KEY,
  permit_number TEXT,
  permit_name TEXT,
  app_type TEXT,
  issue_date TIMESTAMPTZ,
  project_number TEXT,
  full_address TEXT,
  street_number TEXT,
  street_name TEXT,
  status TEXT,
  raw JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_permits_raw_brazoria_issue_date ON permits_raw_brazoria(issue_date);
CREATE INDEX idx_permits_raw_brazoria_status ON permits_raw_brazoria(status);
CREATE INDEX idx_permits_raw_brazoria_app_type ON permits_raw_brazoria(app_type);
```

### Galveston County Table

```sql
CREATE TABLE permits_raw_galveston (
  event_id TEXT PRIMARY KEY,
  permit_number TEXT,
  permit_name TEXT,
  app_type TEXT,
  issue_date TIMESTAMPTZ,
  project_number TEXT,
  full_address TEXT,
  street_number TEXT,
  street_name TEXT,
  status TEXT,
  raw JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_permits_raw_galveston_issue_date ON permits_raw_galveston(issue_date);
CREATE INDEX idx_permits_raw_galveston_status ON permits_raw_galveston(status);
CREATE INDEX idx_permits_raw_galveston_app_type ON permits_raw_galveston(app_type);
```

## Environment Setup

Ensure you have the following environment variables configured:

```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
```

## Usage Examples

### Scrape specific county

```bash
# Scrape Harris County (existing functionality)
python -m permit_leads scrape --jurisdiction tx-harris --days 7

# Scrape Fort Bend County
python -m permit_leads scrape --jurisdiction tx-fort-bend --days 7

# Scrape Brazoria County
python -m permit_leads scrape --jurisdiction tx-brazoria --days 7

# Scrape Galveston County
python -m permit_leads scrape --jurisdiction tx-galveston --days 7
```

### Scrape all active counties

```bash
# Scrape all active Texas counties (includes all 4 counties above)
python -m permit_leads scrape --region-aware --days 7
```

## Data Flow

1. **Jurisdiction-Specific Scraping**: Each county's data is scraped from its configured ArcGIS FeatureServer
2. **Table Routing**: Data is automatically routed to the correct Supabase table based on jurisdiction
3. **Conflict Resolution**: Uses `event_id` column for idempotent upserts
4. **Batch Processing**: Processes data in chunks of 500 records for optimal performance

## Table Schema Notes

- **event_id**: Primary key for conflict resolution and deduplication
- **permit_number**: The official permit number from the county
- **permit_name**: Name/title of the permit
- **app_type**: Application/permit type (residential, commercial, etc.)
- **issue_date**: When the permit was issued
- **full_address**: Complete property address
- **status**: Current permit status
- **raw**: Raw JSON data from the source API for debugging/analysis
- **created_at/updated_at**: Timestamp tracking for database records

## Monitoring

All Supabase operations include comprehensive logging:

```
INFO:permit_leads.sinks.supabase_sink:Starting upsert of 1250 records in 3 chunks of 500
INFO:permit_leads.sinks.supabase_sink:Successfully upserted 500 records to permits_raw_fort_bend
INFO:permit_leads.sinks.supabase_sink:Chunk 1 complete: 500 success, 0 failed
INFO:permit_leads.main:Supabase upsert completed: 1250 success, 0 failed
```

## Error Handling

The system includes graceful error handling:

- **Missing Environment Variables**: Falls back gracefully with warning messages
- **Connection Issues**: Logs errors but allows other outputs (CSV, SQLite) to succeed
- **Table Not Found**: Provides clear error messages with table creation SQL
- **Batch Failures**: Continues processing remaining chunks if individual chunks fail