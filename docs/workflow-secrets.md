# Workflow Secrets Checklist

This checklist enumerates the required GitHub secrets for Harris/Dallas scrapers and ingest-agents-min.yml workflow.

## 🔐 Required Secrets Setup

### For Harris County Scraper (`permits-harris.yml`)

- [ ] **`SUPABASE_URL`** - Your Supabase project URL
  - Format: `https://your-project-id.supabase.co`
  - Required for database connectivity

- [ ] **`SUPABASE_SERVICE_ROLE_KEY`** - Supabase service role key  
  - Format: JWT token starting with `eyJ`
  - Required for database operations with full access

  - Format: `https://<harris-county-permits-endpoint>`
  - Obtain the correct endpoint from the Harris County GIS portal or contact Harris County IT.
  - Required for permit data scraping

### For Dallas County Scraper (`scrape-dallas.yml`)

- [ ] **`SUPABASE_URL`** - Your Supabase project URL (same as above)
  - Format: `https://your-project-id.supabase.co`
  - Required for database connectivity

- [ ] **`SUPABASE_SERVICE_ROLE_KEY`** - Supabase service role key (same as above)
  - Format: JWT token starting with `eyJ`
  - Required for database operations with full access

- [ ] **`DALLAS_PERMITS_URL`** - Dallas County permits data source
  - Format: URL endpoint for Dallas County permit data
  - Required for permit data scraping

### For Ingest Agents Minimal (`ingest-agents-min.yml`)

- [ ] **`INGEST_URL`** - Vercel ingest endpoint
  - Format: `https://your-app.vercel.app/api/permits/ingest`
  - Required for permit data ingestion

- [ ] **`CRON_SECRET`** - Authentication secret for secured endpoints
  - Format: Secure random string
  - Required for endpoint authentication

- [ ] **`DEBUG_URL`** - Vercel debug endpoint
  - Format: `https://your-app.vercel.app/api/_debug/sb`
  - Required for database verification

#### Optional for GitHub Agent Integration

- [ ] **`SUPABASE_FUNCTION_URL`** - Supabase function endpoint (optional)
  - Format: Supabase function URL
  - Used for GitHub Agent invocation

- [ ] **`AGENT_SECRET`** - GitHub Agent authentication secret (optional)
  - Format: Secure random string
  - Used for GitHub Agent authentication

## 📝 How to Add Secrets in GitHub

### Step-by-Step Instructions

1. **Navigate to your repository on GitHub**
   - Go to `https://github.com/your-username/your-repo-name`

2. **Access repository settings**
   - Click **Settings** tab (in the repository toolbar)
   - In the left sidebar, click **Secrets and variables**
   - Click **Actions**

3. **Add each required secret**
   - Click **New repository secret**
   - Enter the **Name** exactly as shown above (case-sensitive)
   - Enter the **Secret value**
   - Click **Add secret**

4. **Verify all secrets are configured**
   - Check that all required secrets appear in your secrets list
   - Missing secrets will cause workflow failures

## ✅ Verification Checklist

After adding all secrets, verify your setup:

- [ ] All Harris County scraper secrets are present
- [ ] All Dallas County scraper secrets are present  
- [ ] All ingest agents minimal secrets are present
- [ ] Optional GitHub Agent secrets added if needed
- [ ] Test workflow runs complete successfully
- [ ] No "secret missing" errors in workflow logs

## 🔍 Quick Reference

| Workflow | Required Secrets Count | Optional Secrets |
|----------|----------------------|------------------|
| `permits-harris.yml` | 3 | 0 |
| `scrape-dallas.yml` | 3 | 0 |
| `ingest-agents-min.yml` | 3 | 2 |

**Total unique secrets needed:** 5 (SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are shared)

---

*For detailed documentation, see [workflows-secrets.md](./workflows-secrets.md) which covers all repository workflows.*