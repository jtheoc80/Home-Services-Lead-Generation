# Texas Building Permits Data Integration

This document describes the multi-jurisdiction building permits data integration for major Texas cities and counties, providing comprehensive permit intelligence for contractors and lead generation.

## Supported Jurisdictions

### 1. Dallas (Socrata API)
- **Data Source**: Dallas Open Data Portal
- **Dataset ID**: `e7gq-4sah`
- **API Endpoint**: `https://www.dallasopendata.com/resource/e7gq-4sah.json`
- **Documentation**: [Dallas Building Permits Dataset](https://www.dallasopendata.com/City-Services/Building-Permits/e7gq-4sah)
- **Update Frequency**: Daily
- **Key Fields**: permit_number, issued_date, address, work_description, permit_status, estimated_cost, contractor_name

### 2. Austin (Socrata API)
- **Data Source**: Austin Open Data Portal  
- **Dataset ID**: `3syk-w9eu`
- **API Endpoint**: `https://data.austintexas.gov/resource/3syk-w9eu.json`
- **Documentation**: [Austin Building Permits Dataset](https://data.austintexas.gov/Building-and-Development/Issued-Construction-Permits/3syk-w9eu)
- **Update Frequency**: Daily
- **Key Fields**: permit_number, issued_date, original_address1, description, status_current, total_valuation, applicant_name

### 3. Arlington (ArcGIS FeatureServer)
- **Data Source**: City of Arlington GIS Portal
- **FeatureServer**: "Issued Permits" 
- **API Endpoint**: `https://gis.arlingtontx.gov/arcgis/rest/services/OpenData/Permits/FeatureServer/0`
- **Documentation**: [Arlington GIS Open Data Portal](https://gis.arlingtontx.gov/portal/home/)
- **Update Frequency**: Weekly
- **Key Fields**: PermitNumber, IssueDate, Address, Description, Status, PermitType, EstimatedCost, ContractorName

### 4. Harris County (ArcGIS FeatureServer)
- **Data Source**: Harris County GIS Portal
- **FeatureServer**: "Issued Permits"
- **API Endpoint**: `https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0`
- **Update Frequency**: Daily
- **Key Fields**: PERMITNUMBER, ISSUEDDATE, FULLADDRESS, PROJECTNAME, STATUS, APPTYPE

### 5. Houston (Texas Public Information Act - TPIA)
- **Data Source**: Manual CSV requests via TPIA
- **Status**: Placeholder implementation with request template generation
- **Process**: Generate TPIA request → Submit to City of Houston → Receive CSV → Process manually
- **Reason**: Houston does not provide direct API access to building permit data

## Data Pipeline Architecture

### Incremental Data Pulls
All API sources (Dallas, Austin, Arlington, Harris County) support incremental updates:
- **Socrata sources**: Use `updated_field` parameter with SoQL `$where` clauses
- **ArcGIS sources**: Use `date_field` parameter with date range filters
- **Rate limiting**: Maximum 5 requests per second with exponential backoff

### Normalization Process
Raw permit data is transformed into a standardized `permits_gold` schema:

#### Common Columns
- `jurisdiction`: Source city/county (dallas, austin, arlington, harris_county, houston)
- `issued_date`: Standardized permit issue date
- `work_type`: Normalized work classification (residential, commercial, multi_family, infrastructure)
- `address`: Cleaned and standardized address
- `valuation`: Project value in USD
- `geom`: PostGIS geometry point for spatial queries

#### Data Quality Features
- **Duplicate detection**: Composite unique constraints on jurisdiction + permit_id
- **Coordinate validation**: Texas geographic bounds checking
- **Value categorization**: Project values grouped into analytical bands
- **Text normalization**: Standardized names, addresses, and descriptions

## Configuration

### Sources Configuration (`config/sources.yaml`)
```yaml
sources:
  - name: Dallas Building Permits (Socrata)
    type: socrata
    domain: "www.dallasopendata.com"
    dataset_id: "e7gq-4sah"
    updated_field: "issued_date"
    primary_key: "permit_number"
    
  - name: Austin Building Permits (Socrata)
    type: socrata
    domain: "data.austintexas.gov"
    dataset_id: "3syk-w9eu"
    updated_field: "issued_date"
    primary_key: "permit_number"
    
  - name: Arlington Issued Permits (ArcGIS)
    type: arcgis_feature_service
    url: "https://gis.arlingtontx.gov/arcgis/rest/services/OpenData/Permits/FeatureServer/0/query"
    updated_field: "IssueDate"
    primary_key: "PermitNumber"
    
  - name: Houston Open Records (TPIA)
    type: tpia_csv
    jurisdiction: "houston"
    updated_field: "issue_date"
    primary_key: "permit_number"
```

## Houston TPIA Process

Since Houston does not provide API access, we implement a Texas Public Information Act (TPIA) request process:

### 1. Generate Request Template
```python
from permit_leads.adapters.tpia_adapter import TPIAAdapter

adapter = TPIAAdapter({"jurisdiction": "houston"})
template = adapter.generate_tpia_request_template()
```

### 2. Submit Request
- File template with Houston City Clerk
- Wait for response (10 business days maximum)
- Pay any processing fees if required

### 3. Process CSV Data
- Save received CSV files to `./data/tpia/houston_permits_YYYYMMDD.csv`
- Run ETL process to normalize and import data

### 4. Status Monitoring
```python
status = adapter.get_status()
print(f"CSV files available: {status['csv_files_available']}")
```

## Rate Limiting and API Compliance

### Socrata APIs (Dallas, Austin)
- **Rate Limit**: 5 requests per second
- **Retry Strategy**: Exponential backoff with jitter
- **Authentication**: App tokens recommended for higher limits
- **SoQL Support**: Advanced queries with `$where`, `$limit`, `$offset`

### ArcGIS FeatureServers (Arlington, Harris County)
- **Rate Limit**: 5 requests per second  
- **Batch Size**: Respects `maxRecordCount` from service metadata
- **Pagination**: Automatic handling with `resultOffset` and `resultRecordCount`
- **Geometry**: Full spatial data preservation with coordinate validation

## Usage Examples

### Fetch Recent Permits
```python
from permit_leads.adapters.socrata_adapter import SocrataAdapter
from datetime import datetime, timedelta

# Dallas permits from last 30 days
config = {
    "domain": "www.dallasopendata.com",
    "dataset_id": "e7gq-4sah",
    "updated_field": "issued_date",
    "mappings": {"permit_number": "permit_number", "address": "address"}
}

adapter = SocrataAdapter(config)
since = datetime.now() - timedelta(days=30)
permits = list(adapter.fetch_since(since, limit=1000))
```

### Normalize and Store
```python
from permit_leads.normalizer import PermitNormalizer

normalizer = PermitNormalizer()
normalized_permits = normalizer.normalize_batch(permits, config)

# Insert into permits_gold table
# (Database insertion logic here)
```

## Analytics and Lead Generation

The normalized `permits_gold` table enables powerful analytics:

### High-Value Residential Projects
```sql
SELECT * FROM permits_analytics 
WHERE work_type = 'residential' 
  AND valuation > 50000 
  AND issued_date > NOW() - INTERVAL '30 days'
ORDER BY valuation DESC;
```

### Geographic Clustering
```sql
SELECT jurisdiction, ST_ClusterKMeans(geom, 5) OVER() as cluster_id, *
FROM permits_gold 
WHERE geom IS NOT NULL 
  AND work_type = 'residential';
```

### Contractor Activity Analysis
```sql
SELECT contractor_name, COUNT(*), AVG(valuation)
FROM permits_gold 
WHERE contractor_name IS NOT NULL
GROUP BY contractor_name
ORDER BY COUNT(*) DESC;
```

## Data Quality Monitoring

- **Freshness**: Track last successful update per jurisdiction
- **Completeness**: Monitor field population rates
- **Accuracy**: Validate coordinates and value ranges
- **Consistency**: Check for duplicate permits across sources

## Future Enhancements

1. **Additional Cities**: Fort Worth, San Antonio, El Paso
2. **Real-time Webhooks**: For jurisdictions that support them  
3. **ML Enhancement**: Automated work type classification
4. **Geocoding**: Address standardization and coordinate enrichment
5. **Lead Scoring**: Predictive models for contractor opportunity ranking

## Troubleshooting

### Common Issues
- **Rate Limiting**: Reduce request frequency or implement exponential backoff
- **Data Format Changes**: Monitor API documentation for schema updates
- **Missing Coordinates**: Implement geocoding fallback for address-only records
- **TPIA Delays**: Houston records may have 10+ day delays

### Monitoring Commands
```bash
# Check adapter status
python -m permit_leads.adapters.socrata_adapter --status

# Validate normalization
python -m permit_leads.normalizer --test

# Monitor ETL pipeline
python -m permit_leads.etl_state --check-all
```

---

*This documentation is maintained as part of the Texas permits ingestion feature. For technical support, see the main project README.*