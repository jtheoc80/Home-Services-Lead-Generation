# Supabase Backup Validation System

This system provides automated monthly validation of Supabase database and storage backups to ensure they are restorable and functional. It consists of three main components that work together to export, restore, and validate backups.

## 🎯 Purpose

The backup validation system addresses a critical gap: **proving that backups actually work**. Many backup systems create backups but never test if they can be restored successfully. This system:

- ✅ Exports production Supabase database and storage data
- ✅ Restores the backup to a staging environment  
- ✅ Runs comprehensive smoke tests to validate functionality
- ✅ Reports pass/fail results with detailed information
- ✅ Provides confidence that production backups are reliable

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Production     │────│  Backup Export   │────│  Backup Files   │
│  Supabase       │    │  Script          │    │  (.tar.gz)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  GitHub Actions │────│  Monthly         │────│  Restore Script │
│  (Scheduler)    │    │  Workflow        │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Issue/Slack    │◄───│  Smoke Tests     │────│  Staging        │
│  Notifications  │    │  & Reporting     │    │  Supabase       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📁 Components

### 1. Backup Export Script (`scripts/supabase-backup-export.sh`)

**Purpose:** Export complete Supabase database and storage metadata from production.

**Features:**
- Database schema export using `pg_dump`
- Database data export (excluding auth/system tables)
- Critical application tables export via REST API (JSON format)
- Storage buckets and file listings export
- Backup manifest with metadata
- Compression and checksumming
- Automatic cleanup of old backups

**Usage:**
```bash
# Set environment variables
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE="your-service-role-key"

# Run export
./scripts/supabase-backup-export.sh
```

**Output:**
- `backups/supabase_backup_YYYYMMDD_HHMMSS.tar.gz` - Compressed backup
- `backups/supabase_backup_YYYYMMDD_HHMMSS.tar.gz.sha256` - Checksum file

### 2. Staging Restore Script (`scripts/supabase-staging-restore.sh`)

**Purpose:** Restore a backup to a staging Supabase instance for testing.

**Features:**
- Backup extraction and validation
- Staging database clearing
- Schema and data restoration
- Critical tables restoration via REST API
- Restoration verification
- Detailed restore reporting

**Usage:**
```bash
# Set environment variables
export STAGING_SUPABASE_URL="https://staging-project.supabase.co"
export STAGING_SUPABASE_SERVICE_ROLE="staging-service-role-key"

# Restore latest backup
./scripts/supabase-staging-restore.sh

# Restore specific backup
./scripts/supabase-staging-restore.sh supabase_backup_20240115_143022
```

### 3. Smoke Tests Script (`scripts/supabase-backup-smoke-tests.sh`)

**Purpose:** Run comprehensive validation tests against the restored staging environment.

**Test Suite:**
- ✅ **API Connectivity** - Basic REST API access
- ✅ **Database Schema** - Required tables exist
- ✅ **Data Integrity** - Data format and structure validation
- ✅ **CRUD Operations** - Create, read, update, delete functionality
- ✅ **Authentication** - Security and access control
- ✅ **Storage System** - Storage buckets accessibility  
- ✅ **Performance** - Response time validation
- ✅ **Data Consistency** - No duplicate records or corruption

**Usage:**
```bash
# Set environment variables
export STAGING_SUPABASE_URL="https://staging-project.supabase.co"
export STAGING_SUPABASE_SERVICE_ROLE="staging-service-role-key"

# Run all tests
./scripts/supabase-backup-smoke-tests.sh
```

**Output:**
- `test-results/backup_validation_YYYYMMDD_HHMMSS.json` - JSON test results
- `test-results/backup_validation_YYYYMMDD_HHMMSS.md` - Markdown summary

### 4. Monthly Workflow (`.github/workflows/monthly-backup-validation.yml`)

**Purpose:** Orchestrate the complete backup validation process automatically.

**Schedule:** 1st of each month at 2:00 AM UTC

**Features:**
- Automatic monthly execution
- Manual trigger with options
- Export → Restore → Test pipeline
- GitHub Issues integration
- Slack notifications (optional)
- Artifact storage (30-day retention)
- Comprehensive reporting

## 🛠️ Setup Instructions

### Prerequisites

1. **Production Supabase Instance** - Your main database
2. **Staging Supabase Instance** - Separate instance for testing
3. **GitHub Repository Secrets** - For authentication
4. **System Dependencies** - PostgreSQL client tools, curl, jq

### 1. Create Staging Supabase Instance

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Create a new project for staging (can be smaller/cheaper than production)
3. Note the project URL and service role key

### 2. Configure GitHub Secrets

Add these secrets to your repository (Settings → Secrets and variables → Actions):

**Production Supabase:**
```
SUPABASE_URL=https://your-production-project.supabase.co
SUPABASE_SERVICE_ROLE=your-production-service-role-key
```

**Staging Supabase:**
```
STAGING_SUPABASE_URL=https://your-staging-project.supabase.co
STAGING_SUPABASE_SERVICE_ROLE=your-staging-service-role-key
```

**Optional Notifications:**
```
SLACK_WEBHOOK=https://hooks.slack.com/services/your/webhook/url
```

### 3. Test the System

#### Manual Workflow Test
```bash
# Trigger the workflow manually in GitHub Actions
gh workflow run monthly-backup-validation.yml
```

#### Local Testing
```bash
# Test backup export
export SUPABASE_URL="https://your-production-project.supabase.co"
export SUPABASE_SERVICE_ROLE="your-production-service-role-key"
./scripts/supabase-backup-export.sh

# Test staging restore
export STAGING_SUPABASE_URL="https://your-staging-project.supabase.co"
export STAGING_SUPABASE_SERVICE_ROLE="your-staging-service-role-key"  
./scripts/supabase-staging-restore.sh

# Test smoke tests
./scripts/supabase-backup-smoke-tests.sh
```

## 📊 Monitoring and Alerts

### GitHub Issues

The workflow automatically creates/updates a GitHub issue titled "Monthly Backup Validation Report" with:

- ✅ Overall pass/fail status
- 📊 Detailed component results
- 🔗 Links to workflow runs and artifacts
- 📋 Next steps and recommendations

### Slack Notifications (Optional)

If `SLACK_WEBHOOK` is configured, the workflow sends Slack messages with:

- 🎯 Summary status (pass/fail)
- 📈 Key metrics and timing
- 🔗 Links to detailed reports
- 🎨 Color-coded status indicators

### Artifacts

Each workflow run uploads artifacts containing:

- 💾 Complete backup files (30-day retention)
- 📄 Test results (JSON and Markdown)
- 📋 Restore reports and logs
- 🔍 Debug information

## 🚨 Troubleshooting

### Common Issues

**1. Authentication Errors**
```
Error: Invalid API key
```
- ✅ Verify `SUPABASE_SERVICE_ROLE` secrets are correct
- ✅ Check that service role keys have sufficient permissions
- ✅ Ensure URLs don't have trailing slashes

**2. Database Connection Failures**
```
psql: FATAL: database "postgres" does not exist
```
- ✅ Verify `pg_dump` and `psql` are installed
- ✅ Check Supabase project is accessible
- ✅ Ensure database isn't paused (for staging instances)

**3. Test Failures**
```
FAIL: Data Integrity
```
- ✅ Check if required tables exist in production
- ✅ Verify staging instance has enough resources
- ✅ Review test logs for specific failure details

### Debugging Commands

```bash
# Check backup file integrity
tar -tzf backups/supabase_backup_20240115_143022.tar.gz

# Verify staging connectivity
curl -H "apikey: $STAGING_SUPABASE_SERVICE_ROLE" \
     -H "Authorization: Bearer $STAGING_SUPABASE_SERVICE_ROLE" \
     "$STAGING_SUPABASE_URL/rest/v1/"

# Manual smoke test execution
./scripts/supabase-backup-smoke-tests.sh 2>&1 | tee debug.log
```

## 🔧 Configuration

### Environment Variables

**Backup Export:**
- `SUPABASE_URL` - Production Supabase URL (required)
- `SUPABASE_SERVICE_ROLE` - Production service role key (required)
- `BACKUP_DIR` - Backup storage directory (default: `./backups`)

**Staging Restore:**
- `STAGING_SUPABASE_URL` - Staging Supabase URL (required)
- `STAGING_SUPABASE_SERVICE_ROLE` - Staging service role key (required)

**Smoke Tests:**
- `TEST_RESULTS_DIR` - Test results directory (default: `./test-results`)

### Workflow Options

The monthly workflow supports manual triggers with options:

- `force_export` - Create new backup even if recent one exists
- `skip_cleanup` - Don't clear staging environment after tests
- `notification_channel` - Choose notification destination (github/slack/both)

## 📅 Schedule and Retention

**Backup Schedule:**
- ✅ Automated: 1st of each month at 2:00 AM UTC
- ✅ Manual: Trigger anytime via GitHub Actions UI

**Retention Policy:**
- ✅ Local backups: 5 most recent (auto-cleanup)
- ✅ GitHub artifacts: 30 days
- ✅ Test results: 30 days
- ✅ GitHub issues: Updated monthly (persistent)

## 🔒 Security Considerations

**Service Role Keys:**
- 🔐 Store in GitHub Secrets (encrypted)
- 🔐 Use separate keys for production vs staging
- 🔐 Rotate keys periodically
- 🔐 Monitor key usage in Supabase Dashboard

**Data Handling:**
- 📋 Backups contain production data (handle securely)
- 📋 Staging environment should be isolated
- 📋 Consider data masking for sensitive fields
- 📋 Artifacts are stored in private GitHub repository

**Access Control:**
- 👥 Limit who can trigger manual workflows
- 👥 Monitor backup validation results
- 👥 Review failed validations immediately

## 🎯 Success Criteria

A successful backup validation run should show:

- ✅ **Export:** Backup created and compressed
- ✅ **Restore:** Staging environment restored successfully  
- ✅ **Tests:** All 8 smoke tests pass
- ✅ **Report:** GitHub issue updated with "PASS" status
- ✅ **Notification:** Slack alert (if configured) shows success

If any step fails, investigate immediately as it indicates potential backup system issues.

---

**📧 Questions?** Check the GitHub Issues for this repository or create a new issue with the `backup-validation` label.