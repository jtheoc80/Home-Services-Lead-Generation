# GitHub Actions Setup & Runbook

This repository uses GitHub Actions to automate permit scraping and lead generation. This document explains the workflows, setup requirements, and troubleshooting.

## Overview

The repository includes several automated workflows:

1. **`permit_scrape.yml`** - Main scraping workflow with manual and scheduled triggers
2. **`nightly-scrape.yml`** - Legacy nightly scraping workflow  
3. **`ingest-agents.yml`** - Parallel ingest agents for austin/dallas with verification
4. **`merge-conflict-resolver.yml`** - Automated merge conflict resolution for PRs
5. **`ci.yml`** - Continuous integration with linting, testing, and quality checks
6. **`quality-gate.yml`** - PR quality gate with auto-formatting

## Workflows

### 1. Houston Permit Scraper (`permit_scrape.yml`)

**Purpose**: Scrapes building permit data from Houston-area municipalities and processes it into leads.

**Triggers**:
- **Schedule**: Daily at 6 AM UTC (1 AM CST/2 AM CDT)
- **Manual**: Via GitHub Actions UI with customizable parameters

**Manual Run Parameters**:
- `source`: Which scraper to run (`city_of_houston` or `all`)
- `days`: Number of days to look back (default: 1)
- `sample_data`: Use test data instead of live scraping (default: false)

**What it does**:
1. Sets up Python 3.11 environment
2. Installs dependencies from `permit_leads/requirements.txt`
3. Creates output directory structure
4. Runs the permit scraper
5. Commits new data back to the repository
6. Uploads data as workflow artifacts
7. Generates a summary report

### 2. Nightly Scrape (`nightly-scrape.yml`)

**Purpose**: Legacy workflow for simple nightly scraping.

**Triggers**:
- **Schedule**: Daily at 6 AM UTC
- **Manual**: Via workflow_dispatch

**What it does**:
1. Sets up Python 3.11 environment
2. Installs dependencies
3. Runs scraper for last 7 days
4. Uploads CSV and SQLite artifacts

### 3. Ingest Agents (`ingest-agents.yml`)

**Purpose**: Parallel data ingestion for Austin and Dallas sources with verification.

**Triggers**:
- **Schedule**: Every 6 hours (0, 6, 12, 18 UTC)
- **Manual**: Via workflow_dispatch

**What it does**:
1. **Parallel Ingest**: Runs Austin and Dallas sources simultaneously using matrix strategy
2. **Two-Phase Execution**: Each source performs dry run first, then real ingestion
3. **API Integration**: Calls secured Vercel endpoints with authentication
4. **Verification**: Checks Supabase counts via debug endpoint after ingestion
5. **Error Handling**: Comprehensive logging and GitHub Actions integration

**Required Secrets**:
- `INGEST_URL`: Vercel ingest endpoint (e.g., `https://app.vercel.app/api/permits/ingest`)
- `DEBUG_URL`: Vercel debug endpoint (e.g., `https://app.vercel.app/api/_debug/sb`)
- `CRON_SECRET`: Authentication secret for secured endpoints

**Features**:
- Matrix strategy allows both sources to run even if one fails
- Dry run validation before actual data ingestion
- Real-time verification of database changes
- Detailed workflow summaries and metrics logging

### 4. Merge Conflict Resolver (`merge-conflict-resolver.yml`)

**Purpose**: Automated merge conflict resolution for pull requests with different strategies.

**Triggers**:
- **Manual**: Via workflow_dispatch with inputs

**Manual Run Parameters**:
- `pr_number`: Pull request number to resolve conflicts for (required)
- `strategy`: Resolution strategy - `safe`, `theirs-all`, or `ours-all` (required)

**Example Usage for PR 175**:
```
pr_number: 175
strategy: safe
```

**What it does**:
1. Validates PR state and fetches branch information
2. Attempts merge with specified strategy
3. Applies path-based conflict resolution rules
4. Commits and pushes resolved changes to a new branch
5. Comments on the PR with resolution status
6. Fails if conflicts cannot be automatically resolved

**Strategy Options**:
- `safe`: Conservative - only auto-resolves docs, configs, and lock files
- `theirs-all`: Accept all incoming changes from PR branch  
- `ours-all`: Keep all current changes from base branch

See [MERGE_CONFLICT_RESOLVER.md](MERGE_CONFLICT_RESOLVER.md) for detailed documentation.

## Setup Requirements

### Repository Settings

No special repository settings are required. The workflows use the default `GITHUB_TOKEN` for:
- Checking out code
- Committing scraped data back to the repository
- Uploading artifacts

### Secrets

Currently, **no repository secrets are required**. The workflows operate using:
- **Sample data mode** for testing
- **Public data sources** that don't require authentication
- **Built-in GitHub token** for repository operations

### Permissions

The workflows require the following permissions (automatically granted to `GITHUB_TOKEN`):
- `contents: write` - To commit scraped data and resolved conflicts back to repository
- `actions: read` - To access workflow artifacts
- `pull-requests: write` - To comment on PRs (merge conflict resolver only)

## Configuration

### Environment Variables

The workflows use these environment variables:

- `SAMPLE_DATA`: Set to '1' to use test data (set automatically based on manual run parameters)

### Application Configuration

The scraper is configured via:
- `permit_leads/config/sources.yaml` - Data source definitions
- `permit_leads/.env` - Environment variables (optional, see `.env.example`)

## Runbook

### Manual Execution

1. **Go to Actions tab** in GitHub repository
2. **Select "Houston Permit Scraper"** workflow
3. **Click "Run workflow"**
4. **Configure parameters**:
   - Source: `city_of_houston` for single source, `all` for all sources
   - Days: How many days back to scrape (1-30 recommended)
   - Sample data: Check this for testing with fake data
5. **Click "Run workflow"** button

### Monitoring

**Check workflow status**:
- Go to Actions tab to see running/completed workflows
- Click on a workflow run to see detailed logs
- Check the "Summary" section for permit counts and files created

**Data output locations**:
- **Repository**: New data committed to `data/` directory
- **Artifacts**: Downloaded via Actions UI (30-day retention)

### Troubleshooting

#### Common Issues

**❌ Workflow fails with "No module named permit_leads"**
- **Cause**: Dependencies not installed correctly
- **Solution**: Check `permit_leads/requirements.txt` exists and is valid

**❌ "No new data" message**
- **Cause**: No permits found for the specified date range
- **Solution**: Try increasing the `days` parameter or using sample data

**❌ Git commit fails**
- **Cause**: No changes to commit or permissions issue
- **Solution**: Check if data directory has new files; this is often normal

**❌ Network/scraping errors**
- **Cause**: Target websites may be down or blocking requests
- **Solution**: Try with sample data first, check target website status

#### Debug Steps

1. **Test with sample data**:
   ```bash
   # In manual run, check "Use sample data"
   # Or run locally:
   cd permit_leads
   python -m permit_leads scrape --source city_of_houston --sample --verbose
   ```

2. **Check logs**:
   - Click on failed workflow run
   - Expand each step to see detailed error messages
   - Look for Python tracebacks or HTTP errors

3. **Verify configuration**:
   - Check `permit_leads/config/sources.yaml` for correct URLs
   - Verify `requirements.txt` has all needed dependencies

#### Local Testing

Before relying on Actions, test locally:

```bash
# Clone repository
git clone https://github.com/jtheoc80/Home-Services-Lead-Generation.git
cd Home-Services-Lead-Generation

# Install dependencies
cd permit_leads
pip install -r requirements.txt

# Test with sample data
python -m permit_leads scrape --source city_of_houston --sample --verbose

# Test with real data (small window)
python -m permit_leads scrape --source city_of_houston --days 1 --verbose
```

## Data Management

### Storage

- **Repository**: Scraped data is committed to the `data/` directory
- **Artifacts**: Workflow artifacts are retained for 30 days
- **Database**: SQLite database at `data/permits/permits.db`

### Data Structure

```
data/
├── permits/
│   ├── raw/
│   │   └── city_of_houston/
│   │       └── 2025-08-09.jsonl
│   ├── aggregate/
│   │   ├── permits_2025-08-09.csv
│   │   └── permits_latest.csv
│   └── permits.db
└── leads/
    ├── leads_recent.csv
    └── by_jurisdiction/
        └── city_of_houston_leads.csv
```

### Cleanup

The repository automatically excludes:
- `.env` files (secrets)
- `*.zip` archives
- Python cache files (`__pycache__/`)
- Virtual environments (`venv/`)

## Future Enhancements

### Potential Secrets (if needed later)

If the scrapers need authentication in the future, add these secrets:

- `API_KEY_HOUSTON` - API key for Houston permit system
- `NOTIFICATION_EMAIL` - Email for failure alerts
- `SMTP_PASSWORD` - Password for email notifications

### Monitoring Improvements

Consider adding:
- Slack/email notifications for failures
- Data quality checks
- Performance monitoring
- Lead scoring alerts

## Self-Hosted Runners

For high-volume scraping and processing workloads, consider using self-hosted GitHub Actions runners:

- **Cost Efficiency**: More economical for workflows requiring >500 minutes/month
- **Better Performance**: Dedicated resources and consistent environment
- **Network Control**: Better handling of rate limits and geographic restrictions
- **Custom Configuration**: Pre-installed tools and optimized for scraping workflows

See [Self-Hosted Runners Setup Guide](./self-hosted-runners.md) for detailed configuration instructions.

### Example Self-Hosted Workflows

The repository includes example workflows for self-hosted runners:

- **`self-hosted-health.yml`** - Source health monitoring every 30 minutes
- **`self-hosted-houston-backfill.yml`** - Houston permit archive processing with lead generation

These workflows use `runs-on: [self-hosted, linux, x64, scrape]` and include concurrency controls to prevent overlapping scrapes.

## Support

For issues with the workflows:

1. Check this runbook for common solutions
2. Review workflow logs in the Actions tab
3. Test changes locally before pushing
4. Open an issue with error logs and steps to reproduce

---

*Last updated: August 2025*