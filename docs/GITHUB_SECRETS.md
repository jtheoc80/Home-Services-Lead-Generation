# Required GitHub Secrets Documentation

This document lists all the GitHub repository secrets required for the Home Services Lead Generation workflows to function properly.

## 📋 Required Secrets Overview

The repository uses GitHub Actions workflows that require various secrets for external service integrations. All secrets should be configured in your repository settings under **Settings > Secrets and variables > Actions**.

## 🔐 Production Environment Secrets

### Supabase Integration
- **`SUPABASE_URL`** - Your Supabase project URL
  - Format: `https://your-project-id.supabase.co`
  - Used by: `permits-harris.yml`, `monthly-backup-validation.yml`, `etl-harris.yml`
  - Required for: Database operations, permit data storage

- **`SUPABASE_SERVICE_ROLE_KEY`** - Supabase service role key for full database access
  - Format: `eyJ...` (JWT token starting with eyJ)
  - Used by: `permits-harris.yml`, `monthly-backup-validation.yml`, `etl-harris.yml`
  - ⚠️ **Critical**: This key has full database access - keep secure

- **`SUPABASE_DB_URL`** - PostgreSQL connection string for direct database access
  - Format: `postgresql://postgres:YOUR_DB_PASSWORD@db.YOUR-REF.supabase.co:5432/postgres?sslmode=require`
  - Used by: `db-migrate.yml`
  - Required for: Database migrations and schema changes
  - ⚠️ **Critical**: Contains database password - keep secure

### Harris County Data Source
- **`HC_ISSUED_PERMITS_URL`** - Harris County permits API endpoint
  - Format: `https://cohgispub.hctx.net/arcgis/rest/services/...`
  - Used by: `permits-harris.yml`
  - Required for: Fetching Harris County permit data

### Dallas County Data Source
- **`DALLAS_PERMITS_URL`** - Dallas County permits API endpoint
  - Format: `https://www.dallasopendata.com/resource/e7gq-4sah.json`
  - Used by: `scrape-dallas.yml`
  - Required for: Fetching Dallas County permit data

## 🧪 Staging Environment Secrets

### Staging Supabase (for backup validation)
- **`STAGING_SUPABASE_URL`** - Staging Supabase project URL
  - Format: `https://your-staging-project-id.supabase.co`
  - Used by: `monthly-backup-validation.yml`
  - Required for: Backup restoration testing

- **`STAGING_SUPABASE_SERVICE_ROLE_KEY`** - Staging Supabase service role key
  - Format: `eyJ...` (JWT token)
  - Used by: `monthly-backup-validation.yml`  
  - Required for: Staging database operations during backup validation

## 📢 Notification Secrets (Optional)

### Slack Integration
- **`SLACK_WEBHOOK`** - Slack webhook URL for notifications
  - Format: `https://hooks.slack.com/services/...`
  - Used by: `monthly-backup-validation.yml`, other notification workflows
  - Optional: If not set, Slack notifications will be skipped

## 🔍 Workflow-Specific Requirements

### Harris County Permit Scraper (`permits-harris.yml`)
**Required secrets:**
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`  
- `HC_ISSUED_PERMITS_URL`

**What it does:**
- Scrapes Harris County permit data hourly
- Stores data in Supabase database
- Creates artifacts with permit data

### Dallas County Permit Scraper (`scrape-dallas.yml`)
**Required secrets:**
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`  
- `DALLAS_PERMITS_URL`

**What it does:**
- Scrapes Dallas County permit data daily
- Stores data in Supabase database
- Creates artifacts with permit data

### Database Migrations (`db-migrate.yml`)
**Required secrets:**
- `SUPABASE_DB_URL`

**What it does:**
- Applies Supabase database schema migrations
- Runs dry-run on pull requests for validation
- Executes live migrations on main branch
- Manages database schema evolution

### Monthly Backup Validation (`monthly-backup-validation.yml`)
**Required secrets:**
- `SUPABASE_URL` (production)
- `SUPABASE_SERVICE_ROLE_KEY` (production)
- `STAGING_SUPABASE_URL`
- `STAGING_SUPABASE_SERVICE_ROLE_KEY`

**Optional secrets:**
- `SLACK_WEBHOOK` (for notifications)

**What it does:**
- Creates backups of production database
- Restores backups to staging environment
- Runs validation tests
- Reports results via GitHub issues and optionally Slack

### Auto-resolve JSON Conflicts (`auto-resolve-json.yml`)
**Required secrets:**
- `GITHUB_TOKEN` (automatically provided)

**What it does:**
- Resolves package.json and lockfile conflicts in PRs
- Triggered by `/resolve-json` comments
- Uses intelligent merging strategies

### Auto-resolve Conflicts (`auto-resolve-conflicts.yml`)
**Required secrets:**
- `GITHUB_TOKEN` (automatically provided)

**What it does:**
- Resolves various file conflicts using path-based rules
- Triggered by `/resolve` comments
- Supports multiple resolution strategies

### Quality Gate (`quality-gate.yml`)
**Required secrets:**
- `GITHUB_TOKEN` (automatically provided)

**What it does:**
- Runs linting, type checking, and tests on PRs
- Auto-fixes formatting issues when possible
- Blocks merges on critical failures

## 🛠️ Setup Instructions

### 1. Configure Repository Secrets

1. Go to your repository on GitHub
2. Navigate to **Settings > Secrets and variables > Actions**
3. Click **New repository secret**
4. Add each required secret with the exact name and value

### 2. Verify Secret Configuration

After adding secrets, you can verify they're configured by:

1. Running the `workflow-lint.yml` workflow manually
2. Checking workflow runs for missing secret warnings
3. Using the secret validation workflow (if available)

### 3. Test Workflows

To test that secrets are working correctly:

1. **Harris County Scraper**: Trigger manually via workflow dispatch
2. **Backup Validation**: Run monthly validation manually to test all secrets
3. **Conflict Resolution**: Create a test PR with JSON conflicts and use `/resolve-json`

## 🔒 Security Best Practices

### Secret Management
- ✅ **Use environment-specific secrets** (production vs staging)
- ✅ **Rotate secrets regularly** (quarterly recommended)
- ✅ **Use least-privilege principle** (service roles with minimal required permissions)
- ✅ **Monitor secret usage** in workflow logs

### Access Control
- ✅ **Limit repository access** to necessary team members
- ✅ **Review workflow changes** that access secrets
- ✅ **Use branch protection** on main branch

### Secret Validation
- ✅ **Test secrets after rotation**
- ✅ **Monitor workflow failures** for expired/invalid secrets
- ✅ **Document secret purposes** for team members

## 🚨 Troubleshooting

### Common Issues

**"Secret not found" errors:**
- Check secret name spelling (case-sensitive)
- Verify secret is set at repository level, not environment level
- Ensure secret has a value (not empty)

**"Authentication failed" errors:**
- Verify secret value is correct
- Check if secret has expired or been rotated
- Ensure service has necessary permissions

**Workflow not triggering:**
- Check if workflow conditions are met
- Verify branch protection rules allow workflow runs
- Ensure required secrets are available

### Getting Help

If you encounter issues with secrets:
1. Check workflow run logs for specific error messages
2. Verify secret configuration in repository settings
3. Test individual services outside GitHub Actions
4. Contact repository maintainers for access issues

## 📚 Additional Resources

- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Supabase Service Role Keys](https://supabase.com/docs/guides/api/api-keys)
- [Harris County GIS Services](https://www.hctx.net/departments/information-technology/gis)
- [Slack Webhook Setup](https://api.slack.com/messaging/webhooks)

---

*Last updated: $(date)*
*This document should be updated when new secrets are added or requirements change.*