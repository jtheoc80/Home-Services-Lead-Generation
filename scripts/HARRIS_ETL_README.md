# Harris County ETL Pipeline

This directory contains the implementation of the Harris County permit data ETL (Extract, Transform, Load) pipeline as specified in the project requirements.

## Components

### 1. fetchHarrisIssuedPermits Function (`scripts/harrisPermitsFetcher.ts`)

Core function that fetches Harris County issued permits data with the following features:

- **Count Check**: Calls FeatureServer/0 with `returnCountOnly=true` first
- **Error Handling**: Throws error with full query URL if count==0
- **Pagination**: Pages in 2000-row chunks using `resultOffset` until empty
- **Field Mapping**: Maps fields to standardized schema with proper data types
- **Date Conversion**: Converts ISSUEDDATE milliseconds to ISO UTC format
- **Retry Logic**: Retries 429/5xx errors with exponential backoff and jitter
- **Max Retries**: Up to 5 retry attempts per request
- **Logging**: Logs total number of permits fetched

#### Field Mapping
```typescript
{
  event_id: string;           // EVENTID or OBJECTID
  permit_number: string;      // PERMITNUMBER
  permit_name: string;        // PERMITNAME or PROJECTNAME
  app_type: string;          // APPTYPE
  issue_date_iso: string;    // ISSUEDDATE (ms) → ISO UTC
  full_address: string;      // FULLADDRESS
  street_number: string;     // STREETNUMBER
  street_name: string;       // STREETNAME
  status: string;           // STATUS
  project_number: string;   // PROJECTNUMBER
  raw: Record<string, any>; // Complete original attributes
}
```

### 2. supabaseUpsert Function (`scripts/supabaseUpsert.ts`)

Idempotent upsert utility with the following features:

- **Function Signature**: `supabaseUpsert(table: string, rows: any[], conflict='event_id')`
- **Supabase Integration**: Uses `@supabase/supabase-js` with `SUPABASE_SERVICE_ROLE_KEY`
- **Chunking**: Processes data in 500-row chunks to avoid Supabase limits
- **Error Handling**: Throws detailed error messages on batch failures
- **Idempotency**: Uses conflict resolution on specified column (default: 'event_id')

### 3. CLI Smoke Test (`scripts/etlDelta.ts`)

Command-line tool that validates the ETL pipeline with delta checking:

#### Functionality
1. Reads current `count(*)` from `public.permits_raw_harris`
2. Runs `fetchHarrisIssuedPermits(Date.now()-7*24*3600*1000)` (7 days back)
3. Upserts fetched permits into `permits_raw_harris` table
4. Reads count again and asserts `newCount > oldCount`
5. Prints number of inserted/updated records
6. Exits with code 1 if no new rows detected

#### Usage
```bash
npm run harris:etl-delta
# or
npx tsx scripts/etlDelta.ts
```

#### Output Format
The script outputs JSON summaries for monitoring:
```json
{
  "timestamp": "2025-08-12T14:25:00.010Z",
  "test": "etl-delta",
  "status": "success|failure|error",
  "oldCount": 1000,
  "newCount": 1025,
  "delta": 25,
  "permitsFetched": 30,
  "sinceDate": "2025-08-05T14:25:00.010Z"
}
```

### 4. GitHub Action Workflow (`.github/workflows/etl-harris.yml`)

Automated hourly ETL pipeline with the following features:

#### Triggers
- **Cron Schedule**: Runs hourly at the top of each hour (`0 * * * *`)
- **Manual Trigger**: Supports `workflow_dispatch` for manual execution

#### Environment Variables
- `HC_ISSUED_PERMITS_URL`: Harris County FeatureServer URL
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase service role key for database access
- `SUPABASE_URL`: Supabase project URL

#### Steps
1. **Setup**: Checkout code, setup Node.js, install dependencies
2. **ETL Execution**: Run `scripts/etlDelta.ts` with logging
3. **Log Processing**: Extract JSON summaries for monitoring
4. **Artifact Upload**: Upload logs with 30-day retention
5. **Stale Data Check**: Verify recent data exists (24h failure protection)
6. **Failure Notification**: Detailed failure reporting

#### Monitoring
- Uploads execution logs as GitHub artifacts
- Extracts JSON summaries for external monitoring systems
- Fails if no new records in 24 hours (data staleness protection)

## Environment Variables

### Required
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase service role key for database operations
- `SUPABASE_URL` or `NEXT_PUBLIC_SUPABASE_URL`: Supabase project URL

### Optional
- `HC_ISSUED_PERMITS_URL`: Harris County API URL (defaults to known endpoint)

## Database Schema

The ETL pipeline expects a `permits_raw_harris` table with the following schema:

```sql
CREATE TABLE permits_raw_harris (
  event_id TEXT PRIMARY KEY,
  permit_number TEXT,
  permit_name TEXT,
  app_type TEXT,
  issue_date_iso TIMESTAMPTZ,
  project_number TEXT,
  full_address TEXT,
  street_number TEXT,
  street_name TEXT,
  status TEXT,
  raw JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Recommended indexes
CREATE INDEX idx_permits_raw_harris_issue_date ON permits_raw_harris(issue_date_iso);
CREATE INDEX idx_permits_raw_harris_status ON permits_raw_harris(status);
CREATE INDEX idx_permits_raw_harris_app_type ON permits_raw_harris(app_type);
CREATE INDEX idx_permits_raw_harris_created_at ON permits_raw_harris(created_at);
```

## Testing

### Validation Tests
```bash
# Test the ETL functions (validation only)
npx tsx /tmp/validate-etl.ts

# Test ETL Delta script logic
npx tsx /tmp/test-etl-delta-logic.ts

# End-to-end ETL Delta script test
npx tsx /tmp/test-etl-delta-e2e.ts
```

### Manual Testing
```bash
# Test Harris County API connectivity
npm run harris:smoke

# Run full ETL delta test
npm run harris:etl-delta
```

## Error Handling

### Network Errors
- Automatic retry with exponential backoff and jitter
- Up to 5 retry attempts for 429/5xx errors
- Graceful handling of connection timeouts and resets

### Data Validation
- Validates count > 0 before proceeding with data fetch
- Ensures all required environment variables are present
- Validates Supabase response for each batch

### Monitoring
- Comprehensive JSON logging for external monitoring
- GitHub Action artifacts for debugging
- Stale data detection and alerting

## Performance Characteristics

- **Batch Size**: 2000 records per API request
- **Upsert Chunks**: 500 records per Supabase upsert
- **Timeout**: 30 seconds per API request
- **Retry Delay**: Exponential backoff (2^attempt seconds) + random jitter
- **Memory**: Processes data in chunks to minimize memory usage

## Production Deployment

1. **Set GitHub Secrets**:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `HC_ISSUED_PERMITS_URL` (optional)

2. **Enable Workflow**: The workflow runs automatically hourly

3. **Monitor Execution**: Check GitHub Actions for run status and artifacts

4. **Verify Data**: Check `permits_raw_harris` table for new records

## Troubleshooting

### Common Issues

1. **"No permits found" Error**: 
   - Check if HC_ISSUED_PERMITS_URL is correct
   - Verify API is accessible from deployment environment
   - Confirm date range has available data

2. **Supabase Connection Errors**:
   - Verify SUPABASE_SERVICE_ROLE_KEY is correct
   - Check SUPABASE_URL format
   - Ensure table exists with proper schema

3. **GitHub Action Failures**:
   - Check secrets are configured correctly
   - Review workflow logs in Actions tab
   - Verify artifacts for detailed error information

### Debug Commands

```bash
# Check API connectivity
curl "https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0/query?where=1%3D1&returnCountOnly=true&f=json"

# Test with recent timestamp
curl "https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0/query?where=ISSUEDDATE%20%3E%20$(date -d '7 days ago' +%s)000&returnCountOnly=true&f=json"

# Verify Supabase table
npx tsx -e "
import { createClient } from '@supabase/supabase-js';
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);
supabase.from('permits_raw_harris').select('*', { count: 'exact', head: true }).then(console.log);
"
```