# Houston XLSX Downloader

## Overview

The `scripts/houston_download.ts` script provides a Playwright-based downloader for Houston permit XLSX files. This script automatically finds and downloads XLSX files from Houston permit pages.

## Usage

```bash
# Download weekly permits
npx tsx scripts/houston_download.ts weekly

# Download sold permits  
npx tsx scripts/houston_download.ts sold
```

## Environment Variables

- `HOUSTON_WEEKLY_URL` - URL for Houston weekly permits page
- `HOUSTON_SOLD_URL` - URL for Houston sold permits page  
- `OUT_DIR` - Output directory (default: "artifacts/houston")
- `USER_AGENT` - User agent string (default: "LeadETL/1.0")

## Prerequisites

The script requires Playwright browsers to be installed:

```bash
npx playwright install --with-deps chromium
```

## Workflow Integration

The downloader is automatically integrated into Houston ETL workflows:

- `.github/workflows/etl-houston-ondemand.yml` - On-demand Houston ETL
- `.github/workflows/coh-etl.yml` - Scheduled City of Houston ETL

Both workflows now include:
1. Browser installation (`npx playwright install --with-deps chromium`)
2. XLSX download step
3. Artifact upload for debugging
4. Existing ETL processing

## Implementation Details

- Uses Playwright's headless Chromium browser
- Searches for XLS/XLSX links on the target pages
- Prefers links whose text matches weekly/sold patterns
- Falls back to first available XLSX link if no pattern match
- Creates output directory automatically
- Handles download timeouts (60 seconds)
- Provides detailed error messages

This implementation follows the exact specification from the problem statement.