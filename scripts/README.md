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

### Common Use Cases

Both remediation scripts are designed for:

- **CI/CD pipelines**: Automated deployment recovery
- **Monitoring systems**: Service health remediation
- **Manual troubleshooting**: Quick deployment fixes
- **Scheduled maintenance**: Automated service restarts