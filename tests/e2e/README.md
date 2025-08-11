# Preview Smoke Tests

This directory contains Playwright-based smoke tests that run automatically on Vercel preview deployments.

## What it tests

The smoke tests verify that critical parts of the application are working:

1. **Homepage (`/`)** - Ensures the main landing page loads correctly
2. **Health API (`/api/health`)** - Verifies the health check endpoint returns valid status
3. **Protected Page (`/leads`)** - Tests that protected routes behave correctly (may return 200, 401, or 403)
4. **Overall System Health** - Combines health checks to verify system status

## Artifacts

On test failures, the following artifacts are automatically generated and uploaded:

- **Screenshots** - Visual snapshots of failed pages for debugging
- **HTML Dumps** - Full page HTML content for detailed analysis  
- **Test Reports** - Detailed Playwright HTML reports
- **JUnit XML** - Test results in standard format

## Running Locally

```bash
# Install dependencies
npm ci
npx playwright install chromium

# Run tests against local dev server
npm run dev &
npm run test:smoke

# Run tests with visible browser (for debugging)
npm run test:smoke:headed

# Run tests against specific URL
BASE_URL=https://your-preview-url.vercel.app npm run test:smoke
```

## Configuration

Tests are configured in `playwright.config.ts` and can be customized for:

- Browser selection
- Timeout settings  
- Retry policies
- Screenshot/video capture
- Base URLs

## CI/CD Integration

The workflow `.github/workflows/preview-smoke.yml` automatically:

1. Triggers on successful Vercel deployments
2. Waits for deployment to be accessible
3. Runs smoke tests against the preview URL
4. Comments results on the PR
5. Sets GitHub status checks
6. Uploads artifacts for failed tests

## Adding New Tests

To add new endpoints to test, modify `tests/e2e/smoke.spec.ts` and update the `ENDPOINTS` array:

```typescript
const ENDPOINTS = [
  // ... existing endpoints
  { 
    path: '/new-endpoint', 
    name: 'New Feature',
    expectedStatus: 200,
    type: 'page' // or 'api'
  }
];
```