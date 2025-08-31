# Next.js API Routes - Ingestion/Verification Summary

## Routes with x-cron-secret and CRON_SECRET checks:

1. **frontend/app/api/permits/ingest/route.ts** 
   - HTTP Method: POST
   - Final URL Path: `/api/permits/ingest`

2. **frontend/app/api/permits/permits/ingest/route.ts**
   - HTTP Method: POST  
   - Final URL Path: `/api/permits/permits/ingest`

3. **frontend/app/api/permits/scrape/route.ts**
   - HTTP Method: POST
   - Final URL Path: `/api/permits/scrape`

## Routes returning JSON with keys: ok, leads, permits:

1. **frontend/app/api/permits/scrape/route.ts**
   - HTTP Method: POST
   - Final URL Path: `/api/permits/scrape` 
   - Returns: `ok`, `source`, `fetched`, `upserts`, `errors`, `timestamp`

2. **frontend/app/api/permits/permits/ingest/route.ts**
   - HTTP Method: POST
   - Final URL Path: `/api/permits/permits/ingest`
   - Returns: `ok`, `source`, `fetched`, `dry`, `upserts`, `beforeCount`, `afterCount`, `sample`, `errors`

3. **frontend/app/api/leads/route.ts**
   - HTTP Method: POST
   - Final URL Path: `/api/leads`
   - Returns: `ok`, `trace_id` (when LEADS_TEST_MODE=true)

4. **frontend/app/api/leads/recent/route.ts**
   - HTTP Method: GET
   - Final URL Path: `/api/leads/recent`
   - Returns: `leads`, `data` (array of lead objects)

5. **frontend/app/api/permits/ingest/route.ts**
   - HTTP Method: POST
   - Final URL Path: `/api/permits/ingest`
   - Returns: `success`, `source`, `dry`, `summary`, `counts`, `diagnostics`, `timestamp`

## Notes:
- No routes found under `/frontend/pages/api/**` (repository uses App Router)
- All cron-secret protected routes are POST endpoints for ingestion
- 3 routes have both cron authentication AND return JSON with target keys