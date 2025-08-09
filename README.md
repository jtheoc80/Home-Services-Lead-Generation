# LeadLedgerPro

Automated building permit intelligence platform for contractors – fresh leads daily, scored for conversion.

[![Nightly Scrape](https://github.com/jtheoc80/Home-Services-Lead-Generation/actions/workflows/nightly-scrape.yml/badge.svg)](https://github.com/jtheoc80/Home-Services-Lead-Generation/actions/workflows/nightly-scrape.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 1. Overview

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
