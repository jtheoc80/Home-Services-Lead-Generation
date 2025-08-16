# GitHub Agent Setup

This document describes how to set up the Supabase "gh-agent" that reads DB events and talks back to GitHub.

## Overview

The GitHub Agent consists of:
1. **Database Outbox**: Event table with triggers on `permits` and `leads` tables
2. **Supabase Edge Function**: `/functions/v1/gh-agent` that processes events and posts to GitHub
3. **GitHub Action**: Workflow that invokes the agent periodically

## Setup Steps

### 1. Database Setup

Run the SQL setup script to create the outbox infrastructure:

```sql
-- Run this in your Supabase SQL Editor
\i sql/gh_agent_outbox_setup.sql
```

This creates:
- `public.event_outbox` table with indexes
- Trigger functions for permits and leads
- Helper functions for event processing

### 2. Supabase Edge Function Deployment

Deploy the edge function to your Supabase project:

```bash
# Install Supabase CLI if needed
npm install -g supabase

# Login to Supabase
supabase login

# Link to your project
supabase link --project-ref YOUR_PROJECT_REF

# Deploy the function
supabase functions deploy gh-agent
```

### 3. Environment Variables

Configure the following environment variables in your Supabase project:

```bash
# Set function secrets
supabase secrets set AGENT_SECRET=your-secure-secret-here
supabase secrets set GITHUB_TOKEN=ghp_your-github-token
supabase secrets set GITHUB_REPOSITORY=owner/repo-name

# Optional: For posting comments to a tracking issue
supabase secrets set GITHUB_TRACKING_ISSUE_NUMBER=123
```

### 4. GitHub Repository Secrets

Configure these secrets in your GitHub repository settings:

- `SUPABASE_FUNCTION_URL`: Full URL to your deployed function (e.g., `https://your-project.supabase.co/functions/v1/gh-agent`)
- `AGENT_SECRET`: Same secret used in Supabase (for authentication)

### 5. GitHub Token Permissions

The GitHub token needs the following permissions:
- `repo` scope for repository_dispatch events
- `issues:write` scope for posting comments (if using tracking issue)

## Usage

### Automatic Operation

The agent runs automatically every 15 minutes via GitHub Actions. It:

1. Fetches undelivered events from `event_outbox`
2. Posts to GitHub (either comments or repository_dispatch)
3. Marks events as delivered

### Manual Invocation

You can manually trigger the agent:

```bash
# Via GitHub Actions UI (workflow_dispatch)
# Or via API:
curl -X POST "https://your-project.supabase.co/functions/v1/gh-agent" \
  -H "Content-Type: application/json" \
  -H "x-agent-secret: your-secret"
```

### Testing

Test the outbox triggers by inserting test data:

```sql
-- Test permit trigger
INSERT INTO gold.permits (permit_id, source_id, address, city, county, permit_type)
VALUES ('TEST-001', 'test', '123 Test St', 'Test City', 'Test County', 'Building');

-- Test lead trigger  
INSERT INTO public.leads (name, email, source)
VALUES ('Test Lead', 'test@example.com', 'manual');

-- Check outbox
SELECT * FROM public.event_outbox WHERE delivered_at IS NULL;
```

## Output Modes

The agent supports two output modes:

### 1. Repository Dispatch Events (Default)

Sends `repository_dispatch` events that can trigger other workflows:

```yaml
on:
  repository_dispatch:
    types: [permit_created, lead_created]

jobs:
  handle-event:
    runs-on: ubuntu-latest
    steps:
      - name: Handle permit event
        if: github.event.action == 'permit_created'
        run: echo "New permit: ${{ github.event.client_payload.payload.permit_id }}"
```

### 2. Issue Comments

If `GITHUB_TRACKING_ISSUE_NUMBER` is set, the agent posts formatted comments to that issue instead.

## Monitoring

Monitor the agent via:

1. **GitHub Actions**: Check the `gh-agent` workflow runs
2. **Supabase Logs**: View function execution logs
3. **Database**: Query `event_outbox` for pending/failed events

```sql
-- Check event statistics
SELECT 
  type,
  COUNT(*) as total,
  COUNT(*) FILTER (WHERE delivered_at IS NULL) as pending,
  COUNT(*) FILTER (WHERE delivered_at IS NOT NULL) as delivered
FROM public.event_outbox 
GROUP BY type;
```

## Troubleshooting

### Common Issues

1. **Events not being created**: Check trigger installation and table names
2. **Agent fails with 401**: Verify `AGENT_SECRET` matches in both Supabase and GitHub
3. **GitHub API errors**: Check token permissions and repository name format
4. **Function timeouts**: Reduce batch size or optimize event processing

### Debug Queries

```sql
-- Check recent events
SELECT * FROM public.event_outbox 
ORDER BY created_at DESC 
LIMIT 10;

-- Check failed deliveries (events older than 1 hour without delivery)
SELECT * FROM public.event_outbox 
WHERE delivered_at IS NULL 
  AND created_at < NOW() - INTERVAL '1 hour';

-- Manual cleanup (if needed)
DELETE FROM public.event_outbox 
WHERE delivered_at IS NOT NULL 
  AND created_at < NOW() - INTERVAL '7 days';
```

## Security Notes

- The `X-Agent-Secret` header provides authentication for the edge function
- Use strong, unique secrets and rotate them periodically  
- GitHub tokens should have minimal necessary permissions
- Consider IP restrictions for production deployments