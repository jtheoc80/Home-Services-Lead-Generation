# ETL Run Logging Implementation

This document describes the ETL run logging functionality implemented for the City of Houston ETL pipeline.

## Overview

The ETL run logging system tracks individual ETL executions with detailed metrics, status information, and error handling. Each ETL run is logged to a dedicated `etl_runs` table via the Supabase REST API.

## Files Changed/Created

### 1. `sql/etl_runs_table.sql`
- **Purpose**: Database schema for the `etl_runs` table
- **Features**:
  - Tracks ETL execution metrics (fetched, parsed, upserted, errors)
  - Records issue date ranges (first_issue_date, last_issue_date)
  - Stores execution duration and error messages
  - Includes Row Level Security (RLS) policies
  - Auto-updating `updated_at` timestamp via triggers

### 2. `scripts/lib/logEtlRun.ts`
- **Purpose**: Utility function for logging ETL runs to Supabase
- **Key Functions**:
  - `logEtlRun(data: EtlRunData)`: Logs successful or error ETL runs
  - `logEtlError(source_system, error_message, duration_ms)`: Helper for logging errors
- **Features**:
  - Uses axios to insert data via Supabase REST API (`/rest/v1/etl_runs`)
  - Validates required environment variables
  - Proper error handling without exposing secrets
  - TypeScript interfaces for type safety

### 3. `scripts/ingest-coh.ts`
- **Purpose**: Updated City of Houston ETL script with run logging
- **Changes**:
  - Integrated ETL run logging after upsert operations
  - Computes first/last issue dates from permit data
  - Logs successful runs with metrics: `{ source_system: "city_of_houston", fetched, parsed, upserted, errors }`
  - Logs error runs with try/catch error handling
  - Cleaned up duplicated code from previous versions

## Database Setup

Before using the ETL run logging functionality, ensure the `etl_runs` table exists in your Supabase database:

```sql
-- Run this SQL in your Supabase SQL editor
\i sql/etl_runs_table.sql
```

## Environment Variables

The ETL workflow already has the required environment variables configured:

- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Service role key for database access

These are set in `.github/workflows/coh-etl.yml` from GitHub secrets.

## ETL Run Data Structure

Each ETL run logs the following data:

```typescript
interface EtlRunData {
  source_system: string;        // "city_of_houston"
  fetched: number;              // Total records fetched
  parsed: number;               // Records successfully parsed
  upserted: number;             // Records upserted to database
  errors: number;               // Number of errors (0 for success, >0 for failures)
  first_issue_date?: string;    // Earliest permit issue date (ISO format)
  last_issue_date?: string;     // Latest permit issue date (ISO format)
  status?: 'success' | 'error'; // Run status
  error_message?: string;       // Error details (for failed runs)
  duration_ms?: number;         // Execution duration in milliseconds
}
```

## Usage Examples

### Successful ETL Run
```typescript
await logEtlRun({
  source_system: "city_of_houston",
  fetched: 150,
  parsed: 148,
  upserted: 145,
  errors: 0,
  first_issue_date: "2024-01-01",
  last_issue_date: "2024-01-07",
  status: 'success',
  duration_ms: 5000
});
```

### Error ETL Run
```typescript
await logEtlError(
  "city_of_houston",
  "Connection timeout to data source",
  2500
);
```

## Security Considerations

- **No Secret Exposure**: Error messages are sanitized to prevent leaking API keys or sensitive data
- **RLS Policies**: Database access is controlled via Row Level Security policies
- **Service Role Access**: Only the service role can insert/update ETL run records
- **Authenticated Read Access**: Authenticated users can read ETL runs for monitoring

## Monitoring and Observability

The ETL run logging provides several benefits:

1. **Execution Tracking**: Monitor when ETL runs occur and their duration
2. **Data Quality Metrics**: Track fetched vs. parsed vs. upserted record counts
3. **Error Analysis**: Detailed error logging for failed runs
4. **Issue Date Ranges**: Track the temporal scope of each ETL batch
5. **Historical Trends**: Analyze ETL performance over time

## Testing

To test the implementation:

1. Ensure the `etl_runs` table exists in your database
2. Set up proper environment variables
3. Run the ETL script: `npm run ingest:coh`
4. Check the `etl_runs` table for logged entries

The logging functions include comprehensive error handling, so they should not cause ETL failures even if the logging itself encounters issues.