# Home-Services-Lead-Generation

Creating Leads For Home Service Contractors

*Note: This project is intended to be renamed to **LeadLedgerPro** in a future release.*

## Overview

This repository provides tools and scrapers for generating leads for home service contractors by collecting and processing building permit data from various municipalities.

## Setup

### Prerequisites
- Python 3.11 or higher
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/jtheoc80/Home-Services-Lead-Generation.git
   cd Home-Services-Lead-Generation
   ```

2. **Set up environment variables:**
   ```bash
   # Copy environment example files
   cp .env.example .env
   cp permit_leads/.env.example permit_leads/.env
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   
   # Edit the .env files with your configuration
   ```

3. **Install dependencies:**
   ```bash
   cd permit_leads
   pip install -r requirements.txt
   ```

4. **Test the installation:**
   ```bash
   # Test with sample data
   python -m permit_leads --source city_of_houston --sample --days 7
   ```

### Required Secrets

For production deployments and automated workflows, the following secrets must be configured:

#### GitHub Repository Secrets
- **`DATABASE_URL`**: Database connection string for storing permit data
  - Format: `postgresql://user:password@host:port/database` or `sqlite:///path/to/database.db`
  - Required for: Backend API, ML training pipeline, data persistence

#### Optional API Keys (for enhanced features)
- **`MAPBOX_TOKEN`**: For Mapbox geocoding service
- **`GOOGLE_MAPS_API_KEY`**: For Google Maps geocoding service

To add repository secrets:
1. Go to your GitHub repository Settings
2. Navigate to Secrets and variables → Actions
3. Click "New repository secret"
4. Add the secret name and value

## Components

### Permit Leads Scraper (`permit_leads/`)

A comprehensive Python scraping pipeline that collects recent building permit data for the Houston, TX area and outputs normalized records in multiple formats (CSV, SQLite, JSONL).

**Key Features:**
- 🏠 **Houston-area Coverage**: Initially supports City of Houston with extensible architecture for additional municipalities
- 🔍 **Smart Filtering**: Automatically identifies and filters residential permits for contractor leads
- 📊 **Multiple Output Formats**: CSV, SQLite database, and JSONL for different use cases
- 🔄 **Deduplication**: Prevents duplicate records using permit ID and content hashing
- 🤖 **Polite Scraping**: Respects robots.txt, implements rate limiting, and polite delays
- 🧪 **Sample Data Support**: Test mode with realistic sample data for development
- ⚡ **CLI Interface**: Simple command-line interface with flexible options

**Quick Start:**
```bash
cd permit_leads
pip install -r requirements.txt

# Test with sample data
python -m permit_leads --source city_of_houston --sample --days 7

# Real scraping (when endpoints are configured)
python -m permit_leads --source city_of_houston --days 7 --formats csv sqlite
```

**Architecture:**
- `models/permit.py`: Pydantic-based data models with validation
- `scrapers/`: Scraper implementations (Houston City, extensible for others)
- `adapters/storage.py`: Handles CSV append and SQLite upsert operations
- `utils/`: HTTP utilities, normalization helpers, robots.txt checking
- `tests/`: Comprehensive test suite with sample data fixtures

## Data Enrichment

The permit leads system includes comprehensive data enrichment to increase lead value and improve scoring accuracy.

### Enrichment Pipeline

The enrichment pipeline (`permit_leads/enrich.py`) adds the following data to each permit record:

#### Address & Location
- **Address normalization**: Standardizes formatting and abbreviations
- **Geocoding**: Converts addresses to lat/lon coordinates using configurable providers:
  - Nominatim (OpenStreetMap) - Free, no API key required
  - Mapbox - Commercial, requires API token
  - Google Maps - Commercial, requires API key

#### Parcel/Assessor Data
- **ArcGIS FeatureServer integration**: Fetches property data by coordinates
- **Configurable per county**: Each jurisdiction can have custom endpoints
- **Fields mapped**: APN, year built, heated sqft, lot size, land use

#### Trade Classification
- **NLP keyword matching**: Identifies relevant trades from permit descriptions
- **Supported trades**: roofing, kitchen, bath, pool, fence, windows, foundation, solar, hvac, electrical, plumbing
- **Multiple tags**: Records can have multiple trade classifications

#### Project Analysis
- **Owner classification**: Distinguishes between individual vs LLC/corporate owners
- **Budget bands**: Categorizes project values ($0–5k, $5–15k, $15–50k, $50k+)
- **Start prediction**: Estimates project start date based on jurisdiction-specific inspection timelines

### Enhanced Scoring

The enriched scoring algorithm weights multiple factors:

- **Recency (3x weight)**: Newer permits score higher (0-25 points)
- **Trade match (2x weight)**: High-value trades get priority (roofing: 25pts, kitchen: 24pts, bath: 22pts)
- **Project value (2x weight)**: Logarithmic scaling favors substantial projects
- **Parcel age (1x weight)**: Older homes more likely to need work (15+ years)
- **Inspection status (1x weight)**: Ready-to-proceed permits score higher

Final scores are capped at 100 points.

### Configuration

#### Environment Variables (`.env`)
```bash
# Geocoding provider
GEOCODER=nominatim|mapbox|google
MAPBOX_TOKEN=your_token_here
GOOGLE_MAPS_API_KEY=your_key_here

# County parcel endpoints
HARRIS_COUNTY_PARCELS_URL=https://gis-web.hcad.org/server/rest/services/...
```

#### Per-County Configuration (`permit_leads/enrich_config.yaml`)
```yaml
parcels:
  harris_county:
    endpoint: "https://services.arcgis.com/..."
    field_mapping:
      apn: "ACCOUNT_NUM"
      year_built: "YEAR_BUILT"
      heated_sqft: "BUILDING_SQFT"
      lot_size: "LOT_SIZE"
      land_use: "LAND_USE_CODE"
```

### Usage

#### Database Migration
Before using enrichment, update your database schema:
```bash
python -m permit_leads migrate-db --db data/permits/permits.db
```

#### Export Enriched Leads
```bash
# With full enrichment pipeline
python -m permit_leads export-enriched --lookback 14

# Using existing enriched data only
python -m permit_leads export-enriched --lookback 14 --no-enrich

# Migrate database and export in one step
python -m permit_leads export-enriched --lookback 14 --migrate
```

### Legal & Rate Limiting

- **Respect ToS**: Use official APIs only; don't scrape restricted data
- **Rate limits**: Geocoding providers have rate limits; implement delays for bulk processing
- **PII compliance**: Store only publicly available property records
- **Attribution**: Follow API provider attribution requirements

### Data Sources

#### Geocoding Providers
- **Nominatim**: Free, 1 req/sec limit, requires attribution
- **Mapbox**: 100k free requests/month, commercial usage allowed
- **Google Maps**: Pay-per-use, enterprise features available

#### Parcel Data
- **Harris County, TX**: Public GIS services via ArcGIS
- **Montgomery County, TX**: Custom endpoint configuration
- **Extensible**: Add new counties via configuration files

The enrichment pipeline significantly improves lead quality by providing location context, property characteristics, and intelligent trade matching for more targeted contractor outreach.

## GitHub Actions & Automation

This repository includes automated workflows for daily permit scraping:

- **Scheduled Runs**: Automated daily at 6 AM UTC (1 AM CST/2 AM CDT)
- **Manual Runs**: Trigger via GitHub Actions UI with custom parameters
- **Data Storage**: Results committed to repository and available as downloadable artifacts

See [`docs/github-actions-runbook.md`](docs/github-actions-runbook.md) for complete setup instructions, troubleshooting, and workflow details.

### Nightly Pipeline

The automated permit scraping pipeline runs daily via GitHub Actions:

#### Workflow: `permit_scrape.yml`
- **Schedule**: Daily at 6 AM UTC (1 AM CST/2 AM CDT)
- **Purpose**: Automatically scrape new building permits from configured sources
- **Output**: CSV, SQLite, and JSONL files with permit data
- **Storage**: Results are committed to the repository and available as artifacts

**Pipeline Steps:**
1. Set up Python 3.11 environment
2. Install dependencies from `permit_leads/requirements.txt`
3. Create data directories
4. Run permit scraper for the last 1 day (scheduled) or custom days (manual)
5. Check for new data and commit to repository
6. Upload data artifacts for download
7. Generate summary report

**Data Location:**
- Raw data: `data/permits/raw/`
- Processed data: `data/permits/aggregate/`
- Artifacts available for 30 days after each run

### Manual Run Steps

You can manually trigger the permit scraping workflow with custom parameters:

#### Via GitHub Actions UI:
1. Go to the **Actions** tab in your GitHub repository
2. Select the **"Houston Permit Scraper"** workflow
3. Click **"Run workflow"** button
4. Configure parameters:
   - **Source**: Choose `city_of_houston` or `all`
   - **Days**: Number of days to look back (default: 1)
   - **Sample data**: Check to use test data instead of live scraping
5. Click **"Run workflow"** to start

#### Via GitHub CLI:
```bash
# Run with default parameters (city_of_houston, 1 day)
gh workflow run permit_scrape.yml

# Run with custom parameters
gh workflow run permit_scrape.yml \
  -f source=city_of_houston \
  -f days=7 \
  -f sample_data=false

# Run with sample data for testing
gh workflow run permit_scrape.yml \
  -f source=city_of_houston \
  -f days=7 \
  -f sample_data=true
```

#### Manual Local Execution:
```bash
# Navigate to permit_leads directory
cd permit_leads

# Run scraper locally
python -m permit_leads --source city_of_houston --days 7 --formats csv sqlite jsonl

# Run with sample data for testing
python -m permit_leads --source city_of_houston --sample --days 7
```

**Note**: Manual runs require the `DATABASE_URL` secret to be configured if using database storage.

## Configuration

### Environment Variables

Copy `permit_leads/.env.example` to `permit_leads/.env` and configure as needed:

```bash
cd permit_leads
cp .env.example .env
# Edit .env with your configuration
```

### Data Sources

Configure scraping targets in `permit_leads/config/sources.yaml`.

---

*Note: Always respect website terms of service and robots.txt when scraping. This tool is designed for ethical data collection with proper rate limiting and attribution.*

## Multi-Region Support

LeadLedgerPro supports multiple regions, states, and metropolitan areas through a centralized configuration system. One deployment can serve multiple regions without code changes - only configuration updates are needed.

### Adding a New State/Metro Area

To onboard a new jurisdiction and activate it for lead generation:

#### 1. Update Regions Registry

Edit `config/regions.yaml` to add the new region/metro:

```yaml
regions:
  # Add new state
  florida:
    display_name: "Florida"
    short_name: "FL"
    active: true  # Set to true to activate
    timezone: "America/New_York"
    metros:
      miami:
        display_name: "Miami Metro"
        short_name: "Miami"
        active: true  # Set to true to activate
        center_lat: 25.7617
        center_lng: -80.1918
        radius_miles: 50
        description: "Greater Miami metropolitan area including Miami-Dade County"
        seo_keywords: ["Miami contractors", "Miami permits", "home services Miami"]
        jurisdictions:
          - "Miami-Dade County"
          - "City of Miami"
        data_sources:
          - miami_dade_permits
```

#### 2. Configure Data Sources

Add scraper configuration in `permit_leads/config/sources.yaml`:

```yaml
sources:
  # Add new data source
  - name: Miami-Dade County Permits
    type: arcgis_feature_service
    url: "https://gis.miamidade.gov/server/rest/services/Permits/FeatureServer/0/query"
    date_field: "ISSUE_DATE"
    out_fields: "*"
    mappings:
      permit_number: "PERMIT_NO"
      issued_date: "ISSUE_DATE"
      address: "SITE_ADDRESS"
      description: "WORK_DESCRIPTION"
      status: "STATUS"
      work_class: "PERMIT_TYPE"
      category: "USE_GROUP"
```

#### 3. Add Enrichment Configuration

Update `permit_leads/enrich_config.yaml` for county-specific parcel data:

```yaml
parcels:
  # Add new county configuration
  miami_dade_county:
    endpoint: "https://services.arcgis.com/florida/parcels/FeatureServer/0"
    field_mapping:
      apn: "FOLIO"
      year_built: "YR_BLT"
      heated_sqft: "TOT_LVG_AREA"
      lot_size: "LND_SQFOOT"
      land_use: "DOR_UC"

# Add region-specific trade priorities and inspection timelines
region_configs:
  florida:
    trade_priorities:
      roofing: 35      # Higher priority in hurricane zones
      pool: 28         # Very popular in FL
      hvac: 30         # Hot climate
      # ... other trades
    inspection_days:
      "Miami-Dade County": 7
      "City of Miami": 10
      default: 5
```

#### 4. Deploy Configuration

Once configuration is updated:

1. **Test the scraper** with sample data:
   ```bash
   cd permit_leads
   python -m permit_leads --source miami_dade_permits --sample --days 7
   ```

2. **Verify region API** returns new metro:
   ```bash
   curl http://localhost:3000/api/regions
   ```

3. **Check dynamic pages** are generated:
   ```bash
   # Frontend build should generate: /regions/florida/miami
   npm run build
   ```

4. **Update database** if needed:
   ```bash
   # Run any new database migrations
   python -m backend.app.ingest out/leads_recent.csv
   ```

#### 5. Activate Region

Set `active: true` in the regions configuration to make the new metro visible to users.

### Region-Aware Features

Once configured, the system automatically provides:

- **Region Selection**: Users can select metro areas on the homepage and lead pages
- **Filtered Leads**: API endpoints filter leads by jurisdiction based on selected region
- **SEO Pages**: Dynamic pages at `/regions/{state}/{metro}` with region-specific content
- **Performance**: Database queries use jurisdiction indexes for fast filtering
- **Scoring**: Region-specific trade priorities and value bands

### Configuration Reference

Key configuration files for multi-region support:

| File | Purpose |
|------|---------|
| `config/regions.yaml` | Main registry of regions, metros, and their metadata |
| `permit_leads/config/sources.yaml` | Data source configurations for scrapers |
| `permit_leads/enrich_config.yaml` | County-specific enrichment and trade priorities |
| `backend/app/models.sql` | Database schema with jurisdiction indexes |

### API Endpoints

- `GET /api/regions` - List available regions and metros
- `GET /api/leads?region={region}&metro={metro}` - Get region-filtered leads
- `GET /regions/{region}/{metro}` - SEO-optimized region landing pages

The system is designed to scale to dozens of metros across multiple states while maintaining fast performance and clean separation of concerns.

## Legal Notices

- LeadLedgerPro uses publicly available building permit data.
- All users must comply with Do Not Call, CAN-SPAM, and local solicitation laws.
- No guarantee of accuracy or job acquisition.
- See /terms and /privacy for full details.
