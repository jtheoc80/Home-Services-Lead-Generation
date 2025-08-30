# GitHub Workflows Security Analysis Report

## Overview
Scanned `.github/workflows` for jobs related to scraping/ingest (names including scrape, permits, ingest, metro, etl).
Found **13 workflow files** matching criteria.

---

## 1. `_scrape-python.yml` (Reusable Workflow)

### ⚠️ Steps using secrets.*
- Line 97: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`
- Line 98: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- Line 99: `SOURCE_URL: ${{ secrets.SOURCE_URL }}`
- Line 123: `if [ -z "${{ secrets.SUPABASE_URL }}" ]`
- Line 127: `if [ -z "${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}" ]`
- Line 249: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`
- Line 250: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- Line 251: `SOURCE_URL: ${{ secrets.SOURCE_URL }}`
- Line 271: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`
- Line 272: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- Line 301: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`
- Line 302: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- Line 303: `SOURCE_URL: ${{ secrets.SOURCE_URL }}`
- Line 342-344: Multiple secrets used in conditional checks

### ✅ Use of ${{ inputs.* }} in job/env/if (unsafe for schedule)
- Line 100: `SAMPLE_DATA: ${{ inputs.sample_data == 'true' && '1' || '0' }}` ⚠️ **UNSAFE TERNARY**
- Line 136: `${{ inputs.module }}`
- Line 137: `${{ inputs.days }}`
- Line 138: `${{ inputs.sample_data }}`
- Line 142: `${{ inputs.days }}`
- Line 143: `${{ inputs.sample_data }}`
- Line 147: `${{ inputs.module }}`
- Line 157: `if: steps.run_module.outputs.success != 'true' && inputs.entry_fallback != ''`
- Line 289: `DAYS="${{ inputs.days }}"`
- Line 291: `SAMPLE="${{ inputs.sample_data }}"`

### ⚠️ Ternaries or JS operators inside ${{ }}
- Line 100: `${{ inputs.sample_data == 'true' && '1' || '0' }}` **TERNARY FOUND**

### ✅ Steps missing run/uses (only has name)
- All steps have proper `run` or `uses` directives

### 📁 Upload-artifact paths and working-directory
- **Working directory**: Line 94: `working-directory: .`
- **Upload paths**: 
  - Lines 178-181: `data/`, `logs/`
  - Lines 189-191: `${{ inputs.artifacts_glob }}`
  - Lines 329-334: `artifacts/**/*.csv`, `data/**/*.csv`, `logs/**/*.log`, `logs/etl_output.log`

### 🐍 Python setup/install presence
- ✅ Line 107: `uses: actions/setup-python@v5`
- ✅ Line 221: `uses: actions/setup-python@v5`

### 🔍 Security features presence
- ✅ **Preflight secret check**: Lines 245-264
- ✅ **Supabase REST check**: Lines 266-283
- ✅ **Artifacts/logs upload**: Lines 324-336
- ✅ **Job summary**: Lines 338-346

---

## 2. `etl-harris.yml`

### ⚠️ Steps using secrets.*
- Line 46: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`
- Line 47: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- Line 64: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`
- Line 65: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- Line 79: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`
- Line 80: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- Line 83: `HC_URL="${{ secrets.HC_ISSUED_PERMITS_URL }}"`
- Line 133: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`
- Line 134: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`

### ✅ Use of ${{ inputs.* }} in job/env/if (unsafe for schedule)
- Line 12: `${{ inputs.days_lookback }}` - Safe, only in workflow_dispatch

### ⚠️ Ternaries or JS operators inside ${{ }}
- Line 62: `if: ${{ steps.preflight.outputs.ok == '1' }}` **EQUALITY OPERATOR**
- Line 158: `if (count == 0)` **EQUALITY OPERATOR IN INLINE JS**

### ✅ Steps missing run/uses (only has name)
- All steps have proper `run` or `uses` directives

### 📁 Upload-artifact paths and working-directory
- **Working directory**: Line 26: `working-directory: scripts`
- **Upload paths**: Lines 124-127: `artifacts/**/*.csv`, `logs/**/*.log`, `logs/etl_output.log`

### 🐍 Python setup/install presence
- ❌ **No Python setup** - Uses Node.js (Line 33: `uses: actions/setup-node@v4`)

### 🔍 Security features presence
- ✅ **Preflight secret check**: Lines 43-59
- ✅ **Supabase REST check**: Lines 61-75
- ✅ **Artifacts/logs upload**: Lines 118-128
- ✅ **Job summary**: Lines 177-189

---

## 3. `etl.yml`

### ⚠️ Steps using secrets.*
- Line 55: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`
- Line 56: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- Line 73: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`
- Line 74: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- Line 89: `HC_ISSUED_PERMITS_URL: ${{ secrets.HC_ISSUED_PERMITS_URL }}`
- Line 90: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`
- Line 91: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- Line 92: `SUPABASE_JWT_SECRET: ${{ secrets.SUPABASE_JWT_SECRET }}`
- Line 123: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`
- Line 124: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`

### ✅ Use of ${{ inputs.* }} in job/env/if (unsafe for schedule)
- Line 95: `SINCE_PERIOD="${{ inputs.since }}"` - Safe usage with default

### ⚠️ Ternaries or JS operators inside ${{ }}
- Line 71: `if: ${{ steps.preflight.outputs.ok == '1' }}` **EQUALITY OPERATOR**
- Line 178: `if: steps.check_24h.outputs.zero_records_24h == 'true'` **EQUALITY OPERATOR**

### ✅ Steps missing run/uses (only has name)
- All steps have proper `run` or `uses` directives

### 📁 Upload-artifact paths and working-directory
- **Working directory**: Line 29: `working-directory: permit_leads`
- **Upload paths**: 
  - Lines 115-117: `artifacts/**/*.csv`, `logs/**/*.log`, `logs/etl_output.log`
  - Lines 226-228: `artifacts/**/*.csv`, `logs/**/*.log`, `logs/etl_output.log`

### 🐍 Python setup/install presence
- ✅ Line 36: `uses: actions/setup-python@v4`

### 🔍 Security features presence
- ✅ **Preflight secret check**: Lines 52-68
- ✅ **Supabase REST check**: Lines 70-84
- ✅ **Artifacts/logs upload**: Lines 110-119, 220-230
- ✅ **Job summary**: Lines 232-257

---

## 4. `ingest-agents-min.yml`

### ⚠️ Steps using secrets.*
- Line 30: `INGEST_URL: ${{ secrets.INGEST_URL }}`
- Line 31: `CRON_SECRET: ${{ secrets.CRON_SECRET }}`
- Line 32: `DEBUG_URL: ${{ secrets.DEBUG_URL }}`
- Line 50: `INGEST_URL: ${{ secrets.INGEST_URL }}`
- Line 51: `CRON_SECRET: ${{ secrets.CRON_SECRET }}`
- Line 79: `INGEST_URL: ${{ secrets.INGEST_URL }}`
- Line 80: `CRON_SECRET: ${{ secrets.CRON_SECRET }}`
- Line 91: `DEBUG_URL: ${{ secrets.DEBUG_URL }}`
- Line 109: `DEBUG_URL: ${{ secrets.DEBUG_URL }}`
- Line 123: `DEBUG_URL: ${{ secrets.DEBUG_URL }}`
- Line 170: `SUPABASE_FUNCTION_URL: ${{ secrets.SUPABASE_FUNCTION_URL }}`
- Line 171: `AGENT_SECRET: ${{ secrets.AGENT_SECRET }}`

### ✅ Use of ${{ inputs.* }} in job/env/if (unsafe for schedule)
- No unsafe usage found

### ⚠️ Ternaries or JS operators inside ${{ }}
- Line 178: `if [ "${{ needs.verify.result }}" == "success" ]` **EQUALITY OPERATOR**

### ✅ Steps missing run/uses (only has name)
- All steps have proper `run` or `uses` directives

### 📁 Upload-artifact paths and working-directory
- **Working directory**: Not specified
- **Upload paths**: No upload-artifact steps found

### 🐍 Python setup/install presence
- ❌ **No Python setup**

### 🔍 Security features presence
- ✅ **Preflight secret check**: Lines 26-45, 87-104
- ❌ **Supabase REST check**: Not present
- ❌ **Artifacts/logs upload**: Not present
- ✅ **Job summary**: Lines 174-193

---

## 5. `ingest-agents.yml`

### ⚠️ Steps using secrets.*
- Line 38: `VERCEL_DOMAIN: ${{ secrets.VERCEL_DOMAIN }}`
- Line 39: `CRON_SECRET: ${{ secrets.CRON_SECRET }}`
- Line 57: `VERCEL_DOMAIN: ${{ secrets.VERCEL_DOMAIN }}`
- Line 58: `CRON_SECRET: ${{ secrets.CRON_SECRET }}`

### ✅ Use of ${{ inputs.* }} in job/env/if (unsafe for schedule)
- Line 62: `DRY_RUN="${{ inputs.dry_run }}"` - Safe usage with default

### ⚠️ Ternaries or JS operators inside ${{ }}
- Line 118: `if [ "${{ steps.ingest.outputs.success }}" == "true" ]` **EQUALITY OPERATOR**
- Line 134: `if [ "${{ steps.ingest.outputs.success }}" == "true" ]` **EQUALITY OPERATOR**

### ✅ Steps missing run/uses (only has name)
- All steps have proper `run` or `uses` directives

### 📁 Upload-artifact paths and working-directory
- **Working directory**: Not specified
- **Upload paths**: No upload-artifact steps found

### 🐍 Python setup/install presence
- ❌ **No Python setup**

### 🔍 Security features presence
- ✅ **Preflight secret check**: Lines 34-52
- ❌ **Supabase REST check**: Not present
- ❌ **Artifacts/logs upload**: Not present
- ✅ **Job summary**: Lines 114-145

---

## 6. `ingest-nightly.yml`

### ⚠️ Steps using secrets.*
- Line 39: `VERCEL_DOMAIN: ${{ secrets.VERCEL_DOMAIN }}`
- Line 40: `CRON_SECRET: ${{ secrets.CRON_SECRET }}`
- Line 41: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`
- Line 42: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- Line 81: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`
- Line 82: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- Line 105: `VERCEL_DOMAIN: ${{ secrets.VERCEL_DOMAIN }}`
- Line 106: `CRON_SECRET: ${{ secrets.CRON_SECRET }}`

### ✅ Use of ${{ inputs.* }} in job/env/if (unsafe for schedule)
- Line 69: `SOURCE="${{ github.event.inputs.source }}"` - Safe usage with default
- Line 109: `DRY_RUN="${{ github.event.inputs.dry_run }}"` - Safe usage with default

### ⚠️ Ternaries or JS operators inside ${{ }}
- No ternaries found

### ✅ Steps missing run/uses (only has name)
- All steps have proper `run` or `uses` directives

### 📁 Upload-artifact paths and working-directory
- **Working directory**: Not specified
- **Upload paths**: Lines 150-154: `artifacts/**/*.csv`, `logs/**/*.log`, `logs/etl_output.log`

### 🐍 Python setup/install presence
- ✅ Line 58: `uses: actions/setup-python@v4`

### 🔍 Security features presence
- ✅ **Preflight secret check**: Lines 35-55
- ✅ **Supabase REST check**: Lines 79-93
- ✅ **Artifacts/logs upload**: Lines 146-155
- ❌ **Job summary**: Not present

---

## 7. `ingest-tx-vercel.yml`

### ⚠️ Steps using secrets.*
- Line 36: `VERCEL_DOMAIN: ${{ secrets.VERCEL_DOMAIN }}`
- Line 37: `INGEST_API_KEY: ${{ secrets.INGEST_API_KEY }}`
- Line 55: `VERCEL_DOMAIN: ${{ secrets.VERCEL_DOMAIN }}`
- Line 56: `INGEST_API_KEY: ${{ secrets.INGEST_API_KEY }}`

### ✅ Use of ${{ inputs.* }} in job/env/if (unsafe for schedule)
- Line 59: `SOURCE="${{ inputs.source }}"` - Safe usage with default

### ⚠️ Ternaries or JS operators inside ${{ }}
- Line 109: `if [ "${{ steps.ingest.outputs.success }}" = "true" ]` **EQUALITY OPERATOR**
- Line 121: `if [ "${{ steps.ingest.outputs.success }}" == "true" ]` **EQUALITY OPERATOR**

### ✅ Steps missing run/uses (only has name)
- All steps have proper `run` or `uses` directives

### 📁 Upload-artifact paths and working-directory
- **Working directory**: Not specified
- **Upload paths**: No upload-artifact steps found

### 🐍 Python setup/install presence
- ❌ **No Python setup**

### 🔍 Security features presence
- ✅ **Preflight secret check**: Lines 32-50
- ❌ **Supabase REST check**: Not present
- ❌ **Artifacts/logs upload**: Not present
- ✅ **Job summary**: Lines 102-131

---

## 8. `ingest-tx.yml`

### ⚠️ Steps using secrets.*
- Line 42: `DATABASE_URL: ${{ secrets.DATABASE_URL }}`
- Line 43: `SODA_APP_TOKEN: ${{ secrets.SODA_APP_TOKEN }}`
- Line 86: `DATABASE_URL: ${{ secrets.DATABASE_URL }}`
- Line 112: `DATABASE_URL: ${{ secrets.DATABASE_URL }}`
- Line 113: `SODA_APP_TOKEN: ${{ secrets.SODA_APP_TOKEN }}`
- Line 121: `DATABASE_URL: ${{ secrets.DATABASE_URL }}`
- Line 128: `DATABASE_URL: ${{ secrets.DATABASE_URL }}`
- Line 137: `DATABASE_URL: ${{ secrets.DATABASE_URL }}`
- Line 188: `DATABASE_URL: ${{ secrets.DATABASE_URL }}`
- Line 216: `SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}`

### ✅ Use of ${{ inputs.* }} in job/env/if (unsafe for schedule)
- Line 92: `SOURCES="${{ inputs.sources }}"` - Safe usage with default
- Line 94: `FULL_REFRESH="${{ inputs.full_refresh }}"` - Safe usage with default

### ⚠️ Ternaries or JS operators inside ${{ }}
- No ternaries found

### ✅ Steps missing run/uses (only has name)
- All steps have proper `run` or `uses` directives

### 📁 Upload-artifact paths and working-directory
- **Working directory**: Line 32: `working-directory: pipelines`
- **Upload paths**: 
  - Lines 195-199: `artifacts/**/*.csv`, `logs/**/*.log`, `logs/etl_output.log`
  - Line 206: `../artifacts/`

### 🐍 Python setup/install presence
- ✅ Line 59: `uses: actions/setup-python@v4`

### 🔍 Security features presence
- ✅ **Preflight secret check**: Lines 38-56
- ❌ **Supabase REST check**: Not present
- ✅ **Artifacts/logs upload**: Lines 190-207
- ✅ **Job summary**: Lines 218-248

---

## 9. `permit-ingest.yml`

### ⚠️ Steps using secrets.*
- Line 64: `INGEST_URL: ${{ secrets.INGEST_URL }}`
- Line 65: `CRON_SECRET: ${{ secrets.CRON_SECRET }}`

### ✅ Use of ${{ inputs.* }} in job/env/if (unsafe for schedule)
- Line 36: `source="${{ inputs.source }}"` - Safe usage with default
- Line 38: `DRY_RUN="${{ inputs.dry_run }}"` - Safe usage with default

### ⚠️ Ternaries or JS operators inside ${{ }}
- No ternaries found

### ✅ Steps missing run/uses (only has name)
- All steps have proper `run` or `uses` directives

### 📁 Upload-artifact paths and working-directory
- **Working directory**: Not specified
- **Upload paths**: No upload-artifact steps found

### 🐍 Python setup/install presence
- ❌ **No Python setup**

### 🔍 Security features presence
- ❌ **Preflight secret check**: Not present
- ❌ **Supabase REST check**: Not present
- ❌ **Artifacts/logs upload**: Not present
- ❌ **Job summary**: Not present

---

## 10. `permit_scrape.yml`

### ⚠️ Steps using secrets.*
- No secrets usage found (uses hardcoded city_of_houston)

### ✅ Use of ${{ inputs.* }} in job/env/if (unsafe for schedule)
- Line 51: `DAYS="${{ github.event.inputs.days }}"` - Safe usage with default
- Line 63: `DAYS="${{ inputs.days }}"` - Safe usage with default
- Line 65: `SAMPLE="${{ inputs.sample_data }}"` - Safe usage with default
- Line 67: `SOURCE="${{ inputs.source }}"` - Safe usage with default

### ⚠️ Ternaries or JS operators inside ${{ }}
- No ternaries found

### ✅ Steps missing run/uses (only has name)
- All steps have proper `run` or `uses` directives

### 📁 Upload-artifact paths and working-directory
- **Working directory**: Line 22: `working-directory: permit_leads`
- **Upload paths**: 
  - Lines 184-188: `artifacts/**/*.csv`, `logs/**/*.log`, `logs/etl_output.log`
  - Line 196: `../data/`

### 🐍 Python setup/install presence
- ✅ Line 29: `uses: actions/setup-python@v5`

### 🔍 Security features presence
- ❌ **Preflight secret check**: Not present
- ❌ **Supabase REST check**: Not present
- ✅ **Artifacts/logs upload**: Lines 179-197
- ✅ **Job summary**: Lines 124-177

---

## 11. `permits-harris.yml`

### ⚠️ Steps using secrets.*
- Line 18: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`
- Line 19: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- Line 20: `SOURCE_URL: ${{ secrets.HC_ISSUED_PERMITS_URL != '' && secrets.HC_ISSUED_PERMITS_URL || secrets.SOURCE_URL }}` **TERNARY FOUND**
- Line 40: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`
- Line 41: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- Line 42: `HC_ISSUED_PERMITS_URL: ${{ secrets.HC_ISSUED_PERMITS_URL }}`
- Line 69: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`
- Line 70: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- Line 71: `SOURCE_URL: ${{ secrets.HC_ISSUED_PERMITS_URL || secrets.SOURCE_URL }}`
- Line 167: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`
- Line 168: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- Line 169: `SOURCE_URL: ${{ secrets.HC_ISSUED_PERMITS_URL || secrets.SOURCE_URL }}`
- Line 197: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`
- Line 198: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- Line 199: `SOURCE_URL: ${{ secrets.HC_ISSUED_PERMITS_URL || secrets.SOURCE_URL }}`
- Line 219: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`
- Line 220: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- Line 282: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`
- Line 283: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- Line 284: `SOURCE_URL: ${{ secrets.HC_ISSUED_PERMITS_URL || secrets.SOURCE_URL }}`

### ✅ Use of ${{ inputs.* }} in job/env/if (unsafe for schedule)
- Line 286: `DAYS="${{ inputs.days }}"` - Safe usage with default
- Line 288: `SAMPLE="${{ inputs.sample_data }}"` - Safe usage with default

### ⚠️ Ternaries or JS operators inside ${{ }}
- Line 20: `${{ secrets.HC_ISSUED_PERMITS_URL != '' && secrets.HC_ISSUED_PERMITS_URL || secrets.SOURCE_URL }}` **TERNARY FOUND**
- Line 71: `${{ secrets.HC_ISSUED_PERMITS_URL || secrets.SOURCE_URL }}` **LOGICAL OR**
- Line 169: `${{ secrets.HC_ISSUED_PERMITS_URL || secrets.SOURCE_URL }}` **LOGICAL OR**
- Line 199: `${{ secrets.HC_ISSUED_PERMITS_URL || secrets.SOURCE_URL }}` **LOGICAL OR**
- Line 216: `if: ${{ steps.preflight.outputs.ok == '1' }}` **EQUALITY OPERATOR**
- Line 279: `if: ${{ steps.preflight.outputs.ok == '1' }}` **EQUALITY OPERATOR**
- Line 284: `${{ secrets.HC_ISSUED_PERMITS_URL || secrets.SOURCE_URL }}` **LOGICAL OR**

### ✅ Steps missing run/uses (only has name)
- All steps have proper `run` or `uses` directives

### 📁 Upload-artifact paths and working-directory
- **Working directory**: Line 62: `working-directory: permit_leads`, Line 162: `working-directory: permit_leads`
- **Upload paths**: 
  - Lines 116-120: `artifacts/**/*.csv`, `logs/**/*.log`, `logs/etl_output.log`
  - Lines 147-151: `logs/`, `data/`, `artifacts/`
  - Lines 444-448: `artifacts/**/*.csv`, `logs/**/*.log`, `logs/etl_output.log`
  - Line 457: `../data/`

### 🐍 Python setup/install presence
- ✅ Line 33: `uses: actions/setup-python@v5`
- ✅ Line 78: `uses: actions/setup-python@v5`
- ✅ Line 177: `uses: actions/setup-python@v5`
- ✅ Line 247: `uses: actions/setup-python@v5`

### 🔍 Security features presence
- ✅ **Preflight secret check**: Lines 37-53, 193-212
- ✅ **Supabase REST check**: Lines 215-231
- ✅ **Artifacts/logs upload**: Lines 111-121, 142-151, 440-458
- ✅ **Job summary**: Lines 124-141, 342-431, 460-483

---

## 12. `scrape-dallas.yml`

### ⚠️ Steps using secrets.*
- Line 18: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`
- Line 19: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- Line 20: `SOURCE_URL: ${{ secrets.DALLAS_PERMITS_URL != '' && secrets.DALLAS_PERMITS_URL || secrets.SOURCE_URL }}` **TERNARY FOUND**
- Line 40: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`
- Line 41: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- Line 42: `DALLAS_PERMITS_URL: ${{ secrets.DALLAS_PERMITS_URL }}`
- Line 69: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`
- Line 70: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- Line 71: `SOURCE_URL: ${{ secrets.DALLAS_PERMITS_URL || secrets.SOURCE_URL }}`
- Line 167: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`
- Line 168: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- Line 169: `SOURCE_URL: ${{ secrets.DALLAS_PERMITS_URL || secrets.SOURCE_URL }}`
- Line 197: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`
- Line 198: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- Line 199: `SOURCE_URL: ${{ secrets.DALLAS_PERMITS_URL || secrets.SOURCE_URL }}`
- Line 219: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`
- Line 220: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- Line 262: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`
- Line 263: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- Line 264: `SOURCE_URL: ${{ secrets.DALLAS_PERMITS_URL || secrets.SOURCE_URL }}`

### ✅ Use of ${{ inputs.* }} in job/env/if (unsafe for schedule)
- Line 266: `DAYS="${{ inputs.days }}"` - Safe usage with default
- Line 268: `SAMPLE="${{ inputs.sample_data }}"` - Safe usage with default

### ⚠️ Ternaries or JS operators inside ${{ }}
- Line 20: `${{ secrets.DALLAS_PERMITS_URL != '' && secrets.DALLAS_PERMITS_URL || secrets.SOURCE_URL }}` **TERNARY FOUND**
- Line 71: `${{ secrets.DALLAS_PERMITS_URL || secrets.SOURCE_URL }}` **LOGICAL OR**
- Line 169: `${{ secrets.DALLAS_PERMITS_URL || secrets.SOURCE_URL }}` **LOGICAL OR**
- Line 199: `${{ secrets.DALLAS_PERMITS_URL || secrets.SOURCE_URL }}` **LOGICAL OR**
- Line 216: `if: ${{ steps.preflight.outputs.ok == '1' }}` **EQUALITY OPERATOR**
- Line 259: `if: ${{ steps.preflight.outputs.ok == '1' }}` **EQUALITY OPERATOR**
- Line 264: `${{ secrets.DALLAS_PERMITS_URL || secrets.SOURCE_URL }}` **LOGICAL OR**

### ✅ Steps missing run/uses (only has name)
- All steps have proper `run` or `uses` directives

### 📁 Upload-artifact paths and working-directory
- **Working directory**: Line 62: `working-directory: permit_leads`, Line 162: `working-directory: permit_leads`
- **Upload paths**: 
  - Lines 116-120: `artifacts/**/*.csv`, `logs/**/*.log`, `logs/etl_output.log`
  - Lines 147-151: `logs/`, `data/`, `artifacts/`
  - Lines 424-428: `artifacts/**/*.csv`, `logs/**/*.log`, `logs/etl_output.log`
  - Line 437: `../data/`

### 🐍 Python setup/install presence
- ✅ Line 33: `uses: actions/setup-python@v5`
- ✅ Line 78: `uses: actions/setup-python@v5`
- ✅ Line 177: `uses: actions/setup-python@v5`

### 🔍 Security features presence
- ✅ **Preflight secret check**: Lines 37-53, 193-212
- ✅ **Supabase REST check**: Lines 215-231
- ✅ **Artifacts/logs upload**: Lines 111-121, 142-151, 420-438
- ✅ **Job summary**: Lines 124-141, 322-411, 440-463

---

## 13. `scrape-harris.yml`

### ⚠️ Steps using secrets.*
- Line 21: `SUPABASE_URL: ${{ secrets.SUPABASE_URL }}`
- Line 22: `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`
- Line 23: `SOURCE_URL: ${{ secrets.HC_ISSUED_PERMITS_URL }}`

### ✅ Use of ${{ inputs.* }} in job/env/if (unsafe for schedule)
- Line 17: `days: ${{ inputs.days }}` - Safe usage
- Line 18: `sample_data: ${{ inputs.sample_data }}` - Safe usage

### ⚠️ Ternaries or JS operators inside ${{ }}
- No ternaries found

### ✅ Steps missing run/uses (only has name)
- All steps have proper `uses` directives (calls reusable workflow)

### 📁 Upload-artifact paths and working-directory
- **Working directory**: Not specified (uses reusable workflow)
- **Upload paths**: Handled by reusable workflow

### 🐍 Python setup/install presence
- ✅ Handled by reusable workflow

### 🔍 Security features presence
- ✅ **All handled by reusable workflow** `_scrape-python.yml`

---

## 🚨 CRITICAL SECURITY FINDINGS

### 1. **Unsafe Ternary Expressions**
- `scrape-dallas.yml` Line 20: **REPLACE** with a shell step that sets an output, e.g.:
  ```yaml
  - id: set-permits-url
    run: |
      if [ -n "${{ secrets.DALLAS_PERMITS_URL }}" ]; then
        echo "url=${{ secrets.DALLAS_PERMITS_URL }}" >> $GITHUB_OUTPUT
      else
        echo "url=${{ secrets.SOURCE_URL }}" >> $GITHUB_OUTPUT
      fi

### 2. **Logical Operators in Secret Expressions**
- Multiple files use `||` operator with secrets, which could lead to unintended exposure

### 3. **Equality Operators in Conditionals**
- Multiple `==` operators in `${{ }}` expressions across several files

### 4. **Missing Security Features**
- `permit-ingest.yml`: Missing all security features (preflight, REST check, artifacts, summary)
- `permit_scrape.yml`: Missing preflight and Supabase REST checks
- Several workflows missing Supabase REST checks

### 5. **Secrets Exposure Risk**
- Direct secret usage in conditions and ternary expressions
- Some workflows have extensive secret usage without proper masking validation

---

## 📊 SUMMARY STATISTICS

- **Total Files**: 13
- **Files with Ternaries/JS Operators**: 6
- **Files with Python Setup**: 7
- **Files with Preflight Checks**: 8
- **Files with Supabase REST Checks**: 6
- **Files with Artifacts Upload**: 9
- **Files with Job Summaries**: 10
- **Files with Critical Security Issues**: 6

## 🔒 RECOMMENDATIONS

1. **Replace all ternary expressions** with shell-based conditionals
2. **Avoid logical operators** in secret expressions
3. **Add missing preflight checks** to all workflows
4. **Implement Supabase REST checks** where missing
5. **Add artifacts upload** to workflows missing it
6. **Review secret masking** in all workflows
7. **Standardize working directories** and artifact paths