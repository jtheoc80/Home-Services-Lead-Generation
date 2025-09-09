# GitHub Agent Setup

This document describes how to set up the Supabase "gh-agent" that receives webhooks and integrates with GitHub.

## Overview

The GitHub Agent is a Supabase Edge Function that:
1. **Receives Webhooks**: Accepts webhook payloads from Supabase or external systems
2. **GitHub Integration**: Creates issues, dispatches workflows, and comments on PRs
3. **ETL Event Handling**: Specifically handles ETL success/failure events

## Setup Steps

### 1. Supabase Edge Function Deployment

Deploy the edge function to your Supabase project:

```bash
# Install Supabase CLI if needed
npm install -g supabase

# Login to Supabase
supabase login

# Link to your project
supabase link --project-ref YOUR_PROJECT_REF

# Deploy the function (no JWT verification for webhook endpoint)
supabase functions deploy gh-agent --no-verify-jwt
```

### 2. Environment Variables

Configure the following secrets in your Supabase project:

```bash
# Set function secrets
supabase secrets set GH_TOKEN="ghp_your-github-personal-access-token"
supabase secrets set GH_OWNER="jtheoc80"
supabase secrets set GH_REPO="Home-Services-Lead-Generation"
supabase secrets set WEBHOOK_SECRET="your-random-secret"
```

### 3. GitHub Token Permissions

The GitHub token (`GH_TOKEN`) needs the following permissions:
- `repo` scope for creating issues and repository dispatch events
- `issues:write` scope for posting comments
- `actions:write` scope for dispatching workflows

## Usage

### Webhook Endpoint

Your function will be available at:
```
https://your-project.supabase.co/functions/v1/gh-agent
```

### Supported Event Types

The function handles these event types:

1. **`etl_failed`** - Creates GitHub issue with failure details
2. **`etl_succeeded`** - Creates GitHub issue with success notification  
3. **`dispatch_workflow`** - Triggers `.github/workflows/etl.yml` workflow
4. **`comment_pr`** - Adds comment to specified pull request

### Payload Formats

The function accepts **two payload formats**:

#### 1. Custom Agent Payload (Original Format)
Direct event payload with explicit event types:

```json
{
  "event": "etl_failed",
  "etl_id": "run-123", 
  "city": "houston",
  "days": 7,
  "details": {"error": "Connection timeout"}
}
```

#### 2. DB Webhook Payload (New Format)
Standard Supabase DB webhook format that gets automatically transformed:

```json
{
  "type": "etl_run",
  "table": "etl_runs", 
  "record": {
    "id": "run-456",
    "city": "houston",
    "lookback_days": 14,
    "status": "failed",
    "details": {"error": "Connection timeout"}
  }
}
```

**Transformation Rules:**
- `record.status === 'failed'` → `event: 'etl_failed'`
- `record.status !== 'failed'` → `event: 'etl_succeeded'`  
- `record.id` → `etl_id`
- `record.city` → `city`
- `record.lookback_days` → `days`
- `record.details` → `details`

### Example Payloads

```bash
# ETL Failed Event (Custom Format)
curl -X POST "https://your-project.supabase.co/functions/v1/gh-agent" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your-secret" \
  -d '{
    "event": "etl_failed",
    "etl_id": "run-123",
    "city": "houston",
    "days": 7,
    "details": {"error": "Connection timeout"}
  }'

# ETL Failed Event (DB Webhook Format)
curl -X POST "https://your-project.supabase.co/functions/v1/gh-agent" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your-secret" \
  -d '{
    "type": "etl_run",
    "table": "etl_runs",
    "record": {
      "id": "run-456", 
      "city": "houston",
      "lookback_days": 14,
      "status": "failed",
      "details": {"error": "Connection timeout"}
    }
  }'

# ETL Succeeded Event
curl -X POST "https://your-project.supabase.co/functions/v1/gh-agent" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your-secret" \
  -d '{
    "event": "etl_succeeded",
    "city": "dallas"
  }'

# Dispatch Workflow Event
curl -X POST "https://your-project.supabase.co/functions/v1/gh-agent" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your-secret" \
  -d '{
    "event": "dispatch_workflow",
    "city": "austin",
    "days": 14
  }'

# Comment on PR Event
curl -X POST "https://your-project.supabase.co/functions/v1/gh-agent" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your-secret" \
  -d '{
    "event": "comment_pr",
    "pr_number": 42,
    "message": "ETL processing completed successfully"
  }'
```
on:
  repository_dispatch:
    types: [permit_created, lead_created]

jobs:
  handle-event:
    runs-on: ubuntu-latest
## Response Format

The function returns simple responses:

- **200 OK**: `"ok"` - Event processed successfully
- **400 Bad Request**: `"unknown event"` - Unsupported event type
- **403 Forbidden**: `"forbidden"` - Invalid webhook secret
- **500 Internal Server Error**: `"error: {message}"` - Processing error

## Monitoring

Monitor the agent via:

1. **Supabase Function Logs**: View execution logs in Supabase dashboard
2. **GitHub Issues**: Check for ETL-related issues created by the agent
3. **GitHub Actions**: Monitor workflow dispatches in Actions tab

## Troubleshooting

### Common Issues

1. **403 Forbidden**: 
   - Verify `WEBHOOK_SECRET` matches the `X-Webhook-Secret` header
   - Check if webhook secret is properly configured

2. **GitHub API errors**:
   - Verify `GH_TOKEN` has correct permissions
   - Check `GH_OWNER` and `GH_REPO` are correct
   - Ensure repository exists and token has access

3. **Workflow dispatch failures**:
   - Verify `.github/workflows/etl.yml` exists
   - Check workflow accepts the inputs being sent
   - Ensure token has `actions:write` permission

### Testing Webhook

Test the webhook endpoint:

```bash
# Test with valid secret
curl -X POST "https://your-project.supabase.co/functions/v1/gh-agent" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your-secret" \
  -d '{"event": "etl_succeeded", "city": "test"}'

# Test with invalid secret (should return 403)
curl -X POST "https://your-project.supabase.co/functions/v1/gh-agent" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: wrong-secret" \
  -d '{"event": "etl_succeeded", "city": "test"}'
```

## Security Notes

- The `X-Webhook-Secret` header provides webhook authentication
- Use strong, unique webhook secrets and rotate them periodically  
- GitHub tokens should have minimal necessary permissions
- The function is deployed with `--no-verify-jwt` for webhook access
- Consider additional IP restrictions for production deployments