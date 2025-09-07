# GitHub Copilot Coding Agent Allowlist Request

## Overview

This document contains a request for an administrator to add specific URL patterns to the repository/organization GitHub Copilot coding agent allowlist. These patterns are required for the Home Services Lead Generation system to properly access and integrate with Texas city government data sources, open data portals, ArcGIS mapping services, and supporting infrastructure.

## Required Allowlist Patterns

Please add the following URL patterns to the GitHub Copilot coding agent allowlist:

```
www.houstontx.gov
*.houstontx.gov
houstonpermittingcenter.org
cohtora.houstontx.gov
services.arcgis.com
*.arcgis.com
data.austintexas.gov
data.sanantonio.gov
opendata.sanantonio.gov
gis.dallascityhall.com
*.supabase.co
httpbin.org
```

## Pattern Justification

### Houston City Government Domains

- **`www.houstontx.gov`** - Primary Houston city government website
  - Used for: Accessing permit data and city services
  - Purpose: Weekly archive pages and official permit records

- **`*.houstontx.gov`** - All Houston city government subdomains
  - Used for: Various city department services and data endpoints
  - Purpose: Comprehensive access to city data sources

- **`cohtora.houstontx.gov`** - City of Houston TORA (Technology Operations and Risk Analytics) system
  - Used for: Advanced city data analytics and reporting
  - Purpose: Technical data access and analysis tools

### Permitting Services

- **`houstonpermittingcenter.org`** - Houston Permitting Center
  - Used for: Building permit applications and records
  - Purpose: Sold-permits application and permit tracking

### ArcGIS Mapping Services

- **`services.arcgis.com`** - Esri ArcGIS Online services
  - Used for: Geospatial data and mapping services
  - Purpose: Accessing ArcGIS layers and spatial permit data

- **`*.arcgis.com`** - All ArcGIS subdomains and services
  - Used for: Complete ArcGIS ecosystem access
  - Purpose: Potential ArcGIS layers and mapping integrations

### Texas City Open Data Portals

- **`data.austintexas.gov`** - Austin Open Data Portal (Socrata)
  - Used for: Austin building permits and city data
  - Purpose: Issued construction permits dataset (3syk-w9eu) via Socrata API

- **`data.sanantonio.gov`** - San Antonio Open Data Portal (Socrata)
  - Used for: San Antonio building permits and city data
  - Purpose: Building permit records and city services data

- **`opendata.sanantonio.gov`** - San Antonio Alternative Open Data Portal
  - Used for: Alternative San Antonio data endpoints
  - Purpose: Backup/alternative access to San Antonio permit data

- **`gis.dallascityhall.com`** - Dallas GIS Services
  - Used for: Dallas building permits and geospatial data
  - Purpose: Dallas city GIS services and permit location data

### Database and Infrastructure Services

- **`*.supabase.co`** - Supabase Database Platform
  - Used for: Real-time database and authentication services
  - Purpose: Primary database backend for permit data storage and user management

### Development and Testing Services

- **`httpbin.org`** - HTTP Testing Service
  - Used for: HTTP request/response testing and debugging
  - Purpose: API development, testing request formatting, and debugging data integrations

## Coverage Areas

These patterns provide access to:

1. **Weekly Archive Pages** - Regular permit data updates from Houston city sources
2. **Sold-Permits Application** - Real-time permit sales and transaction data
3. **ArcGIS Layers** - Geospatial permit data and mapping overlays
4. **Multi-City Open Data** - Austin, San Antonio, and Dallas permit datasets
5. **Supabase Database Services** - Real-time data storage and synchronization
6. **Development Tools** - HTTP testing and API debugging capabilities

## Technical Context

The Home Services Lead Generation system integrates with these data sources to:

- Scrape building permit data from Houston city government
- Access geospatial permit information through ArcGIS services
- Collect permit data from major Texas cities (Austin, San Antonio, Dallas)
- Store and synchronize data through Supabase real-time database
- Generate leads from permit activity for home services businesses
- Provide real-time updates on construction and renovation permits
- Test and debug API integrations during development

## Implementation Details

These patterns are referenced in the following system components:

- Houston permit adapters and scrapers
- ArcGIS integration modules
- Austin Socrata API connectors (data.austintexas.gov)
- San Antonio open data adapters (data.sanantonio.gov, opendata.sanantonio.gov)
- Dallas GIS service integrations (gis.dallascityhall.com)
- Supabase database client and real-time subscriptions
- Weekly data synchronization processes
- Permit data enrichment services
- HTTP testing and debugging utilities

## Security Considerations

All patterns listed are:

- Public government data sources (city open data portals)
- Legitimate business data endpoints (ArcGIS services)
- Authorized cloud database services (Supabase)
- Standard development/testing tools (httpbin.org)
- Required for legal permit data access
- Essential for system functionality

## Request Priority

**High** - These patterns are essential for the core functionality of the multi-city permit data ingestion system. Without access to these domains, the application cannot properly:

- Fetch current permit data from Houston, Austin, San Antonio, and Dallas
- Update lead generation pipelines across Texas metro areas
- Provide accurate geospatial information through ArcGIS services
- Maintain data synchronization via Supabase real-time database
- Test and debug API integrations during development
- Store and retrieve permit data efficiently

## Contact Information

For questions about this allowlist request, please contact the development team or refer to the repository documentation for technical details about the data integration requirements.
