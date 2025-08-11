# Harris County Permits FeatureServer Documentation

## Overview

Harris County provides building permit data through an ArcGIS FeatureServer endpoint. This document details the endpoint capabilities, field structure, and query methods for accessing issued permits data.

## Endpoint Information

**Base URL:** `https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0`

**Service Type:** ArcGIS FeatureServer Layer 0  
**Data Source:** Harris County Issued Permits  
**Update Frequency:** Daily (estimated)  
**Coordinate System:** WGS84 (EPSG:4326)

## JSON/GeoJSON Support

The endpoint supports multiple output formats:

- **JSON**: `f=json` - Returns feature data in Esri JSON format
- **GeoJSON**: `f=geojson` - Returns feature data in GeoJSON format  
- **HTML**: `f=html` - Returns human-readable HTML format
- **PBF**: `f=pbf` - Returns Protocol Buffer format

### Format Examples
```
# JSON format (default)
.../FeatureServer/0/query?f=json

# GeoJSON format  
.../FeatureServer/0/query?f=geojson

# HTML format for browser viewing
.../FeatureServer/0/query?f=html
```

## Key Data Fields

Based on the Harris County FeatureServer configuration and requirements, the following key fields are available:

### Core Required Fields
| Field Name | Type | Description | Example |
|------------|------|-------------|---------|
| `PERMITNUMBER` | String | Unique permit identifier | "2024-123456" |
| `PERMITNAME` | String | Project/permit name | "Single Family Residence" |
| `ISSUEDDATE` | Date | Date permit was issued | "2024-01-15" |
| `FULLADDRESS` | String | Complete property address | "123 Main St, Houston, TX 77001" |
| `APPTYPE` | String | Application/permit type | "Building Permit", "Electrical" |
| `PROJECTNUMBER` | String | Associated project number | "PRJ-2024-001" |
| `EVENTID` | String | Event identifier | "EVT-123456" |

### Additional Available Fields
| Field Name | Type | Description | Example |
|------------|------|-------------|---------|
| `PERMITVALUATION` | Number | Estimated project value | 150000 |
| `APPLICANTNAME` | String | Name of permit applicant | "John Doe Construction" |
| `OWNERNAME` | String | Property owner name | "Jane Smith" |
| `STATUS` | String | Current permit status | "Issued", "Pending", "Finaled" |

**Note:** The fields `PERMITNUMBER`, `PERMITNAME`, `ISSUEDDATE`, `FULLADDRESS`, `APPTYPE`, `PROJECTNUMBER`, and `EVENTID` are specifically mentioned as key fields required for lead generation purposes.

## Service Capabilities

### MaxRecordCount
ArcGIS FeatureServer services typically have a `maxRecordCount` limit that restricts the number of features returned in a single query. For Harris County permits:

**MaxRecordCount:** 2000 records per request (typical ArcGIS default)

To retrieve more than 2000 records, use pagination with `resultOffset` parameter.

### Supported Query Operations
- **Spatial queries**: Query by geographic boundaries
- **Attribute queries**: Filter by field values  
- **Date range filtering**: Filter by date fields
- **Sorting**: Order results by field values
- **Pagination**: Handle large result sets

## Example Query URLs

### Basic Query Structure
```
https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0/query?
where=<condition>&
outFields=<fields>&
orderByFields=<field>&
returnGeometry=<true|false>&
f=<format>&
resultOffset=<offset>&
resultRecordCount=<count>
```

### Last 7 Days Query Example

For permits issued in the last 7 days (replace date in query as needed):

**Complete URL:**
```
https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0/query?where=ISSUEDDATE%20%3E%3D%20TIMESTAMP%20%272024-08-04%2000%3A00%3A00%27&outFields=PERMITNUMBER%2CPERMITNAME%2CISSUEDDATE%2CFULLADDRESS%2CAPPTYPE%2CPROJECTNUMBER%2CEVENTID&orderByFields=ISSUEDDATE%20DESC&returnGeometry=false&f=json&resultOffset=0
```

**URL Parameters Breakdown:**
- `where=ISSUEDDATE >= TIMESTAMP '2024-08-04 00:00:00'` - Last 7 days filter (replace date as needed)
- `outFields=PERMITNUMBER,PERMITNAME,ISSUEDDATE,FULLADDRESS,APPTYPE,PROJECTNUMBER,EVENTID` - Specified key fields only
- `orderByFields=ISSUEDDATE DESC` - Sort by most recent first
- `returnGeometry=false` - Exclude spatial geometry for faster response
- `f=json` - JSON output format
- `resultOffset=0` - Start at first record (for pagination)

**Human-readable format for testing:**
```
https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0/query?
where=ISSUEDDATE >= TIMESTAMP '2024-08-04 00:00:00'&
outFields=PERMITNUMBER,PERMITNAME,ISSUEDDATE,FULLADDRESS,APPTYPE,PROJECTNUMBER,EVENTID&
orderByFields=ISSUEDDATE DESC&
returnGeometry=false&
f=json&
resultOffset=0
```

### Pagination Example with resultOffset

For large datasets exceeding the MaxRecordCount limit, use pagination with `resultOffset`:

**Page 1 (records 0-1999):**
```
.../query?where=ISSUEDDATE >= TIMESTAMP '2024-07-01 00:00:00'&
outFields=PERMITNUMBER,PERMITNAME,ISSUEDDATE,FULLADDRESS,APPTYPE,PROJECTNUMBER,EVENTID&
orderByFields=ISSUEDDATE DESC&
returnGeometry=false&
f=json&
resultOffset=0
```

**Page 2 (records 2000-3999):**
```
.../query?where=ISSUEDDATE >= TIMESTAMP '2024-07-01 00:00:00'&
outFields=PERMITNUMBER,PERMITNAME,ISSUEDDATE,FULLADDRESS,APPTYPE,PROJECTNUMBER,EVENTID&
orderByFields=ISSUEDDATE DESC&
returnGeometry=false&
f=json&
resultOffset=2000
```

**Page 3 (records 4000-5999):**
```
.../query?where=ISSUEDDATE >= TIMESTAMP '2024-07-01 00:00:00'&
outFields=PERMITNUMBER,PERMITNAME,ISSUEDDATE,FULLADDRESS,APPTYPE,PROJECTNUMBER,EVENTID&
orderByFields=ISSUEDDATE DESC&
returnGeometry=false&
f=json&
resultOffset=4000
```

**Pagination Algorithm:**
1. Start with `resultOffset=0`
2. Request up to MaxRecordCount (2000) records
3. If exactly 2000 records returned, more pages likely exist
4. Increment `resultOffset` by 2000 for next page
5. Continue until fewer than 2000 records returned

### Filter by Permit Type
```
https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0/query?where=APPTYPE='Building Permit' AND ISSUEDDATE >= TIMESTAMP '2024-08-04 00:00:00'&outFields=*&f=json
```

### High-Value Projects
```
https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0/query?where=PERMITVALUATION > 100000 AND ISSUEDDATE >= TIMESTAMP '2024-08-04 00:00:00'&outFields=*&orderByFields=PERMITVALUATION DESC&f=json
```

## Alternative Data Access: ePermits Project Status Page

### Why the ePermits "Project Status" Page is Not Ideal for Scraping

Harris County also provides permit information through their ePermits system's "Project Status" page, but this interface has significant limitations for automated data collection:

**URL:** `https://epermits.hctx.net/ProjectStatus/` (example)

#### Major Limitations:

1. **Requires Project Number**: The Project Status page requires users to enter a specific project number to view permit details. This creates a chicken-and-egg problem - you need to know the project number to get the permit information, but you need to scrape permits to discover project numbers.

2. **No Bulk Query Capability**: The interface only shows one project at a time, making it impossible to efficiently collect multiple permits or perform date-range queries.

3. **Interactive Form Requirements**: The page likely uses form submissions, CAPTCHA, or session-based authentication that complicates automated access.

4. **Rate Limiting and Anti-Scraping**: Web interfaces often have aggressive rate limiting, IP blocking, or anti-bot measures that can interrupt data collection.

5. **Inconsistent Data Structure**: HTML parsing is fragile and prone to breaking when the website layout changes, requiring frequent maintenance.

6. **No Standardized Output**: Unlike the FeatureServer API which returns structured JSON/GeoJSON, web scraping produces inconsistent HTML that requires complex parsing logic.

#### Recommended Approach:

**Use the FeatureServer API instead** because it provides:
- ✅ Bulk data access with date range filtering
- ✅ Standardized JSON/GeoJSON output format  
- ✅ Pagination support for large datasets
- ✅ No need for pre-existing project numbers
- ✅ Stable API contract less likely to change
- ✅ Better performance and reliability

## Integration Notes

### Current Implementation
The LeadLedgerPro system already integrates with this endpoint through:

**Configuration File:** `config/registry.yaml`
```yaml
- slug: "tx-harris"
  name: "Harris County"
  provider: "arcgis"
  source_config:
    feature_server: "https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0"
    date_field: "ISSUEDDATE"
    field_map:
      permit_id: "PERMITNUMBER"
      issue_date: "ISSUEDDATE"
      address: "FULLADDRESS"
      description: "PROJECTNAME"
      status: "STATUS"
      work_class: "APPTYPE"
      category: "APPTYPE"
      value: "PERMITVALUATION"
      applicant: "APPLICANTNAME"
      owner: "OWNERNAME"
```

**Adapter:** `permit_leads/adapters/arcgis_feature_service.py`

### Rate Limiting Best Practices
- Implement 1-second delays between requests
- Use reasonable `resultRecordCount` values (≤ 2000)
- Monitor for HTTP 429 (Too Many Requests) responses
- Implement exponential backoff for failed requests

### Error Handling
Common error scenarios to handle:
- **Service unavailable**: HTTP 503 or timeout responses
- **Invalid query**: Malformed where clauses or field names
- **Rate limiting**: HTTP 429 responses
- **Data format changes**: Field renames or type changes

## Data Quality Notes

### Expected Data Volume
- **Daily permits**: 50-200 new permits per day (estimated)
- **Historical data**: Multiple years of permit records available
- **Peak periods**: Higher permit activity in spring/summer months

### Data Completeness
- Not all fields may be populated for every permit
- `PERMITVALUATION` may be zero or null for some permits
- Address formatting may vary between records
- Status values may include various states beyond "Issued"

## Summary

The Harris County FeatureServer endpoint provides robust, API-based access to permit data that is ideal for automated lead generation systems. The standardized JSON output, date filtering capabilities, and pagination support make it far superior to scraping the ePermits Project Status page for bulk data collection purposes.

For integration into lead generation systems, use the FeatureServer API with appropriate rate limiting and error handling to ensure reliable, long-term data access.