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