# Source Health Monitoring

This directory contains the Source Health monitoring system that tracks the availability and performance of Texas permit data sources.

## Overview

The Source Health system consists of:

1. **GitHub Action** (`.github/workflows/source-health.yml`) - Runs hourly to probe data sources
2. **Probe Script** (`scripts/probeSources.ts`) - Tests each data source and records health metrics  
3. **Database Schema** (`sql/source_health_setup.sql`) - Tables and views for storing health data

## Data Sources Monitored

| Source | Type | Description |
|--------|------|-------------|
| `austin_socrata` | Socrata API | City of Austin permit data |
| `sa_socrata` | Socrata API | City of San Antonio permit data |
| `dallas_socrata` | Socrata API | City of Dallas permit data |
| `houston_csv` | CSV/HTTP | City of Houston permit CSV file |
| `harris_county` | ArcGIS | Harris County ArcGIS services |

## Environment Variables Required

- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `AUSTIN_SOCRATA_APP_TOKEN` - Austin Socrata API token
- `SA_SOCRATA_APP_TOKEN` - San Antonio Socrata API token

## Setup

1. **Database Setup**: Run the SQL schema setup
   ```bash
   psql "$SUPABASE_URL" < sql/source_health_setup.sql
   ```

2. **GitHub Secrets**: Add the required environment variables to GitHub repository secrets

3. **Manual Test**: Test the probe script locally
   ```bash
   npx tsx scripts/test_probeSources.ts
   npx tsx scripts/probeSources.ts
   ```

## Workflow Schedule

- **Automatic**: Runs every hour at 15 minutes past the hour (`15 * * * *`)
- **Manual**: Can be triggered via GitHub Actions UI

## Health Status Values

- **online** ✅ - Source responding normally with expected data
- **limited** ⚠️ - Source responding but with issues (slow, partial data)  
- **offline** ❌ - Source not responding or returning errors

## Monitoring Output

The GitHub Action produces a formatted health summary in the workflow run that shows:
- Source name and status
- Response time in milliseconds
- Number of records available
- Error messages (if any)

## Database Schema

### `source_health` table
Stores all health check records with timestamp history.

### `source_health_latest` view  
Shows the most recent health status for each source.

## Testing

```bash
# Test script functionality
npx tsx scripts/test_probeSources.ts

# Test with mock environment (will fail on network calls)
SUPABASE_URL="https://test.supabase.co" SUPABASE_SERVICE_ROLE_KEY="test" npx tsx scripts/probeSources.ts
```