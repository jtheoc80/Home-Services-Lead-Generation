# Workflow Secrets Scanner Report

## Summary
- **Files scanned:** 45
- **Files with secrets:** 19
- **Unique secrets found:** 9
- **Total secret usages:** 136

## Patterns Found
- **Supabase:** 92 usages
- **Permits Url:** 22 usages
- **Vercel Token:** 14 usages
- **Railway Token:** 8 usages

## Detailed Findings
### .github/workflows/_scrape-python.yml

- `SUPABASE_SERVICE_ROLE_KEY` - **Required**
  - Pattern type: supabase
  - Context: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- `SUPABASE_URL` - **Required**
  - Pattern type: supabase
  - Context: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`

### .github/workflows/db-migrate.yml

- `SUPABASE_DB_URL` - **Required**
  - Pattern type: supabase
  - Context: `SUPABASE_DB_URL: ${{ secrets.SUPABASE_DB_URL }} # postgres connection string (service role)`

### .github/workflows/dependabot-auto.yml

- `SUPABASE_SERVICE_ROLE_KEY` - **Required**
  - Pattern type: supabase
  - Context: `SRV: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`

### .github/workflows/e2e.yml

- `SUPABASE_SERVICE_ROLE_KEY` - **Required**
  - Pattern type: supabase
  - Context: `echo "SUPABASE_SERVICE_ROLE_KEY=${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}" >> $GITHUB_ENV`
- `SUPABASE_URL` - **Required**
  - Pattern type: supabase
  - Context: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`

### .github/workflows/etl-harris.yml

- `HC_ISSUED_PERMITS_URL` - **Required**
  - Pattern type: permits_url
  - Context: `HC_URL="${{ secrets.HC_ISSUED_PERMITS_URL }}"`
- `SUPABASE_SERVICE_ROLE_KEY` - **Required**
  - Pattern type: supabase
  - Context: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- `SUPABASE_URL` - **Required**
  - Pattern type: supabase
  - Context: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`

### .github/workflows/etl.yml

- `HC_ISSUED_PERMITS_URL` - **Required**
  - Pattern type: permits_url
  - Context: `HC_ISSUED_PERMITS_URL: ${{ secrets.HC_ISSUED_PERMITS_URL }}`
- `SUPABASE_JWT_SECRET` - **Required**
  - Pattern type: supabase
  - Context: `SUPABASE_JWT_SECRET: ${{ secrets.SUPABASE_JWT_SECRET }}`
- `SUPABASE_SERVICE_ROLE_KEY` - **Required**
  - Pattern type: supabase
  - Context: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- `SUPABASE_URL` - **Required**
  - Pattern type: supabase
  - Context: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`

### .github/workflows/gh-agent.yml

- `SUPABASE_FUNCTION_URL` - **Required**
  - Pattern type: supabase
  - Context: `SUPABASE_FUNCTION_URL: ${{ secrets.SUPABASE_FUNCTION_URL }}`

### .github/workflows/ingest-agents-min.yml

- `SUPABASE_FUNCTION_URL` - **Required**
  - Pattern type: supabase
  - Context: `SUPABASE_FUNCTION_URL: ${{ secrets.SUPABASE_FUNCTION_URL }}`

### .github/workflows/ingest-nightly.yml

- `SUPABASE_SERVICE_ROLE_KEY` - **Required**
  - Pattern type: supabase
  - Context: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- `SUPABASE_URL` - **Required**
  - Pattern type: supabase
  - Context: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`

### .github/workflows/lighthouse.yml

- `VERCEL_TOKEN` - **Required**
  - Pattern type: vercel_token
  - Context: `VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}`

### .github/workflows/monthly-backup-validation.yml

- `SUPABASE_SERVICE_ROLE_KEY` - **Required**
  - Pattern type: supabase
  - Context: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- `SUPABASE_URL` - **Required**
  - Pattern type: supabase
  - Context: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`

### .github/workflows/permits-harris.yml

- `HC_ISSUED_PERMITS_URL` - *Optional*
  - Pattern type: permits_url
  - Context: `SOURCE_URL: ${{ secrets.HC_ISSUED_PERMITS_URL != '' && secrets.HC_ISSUED_PERMITS_URL || secrets.SOURCE_URL }}`
- `SUPABASE_SERVICE_ROLE_KEY` - **Required**
  - Pattern type: supabase
  - Context: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- `SUPABASE_URL` - **Required**
  - Pattern type: supabase
  - Context: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`

### .github/workflows/railway-expose-and-url.yml

- `RAILWAY_TOKEN` - **Required**
  - Pattern type: railway_token
  - Context: `RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}`

### .github/workflows/schema-drift.yml

- `SUPABASE_SERVICE_ROLE_KEY` - **Required**
  - Pattern type: supabase
  - Context: `if [ -z "${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}" ]; then`

### .github/workflows/scrape-dallas.yml

- `DALLAS_PERMITS_URL` - *Optional*
  - Pattern type: permits_url
  - Context: `SOURCE_URL: ${{ secrets.DALLAS_PERMITS_URL != '' && secrets.DALLAS_PERMITS_URL || secrets.SOURCE_URL }}`
- `SUPABASE_SERVICE_ROLE_KEY` - **Required**
  - Pattern type: supabase
  - Context: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- `SUPABASE_URL` - **Required**
  - Pattern type: supabase
  - Context: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`

### .github/workflows/scrape-harris.yml

- `HC_ISSUED_PERMITS_URL` - **Required**
  - Pattern type: permits_url
  - Context: `SOURCE_URL: ${{ secrets.HC_ISSUED_PERMITS_URL }}`
- `SUPABASE_SERVICE_ROLE_KEY` - **Required**
  - Pattern type: supabase
  - Context: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- `SUPABASE_URL` - **Required**
  - Pattern type: supabase
  - Context: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`

### .github/workflows/stack-monitor.yml

- `RAILWAY_TOKEN` - **Required**
  - Pattern type: railway_token
  - Context: `RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}`
- `SUPABASE_SERVICE_ROLE_KEY` - **Required**
  - Pattern type: supabase
  - Context: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- `SUPABASE_URL` - **Required**
  - Pattern type: supabase
  - Context: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`
- `VERCEL_TOKEN` - **Required**
  - Pattern type: vercel_token
  - Context: `VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}`

### .github/workflows/supabase-heartbeat.yml

- `SUPABASE_SERVICE_ROLE_KEY` - **Required**
  - Pattern type: supabase
  - Context: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- `SUPABASE_URL` - **Required**
  - Pattern type: supabase
  - Context: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`

### .github/workflows/vercel-log-digest.yml

- `VERCEL_TOKEN` - **Required**
  - Pattern type: vercel_token
  - Context: `VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}`

## All Unique Secrets

- `DALLAS_PERMITS_URL` - **Required** (used in 1 file)
- `HC_ISSUED_PERMITS_URL` - **Required** (used in 4 files)
- `RAILWAY_TOKEN` - **Required** (used in 2 files)
- `SUPABASE_DB_URL` - **Required** (used in 1 file)
- `SUPABASE_FUNCTION_URL` - **Required** (used in 2 files)
- `SUPABASE_JWT_SECRET` - **Required** (used in 1 file)
- `SUPABASE_SERVICE_ROLE_KEY` - **Required** (used in 13 files)
- `SUPABASE_URL` - **Required** (used in 11 files)
- `VERCEL_TOKEN` - **Required** (used in 3 files)