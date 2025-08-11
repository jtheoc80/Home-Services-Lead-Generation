
# LeadLedgerPro

Automated building permit intelligence platform for contractors – fresh leads daily, scored for conversion.

[![Nightly Scrape](https://github.com/jtheoc80/Home-Services-Lead-Generation/actions/workflows/nightly-scrape.yml/badge.svg)](https://github.com/jtheoc80/Home-Services-Lead-Generation/actions/workflows/nightly-scrape.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 1. Overview

# Houston Home Services Lead Generation

**LeadLedgerPro - Houston Metro Edition**

A lead generation platform for home service contractors focused exclusively on the Houston metropolitan area. This system automatically collects and processes building permit data from Houston-area counties to identify high-quality leads for contractors.

## 🏙️ Houston-First Scope

This platform is currently scoped to serve **Houston Metro area only**, including:

- **Harris County** (tx-harris)
- **Fort Bend County** (tx-fort-bend) 
- **Brazoria County** (tx-brazoria)
- **Galveston County** (tx-galveston)

*Other regions may be added in future releases based on demand and data availability.*

## 🚀 Key Features

- **Automated Lead Collection**: Nightly scraping of permit data from Houston-area counties
- **Smart Notifications**: In-app notifications for leads matching your criteria
- **Lead Scoring**: ML-powered scoring to identify the highest quality opportunities
- **Dashboard-Only Access**: No CSV exports - all data accessible through the web dashboard
- **Real-Time Updates**: Live notifications when new matching leads are available

## ⚡ 5-Minute Quickstart

Get LeadLedgerPro running locally in 5 minutes with sample data:

### Prerequisites
- Python 3.11+ and Node.js 16+
- PostgreSQL (not required for demo - uses SQLite)

### Quick Setup Commands

```bash
# 1. Clone and setup environment
git clone https://github.com/jtheoc80/Home-Services-Lead-Generation.git
cd Home-Services-Lead-Generation

# 2. Set up environment variables
cp .env.example .env
cp backend/.env.example backend/.env  
cp frontend/.env.local.example frontend/.env.local

# Edit backend/.env - for demo, use SQLite:
# DATABASE_URL=sqlite:///leadledger_demo.db
# SUPABASE_URL=https://demo.supabase.co
# SUPABASE_SERVICE_ROLE=demo_key
# SUPABASE_JWT_SECRET=demo_jwt_secret

# Edit frontend/.env.local:
# SUPABASE_URL=https://demo.example.com
# SUPABASE_SERVICE_ROLE=demo_key
# SUPABASE_JWT_SECRET=demo_jwt_secret

# Edit frontend/.env.local:
# NEXT_PUBLIC_SUPABASE_URL=https://demo.example.com
# NEXT_PUBLIC_SUPABASE_ANON_KEY=demo_anon_key

# 3. Install dependencies
pip install -r permit_leads/requirements.txt
pip install -r backend/requirements.txt
cd frontend && npm install && cd ..

# 4. Run scraper with sample data (generates ~6 sample permits)
python -m permit_leads --source city_of_houston --sample --days 7 --formats csv

# 5. Optional: Ingest sample data (requires database setup)
# python backend/app/ingest.py data/leads/by_jurisdiction/city_of_houston_leads.csv

# 6. Start backend server (runs on port 8000)
cd backend && python main.py &
cd ..

# 7. Start frontend (runs on port 3000)
cd frontend && npm run dev &
cd ..

# 8. Verify everything works
curl http://localhost:8000/healthz  
# Expected: {"status":"ok","version":"1.0.0","db":"down"}  (db down is OK for demo)

# 9. View demo application
open http://localhost:3000  # Homepage with nice UI
open http://localhost:3000/dashboard  # Dashboard (requires login setup for full functionality)
```

### Quick Verification Checklist

- ✅ **Backend Health**: `http://localhost:8000/healthz` returns status "ok"
- ✅ **API Docs**: `http://localhost:8000/docs` shows FastAPI documentation 
- ✅ **Frontend**: `http://localhost:3000` displays LeadLedgerPro homepage
- ✅ **Sample Data**: Check `data/leads/by_jurisdiction/city_of_houston_leads.csv` for 6 generated sample permits
- ⚠️ **Database**: Shows "down" status for demo (database setup optional for quickstart)

### What You'll See

![LeadLedgerPro Homepage](quickstart-homepage-demo.png)
*Professional homepage with feature overview*

![LeadLedgerPro Dashboard](quickstart-dashboard-demo.png)  
*Lead management dashboard interface*

![LeadLedgerPro API Documentation](quickstart-api-docs-demo.png)
*FastAPI Swagger documentation*

- **Homepage**: Professional landing page with feature overview
- **Dashboard**: Lead management interface (login required for full features)
- **Sample Data**: 6 Houston building permits with realistic details
- **API**: FastAPI backend with health checks and Swagger docs

### Next Steps After Quickstart

1. Set up real PostgreSQL database (see full installation guide below)
2. Configure Supabase for authentication 
3. Run full scraper against live permit data
4. Set up data ingestion pipeline

---

## ⚡ Quick Start

### Prerequisites
- Python 3.11 or higher
- PostgreSQL database
- Node.js 16+ (for frontend)

### Installation

1. **Clone and setup:**
   ```bash
   git clone https://github.com/jtheoc80/Home-Services-Lead-Generation.git
   cd Home-Services-Lead-Generation
   ```

2. **Configure environment:**
   ```bash
   # Backend configuration
   cp backend/.env.example backend/.env
   # Edit backend/.env with your database URL and settings
   
   # Frontend configuration  
   cp frontend/.env.example frontend/.env.local
   # Edit frontend/.env.local with your Supabase/API settings
   ```

3. **Install dependencies:**

   **Option A: Automated setup (recommended)**
   ```bash
   # Using Python setup script
   python3 setup.py
   
   # OR using shell script
   ./setup.sh
   
   # OR using Make
   make install
   ```

   **Option B: Manual installation**
   ```bash
   # Install scraper dependencies
   pip install -r permit_leads/requirements.txt
   
   # Install backend dependencies
   pip install -r backend/requirements.txt
   ```

   **Install frontend dependencies (all options)**
   ```bash
   cd frontend && npm install
   ```

4. **Setup database:**
   ```bash
   # Run database migrations with error handling
   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -b -e -f backend/app/models.sql
   ```

## 🔧 Configuration

### Backend Settings (`backend/.env`)

Key configuration variables:

```bash
# Houston-only scope
LAUNCH_SCOPE=houston
DEFAULT_REGION=tx-houston
ALLOW_EXPORTS=false

# Database and services
DATABASE_URL=postgresql://user:pass@host:port/db
SENDGRID_API_KEY=your_key_here

# Lead scoring and notifications
USE_ML_SCORING=false
MIN_SCORE_THRESHOLD=70.0
```

### Frontend Settings (`frontend/.env.local`)

```bash
# Houston-focused frontend
NEXT_PUBLIC_LAUNCH_SCOPE=houston
NEXT_PUBLIC_EXPORTS_ENABLED=false
NEXT_PUBLIC_FEATURE_NOTIFICATIONS=true

# API configuration
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
```

## 🤖 Automated Pipeline

The system runs a **nightly pipeline** that:

1. Scrapes permit data from Houston-area counties
2. Processes and enriches the data
3. Ingests leads into PostgreSQL database
4. Generates notifications for matching user preferences
5. Stores audit artifacts for compliance

**Pipeline Schedule**: Daily at 5:00 AM UTC (Midnight Central Time)

### Manual Pipeline Execution

You can trigger the pipeline manually:

```bash
# Run via GitHub Actions (if you have access)
gh workflow run nightly-pipeline.yml

# Or run locally
python permit_leads/main.py --days 14 --outdir out
python backend/app/ingest.py out/leads_recent.csv
```

## 📊 Dashboard Access

All lead data is accessible exclusively through the web dashboard:

- **No CSV Exports**: Data export functionality is disabled by design
- **Save Views**: Use built-in filtering and "Save View" functionality
- **Notifications**: Get alerted when new leads match your criteria
- **Real-Time**: Dashboard updates automatically with new leads

## 🔒 Data Access Policy

### No-Download Policy

This system implements a **strict no-download policy**:

- ❌ CSV export endpoints are disabled (`ALLOW_EXPORTS=false`)
- ❌ Bulk data downloads are not permitted
- ✅ Dashboard viewing and filtering is fully supported
- ✅ "Save View" functionality for custom lead lists
- ✅ In-app notifications for new leads

### Admin Access Only

Data exports are restricted to system administrators only and require:
- Admin-level authentication
- `ALLOW_EXPORTS=true` environment variable
- Audit logging of all export activities

## 📧 Notifications

Configure your notification preferences to receive alerts for:

- **Lead Score Threshold**: Minimum score to trigger notifications (default: 70+)
- **Counties**: Choose which counties to monitor
- **Channels**: In-app notifications (email coming soon)
- **Trade Tags**: Filter by specific contractor types
- **Value Threshold**: Minimum estimated project value

Access notification settings at: `/api/me/notifications/prefs`

## 🏗️ Development

### Project Structure

```
├── permit_leads/          # Lead scraping and processing
├── backend/              # API and database management
│   ├── app/
│   │   ├── settings.py   # Centralized configuration
│   │   ├── models.sql    # Database schema
│   │   └── utils/        # Utility modules
├── frontend/             # Next.js web dashboard
│   ├── lib/config.ts     # Frontend configuration
│   └── pages/api/        # API endpoints
├── config/
│   └── registry.yaml     # County/jurisdiction configuration
└── .github/workflows/    # Automated pipelines
```

### Adding New Counties

To add new Houston-area counties:

1. Update `config/registry.yaml` with new jurisdiction
2. Set `active: true` for the new county
3. Ensure scraper adapter exists for the data source
4. Test with `python permit_leads/main.py --jurisdiction new-county`

## 📋 Legal and Compliance

### Data Usage

- All permit data is sourced from **public records** only
- Data is used for **legitimate business purposes** (lead generation)
- No personal information is stored beyond what's publicly available
- System complies with **public records access laws**

### Rate Limiting

- Scrapers implement respectful rate limiting (1-second delays)
- Robots.txt compliance for all data sources
- Maximum 1000 records per source per run

### Privacy

- No personal contact information is stored
- Only business-related permit information is processed
- Users control their own notification preferences
- No cross-user data sharing

## 🆘 Support

### Common Issues

**Pipeline Failures**: Check logs in GitHub Actions artifacts
**Missing Notifications**: Verify your preferences in dashboard settings
**Database Connection**: Ensure `DATABASE_URL` is correctly configured

### Getting Help

1. Check the [Issues](https://github.com/jtheoc80/Home-Services-Lead-Generation/issues) page
2. Review pipeline logs in GitHub Actions
3. Contact system administrators for access issues

## 📈 Roadmap

- [ ] Email notification channel
- [ ] SMS notifications (future)
- [ ] ML lead scoring (beta testing)
- [ ] Mobile app companion
- [ ] Additional Texas markets (Austin, San Antonio, Dallas)

---

**Houston Metro Lead Generation** - Connecting contractors with opportunities in America's 4th largest city.

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


**Problem:** Contractors waste countless hours chasing cold leads, often competing for the same opportunities everyone else already knows about.

**Solution:** LeadLedgerPro automatically scrapes and enriches public building permit data, ranks opportunities using intelligent scoring, and delivers exclusive or semi-exclusive leads to paying subscribers before competitors even know they exist.

**Data Sources:**
- Harris County, Texas
- Fort Bend County, Texas  
- Brazoria County, Texas
- Galveston County, Texas
- *(Expandable to additional counties and states)*

**Enrichment Pipeline:**
- Parcel data integration for property details
- Zoning classification and restrictions
- Owner type identification (homeowner vs. investor)
- Trade-specific tagging (roofing, HVAC, electrical, etc.)
- Property value bands and market analysis
- Geocoding and territory mapping

**Outputs:**
- Scored CSV exports for CRM import
- Real-time contractor dashboard with filters
- Trade-specific RSS/API feeds
- Priority lead notifications

## 2. Features

- **🤖 Nightly Automated Scraping** - GitHub Actions-powered data collection runs every night at 6 AM UTC
- **🎯 Lead Scoring Model** - Proprietary algorithm weighing recency, trade match, project value, and home age
- **⚡ REST API (FastAPI)** - Modern API for frontend integration and partner connections
- **🔐 Secure Authentication** - Supabase-powered JWT with role-based access control
- **💳 Flexible Payments** - Stripe integration for USD plus crypto gateway (BTC, ETH, XRP)
- **📊 Contractor Dashboard** - Next.js frontend with advanced search, filters, and score-based sorting
- **👨‍💼 Admin Panel** - Monitor pipeline runs and trigger manual data collection
- **📈 Lead Analytics** - Track conversion rates and ROI by lead source and score

## 3. Tech Stack

- **Backend:** FastAPI, SQLAlchemy, PostgreSQL, Python 3.11
- **Frontend:** Next.js, TypeScript, Tailwind CSS
- **Data Pipeline:** Python scraper with enrichment modules
- **CI/CD:** GitHub Actions (nightly + manual dispatch)
- **Authentication:** Supabase (JWT + Row Level Security)
- **Payments:** Stripe + crypto gateway integration
- **Hosting:** Railway (backend), Vercel (frontend), GitHub Actions (data pipeline)

## 4. Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  GitHub Actions │────│  Python Scraper  │────│  Data Enrichment│
│  (Nightly Cron) │    │  (Permit Sites)  │    │  (Parcel/Value) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│    PostgreSQL   │◄───│   FastAPI Server │────│   Next.js App   │
│   (Leads DB)    │    │   (Scoring API)  │    │  (Dashboard UI) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Supabase Auth  │
                       │   Stripe Pay     │
                       └──────────────────┘
```

**Workflow:**
1. GitHub Actions triggers nightly scraper
2. Scraper collects permits from county websites
3. Enrichment adds parcel data, scoring, trade tags
4. Data stored in PostgreSQL with deduplication
5. FastAPI serves scored leads via REST endpoints
6. Next.js dashboard provides contractor interface
7. Supabase handles auth, Stripe processes payments

## 5. Getting Started (Local Dev)

### 1. Clone & Install Backend
```bash
git clone https://github.com/jtheoc80/Home-Services-Lead-Generation.git
cd Home-Services-Lead-Generation

# Install Python dependencies
cd permit_leads
python -m venv .venv && source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

### 2. Configure Environment
```bash
# Edit .env with your credentials
DATABASE_URL=postgresql://user:password@localhost:5432/leadledger
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
STRIPE_SECRET_KEY=sk_test_your_stripe_key
```

### 3. Run Data Pipeline
```bash
# Test scraper with sample data
python -m permit_leads --source city_of_houston --sample --days 7

# Run real scraping (production)
python -m permit_leads --source city_of_houston --days 7 --formats csv sqlite
```

### 4. Start API Server
```bash
# Install FastAPI dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary

# Start development server
uvicorn api.main:app --reload --port 8000
```

### 5. Launch Frontend
```bash
# Install Node.js dependencies
cd ../frontend
npm install

# Start development server
npm run dev
```

### 6. Access Applications
- **API Documentation:** http://localhost:8000/docs
- **Frontend Dashboard:** http://localhost:3000
- **Admin Panel:** http://localhost:3000/admin

## 6. Development

### Running Tests
```bash
# Backend tests
cd permit_leads
python -m pytest tests/

# Frontend tests  
cd frontend
npm test
```

### Manual Pipeline Trigger
```bash
# Trigger GitHub Actions workflow manually
gh workflow run nightly-scrape.yml
```

### Database Migrations
```bash
# Apply schema changes
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Add new table"
```

## 7. Deployment

The application is designed for production deployment across multiple services:

- **Data Pipeline:** GitHub Actions (automated)
- **Backend API:** Railway or similar container platform
- **Frontend:** Vercel or Netlify
- **Database:** Railway PostgreSQL or AWS RDS
- **Auth/Storage:** Supabase

See `deploy/` directory for production configuration templates.

## 8. Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 9. License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**LeadLedgerPro** - Turn public permit data into private profit. Get exclusive leads before your competition even knows they exist.
=======
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

---

*Note: Always respect website terms of service and robots.txt when scraping. This tool is designed for ethical data collection with proper rate limiting and attribution.*

## Connect Supabase

LeadLedgerPro uses Supabase for authentication and user management. Follow these steps to set up your Supabase connection:

### 1. Create a Supabase Project

1. Go to [Supabase](https://supabase.com) and create a new project
2. Wait for the database to be provisioned

### 2. Get Your Project Credentials

From your Supabase project dashboard:

1. **Project URL**: Go to Settings → API → Project URL
2. **Anon Key**: Go to Settings → API → Project API keys → `anon` key
3. **JWT Secret**: Go to Settings → API → JWT Settings → JWT Secret

### 3. Configure Environment Variables

#### Frontend (.env.local)
```bash
cd frontend
cp .env.local.example .env.local
```

Edit `.env.local` and add your Supabase credentials:
```bash
NEXT_PUBLIC_SUPABASE_URL=your_project_url_here
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key_here
NEXT_PUBLIC_API_BASE=http://localhost:8000
NEXT_PUBLIC_DEFAULT_REGION=tx-houston
```

#### Backend (.env)
```bash
cd backend
cp .env.example .env
```

Edit `.env` and add your Supabase credentials:
```bash
SUPABASE_URL=your_project_url_here
SUPABASE_JWT_SECRET=your_jwt_secret_here
SUPABASE_SERVICE_ROLE=your_service_role_key_here
```

### 4. Security Notes

⚠️ **Important Security Guidelines:**

- **Never expose service role keys in frontend code** - The service role key should only be used in backend services
- **Use anon keys in frontend** - The anon key is safe to use in client-side code
- **JWT Secret is for backend only** - Used for verifying JWT tokens from Supabase
- **Keep .env files out of version control** - Add them to .gitignore

### 5. Authentication Flow

1. **Login**: Users sign in via magic link using `/login` page
2. **JWT Token**: Supabase provides a JWT token after successful authentication
3. **API Requests**: Frontend sends JWT token in Authorization header as `Bearer <token>`
4. **Backend Verification**: FastAPI verifies the JWT using the JWT secret
5. **Protected Routes**: Access `/api/me` and other protected endpoints

### 6. Testing the Integration

1. Start the backend server:
   ```bash
   cd backend
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

2. Start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. Visit `http://localhost:3000/login` to test authentication
4. After login, test the `/api/me` endpoint with your JWT token

---

## Legal Notices

- LeadLedgerPro uses publicly available building permit data.
- All users must comply with Do Not Call, CAN-SPAM, and local solicitation laws.
- No guarantee of accuracy or job acquisition.
- See /terms and /privacy for full details.

