# City of Houston ETL Script

## Overview

The `scripts/ingest-coh.ts` script is a complete ETL (Extract, Transform, Load) pipeline for ingesting City of Houston permit data. It fetches permit data from Houston's weekly XLSX files and optionally from sold permits data, then upserts the data to a Supabase database.

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