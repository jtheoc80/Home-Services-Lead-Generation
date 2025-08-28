# GitHub Actions Required Secrets Documentation

This document lists all secrets required by the GitHub Actions workflows in this repository.

## Required Secrets by Workflow

### Core Supabase Operations
These secrets are required for most workflows that interact with the database:

- **`SUPABASE_URL`** - Production Supabase project URL
- **`SUPABASE_SERVICE_ROLE_KEY`** - Production Supabase service role key with full database access

### Harris County Permit Scraping
Required for `permits-harris.yml`:

- **`SUPABASE_URL`** - Production database URL (also used above)
- **`SUPABASE_SERVICE_ROLE_KEY`** - Production database service key (also used above)  
- **`HC_ISSUED_PERMITS_URL`** - Harris County ArcGIS Feature Server URL for permit data

### Backup Validation
Required for `monthly-backup-validation.yml`:

- **`SUPABASE_URL`** - Production Supabase URL (also used above)
- **`SUPABASE_SERVICE_ROLE`** - Production service role key (also used above)
- **`STAGING_SUPABASE_URL`** - Staging/test Supabase project URL for restore testing
- **`STAGING_SUPABASE_SERVICE_ROLE`** - Staging Supabase service role key
- **`SLACK_WEBHOOK`** - Optional Slack webhook URL for notifications

### CI/CD & Bot Operations
Required for various automation workflows:

- **`GITHUB_TOKEN`** - Automatically provided by GitHub Actions for repository access

## Secret Configuration Guide

### 1. Supabase Secrets

#### Production Database (`SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`)
1. Go to your Supabase project dashboard
2. Navigate to Settings → API
3. Copy the "Project URL" for `SUPABASE_URL`
4. Copy the "service_role" key (not anon key) for `SUPABASE_SERVICE_ROLE_KEY`

#### Staging Database (`STAGING_SUPABASE_URL` and `STAGING_SUPABASE_SERVICE_ROLE`)
1. Create a separate Supabase project for staging/testing
2. Follow the same steps as production but use the staging project values

### 2. Harris County Permits (`HC_ISSUED_PERMITS_URL`)
This should be the URL to the Harris County ArcGIS Feature Server endpoint:
```
https://cohgispub.hctx.net/cohgisp/rest/services/Business/IssuedPermits/FeatureServer/0
```

### 3. Slack Notifications (`SLACK_WEBHOOK`)
1. Create a Slack app in your workspace
2. Enable Incoming Webhooks
3. Create a webhook for your desired channel
4. Copy the webhook URL

## Adding Secrets to GitHub

1. Go to your GitHub repository
2. Navigate to Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add the secret name and value
5. Click "Add secret"

## Security Best Practices

### Secret Naming
- Use UPPERCASE with underscores for consistency
- Include the service name for clarity (e.g., `SUPABASE_URL`)
- Don't include credentials in secret names

### Secret Values
- **Never commit secrets to git** - they should only exist in GitHub repository secrets
- Use service role keys (not anon keys) for database operations
- Rotate secrets periodically
- Use minimum required permissions

### Environment Separation
- Use separate secrets for production vs staging environments
- Staging databases should contain no real customer data
- Test webhook URLs should point to development channels

## Workflow-Specific Secret Usage

| Workflow | Secrets Used | Purpose |
|----------|-------------|---------|
| `permits-harris.yml` | `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `HC_ISSUED_PERMITS_URL` | Scrape and store permit data |
| `monthly-backup-validation.yml` | `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE`, `STAGING_SUPABASE_URL`, `STAGING_SUPABASE_SERVICE_ROLE`, `SLACK_WEBHOOK` | Backup testing and notifications |
| `quality-gate.yml` | `GITHUB_TOKEN` | Auto-fix and PR commenting |
| `auto-resolve-json.yml` | `GITHUB_TOKEN` | Conflict resolution and PR management |
| `auto-resolve-conflicts.yml` | `GITHUB_TOKEN` | Conflict resolution and PR management |

## Troubleshooting

### Missing Secrets
If a workflow fails with "secret not found":
1. Check the secret name matches exactly (case-sensitive)
2. Verify the secret exists in repository settings
3. Ensure your account has permission to view/edit secrets

### Invalid Secrets
If a workflow fails with authentication errors:
1. Verify the secret value is correct
2. Check that service role keys haven't been rotated
3. Test the secret value manually (e.g., database connection)

### Permission Issues
If secrets work locally but fail in GitHub Actions:
1. Ensure you're using service role keys (not anon keys)
2. Check Supabase RLS policies allow service role access
3. Verify the staging environment exists and is accessible

## Validation

Use the workflow linter to check for missing secret documentation:

```bash
npm run workflow:lint
```

This will warn about workflows that use secrets but lack documentation.