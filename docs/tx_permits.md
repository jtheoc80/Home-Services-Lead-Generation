
# Texas Permits Integration

This document describes the Texas Permits integration that ingests permit data from Dallas, Austin, and Arlington, normalizes it into the `gold.permits` schema, and provides lead scoring capabilities.

## Overview

The TX Permits system integrates three major Texas metropolitan areas:
- **Dallas** - Building permits from Dallas Open Data (Socrata)
- **Austin** - Building permits from Austin Open Data (Socrata) 
- **Arlington** - Building permits from Arlington GIS (ArcGIS)

Data flows through a standardized pipeline: Raw Ingestion → Normalization → Lead Scoring → API/UI.

## API Endpoints

### Demo Endpoints

#### GET /api/demo/permits
Returns the latest 50 permits from gold.permits for demo purposes.

**Parameters:**
- `city` (optional): Filter by city (Dallas, Austin, Arlington)

**Response:**

# Texas Permits Integration - API Documentation

This document provides comprehensive documentation for the Texas permits integration including dataset links and curl examples for testing the API endpoints.

## Overview

The Texas Permits Integration provides real-time access to building permit data from major Texas cities:
- **Dallas** (Socrata API): Building permits with daily updates
- **Austin** (Socrata API): Issued construction permits with daily updates  
- **Arlington** (ArcGIS API): Property permits with real-time updates

## Data Sources

### Dallas Building Permits
- **Dataset**: Dallas Open Data Portal
- **ID**: `e7gq-4sah`  
- **URL**: https://www.dallasopendata.com/City-Services/Building-Permits/e7gq-4sah
- **API Endpoint**: `https://www.dallasopendata.com/resource/e7gq-4sah.json`
- **Update Frequency**: Daily
- **Key Fields**: permit_number, issued_date, address, work_description, permit_status, estimated_cost, contractor_name

### Austin Construction Permits
- **Dataset**: Austin Open Data Portal
- **ID**: `3syk-w9eu`
- **URL**: https://data.austintexas.gov/Building-and-Development/Issued-Construction-Permits/3syk-w9eu
- **API Endpoint**: `https://data.austintexas.gov/resource/3syk-w9eu.json`
- **Update Frequency**: Daily
- **Key Fields**: permit_number, issued_date, original_address1, description, status_current, total_valuation, applicant_name

### Arlington Property Permits
- **Dataset**: Arlington GIS Open Data
- **Layer**: Layer 1 - Issued Permits
- **URL**: https://gis2.arlingtontx.gov/agsext2/rest/services/OpenData/OD_Property/MapServer/1
- **API Endpoint**: `https://gis2.arlingtontx.gov/agsext2/rest/services/OpenData/OD_Property/MapServer/1/query`
- **Update Frequency**: Real-time
- **Key Fields**: OBJECTID, PermitNum, IssueDate, Address, Description, Status, PermitType, EstimatedCost

## API Endpoints

### 1. GET /api/demo/permits

Get recent permits for the demo interface with optional city filtering.

**Parameters:**
- `city` (optional): Filter by city name (Dallas, Austin, Arlington)
- `limit` (optional): Number of results (default: 50, max: 100)

**Response Format:**

```json
[
  {
    "permit_id": "string",
    "city": "string", 
    "permit_type": "string",

    "issued_at": "2024-01-01T00:00:00Z",
    "valuation": 50000,
    "address_full": "string",
    "contractor_name": "string",
    "status": "string"
  }
]
```

#### GET /api/leads/scores
Returns the latest 50 permits with their lead scores.

**Parameters:**
- `city` (optional): Filter by city (Dallas, Austin, Arlington)
- `limit` (optional): Number of results (1-100, default 50)

**Response:**

    "issued_at": "2024-01-15T10:30:00Z",
    "valuation": 50000,
    "address_full": "123 Main St, Dallas, TX 75201",
    "contractor_name": "ABC Construction",
    "status": "ACTIVE"
  }
]
```

### 2. GET /api/leads/scores

Get permits with lead scores computed by the scoring algorithm v0.

**Parameters:**
- `city` (optional): Filter by city name (Dallas, Austin, Arlington)
- `limit` (optional): Number of results (default: 50, max: 100)

**Response Format:**

```json
[
  {
    "permit_id": "string",
    "city": "string",

    "issued_at": "2024-01-01T00:00:00Z", 
    "score": 85,
    "reasons": ["Recent lead (+75.0 pts: 0 days old)", "High-value trade match: roofing (+50.0 pts)"]
  }
]
```

### Lead Scoring Endpoints

#### POST /v1/lead-score
Score a single lead using the v0 algorithm.

**Request:**
```json
{
  "lead": {
    "created_at": "2024-01-01T00:00:00Z",
    "trade_tags": ["roofing", "kitchen"],
    "value": 50000,
    "year_built": 1995,
    "owner_kind": "individual"
  },
  "version": "v0"
}
```

**Response:**
```json
{
  "lead_id": "uuid",
  "version": "v0",
  "score": 85,
  "reasons": ["Recent lead (+75.0 pts: 0 days old)", "..."],
  "scored_at": "2024-01-01T00:00:00Z"
}
```

## Data Schema

### gold.permits Table

| Field | Type | Description |
|-------|------|-------------|
| source_id | text | Source identifier (dallas_permits, austin_permits, arlington_permits) |
| permit_id | text | Unique permit identifier from source |
| jurisdiction | text | Jurisdiction name |
| city | text | City name |
| county | text | County name |
| state | text | State (always 'TX') |
| status | text | Permit status (ACTIVE, CLOSED, PENDING, CANCELLED) |
| permit_type | text | Type of permit (BUILDING, ELECTRICAL, etc.) |
| subtype | text | Permit subtype |
| work_class | text | Classification of work |
| description | text | Project description |
| applied_at | timestamptz | Date application was submitted |
| issued_at | timestamptz | Date permit was issued |
| finaled_at | timestamptz | Date permit was finalized |
| address_full | text | Full project address |
| postal_code | text | ZIP code |
| parcel_id | text | Property parcel identifier |
| valuation | numeric | Estimated project value |
| contractor_name | text | Contractor name |
| contractor_license | text | Contractor license number |
| latitude | double precision | Latitude coordinate |
| longitude | double precision | Longitude coordinate |
| geom | geometry(Point,4326) | PostGIS point geometry |
| url | text | Link to source record |
| provenance | jsonb | Source metadata and processing info |
| record_hash | text | SHA1 hash for change detection |
| updated_at | timestamptz | Last update timestamp |

**Primary Key:** (source_id, permit_id)

**Indexes:**
- BRIN index on `issued_at` for time-range queries
- GIST index on `geom` for spatial queries
- BTREE index on `(city, county)` for jurisdiction filtering
- BTREE index on `permit_type` for type filtering

### gold.lead_scores Table

| Field | Type | Description |
|-------|------|-------------|
| lead_id | text | SHA1 hash of source_id\|\|permit_id |
| version | text | Scoring algorithm version |
| score | integer | Lead score (0-100) |
| reasons | text[] | List of scoring reasons |
| created_at | timestamptz | Score computation timestamp |

**Primary Key:** (lead_id, version)

## Data Sources

### Dallas Permits
- **API**: Dallas Open Data (Socrata)
- **Dataset**: e7gq-4sah
- **Endpoint**: https://www.dallasopendata.com/resource/e7gq-4sah.json
- **Update Field**: last_update_date, issued_date, file_date
- **Primary Key**: permit_number, application_number, record_id
- **License**: Public Domain

### Austin Permits  
- **API**: Austin Open Data (Socrata)
- **Dataset**: 3syk-w9eu
- **Endpoint**: https://data.austintexas.gov/resource/3syk-w9eu.json
- **Update Field**: last_update, issued_date, applied_date
- **Primary Key**: permit_num, record_id, application_number
- **License**: Public Domain

### Arlington Permits
- **API**: Arlington GIS (ArcGIS)
- **Layer**: 1
- **Endpoint**: https://gis2.arlingtontx.gov/agsext2/rest/services/OpenData/OD_Property/MapServer/1
- **Update Field**: EditDate, IssueDate, AppliedDate
- **Primary Key**: OBJECTID, PermitNum, RecordID
- **License**: Public Domain

## Field Mapping

The normalization process uses configurable field aliases to map source-specific field names to the standardized schema. The system tries multiple field names in order of preference:

**Common Mappings:**
- `permit_id`: permit_number, permit_no, record_id, application_number
- `issued_at`: issued_date, issue_date, issued, issue_dt
- `status`: status, permit_status, current_status
- `description`: description, work_description, scope_of_work
- `valuation`: estimated_cost, job_value, valuation, declared_value

See `normalizers/field_aliases.py` for complete mappings.

## Lead Scoring v0

The v0 scoring algorithm uses a rules-based approach with weighted factors:

**Scoring Components:**
1. **Recency** (max 25 pts × 3 weight = 75 pts): More recent permits score higher
2. **Trade Match** (max 25 pts × 2 weight = 50 pts): High-value trade categories (roofing, kitchen, etc.)
3. **Project Value** (max 25 pts × 2 weight = 50 pts): Higher valuations score better
4. **Property Age** (max 15 pts × 1 weight = 15 pts): Older properties score higher
5. **Owner Type** (max 10 pts × 1 weight = 10 pts): Individual owners score highest

**Score Ranges:**
- 80-100: High-quality leads
- 60-79: Medium-quality leads  
- 0-59: Lower-quality leads

## Ingestion Pipeline

The automated pipeline runs nightly and can be triggered manually:

1. **Database Migration**: Apply schema changes via `make db-migrate`
2. **Raw Data Loading**: `python -m pipelines.load_raw` - Incremental ingestion from sources
3. **Normalization**: `python -m pipelines.normalize_permits` - Normalize to gold.permits schema
4. **Lead Scoring**: `python -m pipelines.publish` - Compute v0 scores for new/updated permits
5. **Data Quality**: Great Expectations validation checks

## Data Quality Checks

Automated Great Expectations validation includes:
- **Not-null permit_id**: All permits must have valid identifiers
- **Date validation**: At least one of issued_at/applied_at must be present
- **Valuation validation**: Valuation ≥ 0 when present
- **Geometry validation**: Valid PostGIS geometry when lat/long provided
- **Rowcount delta**: Warn if daily ingestion varies by ±50%

## Rate Limiting

**API Rate Limits:**
- Socrata: 5 requests/second
- ArcGIS: 5 requests/second
- Pagination: 1000 records per request

## Caveats and Limitations

1. **Data Freshness**: Sources update at different frequencies (daily for most)
2. **Field Availability**: Not all sources provide the same fields (e.g., contractor info)
3. **Coordinate Quality**: Some permits may lack accurate lat/long coordinates
4. **Historical Data**: Initial loads are limited to recent data (typically 30 days)
5. **Rate Limiting**: API quota limits may affect large historical imports
6. **Duplicate Detection**: Uses SHA1 hashing to detect record changes, not cross-source deduplication

## Links

- [Dallas Open Data Portal](https://www.dallasopendata.com/dataset/e7gq-4sah)
- [Austin Open Data Portal](https://data.austintexas.gov/d/3syk-w9eu)  
- [Arlington Open Data Portal](https://gis2.arlingtontx.gov/open-data)
- [Demo UI](/demo/tx-permits)
- [API Documentation](/docs)

## Monitoring

Monitor the pipeline health via:
- **Health Check**: GET /healthz - Shows ingestion status
- **Workflow Logs**: GitHub Actions logs for pipeline runs
- **Data Quality Reports**: Great Expectations validation results
- **Sample Data Artifacts**: CSV samples generated by pipeline runs

For issues or questions, check the pipeline logs in GitHub Actions or contact the development team.

    "issued_at": "2024-01-15T10:30:00Z", 
    "score": 85,
    "reasons": ["High valuation", "Recent permit", "Residential"]
  }
]
```

## curl Examples

### Get All Recent Permits
```bash
curl -X GET "http://localhost:8000/api/demo/permits" \
  -H "accept: application/json"
```

### Get Dallas Permits Only
```bash
curl -X GET "http://localhost:8000/api/demo/permits?city=Dallas" \
  -H "accept: application/json"
```

### Get Austin Permits with Limit
```bash
curl -X GET "http://localhost:8000/api/demo/permits?city=Austin&limit=25" \
  -H "accept: application/json"
```

### Get Lead Scores for All Cities
```bash
curl -X GET "http://localhost:8000/api/leads/scores" \
  -H "accept: application/json"
```

### Get Lead Scores for Arlington
```bash
curl -X GET "http://localhost:8000/api/leads/scores?city=Arlington&limit=20" \
  -H "accept: application/json"
```

### Test API Health
```bash
curl -X GET "http://localhost:8000/health" \
  -H "accept: application/json"
```

## Lead Scoring Algorithm v0

The scoring algorithm evaluates permits based on multiple factors:

### Scoring Criteria
1. **Recency** (Weight: 3x): Newer permits score higher (0-25 points)
2. **Project Value** (Weight: 2x): Higher valuations get better scores (0-25 points)  
3. **Permit Type** (Weight: 2x): Residential renovation/construction prioritized (0-25 points)
4. **Location Quality** (Weight: 1x): Urban areas with good access (0-15 points)
5. **Completeness** (Weight: 1x): Records with complete data (0-10 points)

### Score Ranges
- **80-100**: Excellent leads (High priority)
- **60-79**: Good leads (Medium priority)
- **40-59**: Fair leads (Low priority)
- **0-39**: Poor leads (Review manually)

## Data Pipeline

### Incremental Loading
The system supports incremental updates using the `updated_since` parameter:

```bash
# Dallas permits updated in last 24 hours
curl "https://www.dallasopendata.com/resource/e7gq-4sah.json?\$where=updated_at%3E%272024-01-15T00:00:00%27"

# Austin permits issued in last week  
curl "https://data.austintexas.gov/resource/3syk-w9eu.json?\$where=issued_date%3E%272024-01-08T00:00:00%27"

# Arlington permits with recent edit dates
curl "https://gis2.arlingtontx.gov/agsext2/rest/services/OpenData/OD_Property/MapServer/1/query?where=EditDate%3E%27timestamp%20%272024-01-15%2000:00:00%27%27&f=json"
```

### Manual Pipeline Execution
```bash
# Load raw data from all sources
python -m pipelines.load_raw --only dallas_permits,austin_permits,arlington_permits --since 2024-01-01

# Normalize to gold schema  
python -m pipelines.normalize_permits

# Compute lead scores
python -m pipelines.publish
```

### Automated Pipeline (GitHub Actions)
The pipeline runs automatically:
- **Schedule**: Nightly at 5 AM UTC (11 PM CST)
- **Manual Trigger**: Available via GitHub Actions UI
- **Workflow**: `.github/workflows/ingest-tx.yml`

## Database Schema

### gold.permits Table
```sql
CREATE TABLE gold.permits (
  source_id text not null,
  permit_id text not null,
  jurisdiction text,
  city text,
  county text,
  state text default 'TX',
  status text,
  permit_type text,
  subtype text,
  work_class text,
  description text,
  applied_at timestamptz,
  issued_at timestamptz,
  finaled_at timestamptz,
  address_full text,
  postal_code text,
  parcel_id text,
  valuation numeric,
  contractor_name text,
  contractor_license text,
  latitude double precision,
  longitude double precision,
  geom geometry(Point,4326),
  url text,
  provenance jsonb default '{}'::jsonb,
  record_hash text not null,
  updated_at timestamptz default now(),
  primary key (source_id, permit_id)
);
```

### gold.lead_scores Table
```sql
CREATE TABLE gold.lead_scores (
  lead_id text not null,
  version text not null,
  score integer not null check (score >= 0 and score <= 100),
  reasons text[] not null,
  created_at timestamptz default now(),
  primary key (lead_id, version)
);
```

## Demo Interface

### Access the Demo
Visit the live demo at: `http://localhost:3000/demo/tx-permits`

### Features
- Real-time permit data display
- City filtering (Dallas, Austin, Arlington)
- Lead score visualization
- Responsive design for mobile/desktop
- Automatic data refresh

### Demo API Integration
The demo page uses these API calls:
```javascript
// Fetch permits
const permits = await fetch('/api/demo/permits?city=Dallas');

// Fetch lead scores  
const scores = await fetch('/api/leads/scores?city=Dallas&limit=50');
```

## Data Quality & Validation

### Great Expectations Checks
- Primary key presence and uniqueness
- Date field validation (issued_at, applied_at)
- Valuation ≥ 0 for economic validity
- Valid Texas coordinates (lat/lng bounds)
- Required field completeness

### Run Quality Checks
```bash
python great_expectations/permits_validation.py
```

## Troubleshooting

### Common Issues

1. **Rate Limiting**
   - Set `SODA_APP_TOKEN` environment variable
   - Reduce request frequency in configuration

2. **Database Connection**
   - Verify `DATABASE_URL` is correctly set
   - Check PostgreSQL service status
   - Ensure PostGIS extension is installed

3. **Missing Data**
   - Check source API availability
   - Verify date range parameters
   - Review incremental state tracking

### Debug Commands
```bash
# Test API connectivity
python -c "from ingest.socrata import fetch; print(fetch('www.dallasopendata.com', 'e7gq-4sah', limit=1))"

# Check database schema
psql $DATABASE_URL -c "\dt gold.*"

# Validate recent data
python great_expectations/permits_validation.py
```

## Production Deployment

### Environment Variables
```bash
DATABASE_URL=postgresql://user:password@host:5432/leadledderpro
SODA_APP_TOKEN=your_socrata_app_token
SUPABASE_URL=https://project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

### Performance Considerations
- Enable PostgreSQL query optimization
- Configure appropriate connection pooling
- Monitor API rate limits
- Set up database indexing for spatial queries

## Support

For technical support or questions:
- Review GitHub Issues: [Home Services Lead Generation Issues](https://github.com/jtheoc80/Home-Services-Lead-Generation/issues)
- Check pipeline logs in GitHub Actions
- Verify data quality with Great Expectations reports
