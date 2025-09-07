# Unified Sources Configuration

The `config/sources.yml` file provides a unified registry for all data sources used by the probe and ETL systems. This is the "one registry to rule them all" that centralizes source configuration.

## Format

Each source entry follows this standard format:

```yaml
- key: unique_source_identifier
  kind: source_type                    # arcgis, socrata, static_xlsx, etc.
  # ... type-specific configuration
  date_field: field_name              # Field containing the date for incremental queries
  auth: authentication_method         # none, app_token, basic, etc.
  lookback_days: number              # Default lookback period for incremental queries
```

## Source Types

### ArcGIS FeatureServer/MapServer

```yaml
- key: example_arcgis_source
  kind: arcgis
  base: "https://hostname/path/FeatureServer/0"
  date_field: ISSUEDDATE
  date_unit: ms_epoch                 # or 'date' for standard date format
  auth: none
  lookback_days: 7
```

**Requirements:**
- `base` URL must point to a FeatureServer or MapServer layer endpoint
- URL must return valid JSON when appended with `?f=pjson`
- `date_unit` specifies whether dates are milliseconds since epoch or standard dates

### Socrata Open Data

```yaml
- key: example_socrata_source
  kind: socrata
  host: data.example.gov
  resource: dataset-id-1234
  app_token_env: EXAMPLE_SOCRATA_APP_TOKEN
  date_field: issued_date
  auth: app_token
  lookback_days: 7
```

**Requirements:**
- `host` is the Socrata domain (without https://)
- `resource` is the dataset identifier
- `app_token_env` references environment variable containing app token

### Static Excel/CSV Files

```yaml
- key: example_xlsx_source
  kind: static_xlsx
  url: ${EXAMPLE_XLSX_URL}
  parse: custom_parser_name
  date_field: issue_date
  auth: none
  lookback_days: 365
```

**Requirements:**
- `url` can reference environment variables using `${VAR_NAME}` syntax
- `parse` specifies the custom parsing method for the file format

## Environment Variables

The configuration supports environment variable substitution using `${VAR_NAME}` syntax:

- `${HOUSTON_WEEKLY_XLSX_URL}` - URL for Houston weekly permit data
- `${SA_PERMITS_RESOURCE_ID}` - San Antonio Socrata dataset ID
- `${FORT_WORTH_PERMITS_RESOURCE_ID}` - Fort Worth Socrata dataset ID
- `${AUSTIN_SOCRATA_APP_TOKEN}` - Austin Socrata API app token
- `${SA_SOCRATA_APP_TOKEN}` - San Antonio Socrata API app token
- `${DALLAS_SOCRATA_APP_TOKEN}` - Dallas Socrata API app token
- `${FORT_WORTH_SOCRATA_APP_TOKEN}` - Fort Worth Socrata API app token

## Validation

Use the provided validation scripts to ensure configuration integrity:

```bash
# Test configuration format and structure
python test_unified_sources.py

# Validate ArcGIS endpoints return JSON (requires internet)
python validate_arcgis_endpoints.py
```

## Usage

### Loading Sources in Python

```python
import yaml
from pathlib import Path

def load_sources():
    """Load source configurations from unified registry."""
    with open("config/sources.yml") as f:
        return yaml.safe_load(f)

sources = load_sources()
for source in sources:
    print(f"Source: {source['key']} ({source['kind']})")
```

### Filtering by Type

```python
# Get all ArcGIS sources
arcgis_sources = [s for s in sources if s['kind'] == 'arcgis']

# Get all Socrata sources  
socrata_sources = [s for s in sources if s['kind'] == 'socrata']
```

### Environment Variable Resolution

```python
import os
import re

def resolve_env_vars(config_value):
    """Resolve ${VAR_NAME} patterns in configuration values."""
    if isinstance(config_value, str):
        return re.sub(r'\$\{([^}]+)\}', lambda m: os.getenv(m.group(1), ''), config_value)
    return config_value

# Apply to all source configurations
for source in sources:
    for key, value in source.items():
        source[key] = resolve_env_vars(value)
```

## Texas Data Sources Included

The current configuration includes these Texas jurisdictions:

| Key | Type | Jurisdiction | Coverage |
|-----|------|-------------|----------|
| `city_of_houston_weekly` | static_xlsx | Houston | Weekly permits |
| `city_of_houston_sold` | arcgis | Harris County | Issued permits |  
| `city_of_austin_permits` | socrata | Austin | Building permits |
| `city_of_san_antonio_permits` | socrata | San Antonio | Building permits |
| `city_of_dallas_permits` | socrata | Dallas | Building permits |
| `harris_county_permits` | arcgis | Harris County | County permits |
| `city_of_arlington_permits` | arcgis | Arlington | Building permits |
| `galveston_county_permits` | arcgis | Galveston County | Building permits |
| `city_of_fort_worth_permits` | socrata | Fort Worth | Building permits |

## Migration from Legacy Configurations

This unified configuration complements (but does not replace) the existing `permit_leads/config/sources.yaml` file. The legacy configuration continues to work for backward compatibility.

For new implementations, use this unified `config/sources.yml` format for consistency across probe and ETL systems.