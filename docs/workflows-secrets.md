# Required Secrets for Workflows

This document lists the required GitHub repository secrets needed for the automated workflows in this project. These secrets must be configured in **GitHub → Settings → Secrets and variables → Actions** for the workflows to function properly.

## 🔑 Required Secrets

### 1. `SUPABASE_URL`

**Description:** Your Supabase project URL for database connectivity.

**Format:** `https://your-project-id.supabase.co`

**Where to find:** Supabase Dashboard → Settings → API → Project URL

**Used in workflows:**
- [`monthly-backup-validation.yml`](.github/workflows/monthly-backup-validation.yml) - For production database backup operations
- [`etl-harris.yml`](.github/workflows/etl-harris.yml) - For Harris County ETL pipeline data ingestion
- [`permits-harris.yml`](.github/workflows/permits-harris.yml) - For Harris County permit scraper operations  
- [`etl.yml`](.github/workflows/etl.yml) - For nightly ETL data processing
- [`schema-drift.yml`](.github/workflows/schema-drift.yml) - For schema comparison and drift detection (as `NEXT_PUBLIC_SUPABASE_URL`)

---

### 2. `SUPABASE_SERVICE_ROLE_KEY`

**Description:** Your Supabase service role key for server-side database operations with full access privileges.

**Format:** Long JWT token starting with `eyJ`

**Where to find:** Supabase Dashboard → Settings → API → service_role key

**Security Note:** ⚠️ This key has full database access. Never expose it in client-side code.

**Used in workflows:**
- [`monthly-backup-validation.yml`](.github/workflows/monthly-backup-validation.yml) - For production database export/import operations (as `SUPABASE_SERVICE_ROLE`)
- [`etl-harris.yml`](.github/workflows/etl-harris.yml) - For data ingestion and database operations
- [`permits-harris.yml`](.github/workflows/permits-harris.yml) - For permit data storage operations
- [`etl.yml`](.github/workflows/etl.yml) - For automated data processing and ingestion
- [`schema-drift.yml`](.github/workflows/schema-drift.yml) - For read-only schema comparison

---

### 3. `HC_ISSUED_PERMITS_URL`

**Description:** Harris County ArcGIS FeatureServer URL for issued permits data.

**Format:** `https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0`

**Default value:** If not set, workflows use the standard Harris County permits endpoint

**Used in workflows:**
- [`etl-harris.yml`](.github/workflows/etl-harris.yml) - For Harris County permit data source
- [`permits-harris.yml`](.github/workflows/permits-harris.yml) - For permit scraping operations
- [`etl.yml`](.github/workflows/etl.yml) - For ETL data source configuration

## 🛠️ How to Set Secrets in GitHub

### Step 1: Navigate to Repository Settings
1. Go to your GitHub repository
2. Click **Settings** (in the repository toolbar)
3. In the left sidebar, click **Secrets and variables**
4. Click **Actions**

### Step 2: Add Each Secret
1. Click **New repository secret**
2. Enter the **Name** (exactly as shown above, case-sensitive)
3. Enter the **Secret value**
4. Click **Add secret**

### Step 3: Verify All Secrets Are Set
After adding all secrets, you should see:
- ✅ `SUPABASE_URL`
- ✅ `SUPABASE_SERVICE_ROLE_KEY`  
- ✅ `HC_ISSUED_PERMITS_URL`

## 🔧 Alternative Setup with GitHub CLI

If you have [GitHub CLI](https://cli.github.com/) installed and authenticated:

```bash
# Set all required secrets interactively (will prompt for values)
gh secret set SUPABASE_URL
gh secret set SUPABASE_SERVICE_ROLE_KEY  
gh secret set HC_ISSUED_PERMITS_URL

# Or set values directly
gh secret set SUPABASE_URL --body "https://your-project-id.supabase.co"
gh secret set SUPABASE_SERVICE_ROLE_KEY --body "your-service-role-key-here"
gh secret set HC_ISSUED_PERMITS_URL --body "https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0"
```

**Verify secrets are set:**
```bash
gh secret list
```

## ⚠️ Important Notes

### Security Best Practices
- **Never commit secrets to code** - These values should only exist in GitHub Secrets
- **Rotate keys regularly** - Update Supabase service role keys periodically
- **Monitor access** - Review Supabase Dashboard logs for service role key usage
- **Separate environments** - Use different keys for development, staging, and production

### Troubleshooting
- **Workflow failures:** Check that all three secrets are properly set with correct values
- **Authentication errors:** Verify the Supabase service role key is valid and not expired
- **Data source issues:** Confirm the Harris County permits URL is accessible and returns data
- **Secret not found:** Ensure secret names match exactly (case-sensitive)

### Workflow Dependencies
Most automated workflows will fail if these secrets are missing or invalid:
- ETL pipelines will not be able to store data
- Backup validation will fail without database access
- Harris County permit scraping will not function
- Schema drift detection requires read access to compare schemas

## 📚 Related Documentation

- [Supabase Setup Guide](./supabase.md) - Database configuration and migration instructions
- [Harris County Permits Endpoint](./harris-county-permits-endpoint.md) - Detailed API documentation
- [Backup Validation System](./BACKUP_VALIDATION.md) - Automated backup and testing workflow

---

*This documentation covers the core secrets required for workflow automation. Additional secrets may be needed for specific features like Slack notifications or staging environments.*