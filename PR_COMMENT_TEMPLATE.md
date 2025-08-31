## 🚀 Maintainer Instructions: Pipeline Testing

To confirm the permit scraper pipeline is working correctly, please follow these steps:

### 1. Test Harris County Scraper (`permits-harris.yml`)

**First - Test Run:**
- Go to Actions → "Harris County Permit Scraper" → "Run workflow"
- Set: `days=1`, `sample_data=true`
- Click "Run workflow"

**Then - Production Run:**
- After test completes, run again with: `days=1`, `sample_data=false`

### 2. Test Dallas County Scraper (`scrape-dallas.yml`)

**First - Test Run:**
- Go to Actions → "Dallas County Permit Scraper" → "Run workflow"  
- Set: `days=1`, `sample_data=true`
- Click "Run workflow"

**Then - Production Run:**
- After test completes, run again with: `days=1`, `sample_data=false`

### ✅ Expected Results

- ✅ Both test runs complete successfully with sample data
- ✅ Both production runs complete successfully with real data  
- ✅ Preflight checks pass for all runs
- ✅ Data artifacts are uploaded
- ✅ No critical errors in workflow logs

### 📚 Additional Resources

For detailed instructions and troubleshooting, see:
- [Maintainer Workflow Instructions](docs/MAINTAINER_WORKFLOW_INSTRUCTIONS.md)
- [GitHub Actions Runbook](docs/github-actions-runbook.md)
- [Workflow Secrets Configuration](docs/workflows-secrets.md)

---

*These instructions verify the end-to-end permit data pipeline from sample testing through production data processing.*