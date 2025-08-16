# Watchdog Implementation

This document describes the automated watchdog system that monitors data ingestion flow and creates GitHub issues when problems are detected.

## Overview

The watchdog system consists of:

1. **Debug Endpoint** (`/api/_debug/sb`) - Backend endpoint that reports system health and recent permit counts
2. **Watchdog Workflow** (`.github/workflows/watchdog.yml`) - Daily automated check that probes the endpoint and files issues

## Debug Endpoint: `/api/_debug/sb`

### Purpose
Provides a lightweight health check specifically designed for automated monitoring of:
- Database connectivity
- Recent permit ingestion (last 24 hours)
- Ingestion pipeline health

### Authentication
- Requires `X-Debug-Key` header with value matching `DEBUG_API_KEY` environment variable
- Returns 401 if unauthorized
- Returns 503 if `DEBUG_API_KEY` not configured

### Response Format
```json
{
  "ok": true,
  "permits": 42,
  "response_time_ms": 123.45,
  "ts": 1704067200
}
```

### Fields
- `ok` (boolean): Overall system health status
- `permits` (integer): Count of permits ingested in the last 24 hours
- `response_time_ms` (number): Response time in milliseconds
- `ts` (integer): Unix timestamp of the response

### Health Logic
The endpoint returns `ok: false` when:
- Database connectivity fails
- No permits ingested in last 24 hours AND ingestion is stale (>25 hours old)
- No permits ingested in last 24 hours AND last ingestion status was not 'success'
- No ingestion state records found

## Watchdog Workflow

### Schedule
- Runs daily at 06:30 UTC (after the ingest agents complete)
- Can be triggered manually via `workflow_dispatch`

### Required Secrets
- `DEBUG_URL`: Full URL to the backend `/api/_debug/sb` endpoint
- `DEBUG_API_KEY`: Secret key for endpoint authentication

### Example Secret Values
```bash
DEBUG_URL=https://your-backend.railway.app/api/_debug/sb
DEBUG_API_KEY=your-secret-debug-key-here
```

### Workflow Logic
1. **Probe Step**: 
   - Calls the debug endpoint with authentication
   - Parses JSON response to extract `ok` and `permits` fields
   - Sets status to "bad" if `ok != true` OR `permits == 0`

2. **File Issue Step** (only runs if status is "bad"):
   - Searches for existing open issues with title "🚨 Ingest watchdog: data not flowing"
   - Creates new issue if none exists
   - Adds comment to existing issue if one is found
   - Includes the raw debug response for troubleshooting

### Issue Template
When problems are detected, the watchdog creates issues with:
- **Title**: "🚨 Ingest watchdog: data not flowing"
- **Labels**: `["ingest", "watchdog"]`
- **Body**: Includes debug response and remediation steps

### Remediation Steps Provided
The automated issues include these troubleshooting steps:
1. Check Vercel environment variables (URL/keys/CRON_SECRET)
2. Test permit ingestion with dry run: `/api/permits/ingest?source=austin&dry=1`
3. Inspect function logs in Vercel

## Testing

### Backend Endpoint Test
```bash
python test_debug_sb.py
```
Tests the debug endpoint with proper authentication and validates response structure.

### Workflow Logic Test
```bash
./test_watchdog_logic.sh
```
Tests the JSON parsing and status determination logic used in the workflow.

### Curl Command Test
```bash
./test_watchdog_curl.sh
```
Validates the curl command format used in the workflow.

## Deployment Checklist

1. **Backend**: Deploy the updated `main.py` with the new `/api/_debug/sb` endpoint
2. **Environment**: Set `DEBUG_API_KEY` environment variable in the backend deployment
3. **Secrets**: Configure GitHub repository secrets:
   - `DEBUG_URL`: Point to your backend's debug endpoint
   - `DEBUG_API_KEY`: Same value as backend environment variable
4. **Workflow**: The `.github/workflows/watchdog.yml` will activate automatically

## Security Considerations

- Debug endpoint requires authentication to prevent information disclosure
- Debug key should be a strong, randomly generated value
- Response includes minimal information needed for monitoring
- No sensitive data is exposed in the debug response

## Monitoring

- Successful runs produce no notifications
- Failed runs create/update GitHub issues automatically
- Check the Actions tab for workflow execution history
- Review created issues for patterns in system problems