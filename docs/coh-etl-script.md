# City of Houston ETL Script

## Overview

The `scripts/ingest-coh.ts` script is a complete ETL (Extract, Transform, Load) pipeline for ingesting City of Houston permit data. It fetches permit data from Houston's weekly XLSX files and optionally from sold permits data, then upserts the data to a Supabase database.

## Automation Workflows

### Scheduled ETL (Daily)

The main Houston ETL runs automatically via `.github/workflows/coh-etl.yml`:
- Runs daily at 6 AM UTC
- Uses standard GitHub Actions runners
- Includes optional archive backfill functionality

### On-Demand ETL (Manual)

A new on-demand workflow is available via `.github/workflows/etl-houston-ondemand.yml`:
- **Trigger**: Manual workflow dispatch from GitHub Actions UI
- **Runner**: Self-hosted with scraping capabilities `[self-hosted, linux, x64, scrape]`
- **Configurable**: Lookback window (default: 14 days)
- **Concurrency**: Single instance with group `etl-houston`

To run the on-demand ETL:
1. Go to GitHub Actions → "ETL — Houston (on-demand)"
2. Click "Run workflow"
3. Optionally adjust the "Lookback window in days" (default: 14)
4. Click "Run workflow" to start

## Usage

```bash
# Set required environment variables
export SUPABASE_URL=your_supabase_project_url
export SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
export HOUSTON_WEEKLY_XLSX_URL=url_to_houston_weekly_xlsx_file

# Run the script
npx tsx scripts/ingest-coh.ts

# Or use the npm script
npm run ingest:coh
```

## Required Environment Variables

- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key for database access
- `HOUSTON_WEEKLY_XLSX_URL` - URL to the Houston weekly permits XLSX file

## Optional Environment Variables

- `HOUSTON_SOLD_PERMITS_URL` - URL for Houston sold permits data (optional)
- `DAYS` - Number of days to look back for permits (default: 7)
- `ETL_ALLOW_EMPTY` - Set to "1" to exit gracefully when no records found

## GitHub Secrets Configuration

For the automated workflows to work, configure these secrets in GitHub Settings → Secrets and variables → Actions:

**Required Secrets:**
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `HOUSTON_WEEKLY_URL` - Houston weekly permits XLSX URL
- `HOUSTON_SOLD_URL` - Houston sold permits URL (optional)

**Optional Secrets:**
- `USER_AGENT` - Custom user agent for HTTP requests (optional)

The on-demand workflow will validate connectivity to Houston endpoints before starting the ETL process.

## What the Script Does

1. **Fetches Data**: Downloads permit data from Houston XLSX sources
2. **Processes Data**: Normalizes and validates the permit records
3. **Upserts to Database**: Saves the data to Supabase using batch upserts
4. **Logs Results**: Records ETL run statistics and status
5. **Generates Reports**: Creates summary JSON files for monitoring
6. **Post-processing**: Calls artifact management scripts

## Output

The script creates:

- `logs/etl-summary.json` - Summary of the ETL run with statistics
- `logs/etl_output.log` - Detailed log file
- Console output with progress and status information

## Error Handling

- Validates all required environment variables
- Handles network errors gracefully
- Provides detailed error messages
- Logs all errors to the database
- Continues with partial data when possible
- Can be configured to allow empty result sets

## Preflight Checks

The City of Houston ETL workflow includes preflight connectivity checks via `scripts/houston-preflight.py`. This script:

- **Validates Environment Variables**: Ensures all required variables are set
- **URL Format Validation**: Verifies all URLs are properly formatted
- **Supabase Connectivity**: Tests database connection (critical - blocks workflow if failed)
- **Houston Endpoints**: Tests connectivity to Houston city websites (non-critical - warnings only)

### Connectivity Issues

If you encounter connectivity issues with Houston endpoints:

1. **Network Access**: The runner may not have access to www.houstontx.gov
   - **Solution**: Add www.houstontx.gov to the allowlist (see `COPILOT_ALLOWLIST_REQUEST.md`)
   - **Alternative**: Use a self-hosted runner with network access

2. **Endpoint Temporarily Down**: Houston city websites may be temporarily unavailable
   - **Result**: Workflow continues with warnings but does not fail
   - **Mitigation**: ETL may work with cached or alternative data sources

3. **Critical vs Non-Critical Failures**:
   - **Critical**: Supabase connectivity issues will stop the workflow
   - **Non-Critical**: Houston endpoint issues generate warnings but allow workflow to proceed

### Running Preflight Checks Manually

```bash
# Set required environment variables first
export SUPABASE_URL=your_supabase_project_url
export SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
export HOUSTON_WEEKLY_XLSX_URL=url_to_houston_weekly_xlsx_file

# Run preflight checks
python scripts/houston-preflight.py
```

## Integration

This script integrates with the existing repository infrastructure:

- Uses existing Houston permit adapters (`scripts/adapters/houstonXlsx.ts`)
- Leverages the Supabase upsert utilities (`scripts/lib/supabaseUpsert.ts`)
- Integrates with ETL run logging (`scripts/lib/logEtlRun.ts`)
- Calls post-processing artifacts script (`scripts/ensure_artifacts.py`)

## Testing

Run the validation test to verify the script works correctly:

```bash
npx tsx scripts/test-coh-validation.ts
```

This test verifies:
- Environment variable validation
- Script execution without syntax errors
- NPM script functionality
- Error handling capabilities

## Troubleshooting

### Common Issues

#### "Houston endpoint connection error" in GitHub Actions

**Symptom**: Workflow fails with connectivity check errors to www.houstontx.gov

**Cause**: GitHub Actions runners may not have access to Houston city government websites

**Solutions**:
1. **Allowlist the domain**: Request to add www.houstontx.gov to the GitHub Copilot allowlist
2. **Use self-hosted runner**: Set up a runner with network access to Houston endpoints
3. **Expected behavior**: As of the latest update, Houston endpoint failures are non-critical and should not stop the workflow

#### Environment Variable Issues

**Symptom**: "Missing required environment variables" error

**Solution**: Ensure all required secrets are configured in GitHub repository settings:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY` 
- `HOUSTON_WEEKLY_XLSX_URL`

#### Supabase Connectivity Issues

**Symptom**: "Supabase connectivity: Health check failed"

**Solutions**:
- Verify Supabase URL and service role key are correct
- Check if Supabase project is accessible
- Ensure service role has proper permissions