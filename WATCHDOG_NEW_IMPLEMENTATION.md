# Watchdog Implementation - System Health Monitoring

This document describes the new automated watchdog system that monitors the health of Railway, Vercel, and ETL processes.

## Overview

The new watchdog system (`.github/workflows/watchdog.yml`) provides comprehensive monitoring of:

1. **Frontend Health** - Vercel deployment health via `/api/health` endpoint
2. **Backend Health** - Railway deployment health via `/healthz` endpoint  
3. **ETL Freshness** - Database freshness by checking permit counts in the last 24 hours

## Schedule

- **Automatic**: Runs every 30 minutes (`*/30 * * * *`)
- **Manual**: Can be triggered via `workflow_dispatch` in GitHub Actions

## Required Secrets

Configure these GitHub repository secrets for the workflow to function:

```bash
FRONTEND_URL=https://your-frontend.vercel.app
BACKEND_URL=https://your-backend.railway.app
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
```

## Health Checks

### Frontend Health Check
```bash
curl -f -s --max-time 30 "$FRONTEND_URL/api/health"
```
- Tests Vercel deployment availability
- Checks frontend health endpoint response

### Backend Health Check  
```bash
curl -f -s --max-time 30 "$BACKEND_URL/healthz"
```
- Tests Railway deployment availability
- Checks backend health endpoint response

### ETL Freshness Check
```python
python scripts/check_etl_freshness.py
```
- Queries Supabase REST API for permits issued in last 24 hours
- Uses `content-range` header to get count without downloading data
- Constructs query: `GET /rest/v1/permits?issue_date=gte.{24h_ago}&limit=1`
- Returns count of recent permits for data freshness validation

## Status Determination

- **Healthy**: All endpoints responding, ETL data is fresh
- **Warning**: ETL data is stale (0 permits in 24h) but endpoints healthy  
- **Unhealthy**: One or more endpoints failing or ETL check failed

## Issue Creation

When critical issues are detected (`unhealthy` status):

1. **Searches** for existing open "System Health Alert" issues
2. **Creates** new issue if none exists, or **comments** on existing issue
3. **Includes** detailed health check results table
4. **Provides** troubleshooting steps for each component

## Testing

Run the validation test suite:

```bash
python test_watchdog_implementation.py
```

This validates:
- ETL script environment variable handling
- ETL script URL construction 
- Curl command availability
- Workflow YAML syntax and structure

## Files

- `.github/workflows/watchdog.yml` - Main workflow file
- `scripts/check_etl_freshness.py` - ETL freshness checker script
- `test_watchdog_implementation.py` - Test suite

## Migration from Old Watchdog

The previous watchdog checked a single debug endpoint daily. The new implementation:

- ✅ Runs every 30 minutes instead of daily
- ✅ Checks multiple endpoints (frontend, backend, database)
- ✅ Uses direct curl health checks instead of custom debug endpoint
- ✅ Validates ETL data freshness via Supabase API
- ✅ Provides more detailed issue reporting with troubleshooting steps

## Troubleshooting

### Frontend Issues
- Check Vercel deployment logs and status
- Verify environment variables in Vercel dashboard
- Test endpoint manually: `curl {FRONTEND_URL}/api/health`

### Backend Issues
- Check Railway deployment logs and status  
- Verify environment variables in Railway dashboard
- Test endpoint manually: `curl {BACKEND_URL}/healthz`

### ETL/Database Issues
- Check Supabase project status: https://status.supabase.com
- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` secrets
- Check recent ETL workflow runs for failures
- Review permit ingestion pipeline status