# Houston ETL and Lead Generation Quick Start

This guide shows how to run the Houston ETL workflow and mint leads as specified in the problem statement.

## Quick Commands

```bash
# 1. Validate setup
npm run houston:validate

# 2. Test run (dry run mode)
npm run houston:etl-and-mint:dry-run

# 3. Production run
npm run houston:etl-and-mint

# 4. Shell script alternative
./scripts/run-houston-etl.sh --dry-run
./scripts/run-houston-etl.sh
```

## Required Environment Variables

```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your_service_role_key"
```

Optional (for ETL):
```bash
export HOUSTON_WEEKLY_XLSX_URL="houston_weekly_url"
export HOUSTON_SOLD_PERMITS_URL="houston_sold_url"
export USER_AGENT="LeadLedgerETL/1.0"
```

## Problem Statement Implementation

The solution implements these exact requirements:

### 1. Run Houston ETL on Self-Hosted Runner
- **Manual Trigger**: Use GitHub Actions "ETL — Houston (on-demand)" workflow
- **Automatic**: Script attempts to trigger workflow, falls back to local execution
- **Local Execution**: `npm run ingest:coh`

### 2. Execute Supabase SQL Commands
The script automatically executes:

```sql
-- Check permits from last 7 days
SELECT count(*) FROM public.permits 
WHERE issued_date >= now() - interval '7 days';

-- Mint leads (limit 50, last 365 days)  
SELECT public.upsert_leads_from_permits_limit(50,365);

-- Get latest leads
SELECT source, external_permit_id, name, county, trade, address, zipcode, created_at 
FROM public.leads 
ORDER BY created_at DESC 
LIMIT 50;
```

### 3. Troubleshooting (if leads=0)
Automatically:
- Prints last ETL job logs from `etl_runs` table
- Verifies Houston data sources (XLSX URLs)
- Checks for constraint/RLS errors
- Provides debugging suggestions

## Manual SQL Execution

### Option 1: Supabase Dashboard
1. Open Supabase Dashboard → SQL Editor
2. Run file: `sql/houston-etl-mint-leads.sql`

### Option 2: Direct Queries
```sql
-- Step 1: Check permits
SELECT count(*) FROM public.permits WHERE issued_date >= now() - interval '7 days';

-- Step 2: Mint leads  
SELECT public.upsert_leads_from_permits_limit(50,365);

-- Step 3: Check results
SELECT source, external_permit_id, name, county, trade, address, zipcode, created_at 
FROM public.leads ORDER BY created_at DESC LIMIT 50;
```

## GitHub Actions Workflow

### Trigger On-Demand Workflow
```bash
# Using GitHub CLI
gh workflow run .github/workflows/etl-houston-ondemand.yml --field days=14

# Using GitHub Web UI
# 1. Go to Actions → "ETL — Houston (on-demand)"
# 2. Click "Run workflow"  
# 3. Set days (default: 14)
# 4. Click "Run workflow"
```

The workflow runs on self-hosted runners with tags: `[self-hosted, linux, x64, scrape]`

## Files Created

| File | Purpose |
|------|---------|
| `scripts/run-houston-etl-and-mint-leads.ts` | Main TypeScript implementation |
| `scripts/run-houston-etl.sh` | Shell script wrapper |
| `sql/houston-etl-mint-leads.sql` | SQL commands for manual execution |
| `scripts/validate-houston-etl.ts` | Validation script |
| `HOUSTON_ETL_MINT_LEADS_IMPLEMENTATION.md` | Detailed documentation |

## Validation

Check if everything is set up correctly:
```bash
npm run houston:validate
```

This validates:
- ✅ Required migration files exist
- ✅ Scripts are present and executable  
- ✅ Supabase functions are callable (if env vars set)
- ✅ Database tables exist

## Troubleshooting

### Common Issues

**No leads generated:**
- Check permits exist: Script automatically verifies
- Review ETL logs: Script fetches from `etl_runs` table
- Verify data sources: Script tests Houston URLs

**Environment errors:**
- Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY
- Check Supabase project settings

**Permission errors:**
- Verify service role key has required permissions
- Check RLS policies on leads/permits tables

**Network errors:**
- Ensure Houston URLs are accessible
- Check firewall/proxy settings

### Debug Mode

Run with dry-run to see what would happen:
```bash
npm run houston:etl-and-mint:dry-run
```

### Manual ETL Only

If you just want to run the ETL without lead generation:
```bash
npm run ingest:coh
```

## Success Indicators

After running successfully, you should see:
1. ✅ Houston ETL completed  
2. ✅ Permits count for last 7 days
3. ✅ Lead generation stats (inserted/updated/total)
4. ✅ Sample of latest leads
5. 📝 Summary written to `logs/houston-etl-mint-leads-summary.json`

## Support

If you encounter issues:
1. Run validation: `npm run houston:validate`
2. Test dry-run: `npm run houston:etl-and-mint:dry-run`
3. Check logs in `logs/` directory
4. Review ETL runs in Supabase `etl_runs` table