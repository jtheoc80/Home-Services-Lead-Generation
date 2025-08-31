# Nightly ETL Guardian Bot Usage Guide

The Nightly ETL Guardian Bot is an automated workflow that processes Harris County permit data hourly. This guide covers manual triggering, reviewing changes, and rollback procedures.

## 🚀 How to Manually Trigger

### Option 1: GitHub Actions UI (Recommended)

1. **Navigate to the repository**:
   - Go to https://github.com/jtheoc80/Home-Services-Lead-Generation

2. **Open Actions tab**:
   - Click the **Actions** tab at the top of the repository

3. **Select the workflow**:
   - Click on **"Nightly ETL"** in the left sidebar
   - This is the Nightly ETL Guardian Bot workflow

4. **Run workflow**:
   - Click the **"Run workflow"** button (blue button on the right)
   - Configure parameters if needed:
     - **Since**: Time window (e.g., `1d`, `2h`, `30m`) - Default: `1d`
     - **Force**: Force ingest even if 0 records found - Default: `false`
   - Click **"Run workflow"** to start

### Option 2: GitHub CLI

```bash
# Quick trigger with defaults
gh workflow run etl.yml

# Custom time window
gh workflow run etl.yml -f since=2d

# Force processing even with no records
gh workflow run etl.yml -f force=true

# Custom parameters
gh workflow run etl.yml -f since=6h -f force=false
```

## 📊 What the Bot Changes

### Data Processing
- **Source**: Harris County permit data from ArcGIS FeatureServer
- **Target**: Supabase `permits_raw_harris` table
- **Processing**: Fetches, normalizes, and upserts permit records

### Files Modified
- **Artifacts**: Creates CSV files in `permit_leads/artifacts/`
- **Logs**: Generates processing logs in `permit_leads/logs/`
- **Database**: Updates Supabase tables with new permit data

### Outputs Generated
1. **CSV Files**: Processed permit data for analysis
2. **Log Files**: Detailed processing information
3. **Summary Reports**: JSON summaries for monitoring
4. **GitHub Artifacts**: Uploaded with 14-day retention

## 🔍 How to Review Changes

### 1. Monitor Workflow Execution

**Real-time monitoring**:
- Go to Actions → Nightly ETL → [Latest run]
- Watch the progress in real-time
- Check each step for success/failure indicators

**Key steps to monitor**:
- ✅ Preflight checks (secrets validation)
- ✅ Supabase connectivity test
- ✅ ETL scraping execution
- ✅ Data ingestion (if records found)
- ✅ Artifact uploads

### 2. Review Workflow Summary

After completion, check the **Summary** section:
- **Time period processed**: Configured window (default 1 day)
- **Records processed**: Number of permits scraped
- **Supabase REST status**: Database connectivity
- **Log tail**: Last 25 lines of processing output

### 3. Download and Examine Artifacts

**Artifact contents**:
```
nightly-etl-{run_id}/
├── permit_leads/artifacts/
│   └── *.csv                    # Processed permit data
├── permit_leads/logs/
│   ├── etl_output.log          # Main processing log
│   └── *.log                   # Additional log files
```

**To download**:
1. Go to the completed workflow run
2. Scroll to **Artifacts** section at the bottom
3. Click to download the `nightly-etl-{run_id}` archive

### 4. Verify Database Changes

**Check Supabase**:
1. Open your Supabase dashboard
2. Navigate to Table Editor → `permits_raw_harris`
3. Verify new records with recent `created_at` timestamps
4. Check record counts match the workflow summary

**SQL verification**:
```sql
-- Count records from last run
SELECT COUNT(*) 
FROM permits_raw_harris 
WHERE created_at >= NOW() - INTERVAL '1 hour';

-- Check latest permits
SELECT permit_id, address, issue_date, created_at
FROM permits_raw_harris 
ORDER BY created_at DESC 
LIMIT 10;
```

## 🔄 How to Rollback (Revert Changes)

### Scenario 1: Bad Data Ingested

**If incorrect data was processed into the database:**

1. **Identify the problematic time range**:
   ```sql
   -- Find records from the bad run
   SELECT MIN(created_at), MAX(created_at), COUNT(*)
   FROM permits_raw_harris 
   WHERE created_at >= 'YYYY-MM-DD HH:MM:SS'  -- Start of bad run
     AND created_at <= 'YYYY-MM-DD HH:MM:SS'; -- End of bad run
   ```

2. **Delete the problematic records**:
   ```sql
   -- CAUTION: This permanently deletes data
   DELETE FROM permits_raw_harris 
   WHERE created_at >= 'YYYY-MM-DD HH:MM:SS'  -- Start of bad run
     AND created_at <= 'YYYY-MM-DD HH:MM:SS'; -- End of bad run
   ```

3. **Verify deletion**:
   ```sql
   -- Confirm records are removed
   SELECT COUNT(*) 
   FROM permits_raw_harris 
   WHERE created_at >= 'YYYY-MM-DD HH:MM:SS';
   ```

### Scenario 2: Workflow Configuration Issues

**If the workflow itself needs to be reverted:**

1. **Identify the problematic commit**:
   ```bash
   git log --oneline .github/workflows/etl.yml
   ```

2. **Revert the workflow file**:
   ```bash
   # Revert to a specific commit
   git checkout HEAD~1 -- .github/workflows/etl.yml
   
   # Or revert to a specific hash
   git checkout abc1234 -- .github/workflows/etl.yml
   ```

3. **Commit the reversion**:
   ```bash
   git add .github/workflows/etl.yml
   git commit -m "revert: Rollback Nightly ETL workflow to stable version"
   git push
   ```

### Scenario 3: Environment/Secrets Issues

**If secrets or environment variables were corrupted:**

1. **Check current secrets**:
   - Go to Repository Settings → Secrets and variables → Actions
   - Verify all required secrets are present:
     - `SUPABASE_URL`
     - `SUPABASE_SERVICE_ROLE_KEY`
     - `HC_ISSUED_PERMITS_URL` (optional)

2. **Re-run with corrected configuration**:
   - Update the problematic secrets
   - Manually trigger the workflow again
   - Monitor for successful completion

### Emergency Stop

**To immediately stop all ETL processing:**

1. **Cancel running workflows**:
   - Go to Actions → Nightly ETL
   - Click on any running workflow
   - Click **"Cancel workflow"**

2. **Disable the workflow temporarily**:
   ```bash
   # Comment out the schedule trigger
   git checkout main
   # Edit .github/workflows/etl.yml
   # Comment out the cron schedule line
   git commit -m "temp: Disable ETL schedule for maintenance"
   git push
   ```

3. **Re-enable when ready**:
   ```bash
   # Uncomment the schedule trigger
   # Edit .github/workflows/etl.yml
   # Restore the cron schedule line
   git commit -m "fix: Re-enable ETL schedule after maintenance"
   git push
   ```

## 🛡️ Safety Guidelines

### Before Manual Triggering
- ✅ Check that no other ETL workflows are currently running
- ✅ Verify Supabase is accessible and healthy
- ✅ Confirm you have the correct time window configured
- ✅ Use `force=false` unless specifically needed

### During Execution
- ✅ Monitor the workflow progress in real-time
- ✅ Check logs for any error patterns or warnings
- ✅ Verify expected record counts align with time window

### After Completion
- ✅ Download and inspect artifacts
- ✅ Verify database changes are as expected
- ✅ Check for any error notifications
- ✅ Confirm data quality and completeness

### Rollback Best Practices
- ⚠️ **Always backup before deletion**: Create a backup of affected data
- ⚠️ **Test rollback procedures**: Use staging environment when possible
- ⚠️ **Document changes**: Record what was changed and why
- ⚠️ **Coordinate with team**: Inform stakeholders of rollback operations

## 📞 Troubleshooting

### Common Issues

**"No records found"**:
- Check if the time window is appropriate
- Verify the source URL is accessible
- Consider using `force=true` to process anyway

**"Supabase connection failed"**:
- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` secrets
- Check Supabase service status
- Test connectivity manually

**"Artifacts not uploaded"**:
- Check if workflow completed successfully
- Look for disk space or permission issues
- Artifacts are retained for 14 days only

### Getting Help

1. **Check existing issues**: Search GitHub issues for similar problems
2. **Review documentation**: Consult [GitHub Actions Runbook](github-actions-runbook.md)
3. **Create an issue**: Include workflow run ID and error messages
4. **Contact maintainers**: Reach out via repository discussions

---

## 📋 Quick Reference

### Default Schedule
- **Frequency**: Hourly (at the top of each hour)
- **Cron**: `0 * * * *`
- **Timezone**: UTC

### Manual Trigger Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `since` | string | `1d` | Time window (1d, 2h, 30m, etc.) |
| `force` | boolean | `false` | Process even if 0 records found |

### Required Secrets
| Secret | Purpose |
|--------|---------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Database access key |
| `HC_ISSUED_PERMITS_URL` | Harris County data source (optional) |

### Artifact Retention
- **Duration**: 14 days
- **Contents**: CSV files, logs, summaries
- **Naming**: `nightly-etl-{github.run_id}`