# Visual Regression Testing

This repository includes automated visual regression testing to detect unintended UI changes in production.

## Overview

The visual regression testing system:
- 📸 Captures screenshots of key pages nightly
- 🔍 Compares them to baseline images using pixel difference analysis
- 🚨 Opens GitHub Issues when visual drift exceeds the threshold
- 📁 Stores before/after images as artifacts for easy review

## Key Pages Tested

- **Homepage** (`/`) - Main landing page with hero section and features
- **Login** (`/login`) - Authentication form
- **Dashboard** (`/dashboard`) - Main application interface
- **Admin** (`/admin`) - Administrative panel
- **API Docs** (`/docs`) - FastAPI Swagger documentation (if backend URL provided)

## Configuration

### Environment Variables

Required in GitHub Secrets:
```bash
FRONTEND_URL=https://your-app.vercel.app    # Production frontend URL
BACKEND_URL=https://your-api.railway.app    # Production backend URL (optional)
```

### Workflow Parameters

The workflow accepts these input parameters:

- **`baseline_mode`** (boolean): Update baseline images instead of comparing
- **`threshold`** (number, 0.0-1.0): Pixel difference threshold (default: 0.05)
- **`pages`** (string): Comma-separated list of pages to test (default: all)

## Usage

### Automatic Nightly Runs

The workflow runs automatically every night at 09:00 UTC (3:00 AM CST / 4:00 AM CDT).

### Manual Execution

#### Test Against Current Baselines
```bash
gh workflow run visual-regression.yml
```

#### Update Baseline Images
```bash
gh workflow run visual-regression.yml \
  --field baseline_mode=true
```

#### Custom Threshold
```bash
gh workflow run visual-regression.yml \
  --field threshold=0.1
```

#### Test Specific Pages
```bash
gh workflow run visual-regression.yml \
  --field pages="homepage,login"
```

### Local Development

#### Install Dependencies
```bash
npm install
npm run visual:install
```

#### Run Tests Locally
```bash
# Set environment variables
export FRONTEND_URL=http://localhost:3000
export BACKEND_URL=http://localhost:8000

# Run visual tests
npm run visual:test

# Update baselines
npm run visual:baseline
```

## When Visual Changes Are Detected

### 1. GitHub Issue Created

When visual drift exceeds the threshold, an issue is automatically created with:
- 📊 Summary of failed tests
- 📸 Links to download current screenshots
- 🔍 Links to download difference images
- 📋 Detailed test results

### 2. Review Process

1. **Download Artifacts**: Get current screenshots and diff images from the workflow run
2. **Review Changes**: Compare the differences to understand what changed
3. **Determine Action**:
   - **Intentional changes** (new features, design updates): Update baselines
   - **Unintended regressions**: Investigate and fix the root cause

### 3. Update Baselines (if changes are approved)

```bash
gh workflow run visual-regression.yml \
  --field baseline_mode=true
```

This will:
- Capture new screenshots
- Replace baseline images
- Close any open visual regression issues

## Artifacts

Each workflow run generates these artifacts:

- **`visual-regression-baselines`** (90 days): Current baseline images
- **`visual-regression-current-{run-number}`** (30 days): Screenshots from this run
- **`visual-regression-diffs-{run-number}`** (30 days): Difference images (if failures detected)
- **`visual-regression-results-{run-number}`** (30 days): Detailed JSON results and markdown summary

## Troubleshooting

### No Baseline Images

If baselines don't exist, tests will pass with a warning. Run with `baseline_mode: true` to create initial baselines.

### High False Positive Rate

If tests frequently fail due to dynamic content:
1. Increase the `threshold` parameter
2. Modify the script to mask dynamic areas
3. Add more specific `waitFor` conditions for content to load

### Pages Requiring Authentication

Pages like `/dashboard` and `/admin` may require authentication. The script includes `allowError: true` for these pages, so they won't fail the entire test suite if inaccessible.

### Frontend Not Accessible

Ensure `FRONTEND_URL` is correctly configured and the site is publicly accessible. The workflow will fail early if it cannot reach the frontend.

## Technical Details

### Implementation

- **Browser**: Chromium via Playwright
- **Screenshot**: Full page, 1920x1080 viewport
- **Comparison**: Pixel-by-pixel difference analysis
- **Threshold**: Configurable pixel difference ratio (default: 5%)

### File Structure

```
screenshots/
├── baselines/           # Reference images (stored as artifacts)
├── current/            # Screenshots from current run (gitignored)
└── diffs/              # Difference images (gitignored)

scripts/
└── visual-regression.js # Main testing script

.github/workflows/
└── visual-regression.yml # GitHub Actions workflow
```

## Integration with Existing Monitoring

This visual regression testing complements the existing stack monitoring:
- **Stack Monitor** (`stack-monitor.yml`): Health checks and uptime monitoring
- **Visual Regression** (`visual-regression.yml`): UI change detection
- **Nightly Pipeline** (`nightly-pipeline.yml`): Data processing and lead generation

All three systems work together to ensure comprehensive application monitoring.