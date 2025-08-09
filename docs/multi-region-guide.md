# Multi-Region Configuration Guide

LeadLedgerPro now supports multi-region scale with configurable jurisdictions and data sources. This guide covers the new multi-region system.

## Quick Start

### 1. Environment Setup

```bash
# Copy and configure environment variables
cp .env.example .env

# Edit .env to set:
DATABASE_URL=postgresql://user:password@localhost:5432/leadledger
USE_POSTGIS=true  # Optional: for advanced spatial queries
```

### 2. Database Migration

```bash
# Run database migrations
python -m backend.app.postgis_migration --migrate

# Sync registry configuration to database
python -m backend.app.admin_tools sync --all
```

### 3. Region-Aware Scraping

```bash
# Scrape all active jurisdictions
python -m permit_leads scrape --region-aware --days 7

# Scrape specific jurisdiction
python -m permit_leads scrape --jurisdiction tx-harris --days 3

# Test jurisdiction configuration
python -m backend.app.admin_tools test tx-harris
```

## Configuration

### Registry File: `config/registry.yaml`

The registry defines regions, jurisdictions, and their data source configurations:

```yaml
regions:
  - slug: "tx"
    name: "Texas" 
    level: "state"
    parent: null

jurisdictions:
  - slug: "tx-harris"
    name: "Harris County"
    region_slug: "tx"
    state: "TX"
    provider: "arcgis"
    source_config:
      feature_server: "https://example.com/FeatureServer/0"
      field_map:
        permit_id: "PERMITNUMBER"
        address: "FULLADDRESS"
```

### Data Providers

Supported data source types:

- **arcgis**: ArcGIS Feature Server
- **accela**: Accela HTML interface  
- **opengov**: OpenGov API
- **html**: Generic HTML scraping

## API Usage

### Region Filtering

```python
from backend.app.leads_api import LeadsAPI

api = LeadsAPI(database_url)

# Filter by region
leads = api.get_leads(region="tx-houston", limit=50)

# Geographic search
leads = api.get_leads(
    lat=29.7604, 
    lon=-95.3698, 
    radius_km=10,
    min_score=70
)

# List available regions
regions = api.get_regions()
```

### Admin Tools

```bash
# List all regions
python -m backend.app.admin_tools list regions

# List jurisdictions in a region  
python -m backend.app.admin_tools list jurisdictions --region tx-houston

# Enable/disable jurisdiction
python -m backend.app.admin_tools status tx-harris --active
python -m backend.app.admin_tools status tx-harris --inactive
```

## PostGIS Integration

When `USE_POSTGIS=true`, LeadLedgerPro uses PostGIS for efficient spatial queries:

- Automatic geometry column creation (`geom`)
- Spatial indexing with GIST
- ST_DWithin for radius queries
- Trigger-based geometry updates

Fallback to Haversine distance when PostGIS unavailable.

## Region-Aware ML Scoring

```bash
# Train region-specific calibrators
python -m backend.app.region_scoring --train --save models/regional_calibration.pkl

# Test scoring with regional adjustment
python -m backend.app.region_scoring --load models/regional_calibration.pkl \
    --score 85 --region tx-houston --state TX
```

## Adding New Jurisdictions

1. **Update Registry**: Add to `config/registry.yaml`
2. **Configure Data Source**: Set provider and field mapping
3. **Sync to Database**: `python -m backend.app.admin_tools sync --jurisdictions`
4. **Test Configuration**: `python -m backend.app.admin_tools test new-jurisdiction-slug`
5. **Activate**: `python -m backend.app.admin_tools status new-jurisdiction-slug --active`

## Migration from Legacy System

The new system maintains backward compatibility:

```bash
# Legacy scraping still works
python -m permit_leads scrape --source city_of_houston --days 7

# Gradually migrate to region-aware
python -m permit_leads scrape --region-aware --days 7
```

## Plans and Pricing

Region-aware plans are configured in the registry:

```yaml
plans:
  - slug: "metro-starter"
    monthly_price_cents: 9900
    credits: 100
    scope: "metro"
    regions: ["tx-houston"]
```

## Troubleshooting

### Common Issues

1. **Config Loading Errors**: Verify `config/registry.yaml` syntax
2. **Database Connection**: Check `DATABASE_URL` environment variable
3. **PostGIS Issues**: Set `USE_POSTGIS=false` to disable spatial features
4. **Jurisdiction Not Found**: Run `admin_tools sync --jurisdictions`

### Debug Mode

```bash
# Enable verbose logging
python -m permit_leads scrape --region-aware --verbose --days 1 --dry-run
```

### Performance Monitoring

Monitor jurisdiction performance:

```bash
# Check lead counts by jurisdiction
python -m backend.app.admin_tools list jurisdictions

# Test individual jurisdiction
python -m backend.app.admin_tools test tx-harris
```