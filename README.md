
# LeadLedgerPro

Automated building permit intelligence platform for contractors – fresh leads daily, scored for conversion.

[![Nightly Scrape](https://github.com/jtheoc80/Home-Services-Lead-Generation/actions/workflows/nightly-scrape.yml/badge.svg)](https://github.com/jtheoc80/Home-Services-Lead-Generation/actions/workflows/nightly-scrape.yml)
[![Security Checks](https://github.com/jtheoc80/Home-Services-Lead-Generation/actions/workflows/security.yml/badge.svg)](https://github.com/jtheoc80/Home-Services-Lead-Generation/actions/workflows/security.yml)
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
- **OpenAPI Integration**: Auto-generated TypeScript and Python clients with API validation

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
# In a new terminal window/tab, run:
cd backend
python main.py

# 7. Start frontend (runs on port 3000)
# In another new terminal window/tab, run:
cd frontend
npm run dev

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


## 💳 Payments (Stripe) Quickstart

Set up the billing system with Stripe for subscriptions and lead credits:

### Prerequisites
- Stripe account ([stripe.com](https://stripe.com))
- Get your test API keys from [Stripe Dashboard](https://dashboard.stripe.com/test/apikeys)

### Quick Setup Commands

```bash
# 1. Configure Stripe environment variables
cp backend/.env.example backend/.env
# Edit backend/.env and add your Stripe test keys:
# STRIPE_SECRET_KEY=sk_test_xxx
# STRIPE_WEBHOOK_SECRET=whsec_xxx (get from webhook local forwarding)
# STRIPE_PUBLISHABLE_KEY=pk_test_xxx

cp frontend/.env.example frontend/.env.local  
# Edit frontend/.env.local and add:
# NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_xxx

# 2. Install Stripe dependency
cd backend && pip install stripe
cd ../frontend && npm install @stripe/stripe-js

# 3. Apply billing database schema
make db-billing

# 4. Seed Stripe products and prices
make billing-seed
# Copy the output price IDs to your backend/.env

# 5. Start local development with webhooks
make billing-webhook
```

### Quick Verification Checklist

After setup, verify these work:

- ✅ Backend health shows Stripe configured: `curl http://localhost:8000/healthz`
- ✅ Frontend billing page loads: `http://localhost:3000/billing`
- ✅ Stripe webhook forwarding: Terminal shows "Ready! You are using Stripe API Version..."
- ✅ Test checkout: Trigger `stripe trigger checkout.session.completed`

### What You'll See

**Billing Pages:**
- **Plan Selection**: `/billing` - Choose Starter ($199/mo) or Pro ($399/mo) plans
- **Credit Purchase**: Buy 50-credit packs for $49
- **Customer Portal**: Manage billing, view invoices, update payment methods
- **Success/Cancel**: Payment completion pages

**Test Credit Flow:**
1. Purchase credit pack → Credits added to balance
2. Claim a lead → 1 credit deducted
3. Insufficient credits → 402 error with upgrade CTA

### Next Steps After Quickstart

1. Configure live Stripe keys for production
2. Set up webhook endpoint on your live domain
3. Configure subscription plan benefits (lead limits, features)
4. Test the complete payment flow end-to-end

### 🔧 Post-Merge Deployment Checklist

After merging this PR, follow these exact commands to configure Stripe in your environments:

**Vercel (Frontend & Webhook Handler):**
```bash
# Server-side webhook + FE
vercel env add STRIPE_WEBHOOK_SECRET {development|preview|production}
vercel env add INTERNAL_BACKEND_WEBHOOK_URL {development|preview|production}
vercel env add INTERNAL_WEBHOOK_TOKEN {development|preview|production}
vercel env add SUPABASE_URL {development|preview|production}
vercel env add SUPABASE_SERVICE_ROLE_KEY {development|preview|production}
vercel env add NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY {development|preview|production}
vercel redeploy --prod
```

**Railway (Backend):**
```bash
railway variables set STRIPE_SECRET_KEY=sk_test_xxx
railway variables set STRIPE_PRICE_STARTER_MONTHLY=price_xxx
railway variables set STRIPE_PRICE_PRO_MONTHLY=price_xxx
railway variables set STRIPE_PRICE_LEAD_CREDIT_PACK=price_xxx
railway variables set BILLING_SUCCESS_URL=https://<vercel-domain>/billing/success
railway variables set BILLING_CANCEL_URL=https://<vercel-domain>/billing/cancel
railway variables set INTERNAL_WEBHOOK_TOKEN=<same-as-vercel>
```

**Stripe CLI (Local Test):**
```bash
stripe listen --forward-to http://localhost:3000/api/webhooks/stripe
stripe trigger checkout.session.completed
```

**Database Setup:**
```bash
# Apply billing schema to production database
make db-billing  # or run the SQL from backend/app/models.sql manually
```

**Stripe Product Seeding:**
```bash
# Seed products and prices in live Stripe account
make billing-seed  # copy the price IDs to your environment variables
```

**Important Reminders:**
- ⚠️ Never put server secrets in the browser; only NEXT_PUBLIC_* is safe for FE
- 🔐 Set INTERNAL_WEBHOOK_TOKEN to the same value on both Vercel and Railway
- 🎯 Replace <vercel-domain> with your actual Vercel deployment URL
- ✅ Use test keys during development, live keys only in production

**Verification:**
- ✅ Health endpoint shows Stripe configured: `/healthz`
- ✅ Billing page loads without errors: `/billing`
- ✅ Test webhook endpoint receives events
- ✅ Test checkout flow end-to-end

## 🛡️ Security

This project includes comprehensive security measures to protect against vulnerabilities and ensure license compliance:

### Security Features
- **CodeQL SAST Analysis**: Automated static analysis for JavaScript/TypeScript and Python code
- **Dependency Vulnerability Scanning**: Daily scans using npm audit and pip-audit
- **License Compliance Checking**: Automated verification of dependency licenses
- **Scheduled Security Scans**: Daily automated security checks

### Running Security Checks Locally
```bash
# Run comprehensive security check
npm run security:check

# Individual security commands
npm run security:audit    # Check for vulnerabilities
npm run security:licenses # Check license compliance

# Or use the detailed script directly
./scripts/security-check.sh
```

### Security Workflow
The security workflow runs automatically on:
- Push to main/develop branches
- Pull request creation
- Daily at 2 AM UTC

For detailed security configuration and troubleshooting, see [`docs/SECURITY.md`](docs/SECURITY.md).


---

## 🔍 5-Minute Quickstart (Monitoring)

Monitor your stack health across Vercel, Railway, and Supabase:

### Required Environment Variables
Set these in your environment or `.env` file:
```bash
# For comprehensive monitoring
FRONTEND_URL=https://your-app.vercel.app
VERCEL_TOKEN=your_vercel_api_token
RAILWAY_TOKEN=your_railway_api_token  
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE=your_service_role_key
```

### Quick Health Check
```bash
# Run local diagnosis
./scripts/diagnose.sh

# Check stack health across all platforms  
node scripts/stack-health.js

# Test frontend health endpoint (requires running frontend)
curl http://localhost:3000/api/health
```

### Trigger Manual Monitoring
```bash
# Manual stack monitor run
gh workflow run stack-monitor.yml

# Force remediation attempt
gh workflow run stack-monitor.yml --field force_remediation=true
```

### Find Issues and Artifacts
- **GitHub Issues**: Auto-created issues tagged `infrastructure` for failures
- **Workflow Artifacts**: Download logs from [Actions tab](../../actions)
- **Real-time Logs**: Check individual platform dashboards (Vercel, Railway, Supabase)

See [`docs/ops/README.md`](docs/ops/README.md) for complete environment setup guide.

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

4. **Setup Git Secrets (Security)**
   ```bash
   # Install git-secrets to prevent committing sensitive data
   ./scripts/setup-git-secrets.sh
   ```
   
   This sets up pre-commit hooks to block accidental commits of:
   - Supabase service role keys and JWT tokens
   - Vercel API tokens and deploy hooks  
   - Railway API keys and tokens
   - AWS credentials
   
   📖 [Full Git Secrets Documentation](docs/GIT_SECRETS_SETUP.md)

5. **Setup database:**
   ```bash
   # Run database migrations with error handling
   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -b -e -f backend/app/models.sql
   ```

## 🔧 Configuration

### Required Secrets

LeadLedgerPro requires three essential secrets for proper functionality:

#### Core Required Secrets

1. **`SUPABASE_URL`** - Your Supabase project URL
   - Format: `https://your-project-id.supabase.co`
   - Get from: Supabase Dashboard → Settings → API → Project URL

2. **`SUPABASE_SERVICE_ROLE_KEY`** - Your Supabase service role key
   - Format: Long JWT token starting with `eyJ`
   - Get from: Supabase Dashboard → Settings → API → service_role key
   - ⚠️ **Keep secure** - Never expose in frontend code

3. **`HC_ISSUED_PERMITS_URL`** - Harris County issued permits API endpoint
   - Value: `https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0`
3. **`HC_ISSUED_PERMITS_URL`** - Harris County, Texas issued building permits API endpoint
   - Value: `https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0`
   - Used for: Scraping Harris County, Texas building permit data

#### Setting Secrets with GitHub CLI

**Prerequisites:** Install and authenticate with [GitHub CLI](https://cli.github.com/)
```bash
# Install GitHub CLI (if not already installed)
# macOS: brew install gh
# Ubuntu: sudo apt install gh
# Windows: winget install GitHub.cli

# Authenticate
gh auth login
```

**Set all required secrets:**
```bash
# Method 1: Interactive prompts (will ask for values)
gh secret set SUPABASE_URL
gh secret set SUPABASE_SERVICE_ROLE_KEY  
gh secret set HC_ISSUED_PERMITS_URL

# Method 2: Set values directly
gh secret set SUPABASE_URL --body "https://your-project-id.supabase.co"
gh secret set SUPABASE_SERVICE_ROLE_KEY --body "your-service-role-key-here"
gh secret set HC_ISSUED_PERMITS_URL --body "https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0"

# Method 3: Set from file or environment variable
echo "https://your-project-id.supabase.co" | gh secret set SUPABASE_URL --body -
gh secret set HC_ISSUED_PERMITS_URL --body "$HARRIS_COUNTY_PERMITS_URL"

# Method 3: Set from file or environment variable
echo "https://your-project-id.supabase.co" | gh secret set SUPABASE_URL --body -
gh secret set SUPABASE_SERVICE_ROLE_KEY --body "$SUPABASE_SERVICE_ROLE_KEY"
echo "$HARRIS_COUNTY_PERMITS_URL" | gh secret set HC_ISSUED_PERMITS_URL --body -
```

**Verify secrets are set:**
```bash
gh secret list
```

### Local Development Setup

For testing locally, create environment files with these secrets:

#### Frontend (.env.local)
```bash
cd frontend
cp .env.local.example .env.local
```

Edit `frontend/.env.local`:
```bash
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here

# API Configuration  
NEXT_PUBLIC_API_BASE=http://localhost:8000
NEXT_PUBLIC_DEFAULT_REGION=tx-houston
```

#### Backend (.env)
```bash
cd backend  
cp .env.example .env
```

Edit `backend/.env`:
```bash
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
SUPABASE_JWT_SECRET=your-jwt-secret-here

# Harris County Permits
HC_ISSUED_PERMITS_URL=https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/leadledger
```

#### Permit Scraper (.env)
```bash
cd permit_leads
cp .env.example .env  
```

Edit `permit_leads/.env`:
```bash
# Harris County Permits API
HC_ISSUED_PERMITS_URL=https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0

# Database for storing scraped data
DATABASE_URL=postgresql://user:password@localhost:5432/leadledger
```

### Testing Your Configuration

**Test backend connection:**
```bash
cd backend
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('SUPABASE_URL:', os.getenv('SUPABASE_URL', 'NOT SET'))
print('HC_ISSUED_PERMITS_URL:', os.getenv('HC_ISSUED_PERMITS_URL', 'NOT SET'))
print('Service role key configured:', bool(os.getenv('SUPABASE_SERVICE_ROLE_KEY')))
"
```

python scripts/test-config.py
```bash
cd permit_leads
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('HC_ISSUED_PERMITS_URL:', os.getenv('HC_ISSUED_PERMITS_URL', 'NOT SET'))
"
```

### Environment Variables Setup

For **Vercel deployment**, see the complete setup guide: **[VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md)**

**Quick Vercel setup:**
```bash
vercel env add NEXT_PUBLIC_SUPABASE_URL
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY  
vercel env add SUPABASE_SERVICE_ROLE_KEY
vercel env pull  # Pull to local .env.local
vercel --prod    # Deploy (remember to redeploy after env changes!)
```

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
6. **Captures key page screenshots and detects visual regressions**

**Pipeline Schedule**: Daily at 5:00 AM UTC (Midnight Central Time)

### Visual Regression Testing

The platform includes automated visual regression testing to ensure UI stability:

- 📸 **Nightly Screenshots**: Captures key pages (homepage, dashboard, login, admin) 
- 🔍 **Pixel Diff Analysis**: Compares against baseline images with configurable threshold
- 🚨 **Automated Alerts**: Opens GitHub Issues when visual drift exceeds threshold
- 📁 **Before/After Images**: Stores artifacts for easy review and debugging

See [`docs/VISUAL_REGRESSION.md`](docs/VISUAL_REGRESSION.md) for complete setup and usage instructions.

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

# Redis smoke tests
npm run redis:smoke

# Redis chaos tests (simulates provider slowness)
npm run redis:chaos

# Combined Redis tests (standard + chaos)
npm run redis:smoke:all
```

### Chaos Testing

The platform includes chaos engineering tests to validate resilience against Redis provider slowness:

```bash
# Test Redis operations with 250-500ms latency injection
npm run redis:chaos

# Verify graceful degradation and timeout compliance
python scripts/redis_chaos_smoketest.py
```

See [Redis Chaos Testing Documentation](docs/REDIS_CHAOS_TESTING.md) for detailed information.

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

This repository includes automated workflows for daily permit scraping and performance monitoring:

- **Scheduled Runs**: Automated daily at 6 AM UTC (1 AM CST/2 AM CDT)
- **Manual Runs**: Trigger via GitHub Actions UI with custom parameters
- **Data Storage**: Results committed to repository and available as downloadable artifacts
- **Performance Monitoring**: Lighthouse audits on every PR with budget enforcement

See [`docs/github-actions-runbook.md`](docs/github-actions-runbook.md) for complete setup instructions, troubleshooting, and workflow details.

### Performance Monitoring

#### Workflow: `lighthouse.yml`
- **Trigger**: Every pull request to `main` or `develop` branches
- **Purpose**: Audit Vercel preview deployments for performance budgets
- **Budgets**: LCP ≤ 2.5s, TBT ≤ 300ms, CLS ≤ 0.1
- **Output**: Detailed performance report posted as PR comment

**Performance Steps:**
1. Get latest Vercel deployment URL
2. Run Lighthouse CI with 3 test runs
3. Check performance budgets (LCP, TBT, CLS)
4. Generate markdown report with metrics and status
5. Post report to PR as comment
6. Fail job if any budget is exceeded

**Performance Budgets:**
- **Largest Contentful Paint (LCP)**: ≤ 2.5 seconds
- **Total Blocking Time (TBT)**: ≤ 300 milliseconds  
- **Cumulative Layout Shift (CLS)**: ≤ 0.1

The workflow ensures every PR maintains performance standards before merge.

### Nightly Pipeline

The automated permit scraping pipeline runs daily via GitHub Actions:

#### Workflow: `permit_scrape.yml`
- **Schedule**: Daily at 6 AM UTC (1 AM CST/2 AM CDT)
- **Purpose**: Automatically scrape new building permits from configured sources
- **Output**: CSV, SQLite, and JSONL files with permit data
- **Storage**: Results are committed to the repository and available as artifacts

#### Workflow: `visual-regression.yml`
- **Schedule**: Daily at 9 AM UTC (3 AM CST/4 AM CDT)  
- **Purpose**: Capture screenshots and detect visual regressions on production
- **Output**: Current screenshots, difference images, and test results
- **Alerts**: Opens GitHub Issues when visual drift exceeds threshold

**Pipeline Steps:**
1. Set up Python 3.11 environment
2. Install dependencies from `permit_leads/requirements.txt`
3. Create data directories
4. Run permit scraper for the last 1 day (scheduled) or custom days (manual)
5. Check for new data and commit to repository
6. Upload data artifacts for download
7. Generate summary report
8. **[NEW] Capture page screenshots and compare to baselines**

**Data Location:**
- Raw data: `data/permits/raw/`
- Processed data: `data/permits/aggregate/`
- **Screenshots**: `screenshots/` (artifacts only, not committed)
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

## 🔗 OpenAPI Integration

LeadLedgerPro provides a fully documented REST API with auto-generated clients for seamless integration.

### OpenAPI Specification

The API is documented using OpenAPI 3.1 specification:

- **Specification File**: [`openapi.yaml`](./openapi.yaml)
- **Interactive Docs**: Available at `http://localhost:8000/docs` (Swagger UI)
- **ReDoc**: Available at `http://localhost:8000/redoc` (alternative documentation)

### Auto-Generated Clients

#### TypeScript Client (Frontend)

Located at [`frontend/src/lib/api-client.ts`](./frontend/src/lib/api-client.ts)

```typescript
import { apiClient } from './src/lib/api-client';

// Health check
const health = await apiClient.health.healthCheck();

// Get current user
const user = await apiClient.auth.getCurrentUser();

// Cancel subscription
await apiClient.subscription.cancelSubscription({
  cancellationRequest: {
    user_id: 'user123',
    reason_category: 'user_request'
  }
});
```

#### Python Client (Backend Jobs)

Located at [`backend/clients/`](./backend/clients/)

```python
from backend.clients import LeadLedgerProClient

client = LeadLedgerProClient(base_url='http://localhost:8000')

# Health check
health = client.health.health_check()

# Export data
from backend.clients.leadledderpro_client import ExportDataRequest
result = client.export.export_data(
    export_data_request=ExportDataRequest(
        export_type='leads',
        format='csv'
    )
)
```

### API Validation Workflow

GitHub Actions automatically:

1. **Validates OpenAPI spec** syntax and standards compliance
2. **Generates fresh clients** when the API changes
3. **Fails PRs** that change the API without updating `openapi.yaml`
4. **Comments on PRs** with validation results

### Updating the API Specification

When you modify the backend API endpoints:

1. **Update the spec**: Run `python scripts/extract-openapi.py`
2. **Commit changes**: Include both API changes and `openapi.yaml` updates
3. **Validate**: GitHub Actions will validate and regenerate clients

### Available API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/health` | GET | Basic health check |
| `/healthz` | GET | Extended health check |
| `/api/me` | GET | Current user info |
| `/api/subscription/cancel` | POST | Cancel subscription |
| `/api/subscription/reactivate` | POST | Reactivate subscription |
| `/api/subscription/status/{user_id}` | GET | Subscription status |
| `/api/export/data` | POST | Export data |
| `/api/export/status` | GET | Export configuration |
| `/api/admin/cancellations` | GET | Admin cancellation records |
| `/metrics` | GET | Prometheus metrics |

See [`API_CLIENT_EXAMPLES.md`](./API_CLIENT_EXAMPLES.md) for detailed usage examples.

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

## Supabase Debugging

When troubleshooting issues with your Supabase integration, check these specific locations for detailed error information:

### API Logs
Navigate to **Logs → API** and filter with:
```
route:/rest/v1/leads and status 401|403|5xx
```

### Database Logs  
Navigate to **Logs → Database** and filter:
```
ERROR last 15 minutes
```

### Common Failures and Meanings

| Error Code | Meaning | Description |
|------------|---------|-------------|
| `401` | Invalid API Key | Invalid or missing API key authentication |
| `403` | Permission Denied | Row Level Security policy blocking access |
| `23502` | NOT NULL | Required field is missing or null |
| `FK violations` | Foreign Key | Referenced record doesn't exist or constraint failed |

---

## Legal Notices

- LeadLedgerPro uses publicly available building permit data.
- All users must comply with Do Not Call, CAN-SPAM, and local solicitation laws.
- No guarantee of accuracy or job acquisition.
- See /terms and /privacy for full details.

