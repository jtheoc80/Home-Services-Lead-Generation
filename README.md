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

#### New Environment Variables (v2.0+)
- **`ALLOW_EXPORTS`**: Controls data export permissions (`true`/`false`, default: `false`)
- **`REDIS_URL`**: Redis connection for caching and session storage (`redis://host:port/db`)
- **`SENDGRID_API_KEY`**: SendGrid API key for email notifications
- **`TWILIO_SID`**: Twilio Account SID for SMS notifications
- **`TWILIO_TOKEN`**: Twilio Auth Token for SMS notifications  
- **`TWILIO_FROM`**: Twilio phone number for sending SMS (E.164 format)

See [`docs/environment-variables.md`](docs/environment-variables.md) for detailed configuration instructions.

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

The repository also includes a comprehensive regional registry in `config/registry.yaml` that defines:
- **Regions**: Hierarchical geographic areas (national → state → metro)
- **Jurisdictions**: County-level data sources with ArcGIS endpoint configurations

This registry provides a standardized approach to organizing data sources by geographic regions across Texas metro areas including Houston, Dallas-Fort Worth, San Antonio, and Austin.

## Staging Environment

The staging environment provides a safe testing space for new features and changes before production deployment.

### Setup and Deployment

#### Prerequisites
- Staging branch in repository  
- Staging environment secrets configured in GitHub
- Staging infrastructure (database, Redis, application servers)

#### Automatic Deployment
Staging deploys automatically when code is pushed to the `staging` branch:

```bash
# Create and push to staging branch
git checkout -b staging
git push origin staging
```

The deployment pipeline will:
1. Run tests (backend and frontend)
2. Deploy backend with staging environment variables
3. Deploy frontend with staging configuration
4. Run database migrations
5. Seed demo data (200 sample leads + test user)
6. Execute smoke tests
7. Send deployment notifications

#### Manual Deployment
Trigger staging deployment manually via GitHub Actions:

1. Go to **Actions** tab in GitHub repository
2. Select **"Deploy to Staging"** workflow  
3. Click **"Run workflow"**
4. Choose options:
   - Force deployment (skip test failures)
   - Skip tests entirely
5. Click **"Run workflow"** to start

#### Environment Configuration
Staging uses environment-specific secrets:

**Backend Staging Secrets:**
- `DATABASE_URL_STAGING`: Staging database connection
- `SECRET_KEY_STAGING`: Application secret key
- `REDIS_URL_STAGING`: Redis cache connection  
- `SENDGRID_API_KEY_STAGING`: Email service key
- `TWILIO_SID_STAGING` / `TWILIO_TOKEN_STAGING`: SMS service credentials

**Frontend Staging Secrets:**
- `NEXT_PUBLIC_API_BASE_STAGING`: Staging API URL
- `NEXT_PUBLIC_SUPABASE_URL_STAGING`: Staging Supabase project
- `NEXT_PUBLIC_SUPABASE_ANON_KEY_STAGING`: Staging Supabase key

### Local Staging Development

#### Quick Setup
```bash
# Set up staging environment locally
make staging-setup

# Configure environment variables
# Edit backend/.env and frontend/.env.local with staging values

# Run database migration
make stage-migrate

# Seed demo data  
make stage-seed

# Start development servers
make dev
```

#### Manual Setup Steps
1. **Environment Configuration:**
   ```bash
   # Set staging mode
   export APP_ENV=staging
   export NEXT_PUBLIC_ENV=staging
   ```

2. **Database Setup:**
   ```bash
   # Run migrations
   python scripts/migrate.py
   
   # Add demo data
   python scripts/seed_demo.py --lead-count 200
   ```

3. **Development Servers:**
   ```bash
   # Backend (http://localhost:8000)
   make dev-backend
   
   # Frontend (http://localhost:3000)  
   make dev-frontend
   ```

### Staging Features

#### Demo Data
Staging includes 200 sample leads with realistic data:
- Multiple jurisdictions (Houston area)
- Various work classes and categories
- Enriched location and parcel data
- ML scoring and classification
- Test user account: `test@leadledderpro.com`

#### Visual Indicators
- Prominent orange staging banner in frontend header
- Environment indicator in API responses
- Debug tools and enhanced logging
- Staging-specific API endpoints

#### Health Monitoring
Health check endpoints for monitoring:
```bash
# Overall health status
curl https://staging-api.leadledderpro.com/health

# Readiness check (for load balancers)
curl https://staging-api.leadledderpro.com/health/ready

# Liveness check (for container orchestration)
curl https://staging-api.leadledderpro.com/health/live
```

### Smoke Testing

Automated smoke tests verify staging deployment:

1. **Backend Health:** API endpoints respond correctly
2. **Database Connectivity:** Migration and data access work  
3. **Frontend Accessibility:** Application loads and renders
4. **Integration:** API calls from frontend succeed

Manual smoke testing:
```bash
# Test health endpoints
make health

# Verify staging banner appears in frontend
# Visit staging URL and confirm orange banner is visible

# Test demo data access
# Log in with test account and browse sample leads
```

### Troubleshooting

#### Common Issues

**Migration Failures:**
```bash
# Check database connectivity
python scripts/migrate.py --dry-run

# Run with verbose logging
python scripts/migrate.py --verbose
```

**Seed Data Problems:**  
```bash
# Reset and re-seed
make stage-migrate
make stage-seed
```

**Frontend Build Errors:**
```bash
# Check environment variables
make validate-env

# Clean and rebuild
make clean
make build-frontend
```

**Health Check Failures:**
```bash
# Check service status
curl -v http://localhost:8000/health

# Review logs for database/Redis connectivity issues
```

#### Getting Help
- Check deployment logs in GitHub Actions
- Verify staging environment secrets are configured
- Ensure staging infrastructure is healthy
- Contact DevOps team for infrastructure issues

---

*Note: Always respect website terms of service and robots.txt when scraping. This tool is designed for ethical data collection with proper rate limiting and attribution.*

## Legal Notices

- LeadLedgerPro uses publicly available building permit data.
- All users must comply with Do Not Call, CAN-SPAM, and local solicitation laws.
- No guarantee of accuracy or job acquisition.
- See /terms and /privacy for full details.
