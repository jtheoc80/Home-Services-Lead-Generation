# Houston ETL and Lead Generation Implementation

This document describes the implementation of the Houston ETL and Lead Generation pipeline as specified in the problem statement.

## Problem Statement Requirements

The implementation addresses the following requirements:

1. **Run the Houston ETL workflow on the self-hosted runner**
2. **Execute Supabase SQL commands:**
   - `select count(*) from public.permits where issued_date >= now() - interval '7 days';`
   - `select public.upsert_leads_from_permits_limit(50,365);`
   - `select source, external_permit_id, name, county, trade, address, zipcode, created_at from public.leads order by created_at desc limit 50;`
3. **Troubleshooting:** If leads=0, print the last ETL job logs and verify sources

## Implementation Files

### 1. Main TypeScript Script
**File:** `scripts/run-houston-etl-and-mint-leads.ts`

Comprehensive TypeScript implementation that:
- Validates environment variables
- Runs Houston ETL locally
- Executes all required Supabase SQL commands via REST API
- Implements troubleshooting when no leads are generated
- Provides detailed logging and error handling
- Supports dry-run mode for testing

**Usage:**
```bash
# Run the full pipeline
npm run houston:etl-and-mint

# Dry run (shows what would be done)
npm run houston:etl-and-mint:dry-run

# Direct execution
tsx scripts/run-houston-etl-and-mint-leads.ts [--dry-run]
```

### 2. Shell Script Wrapper
**File:** `scripts/run-houston-etl.sh`

Bash script wrapper that:
- Checks system requirements
- Attempts to trigger GitHub Actions workflow
- Falls back to local ETL execution
- Calls the TypeScript script
- Provides usage instructions

**Usage:**
```bash
# Run the full pipeline
./scripts/run-houston-etl.sh

# Dry run mode
./scripts/run-houston-etl.sh --dry-run

# Verbose output
./scripts/run-houston-etl.sh --verbose

# Show help
./scripts/run-houston-etl.sh --help
```

### 3. SQL Script for Manual Execution
**File:** `sql/houston-etl-mint-leads.sql`

SQL script that can be executed directly in Supabase SQL Editor:
- Checks permits count for last 7 days
- Calls `upsert_leads_from_permits_limit(50, 365)`
- Retrieves latest leads
- Includes troubleshooting queries for ETL logs and RLS policies

### 4. Package.json Scripts
Added npm scripts for easy execution:
```json
"houston:etl-and-mint": "tsx scripts/run-houston-etl-and-mint-leads.ts",
"houston:etl-and-mint:dry-run": "tsx scripts/run-houston-etl-and-mint-leads.ts --dry-run"
```

## Required Environment Variables

```bash
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Optional (for ETL)
HOUSTON_WEEKLY_XLSX_URL=url_to_houston_weekly_xlsx
HOUSTON_SOLD_PERMITS_URL=url_to_houston_sold_permits
USER_AGENT=LeadLedgerETL/1.0
```

## Workflow Integration

The implementation works with existing GitHub Actions workflows:

### On-Demand Workflow
**File:** `.github/workflows/etl-houston-ondemand.yml`
- Runs on self-hosted runners with tags: `[self-hosted, linux, x64, scrape]`
- Manually triggered via GitHub Actions UI
- Configurable lookback window (default: 14 days)

### Scheduled Workflow  
**File:** `.github/workflows/coh-etl.yml`
- Runs daily at 6 AM UTC
- Also uses self-hosted runners
- Includes optional archive backfill

## Features

### 1. Comprehensive Error Handling
- Validates environment variables
- Handles API failures gracefully
- Provides detailed error messages
- Continues execution when possible

### 2. Troubleshooting Capabilities
When no leads are generated, automatically:
- Fetches recent ETL run logs from `etl_runs` table
- Verifies data source URLs (Houston XLSX endpoints)
- Provides suggestions for fixing constraint/RLS errors
- Checks table permissions and RLS policies

### 3. Data Source Verification
Verifies connectivity to:
- Houston Weekly XLSX URL
- Houston Sold Permits URL
- ArcGIS endpoints (?f=pjson)
- Socrata endpoints ($limit=1 with tokens)

### 4. Logging and Monitoring
- Writes execution summary to `logs/houston-etl-mint-leads-summary.json`
- Logs ETL runs to `etl_runs` table
- Provides detailed console output
- Supports dry-run mode for testing

### 5. SQL Query Implementation
Executes all required SQL commands:
```sql
-- Problem statement requirement 1
SELECT count(*) FROM public.permits 
WHERE issued_date >= now() - interval '7 days';

-- Problem statement requirement 2  
SELECT public.upsert_leads_from_permits_limit(50,365);

-- Problem statement requirement 3
SELECT source, external_permit_id, name, county, trade, address, zipcode, created_at 
FROM public.leads 
ORDER BY created_at DESC 
LIMIT 50;
```

## Usage Examples

### Quick Start
```bash
# Set environment variables
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your_key_here"

# Run the pipeline
npm run houston:etl-and-mint
```

### GitHub Actions Trigger
```bash
# Using GitHub CLI
gh workflow run .github/workflows/etl-houston-ondemand.yml --field days=14
```

### Manual SQL Execution
1. Open Supabase Dashboard
2. Go to SQL Editor
3. Run `sql/houston-etl-mint-leads.sql`

## Testing

### Dry Run Mode
Test the implementation without making changes:
```bash
npm run houston:etl-and-mint:dry-run
```

### Component Testing
Test individual components:
```bash
# Test ETL only
npm run ingest:coh

# Test with existing function
npm run test:etl-logging
```

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**
   - Solution: Set required SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY

2. **No Permits Found**
   - Check if permits exist: `SELECT count(*) FROM permits;`
   - Verify issued_date column has recent data

3. **No Leads Generated**
   - Script automatically runs troubleshooting
   - Check ETL logs in `etl_runs` table
   - Verify RLS policies on leads table

4. **Data Source Connectivity**
   - Script verifies Houston endpoints
   - Check firewall/network access
   - Verify URL configurations

### Debug Output
The implementation provides detailed logging:
- Environment variable validation
- API call details
- SQL query results
- Error messages with context
- Execution timing

## Security Considerations

- Uses Supabase service role key for database access
- Sanitizes error messages to prevent secret leakage
- Respects RLS policies
- Validates all inputs before processing
- Supports dry-run mode for safe testing