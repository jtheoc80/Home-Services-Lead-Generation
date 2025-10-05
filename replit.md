# LeadLedgerPro - Texas Home Services Lead Generation Platform

## Overview
LeadLedgerPro is a comprehensive lead generation platform that scrapes permit data from Texas public sources and converts them into scored, actionable leads for home services contractors. The platform features a Next.js frontend dashboard connected to Supabase for data management.

## Project Status (Updated: October 5, 2025)
- ✅ Multi-region support: Greater Houston, Dallas, Austin, Fort Worth, San Antonio, El Paso
- ✅ Coverage: 11.6M people across 6 major Texas metro areas
- ✅ Homepage displays real-time stats from Supabase database
- ✅ Automated scheduled ingestion service running every 6 hours
- ✅ Authentication temporarily disabled (dashboard accessible without login)
- ✅ Dashboard displaying leads with filtering by region and permit numbers
- ✅ Lead scoring system (Hot/Warm/Cold based on project value)

## Recent Changes
**October 5, 2025 (Latest - Owner/Contractor Separation):**
- ✅ Added database fields: contractor_name, owner_name, lead_type, phone, email
- ✅ Updated all 6 ingestion scripts to separate owner from contractor data
- ✅ Owner names prioritized over contractor names for lead generation (higher value)
- ✅ Lead types automatically set: "owner" (property owner), "contractor" (company), "unknown" (fallback)
- ✅ Updated Lead type, LeadCard UI, and CSV export to display owner/contractor information
- ✅ Restored permit ID display on LeadCard (was accidentally removed during update)
- ⏳ Known Issue: Supabase Cloud PostgREST schema cache takes 1-2 minutes to refresh automatically
- ⏳ Frontend queries may show "column does not exist" error until schema cache refreshes
- ✅ Ingestion service successfully inserting leads with new fields (backend working)
- ✅ Researched premium contact enrichment: Requires custom API integration (Clearbit/Hunter.io/Apollo.io)

**October 5, 2025 (City Expansion):**
- ✅ Added Fort Worth, San Antonio, and El Paso to expand Texas coverage to 11.6M people
- ✅ Created ingestion scripts for all three new cities (Fort Worth, San Antonio, El Paso)
- ✅ Updated TexasCountySelector component to display 6 cities total
- ✅ Updated county mapping system for filtering (tarrant, bexar, elpaso)
- ✅ Updated scheduled ingestion service to run all 6 city ingestion scripts
- ✅ Fixed TypeScript error in DashboardClient (Set spread operator)
- ✅ Successfully tested all three new ingestion scripts with sample data fallback
- ✅ Verified leads from all 6 cities are visible in dashboard

**October 5, 2025 (Earlier):**
- ✅ Updated homepage color theme to navy blue and grey for better readability and professional appearance
- ✅ Migrated Tailwind CSS v4 theme colors from config file to CSS @theme directive
- ✅ Replaced vibrant blue-orange gradient with subdued navy-slate color scheme
- ✅ Added external_permit_id field to dashboard, Lead type, LeadCard component, and CSV export
- ✅ Fixed LeadCard import to use correct type definition from '../types/leads'
- ✅ CSV export now includes permit numbers (external_permit_id column)
- ✅ LeadCard compact view displays "Permit #: [number]" for each lead
- ✅ Successfully ingested 20+ leads with permit numbers (Houston and Austin)
- ✅ Automated scheduled ingestion service set up (runs every 6 hours)
- ✅ Homepage now displays real-time statistics from Supabase instead of hardcoded data
- ✅ Created `/api/stats` endpoint to fetch live metrics (active counties, total leads, qualified leads, success rate)
- ✅ Added proper error handling for API responses with res.ok validation
- ✅ Updated Texas Counties section to show real lead counts per region

**October 4, 2025:**
- Added Dallas and Austin permit ingestion scripts
- Updated TexasCountySelector to display exactly 4 regions: Houston, Harris County, Dallas, Austin
- Removed authentication requirements from dashboard access
- Fixed county filtering with mapping (houston→harris, harris→harris, dallas→dallas, austin→travis)
- Resolved React duplicate key warnings in county selector
- Dashboard queries updated to work with remote Supabase schema constraints
- Fixed Next.js React Server Components errors by disabling dev indicators
- Added CSV export functionality to dashboard (Export CSV button in header)
- Configured deployment for Replit Autoscale (not Vercel)

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
  - `scripts/ingest_fortworth.ts` - Fort Worth/Tarrant County permits (stores as county: 'Tarrant')
  - `scripts/ingest_sanantonio.ts` - San Antonio/Bexar County permits (stores as county: 'Bexar')
  - `scripts/ingest_elpaso.ts` - El Paso County permits (stores as county: 'El Paso')
- **API Routes**: 
  - `/frontend/app/api/ingest-region/route.ts` - Regional ingestion endpoint
  - `/frontend/app/api/stats/route.ts` - Live statistics endpoint (active counties, total leads, qualified leads, success rate)
  - `/frontend/app/api/export/route.ts` - CSV export with external_permit_id
- **Scheduled Service**: `scripts/scheduled-ingestion.ts` - Runs every 6 hours to ingest new permits

### Database (Supabase PostgreSQL)
- **Tables**:
  - `permits` - Raw permit data from public sources
  - `leads` - Processed leads with scoring
- **Key Fields**: external_permit_id, name, address, county, trade, value, lead_score, status

## County/Region Mapping
The platform uses a county mapping system for filtering:
- **Greater Houston** → Maps to Harris county data
- **Dallas** → Maps to Dallas county data
- **Austin** → Maps to Travis county data
- **Fort Worth** → Maps to Tarrant county data
- **San Antonio** → Maps to Bexar county data
- **El Paso** → Maps to El Paso county data

## Texas Coverage
The platform now covers **6 major metro areas** with a combined population of **11.6 million**:
1. Greater Houston (Harris County): 4.7M people
2. Dallas: 2.6M people
3. San Antonio (Bexar County): 1.5M people
4. Austin (Travis County): 1.0M people
5. Fort Worth (Tarrant County): 956K people
6. El Paso: 678K people

**Note on Data Sources:**
- Houston, Dallas, Austin: Use real permit data from open data portals (when API is accessible)
- Fort Worth, San Antonio, El Paso: Currently using sample data generation with fallback to real API when available
- All scripts attempt to fetch from official city APIs first, then fall back to sample data if API unavailable

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
- Navy blue and grey color theme for better readability (not vibrant colors)

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
- Dashboard queries optimized for remote schema: `id, name, owner_name, contractor_name, lead_type, trade, county, status, value, lead_score, score_label, created_at, address, zipcode, external_permit_id, phone, email`
- Ingestion scripts generate unique permit IDs using format: `{SOURCE}-{TIMESTAMP}-{INDEX}` (e.g., HOU-1759627520699-001)

## Known Issues & Workarounds

### Supabase PostgREST Schema Cache Delay
**Issue:** After adding new database columns, Supabase Cloud's PostgREST schema cache may not immediately reflect changes. Frontend queries can show "column does not exist" errors even though the columns exist in the database.

**Cause:** On Supabase Cloud, PostgREST is managed by Supabase and the `NOTIFY pgrst, 'reload schema'` command doesn't work. The schema cache refreshes automatically but with a delay.

**Workaround:** 
1. **Wait 1-2 minutes** - The schema cache should auto-refresh
2. Backend operations (SQL inserts, scheduled ingestion) work immediately
3. Frontend queries will succeed once cache propagates
4. For urgent fixes: Restart the Supabase project via dashboard (if available)

**References:**
- [PostgREST Issue #2791](https://github.com/PostgREST/postgrest/issues/2791)
- [Supabase Discussion #3186](https://github.com/orgs/supabase/discussions/3186)

## Lead Delivery System
Currently, leads are delivered through:
- **CSV Export**: Dashboard has an "Export CSV" button that downloads filtered leads
- **Manual Access**: Users view leads directly in the dashboard with filtering by region

**Future Enhancement Options:**
- Email notifications for new hot leads (requires email integration setup - Resend/SendGrid/Gmail)
- Automated email digests (daily/weekly lead summaries)
- Webhook integrations to send leads to external CRMs
- SMS notifications for urgent high-value leads

**Note on Email Integration:**
User declined email integration during setup. To add email notifications in the future:
1. Use search_integrations tool to find email connectors (Resend recommended)
2. Set up the integration via Replit UI
3. Implement notification logic in ingestion scripts or scheduled jobs

## Deployment
- **Platform**: Replit Autoscale (Cloud Run) - NOT Vercel
- **Build Command**: `cd frontend && npm install && npm run build`
- **Run Command**: `cd frontend && npm start`
- **Port Mapping**: 5000 → 80
- To deploy: Click "Publish" button in Replit or use `replit deployment create`
- Environment variables are automatically transferred from development to production

## Next Steps / TODO
- Re-enable authentication after full site configuration
- Validate ingestion scripts against production Supabase instance
- Consider separating Houston city permits from Harris County permits if data sources allow
- Implement lead status management (New → Qualified → Won)
- Set up automated email notifications (when user is ready)
