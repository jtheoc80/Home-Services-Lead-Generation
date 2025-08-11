# Scripts Directory

This directory contains utility scripts for the Home Services Lead Generation project.

## set-vercel-supabase-env.sh

Sets up Supabase environment variables for all Vercel deployment environments (production, preview, development).

### Prerequisites

- Vercel CLI installed and authenticated
- Access to the Supabase project (anonymous key)

### Usage

```bash
./scripts/set-vercel-supabase-env.sh
```

### What it does

1. Sets `NEXT_PUBLIC_SUPABASE_URL` to `https://wsbnbncapkrdovrrghlh.supabase.co` for all environments
2. Prompts securely for `NEXT_PUBLIC_SUPABASE_ANON_KEY` (input is hidden)
3. Sets the anonymous key for all environments (production, preview, development)
4. Pulls environment variables to local `.env.local` file
5. Provides clear instructions and next steps

### Features

- **Secure input**: Anonymous key input is hidden for security
- **Error handling**: Comprehensive error checking and helpful error messages
- **Idempotent**: Can be run multiple times safely (updates existing variables)
- **Clear feedback**: Detailed progress messages and next steps

### Notes

- The script requires the Vercel CLI to be installed and authenticated
- The Supabase URL is hardcoded as per project requirements
- The script is executable and includes proper bash checks

## remediate-vercel.js

Remediation script for Vercel deployments. Finds the latest non-draft deployment and triggers a redeploy.

### Prerequisites

- Node.js 20+
- Valid Vercel API token

### Environment Variables

- `VERCEL_TOKEN` (required): Vercel API token with deployment permissions
- `TARGET_PROJECT` (optional): Specific project ID or name to target

### Usage

```bash
export VERCEL_TOKEN="your_vercel_token"
export TARGET_PROJECT="your_project_name"  # optional
./scripts/remediate-vercel.js
```

### What it does

1. Fetches user/team information to determine scope
2. Finds the specified project (if TARGET_PROJECT is set) or uses user's deployments
3. Identifies the latest non-draft deployment
4. Triggers a redeploy of that deployment
5. Monitors the deployment progress
6. Reports the new deployment URL and status

### Features

- **No external dependencies**: Uses only Node.js built-ins
- **Clear logging**: Detailed progress messages with emojis
- **Error handling**: Comprehensive error checking with descriptive messages
- **Automation friendly**: Outputs GitHub Actions compatible variables
- **Timeout protection**: 5-minute timeout for deployment monitoring

## remediate-railway.js

Remediation script for Railway services. Restarts services or triggers redeployments via Railway GraphQL v2 API.

### Prerequisites

- Node.js 20+
- Valid Railway API token
- Railway service ID

### Environment Variables

- `RAILWAY_TOKEN` (required): Railway API token with service management permissions
- `RAILWAY_SERVICE_ID` (required): Railway service ID to remediate

### Usage

```bash
export RAILWAY_TOKEN="your_railway_token"
export RAILWAY_SERVICE_ID="your_service_id"
./scripts/remediate-railway.js
```

### What it does

1. Fetches service information and current deployment status
2. Determines remediation strategy (restart vs redeploy)
3. Executes the appropriate operation:
   - **Restart**: If service has a successful deployment
   - **Redeploy**: If no deployment exists or last deployment failed
4. Monitors deployment progress (for redeployments)
5. Reports final service status and URLs

### Features

- **No external dependencies**: Uses only Node.js built-ins
- **Smart remediation**: Chooses restart vs redeploy based on service state
- **Clear logging**: Detailed progress messages with emojis
- **Error handling**: Comprehensive error checking with descriptive messages
- **Automation friendly**: Outputs GitHub Actions compatible variables
- **Progress monitoring**: Real-time deployment status updates

## diagnose.sh

System diagnosis script for the Home Services Lead Generation application. Performs comprehensive health checks and provides actionable hints for system issues.

### Prerequisites

- Bash shell (Linux/macOS compatible)
- Python3 (for database connectivity checks)
- sqlite3 (for permit database checks)

### Usage

```bash
./scripts/diagnose.sh
```

### What it checks

1. **Environment Variables**: Verifies critical and optional environment variables are set
2. **Database Connectivity**: Tests Supabase and SQLite database connections
3. **Migration Status**: Checks for pending database migrations
4. **Scraper Last Run**: Monitors when scrapers were last executed and permit data freshness
5. **Dependencies**: Verifies Python packages and Node.js dependencies

### Exit Codes

- `0`: All checks passed ✅
- `1`: Warnings found (system operational but may have issues) ⚠️
- `2`: Critical errors found (system likely non-operational) ❌

### Features

- **Color-coded output**: Easy to scan results with color indicators
- **Actionable hints**: Specific suggestions for fixing detected issues
- **Comprehensive checks**: Covers all major system components
- **Environment awareness**: Loads `.env` file automatically if present
- **Safe execution**: Read-only checks with no system modifications

### Example Output

```
=============================================================================
Home Services Lead Generation - System Diagnosis
=============================================================================
[PASS] Critical variable SUPABASE_URL is set
[WARN] Missing optional environment variables: REDIS_URL GEOCODER
[PASS] Supabase database connectivity verified
[PASS] Last scraper run: 2025-01-10T15:30:00Z
[INFO] Total permits in database: 1,234
=============================================================================
```

### Troubleshooting

Common issues and solutions:

- **Missing .env file**: Create one based on `.env.example`
- **Database connection failed**: Check Supabase credentials and network access
- **No scraper data**: Run `python3 -m permit_leads` to collect permit data
- **Missing dependencies**: Run `pip install -r backend/requirements.txt`

### Common Use Cases

The diagnosis script and other remediation scripts are designed for:

- **Development setup**: Quick system health verification
- **CI/CD pipelines**: Automated deployment recovery and health checks
- **Monitoring systems**: Service health remediation
- **Manual troubleshooting**: Quick deployment fixes and issue identification
- **Scheduled maintenance**: Automated service restarts and health monitoring