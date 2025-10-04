# LeadLedgerPro - Texas Home Services Lead Generation Platform

## Overview
LeadLedgerPro is a comprehensive lead generation platform that scrapes permit data from Texas public sources and converts them into scored, actionable leads for home services contractors. The platform features a Next.js frontend dashboard connected to Supabase for data management.

## Project Status (Updated: October 4, 2025)
- ✅ Multi-region support: Houston, Harris County, Dallas, Austin
- ✅ Regional permit ingestion scripts operational
- ✅ Authentication temporarily disabled (dashboard accessible without login)
- ✅ Dashboard displaying leads with filtering by region
- ✅ Lead scoring system (Hot/Warm/Cold based on project value)

## Recent Changes
**October 4, 2025:**
- Added Dallas and Austin permit ingestion scripts
- Updated TexasCountySelector to display exactly 4 regions: Houston, Harris County, Dallas, Austin
- Removed authentication requirements from dashboard access
- Fixed county filtering with mapping (houston→harris, harris→harris, dallas→dallas, austin→travis)
- Resolved React duplicate key warnings in county selector
- Dashboard queries updated to work with remote Supabase schema constraints

## Project Architecture

### Frontend (Next.js + TypeScript)
- **Dashboard**: `/frontend/app/dashboard/page.tsx` - Main dashboard with metrics and lead list
- **Components**: 
  - `DashboardClient.tsx` - Client-side dashboard logic with filtering
  - `TexasCountySelector.tsx` - Region selector component
  - Lead scoring and display components
- **Middleware**: Authentication temporarily disabled via empty `protectedRoutes` array

### Backend & Data Ingestion
- **Ingestion Scripts**:
  - `scripts/ingest_houston.ts` - Houston/Harris County permits (stores as county: 'Harris')
  - `scripts/ingest_dallas.ts` - Dallas County permits (stores as county: 'Dallas')
  - `scripts/ingest_austin.ts` - Travis County/Austin permits (stores as county: 'Travis')
- **API Routes**: `/frontend/app/api/ingest-region/route.ts` - Regional ingestion endpoint

### Database (Supabase PostgreSQL)
- **Tables**:
  - `permits` - Raw permit data from public sources
  - `leads` - Processed leads with scoring
- **Key Fields**: external_permit_id, name, address, county, trade, value, lead_score, status

## County/Region Mapping
The platform uses a county mapping system for filtering:
- **Houston** → Maps to Harris county data
- **Harris County** → Maps to Harris county data
- **Dallas** → Maps to Dallas county data
- **Austin** → Maps to Travis county data

Note: Houston and Harris County both display the same leads since Houston permits are stored with county='Harris' in the database.

## Lead Scoring System
- **Hot Leads** (90+): High-value projects, immediate opportunities
- **Warm Leads** (60-89): Medium-value projects, good potential
- **Cold Leads** (<60): Lower-value projects, long-term prospects

Scoring based on:
- Project value/budget
- Permit recency
- Work type/trade category
- Location factors

## User Preferences
- Clean, organized code structure
- Separate components for maintainability
- TypeScript for type safety
- Minimal temporary/debug files

## Environment Configuration
Required secrets (already configured):
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`

## Development Workflow
1. Frontend runs on port 5000 (workflow: "Frontend Server")
2. Database operations use Supabase client
3. Regional ingestion via scripts or API endpoints
4. Authentication currently disabled for development

## Known Schema Differences
- Local dev database has `city`, `state` columns
- Remote Supabase database uses minimal schema
- Dashboard queries optimized for remote schema: `id, name, trade, county, status, value, lead_score, created_at, address, zipcode`

## Next Steps / TODO
- Re-enable authentication after full site configuration
- Validate ingestion scripts against production Supabase instance
- Consider separating Houston city permits from Harris County permits if data sources allow
- Add lead export functionality
- Implement lead status management (New → Qualified → Won)
