# Next.js API Routes Analysis - Ingestion/Verification

## Search Results Summary

This document lists all Next.js API routes implementing ingestion/verification based on the specified criteria:

1. Files named `route.ts` or `*.ts` under `/frontend/app/api/**` or `/frontend/pages/api/**`
2. Routes with "x-cron-secret" and "CRON_SECRET" checks
3. Routes returning JSON with keys: `ok`, `leads`, `permits`

## Routes with x-cron-secret and CRON_SECRET Authentication

### 1. `/api/permits/ingest`
- **File Path**: `frontend/app/api/permits/ingest/route.ts`
- **HTTP Method**: POST
- **Final URL Path**: `/api/permits/ingest`
- **Authentication**: 
  - Checks `x-cron-secret` header
  - Validates against `process.env.CRON_SECRET`
- **Returns JSON with**: `success`, `source`, `dry`, `summary`, `counts`, `diagnostics`, `timestamp`
- **Description**: Main permit ingestion endpoint supporting Austin, Houston, Dallas sources

### 2. `/api/permits/permits/ingest`
- **File Path**: `frontend/app/api/permits/permits/ingest/route.ts`
- **HTTP Method**: POST
- **Final URL Path**: `/api/permits/permits/ingest`
- **Authentication**: 
  - Checks `x-cron-secret` header
  - Validates against `process.env.CRON_SECRET`
- **Returns JSON with**: `ok`, `source`, `fetched`, `dry`, `upserts`, `beforeCount`, `afterCount`, `sample`, `errors`
- **Description**: Alternative permit ingestion endpoint with simplified response format

### 3. `/api/permits/scrape`
- **File Path**: `frontend/app/api/permits/scrape/route.ts`
- **HTTP Method**: POST
- **Final URL Path**: `/api/permits/scrape`
- **Authentication**: 
  - Checks `x-cron-secret` header
  - Validates against `process.env.CRON_SECRET`
- **Returns JSON with**: `ok`, `source`, `fetched`, `upserts`, `errors`, `timestamp`
- **Description**: Permit scraping endpoint for Austin, Houston, Dallas sources

## Routes Returning JSON with ok/leads/permits Keys

### 4. `/api/leads`
- **File Path**: `frontend/app/api/leads/route.ts`
- **HTTP Method**: POST
- **Final URL Path**: `/api/leads`
- **Authentication**: Only available when `LEADS_TEST_MODE=true`
- **Returns JSON with**: `ok`, `trace_id`, optionally `error`
- **Description**: Lead creation endpoint for testing purposes

### 5. `/api/leads/recent`
- **File Path**: `frontend/app/api/leads/recent/route.ts`
- **HTTP Method**: GET
- **Final URL Path**: `/api/leads/recent`
- **Authentication**: None (uses service role internally)
- **Returns JSON with**: `leads`, `data` (array of recent leads)
- **Description**: Fetches recent leads from backend or Supabase fallback

## Directory Structure Verification

- **App Router**: ✅ Used (`/frontend/app/api/**`)
- **Pages Router**: ❌ Not found (`/frontend/pages/api/**` does not exist)

## Total Count

- **Routes with x-cron-secret/CRON_SECRET**: 3
- **Routes returning ok/leads/permits**: 5 (with 2 overlap)
- **Unique routes found**: 5

## Notes

1. All cron-authenticated routes are POST endpoints designed for automated ingestion
2. The `/api/leads/recent` endpoint returns `leads` array for frontend consumption
3. All permit-related endpoints use the "ok" response pattern for status indication
4. Routes use Next.js App Router convention with `route.ts` files