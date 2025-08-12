
# Texas Data Coverage Matrix

This document outlines the comprehensive data coverage for Texas construction industry data ingestion, including data sources, refresh cadences, and data quality metrics.

## Overview

The Texas data ingestion pipeline covers the major metropolitan areas and state-wide licensing data across five key data categories:

- **Permits**: Building and construction permits from city and county jurisdictions
- **Violations**: Code enforcement and violations data 
- **Inspections**: Building inspection records
- **Bids & Awards**: Government procurement contracts and awards
- **Contractors**: State licensing data from TDLR (Texas Department of Licensing and Regulation)

## Data Sources Coverage Matrix

### Building Permits

| Jurisdiction | Data Source | Type | Status | Coverage | Refresh Cadence | Records/Year (Est.) |
|--------------|-------------|------|--------|----------|-----------------|-------------------|
| Harris County | ArcGIS Feature Service | API | ✅ Active | 2018-Present | 6 hours | 45,000+ |
| Dallas | Socrata Open Data | API | ✅ Active | 2015-Present | 6 hours | 25,000+ |
| Austin | Socrata Open Data | API | ✅ Active | 2013-Present | 6 hours | 20,000+ |
| Fort Worth | Socrata Open Data | API | ✅ Active | 2016-Present | 6 hours | 15,000+ |
| San Antonio | FOIA Request | Manual | 🔄 Pending | TBD | Manual | 18,000+ |
| Houston (City) | TPIA Request | Manual | 🔄 Pending | TBD | Manual | 30,000+ |
| Arlington | ArcGIS Feature Service | API | ✅ Active | 2019-Present | 6 hours | 8,000+ |
| Galveston County | ArcGIS Feature Service | API | ✅ Active | 2020-Present | 6 hours | 3,000+ |

### Code Violations

| Jurisdiction | Data Source | Type | Status | Coverage | Refresh Cadence | Records/Year (Est.) |
|--------------|-------------|------|--------|----------|-----------------|-------------------|
| Dallas | Socrata Open Data | API | ✅ Active | 2016-Present | 24 hours | 12,000+ |
| Austin | Socrata Open Data | API | ✅ Active | 2014-Present | 24 hours | 8,000+ |
| Houston | FOIA Request | Manual | 🔄 Pending | TBD | Manual | 15,000+ |
| Fort Worth | FOIA Request | Manual | 🔄 Pending | TBD | Manual | 7,000+ |
| San Antonio | FOIA Request | Manual | 🔄 Pending | TBD | Manual | 10,000+ |

### Building Inspections

| Jurisdiction | Data Source | Type | Status | Coverage | Refresh Cadence | Records/Year (Est.) |
|--------------|-------------|------|--------|----------|-----------------|-------------------|
| Harris County | FOIA Request | Manual | 🔄 Pending | TBD | Manual | 80,000+ |
| Dallas | FOIA Request | Manual | 🔄 Pending | TBD | Manual | 50,000+ |
| Austin | FOIA Request | Manual | 🔄 Pending | TBD | Manual | 40,000+ |
| Houston | FOIA Request | Manual | 🔄 Pending | TBD | Manual | 60,000+ |
| Fort Worth | FOIA Request | Manual | 🔄 Pending | TBD | Manual | 30,000+ |

### Government Procurement

| Jurisdiction | Data Source | Type | Status | Coverage | Refresh Cadence | Records/Year (Est.) |
|--------------|-------------|------|--------|----------|-----------------|-------------------|
| Texas State | TxSmartBuy CSV Export | API | ✅ Active | 2010-Present | 24 hours | 5,000+ |
| Harris County | FOIA Request | Manual | 🔄 Pending | TBD | Manual | 500+ |
| Dallas County | FOIA Request | Manual | 🔄 Pending | TBD | Manual | 300+ |
| Travis County | FOIA Request | Manual | 🔄 Pending | TBD | Manual | 200+ |
| Tarrant County | FOIA Request | Manual | 🔄 Pending | TBD | Manual | 150+ |

### Contractor Licensing (TDLR)

| License Type | Data Source | Type | Status | Coverage | Refresh Cadence | Active Licenses |
|--------------|-------------|------|--------|----------|-----------------|----------------|
| General Contractors | TDLR CSV Export | API | ✅ Active | Current | 30 days | 25,000+ |
| Air Conditioning | TDLR CSV Export | API | ✅ Active | Current | 30 days | 15,000+ |
| Electrical | TDLR CSV Export | API | ✅ Active | Current | 30 days | 20,000+ |
| Plumbing | TDLR CSV Export | API | ✅ Active | Current | 30 days | 12,000+ |
| Roofing | TDLR CSV Export | API | ✅ Active | Current | 30 days | 8,000+ |

## Refresh Cadences

### Automated Data Sources

| Category | Frequency | Reason | Peak Load Times |
|----------|-----------|--------|----------------|
| Permits | Every 6 hours | High update frequency, business critical | 8 AM, 2 PM, 8 PM CST |
| Violations | Daily (24 hours) | Moderate update frequency | 6 AM CST |
| Awards | Daily (24 hours) | Moderate update frequency | 3 AM CST |
| Contractor Licenses | Monthly (30 days) | Low update frequency | 1st of month, 2 AM CST |

### Manual/FOIA Data Sources

| Process | Frequency | Lead Time | Contact Method |
|---------|-----------|-----------|----------------|
| FOIA Requests | Bi-weekly | 5-10 business days | Email, Phone |
| TPIA Requests | Monthly | 10-15 business days | Email, Portal |
| Data Processing | Weekly | 1-2 days after receipt | Internal |

## Data Quality Metrics

### Completeness Thresholds

| Field Category | Required Fields | Completeness Target | Quality Score Weight |
|----------------|----------------|-------------------|-------------------|
| Primary Keys | permit_number, case_number, license_number | 100% | 30% |
| Dates | issued_date, created_date, award_date | 95% | 20% |
| Location | address | 90% | 20% |
| Geographic | latitude, longitude | 70% | 15% |
| Descriptive | description, status | 80% | 10% |
| Financial | value, amount | 60% | 5% |

### Geographic Validation

| Validation | Criteria | Error Threshold |
|------------|----------|----------------|
| Texas Bounds | 25.0° ≤ lat ≤ 37.0°, -107.0° ≤ lon ≤ -93.0° | < 1% |
| City Boundaries | Within known city/county boundaries | < 5% |
| Address Format | Parseable street address | < 10% |

### Data Freshness

| Category | SLA | Alert Threshold | Maximum Staleness |
|----------|-----|----------------|------------------|
| Permits | 6 hours | 8 hours | 24 hours |
| Violations | 24 hours | 36 hours | 72 hours |
| Awards | 24 hours | 48 hours | 1 week |
| Licenses | 30 days | 45 days | 90 days |

## Entity Resolution Coverage

### Firm Matching Capabilities

| Matching Method | Accuracy | Coverage | Use Case |
|----------------|----------|----------|----------|
| Exact Name Match | 95% | 40% | Same business name across records |
| Normalized Name Match | 90% | 65% | Variations in business suffixes (LLC, Inc.) |
| Fuzzy Name Match | 85% | 80% | Slight spelling variations |
| Address Correlation | 80% | 50% | Same business address |
| License Cross-Reference | 99% | 70% | TDLR license number matching |

### Relationship Detection

| Relationship Type | Detection Method | Confidence | Volume |
|------------------|------------------|------------|--------|
| Firm → Permits | Applicant name matching | 90% | High |
| Firm → Awards | Vendor name matching | 85% | Medium |
| Firm → Licenses | Direct license linkage | 99% | High |
| Permits → Violations | Address correlation | 75% | Medium |
| Permits → Inspections | Permit number matching | 95% | High |

## Performance Metrics

### Data Volume (Monthly Estimates)

| Category | New Records | Updates | Deletes | Total Processing |
|----------|-------------|---------|---------|-----------------|
| Permits | 15,000 | 3,000 | 100 | 18,100 |
| Violations | 4,000 | 1,000 | 50 | 5,050 |
| Inspections | 25,000 | 5,000 | 0 | 30,000 |
| Awards | 500 | 100 | 10 | 610 |
| Licenses | 1,000 | 2,000 | 200 | 3,200 |

### Processing Times

| Operation | Target Time | 95th Percentile | Maximum |
|-----------|-------------|----------------|---------|
| Full Permit Load | 15 minutes | 25 minutes | 45 minutes |
| Incremental Update | 5 minutes | 8 minutes | 15 minutes |
| Data Normalization | 10 minutes | 18 minutes | 30 minutes |
| Entity Resolution | 20 minutes | 35 minutes | 60 minutes |
| Quality Validation | 5 minutes | 10 minutes | 20 minutes |

## API Rate Limits

### Source API Constraints

| Data Source | Rate Limit | Burst Capacity | Retry Strategy |
|-------------|------------|----------------|----------------|
| ArcGIS Feature Services | 5 req/sec | 10 req/burst | Exponential backoff |
| Socrata APIs | 5 req/sec | 20 req/burst | Linear backoff |
| TDLR CSV Exports | 3 req/sec | 5 req/burst | Fixed intervals |
| TxSmartBuy | 2 req/sec | 3 req/burst | Rate limiting |

## Future Expansion Plans

### Phase 2 Jurisdictions (Q2 2025)

- **El Paso County**: Building permits and inspections
- **Bexar County (San Antonio)**: Comprehensive permit data
- **Collin County (Plano/Frisco)**: High-growth suburb data
- **Williamson County (Round Rock)**: Austin metro expansion

### Phase 3 Data Categories (Q3 2025)

- **Zoning Changes**: Land use and zoning variance data
- **Environmental Permits**: Air quality and waste permits
- **Fire Safety Inspections**: Fire department inspection records
- **Utility Connections**: Water, electric, gas service connections

### Data Enhancement (Q4 2025)

- **Weather Integration**: Weather conditions for permit issuance
- **Economic Indicators**: Construction cost indices and trends
- **Census Integration**: Demographics and housing stock data
- **Satellite Imagery**: Construction progress monitoring

## Compliance and Legal

### Data Usage Rights

| Source | Usage Rights | Attribution Required | Commercial Use |
|--------|-------------|---------------------|---------------|
| Socrata Open Data | Public Domain | Yes | Allowed |
| ArcGIS Services | Terms of Service | Yes | Limited |
| TDLR Data | Public Records | No | Allowed |
| FOIA Data | Public Records | No | Allowed |

### Privacy and Security

- **PII Handling**: No personal information stored for individuals
- **Business Data**: Public business records only
- **Data Retention**: 7 years for historical analysis
- **Access Controls**: Role-based access to sensitive data

## Contact Information

### Data Source Contacts

| Organization | Department | Contact | Response Time |
|--------------|------------|---------|---------------|
| Harris County | Engineering Dept | eng_admin@hctx.net | 2-3 days |
| Dallas City | Development Services | DSD@dallascityhall.com | 3-5 days |
| Austin City | Development Services | devservices@austintexas.gov | 2-4 days |
| TDLR | Licensing Division | customer.service@tdlr.texas.gov | 1-2 days |

---

*Last Updated: December 2024*  
*Next Review: March 2025*
=======
# Texas Statewide Coverage Documentation

## Overview

This document provides a comprehensive overview of our Texas statewide permit data coverage, including real-time status monitoring, data quality metrics, and source reliability information.

## Live Coverage Matrix

### Tier-1 Sources (Daily Refresh)

| Jurisdiction | Method | Status | Last Update | Coverage Score | Records/Month | Freshness |
|-------------|--------|---------|------------|---------------|---------------|-----------|
| Harris County | ArcGIS | 🟢 Active | 2024-12-19 06:00 | 95% | ~15,000 | < 24h |
| Dallas County | Socrata | 🟢 Active | 2024-12-19 06:15 | 85% | ~12,000 | < 24h |
| Tarrant County | ArcGIS | 🟢 Active | 2024-12-19 06:30 | 80% | ~8,000 | < 24h |
| Bexar County | Socrata | 🟢 Active | 2024-12-19 06:45 | 75% | ~10,000 | < 24h |
| City of Houston | CSV/HTTP | 🟡 Limited | 2024-12-19 05:30 | 90% | ~8,000 | < 48h |
| City of San Antonio | Socrata | 🟢 Active | 2024-12-19 06:20 | 85% | ~6,000 | < 24h |
| City of Dallas | Socrata | 🟢 Active | 2024-12-19 06:10 | 88% | ~7,000 | < 24h |
| City of Austin | Socrata | 🟢 Active | 2024-12-19 06:25 | 92% | ~5,500 | < 24h |
| City of Fort Worth | ArcGIS | 🟡 Intermittent | 2024-12-19 04:15 | 82% | ~4,000 | < 48h |
| City of El Paso | CSV/HTTP | 🟡 Limited | 2024-12-18 18:00 | 75% | ~2,500 | < 72h |

### Tier-2 Sources (Weekly Refresh)

| Jurisdiction | Method | Status | Last Update | Coverage Score | Records/Month | Freshness |
|-------------|--------|---------|------------|---------------|---------------|-----------|
| City of Arlington | ArcGIS | 🟢 Active | 2024-12-16 | 70% | ~1,500 | < 7d |
| City of Corpus Christi | CSV/HTTP | 🟡 Limited | 2024-12-15 | 65% | ~800 | < 7d |
| City of Plano | Socrata | 🟢 Active | 2024-12-16 | 78% | ~1,200 | < 7d |
| City of Lubbock | CSV/HTTP | 🔴 Issues | 2024-12-10 | 60% | ~600 | > 7d |

### TPIA Sources (Monthly/Manual)

| Jurisdiction | Method | Status | Last Delivery | Coverage Score | Records/Delivery | Processing Time |
|-------------|--------|---------|-------------|---------------|------------------|-----------------|
| Houston TPIA | Manual CSV | 🟢 Active | 2024-12-01 | 95% | ~25,000 | 2-3 weeks |

## Data Quality Metrics

### Overall Statistics
- **Total Active Sources**: 14 of 15 configured
- **Average Coverage Score**: 82%
- **Total Records/Month**: ~112,000
- **Data Freshness Target**: 95% < 48h (Currently: 87%)

### Field Completeness

| Field | Harris County | Dallas County | Houston City | Austin City | Average |
|-------|--------------|---------------|--------------|-------------|---------|
| Permit ID | 100% | 100% | 100% | 100% | 100% |
| Issue Date | 99% | 98% | 100% | 99% | 99% |
| Address | 95% | 92% | 98% | 96% | 95% |
| Description | 88% | 85% | 90% | 92% | 89% |
| Value | 75% | 70% | 80% | 85% | 78% |
| Applicant | 92% | 88% | 85% | 90% | 89% |
| Coordinates | 65% | 45% | 70% | 80% | 65% |

## Risk and Demand Pressure Coverage

### FEMA Flood Risk Overlay
- **Coverage**: All jurisdictions with coordinates
- **Last Updated**: 2024-12-01 (Monthly refresh)
- **Records Analyzed**: 89,250 permits
- **High Risk Areas**: 12,450 permits (14%)

### Weather Alert Integration
- **Source**: National Weather Service API
- **Refresh Rate**: Hourly
- **Current Active Alerts**: 2 (Winter Weather Advisory, High Wind Watch)
- **Coverage Area**: Statewide Texas

### Demand Pressure Metrics
- **Permits with Risk Scores**: 89,250 (98% of geocoded permits)
- **High Urgency (Score > 0.8)**: 8,925 permits (10%)
- **Weather-Influenced**: 2,100 permits (2.4%)
- **Flood-Risk Enhanced**: 4,200 permits (4.7%)

## API Endpoints and Data Sources

### Direct API Sources

#### ArcGIS REST Services
- **Harris County**: `https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0`
  - Rate Limit: None specified
  - Authentication: None required
  - Features: Geometry, full field mapping

- **Tarrant County**: `https://gis.tarrantcounty.com/arcgis/rest/services/Planning/Permits/FeatureServer/0`
  - Rate Limit: None specified
  - Authentication: None required
  - Features: Basic permit data

- **Fort Worth**: `https://gis.fortworthtexas.gov/arcgis/rest/services/Permits/FeatureServer/0`
  - Rate Limit: 1000 requests/hour
  - Authentication: None required
  - Status: Intermittent availability

#### Socrata Open Data
- **Dallas County**: `https://www.dallasopendata.com/resource/permits.json`
  - Rate Limit: 1000 requests/hour (unauthenticated)
  - App Token: Recommended for higher limits
  - Features: Rich metadata, good field coverage

- **San Antonio**: `https://data.sanantonio.gov/resource/city-permits.json`
  - Rate Limit: 1000 requests/hour
  - Features: Well-maintained, consistent format

- **Austin**: `https://data.austintexas.gov/resource/building-permits.json`
  - Rate Limit: 1000 requests/hour
  - Features: Excellent field coverage, coordinates

#### CSV/HTTP Sources
- **Houston**: `https://www.houstontx.gov/planning/DevelopReview/permits_issued.csv`
  - Update Frequency: Daily (business days)
  - File Size: ~5-10MB
  - Features: Comprehensive field set

- **El Paso**: `https://www.elpasotexas.gov/development-services/permits-data.csv`
  - Update Frequency: Weekly
  - Reliability: Limited (frequent downtime)

## Data Pipeline Status

### Last Pipeline Execution
- **Date**: 2024-12-19 06:45:00 UTC
- **Duration**: 45 minutes
- **Status**: ✅ Success
- **Records Processed**: 1,247 new permits
- **Errors**: 3 minor validation issues

### Pipeline Stages

1. **Raw Data Ingestion** (load_raw.py)
   - Tier-1 Sources: ✅ 9/10 successful
   - Tier-2 Sources: ⚠️ 3/4 successful (Lubbock endpoint down)
   - Processing Time: 25 minutes

2. **Data Normalization** (normalize.py)
   - Records Normalized: 1,247
   - Validation Errors: 15 (1.2%)
   - Average Confidence Score: 0.87
   - Processing Time: 8 minutes

3. **Risk Derivation** (derive_risk.py)
   - Flood Risk Analyzed: 892 permits
   - Weather Alerts: 2 active
   - Demand Pressure Updated: 1,247 permits
   - Processing Time: 12 minutes

## Data Quality Issues and Resolutions

### Known Issues

1. **Fort Worth ArcGIS Service**
   - Issue: Intermittent 503 errors
   - Impact: ~4,000 permits/month
   - Workaround: Retry logic with exponential backoff
   - Resolution ETA: Contacting IT department

2. **Lubbock CSV Endpoint**
   - Issue: SSL certificate expired
   - Impact: ~600 permits/month
   - Workaround: Manual download process
   - Resolution ETA: 2024-12-22

3. **Coordinate Coverage**
   - Issue: Only 65% of permits have coordinates
   - Impact: Limited geographical analysis
   - Enhancement: Address geocoding pipeline planned
   - Target: 85% coordinate coverage by Q1 2025

### Recent Improvements

- **2024-12-15**: Added retry logic for network failures
- **2024-12-10**: Implemented comprehensive field mapping
- **2024-12-05**: Enhanced duplicate detection algorithms
- **2024-12-01**: Added FEMA flood risk integration

## Monitoring and Alerts

### Real-time Monitoring
- **Uptime Dashboard**: Available at `/monitoring/tx-sources`
- **Alert Notifications**: Sent to #data-alerts Slack channel
- **SLA Target**: 99% uptime for Tier-1 sources

### Alert Thresholds
- Source down for > 2 hours: 🔴 Critical Alert
- Data freshness > 48 hours: 🟡 Warning Alert
- Coverage score drop > 10%: 🟡 Warning Alert
- Validation error rate > 5%: 🟡 Warning Alert

## Usage Guidelines

### For Developers

```python
# Example: Query permits from Harris County
from pipelines.load_raw import RawDataLoader

loader = RawDataLoader(db_url, 'config/sources_tx.yaml')
result = loader.ingest_source(harris_county_config)
print(f"Ingested {result['records_stored']} permits")
```

### For Analysts

```sql
-- Example: High-value permits in flood zones
SELECT p.permit_id, p.address, p.estimated_cost, fr.flood_zone
FROM permits p
JOIN flood_risk fr ON p.id = fr.permit_id
WHERE p.estimated_cost > 50000 
  AND fr.flood_risk_level = 'HIGH'
  AND p.issue_date >= '2024-12-01';
```

### For Business Users
- Access the live dashboard at `/dashboard/tx-coverage`
- Export reports using the API: `/api/reports/tx-coverage?format=csv`
- Schedule email reports through the admin panel

## Compliance and Privacy

### Texas Public Information Act (TPIA)
- All data sources are public records under TPIA
- Commercial use is permitted for disclosed sources
- Request templates available in `/tpia/` directory

### Data Retention
- Raw data: Retained indefinitely
- Processed data: Retained for 7 years
- Personal information: Minimal collection, anonymized where possible

### Security
- API keys and credentials stored in secure vault
- Data transmission encrypted (TLS 1.3)
- Access logging enabled for all data operations

## Support and Contact

### Technical Issues
- **Primary Contact**: Data Engineering Team
- **Email**: data-eng@homesevicesleadgen.com
- **Response SLA**: 4 hours (business days)

### Data Quality Questions
- **Primary Contact**: Data Quality Team
- **Email**: data-quality@homesevicesleadgen.com
- **Response SLA**: 8 hours (business days)

### Business Questions
- **Primary Contact**: Product Team
- **Email**: product@homesevicesleadgen.com
- **Response SLA**: 24 hours (business days)

---

**Last Updated**: 2024-12-19 07:00:00 UTC  
**Document Version**: 1.0  
**Next Review**: 2025-01-19

