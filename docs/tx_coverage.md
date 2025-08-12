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