# GitHub Workflows Supabase Scan Report

## Overview
Scanned `.github/workflows/` for any job that references `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, or `"rest/v1"`.

**Total files scanned:** 38 workflow files  
**Files with target references:** 9 files

---

## 1. permits-harris.yml

### Jobs and Steps with References:

**Job: `preflight`**
- **Step:** "Run preflight checks" (lines 37-53)
  - Uses: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
  - **Status:** ✅ **Runs normally**
  - **Gating:** Not gated by invalid YAML, missing secrets (has validation), schedule-only, or if logic

**Job: `dryrun`** 
- **Step:** Environment variables (lines 66-71)
  - Uses: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
  - **Status:** ⚠️ **Gated by if logic:** `if: github.event_name == 'workflow_dispatch'`
  - **Gating:** Only runs on manual workflow dispatch

**Job: `scrape-harris-permits`**
- **Step:** "Preflight: verify required secrets" (lines 193-213)
  - Uses: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
  - **Status:** ✅ **Runs normally**
  
- **Step:** "Preflight: Supabase REST check" (lines 215-232)
  - Uses: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
  - **Contains:** `rest/v1` reference: `"$SUPABASE_URL/rest/v1/leads?select=id&limit=1"`
  - **Status:** ✅ **Runs normally**
  
- **Step:** "Run Harris County permit scraper" (lines 278-315)
  - Uses: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
  - **Status:** ⚠️ **Gated by if logic:** `if: ${{ steps.preflight.outputs.ok == '1' }}`

### Summary:
- **Invalid YAML:** No
- **Missing secrets protection:** Yes - has preflight validation
- **Schedule-only:** Yes - runs on cron: "15 6 * * *" and workflow_dispatch
- **Never runs due to if logic:** Partially - dryrun job only on manual trigger

---

## 2. stack-monitor.yml

### Jobs and Steps with References:

**Job: `stack-health-check`**
- **Step:** "Run stack health check" (lines 40-87)
  - Uses: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
  - **Status:** ✅ **Runs normally**

### Summary:
- **Invalid YAML:** No
- **Missing secrets protection:** No explicit validation
- **Schedule-only:** Yes - runs on cron: "*/10 * * * *" and workflow_dispatch
- **Never runs due to if logic:** No

---

## 3. monthly-backup-validation.yml

### Jobs and Steps with References:

**Job: `backup-validation`**
- **Step:** "Validate environment variables" (lines 85-103)
  - Uses: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `STAGING_SUPABASE_URL`, `STAGING_SUPABASE_SERVICE_ROLE_KEY`
  - **Status:** ✅ **Runs normally**

- **Step:** Multiple other steps using environment variables (lines 41-51)
  - Uses: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `STAGING_SUPABASE_URL`, `STAGING_SUPABASE_SERVICE_ROLE_KEY`
  - **Status:** ✅ **Runs normally**

### Summary:
- **Invalid YAML:** No
- **Missing secrets protection:** Yes - has explicit validation step
- **Schedule-only:** Yes - runs on cron: "0 2 1 * *" (monthly) and workflow_dispatch
- **Never runs due to if logic:** No

---

## 4. etl.yml

### Jobs and Steps with References:

**Job: `etl`**
- **Step:** "Preflight checks" (lines 52-68)
  - Uses: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
  - **Status:** ✅ **Runs normally**

- **Step:** "Preflight: test Supabase REST" (lines 70-84)
  - Uses: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
  - **Contains:** `rest/v1` reference: `"$SUPABASE_URL/rest/v1/leads?select=id&limit=1"`
  - **Status:** ⚠️ **Gated by if logic:** `if: ${{ steps.preflight.outputs.ok == '1' }}`

- **Step:** "Run ETL scraping" (lines 86-109)
  - Uses: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
  - **Status:** ✅ **Runs normally**

- **Step:** "Run data ingestion" (lines 122-156)
  - Uses: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
  - **Status:** ✅ **Runs normally**

### Summary:
- **Invalid YAML:** No
- **Missing secrets protection:** Yes - has preflight validation
- **Schedule-only:** Yes - runs on cron: '0 * * * *' (hourly) and workflow_dispatch
- **Never runs due to if logic:** Partially - REST check gated by preflight success

---

## 5. dependabot-auto.yml

### Jobs and Steps with References:

**Job: `test-dependabot`**
- **Step:** "Check required secrets" (lines 81-106)
  - Uses: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
  - **Status:** ⚠️ **Gated by if logic:** `if: github.actor == 'dependabot[bot]'`

### Summary:
- **Invalid YAML:** No
- **Missing secrets protection:** Yes - has explicit secret validation
- **Schedule-only:** No - runs on pull_request events
- **Never runs due to if logic:** Yes - only runs for Dependabot PRs

---

## 6. schema-drift.yml

### Jobs and Steps with References:

**Job: `detect-schema-drift`**
- **Step:** "Check required secrets" (lines 37-55)
  - Uses: `NEXT_PUBLIC_SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
  - **Status:** ✅ **Runs normally**

- **Step:** "Run schema drift detection" (lines 57-103)
  - Uses: `NEXT_PUBLIC_SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
  - **Status:** ✅ **Runs normally**

### Summary:
- **Invalid YAML:** No
- **Missing secrets protection:** Yes - has explicit secret validation
- **Schedule-only:** Mixed - runs on cron: '0 2 * * *', workflow_dispatch, and push to main
- **Never runs due to if logic:** No

---

## 7. etl-harris.yml

### Jobs and Steps with References:

**Job: `etl-harris`**
- **Step:** "Preflight checks" (lines 43-59)
  - Uses: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
  - **Status:** ✅ **Runs normally**

- **Step:** "Preflight: test Supabase REST" (lines 61-75)
  - Uses: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
  - **Contains:** `rest/v1` reference: `"$SUPABASE_URL/rest/v1/leads?select=id&limit=1"`
  - **Status:** ⚠️ **Gated by if logic:** `if: ${{ steps.preflight.outputs.ok == '1' }}`

- **Step:** "Run Harris County ETL Delta Test" (lines 77-102)
  - Uses: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
  - **Status:** ✅ **Runs normally**

- **Step:** "Check for stale data (24h failure protection)" (lines 130-169)
  - Uses: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
  - **Status:** ✅ **Runs normally**

### Summary:
- **Invalid YAML:** No
- **Missing secrets protection:** Yes - has preflight validation
- **Schedule-only:** Yes - runs on cron: '0 * * * *' (hourly) and workflow_dispatch
- **Never runs due to if logic:** Partially - REST check gated by preflight success

---

## 8. e2e.yml

### Jobs and Steps with References:

**Job: `e2e-test`**
- **Step:** "Setup environment variables" (lines 80-87)
  - Uses: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
  - **Status:** ⚠️ **Gated by complex if logic:** Only runs on successful deployments or manual dispatch

- **Step:** "Run Supabase delta test" (lines 130-138)
  - Uses: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
  - **Status:** ⚠️ **Gated by complex if logic:** Only runs on successful deployments or manual dispatch

### Summary:
- **Invalid YAML:** No
- **Missing secrets protection:** Uses secrets but no explicit validation shown
- **Schedule-only:** No - runs on deployment_status and workflow_dispatch
- **Never runs due to if logic:** Yes - complex conditional: only on production/preview deployment success

---

## 9. stripe-ci.yml

### Jobs and Steps with References:

**Job: `frontend-billing-build`**
- **Step:** "Build frontend with billing pages" (lines 107-115)
  - Uses: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`
  - **Status:** ✅ **Runs normally**

### Summary:
- **Invalid YAML:** No
- **Missing secrets protection:** Uses secrets but no explicit validation shown
- **Schedule-only:** No - runs on pull_request and push events
- **Never runs due to if logic:** No

---

## Overall Summary

### YAML Validity
✅ **All workflows have valid YAML** - No syntax errors that would prevent execution

### Secret Dependencies
- **7 out of 9 workflows** have explicit secret validation/preflight checks
- **2 workflows** (stack-monitor.yml, stripe-ci.yml) use secrets without explicit validation

### Scheduling Patterns
- **5 workflows** are schedule-only (with workflow_dispatch fallback)
- **4 workflows** run on other triggers (PRs, pushes, deployments)

### Conditional Logic Gating
- **3 workflows** have steps that never run due to if logic:
  - `dependabot-auto.yml`: Only runs for Dependabot PRs
  - `e2e.yml`: Only runs on successful production/preview deployments
  - `permits-harris.yml`: dryrun job only on manual trigger
- **2 workflows** have conditional steps that may not run:
  - `etl.yml`: REST check depends on preflight success
  - `etl-harris.yml`: REST check depends on preflight success

### rest/v1 References
Found in 3 workflows, all in Supabase REST API health checks:
- `permits-harris.yml`: Line 226
- `etl.yml`: Line 80  
- `etl-harris.yml`: Line 71

---

## Recommendations

1. **All workflows are functional** - No invalid YAML blocking execution
2. **Most workflows have good secret validation** - Continue this pattern
3. **Schedule-based workflows will run as expected** - No blocking issues
4. **Conditional workflows require specific triggers** - Document trigger requirements
5. **REST API health checks are consistent** - All use the same pattern for Supabase connectivity testing