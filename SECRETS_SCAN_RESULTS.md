# GitHub Workflows Secret Patterns Scan Results

**Scan Date:** 2024-06-13 14:30 UTC  
**Target Patterns:** `secrets.SUPABASE_*`, `secrets.*_PERMITS_URL`, `VERCEL_TOKEN`, `RAILWAY_TOKEN`  
**Files Scanned:** 45 workflow files in `.github/workflows/`

## Direct Pattern Match Results

### 1. secrets.SUPABASE_* Pattern
**5 unique secrets found, 92 total usages:**

| Secret Name | Files Using It | Required | Usage Count |
|------------|----------------|----------|-------------|
| `SUPABASE_URL` | 11 files | ✅ Required | 41 usages |
| `SUPABASE_SERVICE_ROLE_KEY` | 13 files | ✅ Required | 46 usages |
| `SUPABASE_DB_URL` | 1 file | ✅ Required | 1 usage |
| `SUPABASE_FUNCTION_URL` | 2 files | ✅ Required | 3 usages |
| `SUPABASE_JWT_SECRET` | 1 file | ✅ Required | 1 usage |

### 2. secrets.*_PERMITS_URL Pattern
**2 unique secrets found, 22 total usages:**

| Secret Name | Files Using It | Required | Usage Count |
|------------|----------------|----------|-------------|
| `HC_ISSUED_PERMITS_URL` | 4 files | ✅ Required | 13 usages |
| `DALLAS_PERMITS_URL` | 1 file | ✅ Required | 9 usages |

### 3. VERCEL_TOKEN Pattern
**1 unique secret found, 14 total usages:**

| Secret Name | Files Using It | Required | Usage Count |
|------------|----------------|----------|-------------|
| `VERCEL_TOKEN` | 3 files | ✅ Required | 14 usages |

### 4. RAILWAY_TOKEN Pattern
**1 unique secret found, 8 total usages:**

| Secret Name | Files Using It | Required | Usage Count |
|------------|----------------|----------|-------------|
| `RAILWAY_TOKEN` | 2 files | ✅ Required | 8 usages |

## Files by Secret Usage

### Files Using SUPABASE_* Secrets:
- `.github/workflows/_scrape-python.yml` - SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
- `.github/workflows/db-migrate.yml` - SUPABASE_DB_URL
- `.github/workflows/dependabot-auto.yml` - SUPABASE_SERVICE_ROLE_KEY
- `.github/workflows/e2e.yml` - SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
- `.github/workflows/etl-harris.yml` - SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
- `.github/workflows/etl.yml` - SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_JWT_SECRET
- `.github/workflows/gh-agent.yml` - SUPABASE_FUNCTION_URL
- `.github/workflows/ingest-agents-min.yml` - SUPABASE_FUNCTION_URL
- `.github/workflows/ingest-nightly.yml` - SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
- `.github/workflows/monthly-backup-validation.yml` - SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
- `.github/workflows/permits-harris.yml` - SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
- `.github/workflows/schema-drift.yml` - SUPABASE_SERVICE_ROLE_KEY
- `.github/workflows/scrape-dallas.yml` - SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
- `.github/workflows/scrape-harris.yml` - SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
- `.github/workflows/stack-monitor.yml` - SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
- `.github/workflows/supabase-heartbeat.yml` - SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

### Files Using *_PERMITS_URL Secrets:
- `.github/workflows/etl-harris.yml` - HC_ISSUED_PERMITS_URL
- `.github/workflows/etl.yml` - HC_ISSUED_PERMITS_URL
- `.github/workflows/permits-harris.yml` - HC_ISSUED_PERMITS_URL
- `.github/workflows/scrape-dallas.yml` - DALLAS_PERMITS_URL
- `.github/workflows/scrape-harris.yml` - HC_ISSUED_PERMITS_URL

### Files Using VERCEL_TOKEN:
- `.github/workflows/lighthouse.yml` - VERCEL_TOKEN
- `.github/workflows/stack-monitor.yml` - VERCEL_TOKEN
- `.github/workflows/vercel-log-digest.yml` - VERCEL_TOKEN

### Files Using RAILWAY_TOKEN:
- `.github/workflows/railway-expose-and-url.yml` - RAILWAY_TOKEN
- `.github/workflows/stack-monitor.yml` - RAILWAY_TOKEN

## Required vs Optional Analysis

**All 9 discovered secrets are classified as REQUIRED** based on:
- No fallback patterns with default values detected
- Critical workflow functionality dependencies
- Explicit validation checks in workflow files
- Core infrastructure requirements

**No secrets were classified as OPTIONAL** in the current analysis.

## Summary Statistics

- **Total Files Scanned:** 45
- **Files with Matching Patterns:** 19
- **Unique Secrets Found:** 9
- **Total Secret Usages:** 136
- **Required Secrets:** 9 (100%)
- **Optional Secrets:** 0 (0%)

## Tools Created

1. **Scanner Script:** `scripts/scan_workflow_secrets.py`
2. **Test Suite:** `tests/test_workflow_secrets_scanner.py`
3. **Detailed Report:** `workflow-secrets-scan-report.md`
4. **CSV Data:** `workflow-secrets-scan-report.csv`

---

*This scan was performed using automated pattern matching with context analysis to determine required vs optional status.*