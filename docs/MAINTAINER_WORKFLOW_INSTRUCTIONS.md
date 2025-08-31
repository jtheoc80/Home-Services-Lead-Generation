# Maintainer Workflow Instructions

## Manual Pipeline Testing for Harris County and Dallas County Permit Scrapers

This document provides step-by-step instructions for maintainers to manually test the pipeline by running the Harris County and Dallas County permit scraper workflows.

### 📋 Quick Overview

To confirm the pipeline is working correctly, maintainers should:

1. **Test Run**: Execute both workflows with sample data first
2. **Production Run**: Re-run both workflows with real data

---

## 🏠 Harris County Permit Scraper (`permits-harris.yml`)

### Step 1: Test Run with Sample Data

1. **Navigate to Actions**:
   - Go to the GitHub repository
   - Click the **Actions** tab
   - Select **"Harris County Permit Scraper"** workflow

2. **Run Workflow**:
   - Click **"Run workflow"** button
   - Configure parameters:
     - **Days back**: `1`
     - **Sample mode**: `true`
   - Click **"Run workflow"** to start

3. **Monitor Test Run**:
   - Watch the workflow progress in the Actions tab
   - Check the workflow summary for completion status
   - Verify dry-run artifacts are generated

### Step 2: Production Run with Real Data

After the test run completes successfully:

1. **Run Workflow Again**:
   - Click **"Run workflow"** button
   - Configure parameters:
     - **Days back**: `1`
     - **Sample mode**: `false`
   - Click **"Run workflow"** to start

2. **Monitor Production Run**:
   - Verify the workflow completes without errors
   - Check that real permit data is processed
   - Confirm data artifacts are uploaded

---

## 🏙️ Dallas County Permit Scraper (`scrape-dallas.yml`)

### Step 1: Test Run with Sample Data

1. **Navigate to Actions**:
   - Go to the GitHub repository
   - Click the **Actions** tab
   - Select **"Dallas County Permit Scraper"** workflow

2. **Run Workflow**:
   - Click **"Run workflow"** button
   - Configure parameters:
     - **Days back**: `1`
     - **Sample mode**: `true`
   - Click **"Run workflow"** to start

3. **Monitor Test Run**:
   - Watch the workflow progress in the Actions tab
   - Check the workflow summary for completion status
   - Verify dry-run artifacts are generated

### Step 2: Production Run with Real Data

After the test run completes successfully:

1. **Run Workflow Again**:
   - Click **"Run workflow"** button
   - Configure parameters:
     - **Days back**: `1`
     - **Sample mode**: `false`
   - Click **"Run workflow"** to start

2. **Monitor Production Run**:
   - Verify the workflow completes without errors
   - Check that real permit data is processed
   - Confirm data artifacts are uploaded

---

## ✅ Verification Checklist

After running both workflows, verify:

### For Each Workflow (Harris County & Dallas County):

- [ ] **Test run completed** without errors (sample_data=true)
- [ ] **Production run completed** without errors (sample_data=false)
- [ ] **Preflight checks passed** for both runs
- [ ] **Supabase connectivity** verified
- [ ] **Data artifacts uploaded** to workflow artifacts
- [ ] **Workflow summaries** show expected results

### Expected Outcomes:

- **Test Runs**: Should complete quickly with sample data, generating dry-run artifacts
- **Production Runs**: Should process real permit data and upload data files
- **No Critical Errors**: Both workflows should complete successfully
- **Data Pipeline**: Confirm end-to-end data flow is working

---

## 🔧 Troubleshooting

### Common Issues:

1. **Preflight Check Failures**:
   - Verify required secrets are configured in GitHub Settings
   - Check Supabase connectivity and credentials
   - Refer to [Workflow Secrets Configuration](workflows-secrets.md)

2. **Sample Data Issues**:
   - Sample mode should complete quickly without external API calls
   - Check workflow logs for specific error messages

3. **Production Data Issues**:
   - Verify source URLs are accessible
   - Check rate limiting and API quotas
   - Review error logs in workflow artifacts

### Getting Help:

- Review workflow logs in the Actions tab
- Check the [GitHub Actions Runbook](github-actions-runbook.md)
- Consult [Troubleshooting Guide](workflows-secrets.md#troubleshooting)

---

## 📚 Related Documentation

- [GitHub Actions Runbook](github-actions-runbook.md) - Complete workflow documentation
- [Workflow Secrets Configuration](workflows-secrets.md) - Required secrets setup
- [Harris County Permits Endpoint](harris-county-permits-endpoint.md) - Data source details
- [Dallas County Permits Data](tx_permits.md) - Dallas data source information