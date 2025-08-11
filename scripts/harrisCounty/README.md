# Harris County Issued Permits Script

This script fetches issued permits data from Harris County's ArcGIS FeatureServer and stores it in a Supabase database.

## Setup

### Environment Variables

Create a `.env` file or set the following environment variables:

```bash
# Required
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Optional (defaults to Harris County FeatureServer)
HC_ISSUED_PERMITS_URL=https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0
```

### Database Schema

The script expects a `permits_raw_harris` table in your Supabase database. If it doesn't exist, the script will provide the SQL to create it:

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

## Usage

### Basic Usage (fetch permits from last 3 days)
```bash
npm run harris:permits
```

### Fetch permits since a specific date
```bash
npm run harris:permits -- --since 2024-01-01
npm run harris:permits -- --since 2024-12-01
```

### Direct execution with tsx
```bash
tsx scripts/harrisCounty/issuedPermits.ts --since 2024-01-01
```

## How it Works

1. **Environment Validation**: Checks for required environment variables
2. **Database Check**: Verifies the target table exists in Supabase
3. **ArcGIS Query**: Fetches permits from Harris County FeatureServer using:
   - Date filtering based on `--since` parameter
   - Pagination with 2000 records per batch
   - Automatic retry on pagination
4. **Data Mapping**: Maps ArcGIS fields to standardized schema
5. **Upsert**: Stores data in Supabase using `event_id` for conflict resolution

## Data Mapping

The script maps Harris County ArcGIS fields to a standardized schema:

| Target Field | Source Field | Description |
|--------------|--------------|-------------|
| `event_id` | `EVENTID` or `OBJECTID` | Unique identifier |
| `permit_number` | `PERMITNUMBER` | Permit number |
| `permit_name` | `PERMITNAME` or `PROJECTNAME` | Permit/project name |
| `app_type` | `APPTYPE` | Application type |
| `issue_date` | `ISSUEDDATE` | Issue date (converted to ISO) |
| `project_number` | `PROJECTNUMBER` | Project number |
| `full_address` | `FULLADDRESS` | Complete address |
| `street_number` | `STREETNUMBER` | Street number |
| `street_name` | `STREETNAME` | Street name |
| `status` | `STATUS` | Permit status |
| `raw` | (all fields) | Complete ArcGIS record as JSON |

## Error Handling

The script:
- Exits with code 1 on any HTTP or database errors
- Provides detailed error messages for troubleshooting
- Includes safety limits to prevent infinite pagination loops
- Validates environment variables before execution

## Logging

The script provides detailed logging including:
- Configuration summary
- Batch processing progress
- Record counts
- Error details
- Success confirmation

## Example Output

```
Harris County Issued Permits Fetcher
====================================
Supabase URL: https://your-project.supabase.co
Harris County URL: https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0
Fetching permits since: 2024-01-01T00:00:00.000Z

Table permits_raw_harris exists and is accessible
Fetching batch 1 (offset: 0)
Fetched 2000 permits in this batch
Fetching batch 2 (offset: 2000)
Fetched 1500 permits in this batch
Found 3500 permits to process
Upserted batch 1/4 (1000/3500 total)
Upserted batch 2/4 (2000/3500 total)
Upserted batch 3/4 (3000/3500 total)
Upserted batch 4/4 (3500/3500 total)
Successfully upserted 3500 permits
✅ Successfully completed permit data sync
```