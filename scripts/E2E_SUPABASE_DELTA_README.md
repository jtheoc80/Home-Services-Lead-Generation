# E2E Supabase Delta Test

The `scripts/e2e_supabase_delta.ts` script provides end-to-end testing for the Harris County permits scraping pipeline with Supabase integration.

## What it does

1. **Reads initial count** from `public.permits_raw_harris` table via Supabase REST API using service role credentials
2. **Runs Harris scraper** for a specified time period (default: 3 days) with Supabase sink enabled
3. **Re-reads the count** and asserts that `newCount > oldCount`
4. **Exits with appropriate status codes** and readable error messages

## Usage

### Prerequisites

Set up environment variables:
```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your_service_role_key"
```

### Running the test

```bash
# Run with default settings (3 days)
npm run e2e:supabase-delta

# Run with custom time period
npm run e2e:supabase-delta -- --since=7d

# Test Supabase connection only (dry run)
npm run e2e:supabase-delta -- --dry-run

# Show help
npm run e2e:supabase-delta -- --help
```

### Direct execution

```bash
# Run with tsx directly
tsx scripts/e2e_supabase_delta.ts
tsx scripts/e2e_supabase_delta.ts --since=1d
tsx scripts/e2e_supabase_delta.ts --dry-run
```

## Options

- `--since=<period>` - Time period to scrape (default: 3d)
  - Examples: `1d`, `7d`, `24h`, `2024-01-01`
- `--dry-run` - Only test Supabase connection, skip scraper execution
- `--help`, `-h` - Show help message

## Exit Codes

- **0** - Success: New permits were found and added to the database
- **1** - Failure: No new permits found, scraper failed, or other errors

## Output Example

```
🏠 E2E Supabase Delta Test for Harris County Permits
============================================================
📊 Supabase URL: https://your-project.supabase.co
⏱️  Since: 3d
🧪 Mode: FULL TEST

📈 Step 1: Reading initial count from permits_raw_harris...
   Initial count: 1234

🔄 Step 2: Running Harris scraper for --since=3d...
✅ Harris scraper completed successfully

📊 Step 3: Reading final count from permits_raw_harris...
   Final count: 1267
   Delta: +33

============================================================
📋 TEST RESULTS
============================================================
✅ Test PASSED: Final count (1267) > Initial count (1234), Delta: +33
⏱️  Duration: 45.2s
📊 Summary: 1234 → 1267 (+33)

🎉 E2E test completed successfully!
```

## Error Handling

The script provides detailed error messages and troubleshooting guidance for common issues:

- Missing environment variables
- Supabase connection failures
- Empty scrape results
- Harris County API issues
- Permission problems

## Implementation Notes

- Uses the existing `scripts/harrisCounty/issuedPermits.ts` which writes directly to Supabase
- Leverages Supabase service role for bypassing RLS policies
- Includes a 2-second settling delay after scraping to ensure data consistency
- Supports both absolute dates and relative time periods