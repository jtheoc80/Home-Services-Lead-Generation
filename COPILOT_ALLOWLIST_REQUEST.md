# GitHub Copilot Coding Agent Allowlist Request

## Overview

This document contains a request for an administrator to add specific URL patterns to the repository/organization GitHub Copilot coding agent allowlist. These patterns are required for the Home Services Lead Generation system to properly access and integrate with Houston city government data sources and ArcGIS mapping services.

## Required Allowlist Patterns

Please add the following URL patterns to the GitHub Copilot coding agent allowlist:

```
www.houstontx.gov
*.houstontx.gov
houstonpermittingcenter.org
cohtora.houstontx.gov
services.arcgis.com
*.arcgis.com
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

## Coverage Areas

These patterns provide access to:

1. **Weekly Archive Pages** - Regular permit data updates from Houston city sources
2. **Sold-Permits Application** - Real-time permit sales and transaction data
3. **ArcGIS Layers** - Geospatial permit data and mapping overlays

## Technical Context

The Home Services Lead Generation system integrates with these data sources to:

- Scrape building permit data from Houston city government
- Access geospatial permit information through ArcGIS services
- Generate leads from permit activity for home services businesses
- Provide real-time updates on construction and renovation permits

## Implementation Details

These patterns are referenced in the following system components:

- Houston permit adapters and scrapers
- ArcGIS integration modules
- Weekly data synchronization processes
- Permit data enrichment services

## Security Considerations

All patterns listed are:

- Public government data sources
- Legitimate business data endpoints
- Required for legal permit data access
- Essential for system functionality

## Request Priority

**High** - These patterns are essential for the core functionality of the permit data ingestion system. Without access to these domains, the application cannot properly:

- Fetch current permit data
- Update lead generation pipelines
- Provide accurate geospatial information
- Maintain data synchronization

## Contact Information

For questions about this allowlist request, please contact the development team or refer to the repository documentation for technical details about the data integration requirements.
