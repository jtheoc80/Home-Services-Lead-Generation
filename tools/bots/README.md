# JT Smoke Test Bot Documentation

## Overview

The `tools/bots/jtSmoke.ts` script is a comprehensive end-to-end smoke test for the Home Services Lead Generation API. It validates the entire lead creation and retrieval workflow.

## Usage

```bash
# Basic usage
npm run e2e:jt -- --baseUrl https://your-app.vercel.app

# With debug information
npm run e2e:jt -- --baseUrl https://your-app.vercel.app --debug
```

## Environment Variables

The script validates and requires the following environment variables:

### Required
- `NEXT_PUBLIC_SUPABASE_URL` - Supabase project URL (masked to suffix in logs)
- `SUPABASE_SERVICE_ROLE_KEY` - Service role key for debug endpoint access
- `DEBUG_API_KEY` - Shared secret for trace endpoint authentication

### Optional
- `LEADS_TEST_MODE` - Set to "true" for e2e testing (bypasses RLS policies)

## Test Flow

### Step 1: Create Lead
- POST to `/api/leads` with test data
- Validates response contains `{ ok: true, trace_id }`
- Uses unique email with timestamp: `jt+{timestamp}@example.com`
- Sends test data: `{ name: "JT Smoke", email: "jt+{timestamp}@example.com", phone: "", source: "e2e" }`

### Step 2: Verify Lead Creation
- GET from `/api/leads/recent`
- Confirms the created email appears in recent leads list

### Step 3: Debug Trace (Optional)
- GET from `/api/leads/trace/{trace_id}` with X-Debug-Key header
- Displays processing stages in chronological order
- Shows success/failure status for each stage

## Success Output

On successful completion, outputs:
```
PASS {trace_id}
```

## Error Handling

- Environment validation errors exit with code 1
- API failures show the failing stage and response body
- Network errors display connection details
- All errors exit with code 1

## API Endpoints

The script validates these API endpoints match the requirements:

### POST /api/leads
- Validates request body with zod schema
- Generates trace_id for tracking
- Logs validation and database insertion stages
- Returns `{ ok: true, trace_id }` on success

### GET /api/leads/recent
- Returns last 10 leads ordered by created_at desc
- Uses service role in test mode, anon key otherwise

### GET /api/leads/trace/{id}
- Requires X-Debug-Key header authentication
- Returns ingest_logs for the trace_id in chronological order
- Service role access only

## Example Output

```bash
$ npm run e2e:jt -- --baseUrl https://myapp.vercel.app --debug

Using Supabase URL: *****.supabase.co
LEADS_TEST_MODE: enabled
Step 1: Creating lead with email jt+1754971234567@example.com
Step 1: PASS - Lead created with trace_id: 123e4567-e89b-12d3-a456-426614174000
Step 2: Checking recent leads
Step 2: PASS - Email jt+1754971234567@example.com found in recent leads
Step 3: Fetching trace information for 123e4567-e89b-12d3-a456-426614174000
Step 3: PASS - Trace stages in order:
  1. validate: OK (2024-01-15T10:30:00.123Z)
     Details: {"message":"Validation successful","received_at":"2024-01-15T10:30:00.123Z"}
  2. db_insert: OK (2024-01-15T10:30:00.234Z)
     Details: {"message":"Lead inserted successfully","lead_id":456,"received_at":"2024-01-15T10:30:00.123Z"}
PASS 123e4567-e89b-12d3-a456-426614174000
```