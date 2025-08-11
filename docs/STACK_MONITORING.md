# Stack Monitoring System

This repository includes a comprehensive stack monitoring system that automatically checks the health of all infrastructure components and provides automated alerting and remediation capabilities.

## Components

### 1. Stack Health Monitor (`scripts/stack-health.js`)

A Node.js script that monitors the health of:
- **Vercel**: Frontend deployment status via API
- **Railway**: Backend service health via GraphQL API  
- **Supabase**: Database and auth service connectivity
- **Frontend**: HTTP health check endpoint

**Features:**
- Generates JSON output (`stack-health.json`) and markdown summary
- Measures response times for all services
- Creates exit code file (`.stack-health-exit-code`) for workflow detection
- Handles timeouts and errors gracefully
- Supports Slack notifications for failures

### 2. GitHub Workflow (`.github/workflows/stack-monitor.yml`)

Automated workflow that:
- Runs every 10 minutes (`*/10 * * * *`)
- Can be triggered manually with `workflow_dispatch`
- Uses Node.js 20 and required secrets
- Appends health summary to GitHub Step Summary
- Uploads artifacts on failure
- Creates/updates GitHub issues automatically
- Supports auto-remediation when enabled
- Closes issues when problems are resolved

### 3. Auto-Remediation Scripts

Optional remediation scripts that attempt to fix common issues:
- `scripts/remediate-vercel.js` - Vercel deployment recovery
- `scripts/remediate-railway.js` - Railway service restart/scaling
- `scripts/remediate-supabase.js` - Database connectivity fixes

## Required Secrets

Configure these secrets in your GitHub repository:

| Secret | Description |
|--------|-------------|
| `VERCEL_TOKEN` | Vercel API token for deployment monitoring |
| `RAILWAY_TOKEN` | Railway API token for service health checks |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE` | Supabase service role key |
| `FRONTEND_URL` | Frontend application URL for health checks |
| `SLACK_WEBHOOK` | (Optional) Slack webhook for notifications |

## Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AUTO_REMEDIATE` | Enable automatic remediation | `false` |

## Usage

### Manual Health Check

```bash
# Run health check locally
node scripts/stack-health.js

# With environment variables
FRONTEND_URL=https://your-app.vercel.app \
SUPABASE_URL=https://your-project.supabase.co \
node scripts/stack-health.js
```

### Trigger Manual Workflow

1. Go to Actions → Stack Monitor
2. Click "Run workflow"
3. Optionally enable "Force auto-remediation"

## Output Examples

### Healthy System
```
✅ All services healthy
- Vercel: API accessible (120ms)
- Railway: GraphQL API accessible (89ms)  
- Supabase: REST API accessible (156ms)
- Frontend: Health check passed (234ms)
```

### Degraded System
```
⚠️ System degraded (3/4 services healthy)
❌ Railway: Connection timeout after 10s
✅ Other services operating normally
```

### Critical System
```
🚨 System critical (0/4 services healthy)
❌ Multiple service failures detected
📤 GitHub issue created automatically
📢 Slack notification sent
```

## GitHub Issue Management

The workflow automatically:
- Creates issues titled "Stack Monitor Alert" when failures are detected
- Updates existing issues with latest status
- Adds comments for subsequent failures
- Closes issues when all services return to healthy status
- Tags issues with `bug`, `infrastructure`, `automated` labels

## Auto-Remediation

When enabled (`AUTO_REMEDIATE=true`), the system will:
1. Detect service failures
2. Run appropriate remediation scripts
3. Wait 30 seconds
4. Re-run health checks
5. Report remediation results

## Monitoring Best Practices

1. **Set up alerts**: Configure Slack notifications for immediate awareness
2. **Review regularly**: Check GitHub issues for patterns
3. **Update remediation**: Enhance remediation scripts based on common failures
4. **Monitor costs**: Be aware of API call frequency (every 10 minutes)
5. **Test manually**: Occasionally run manual checks to verify functionality

## Troubleshooting

### Common Issues

**"Token not configured" errors**
- Verify all required secrets are set in GitHub repository settings
- Check token permissions and expiration

**"Connection timeout" errors**  
- Services may be temporarily unavailable
- Check service status pages
- Verify URLs are correct

**Workflow not running**
- Check if repository has Actions enabled
- Verify workflow syntax with `python -c "import yaml; yaml.safe_load(open('.github/workflows/stack-monitor.yml'))"`

### Debugging

1. Check workflow logs in GitHub Actions
2. Review uploaded artifacts for detailed error information
3. Run health check script locally with environment variables
4. Check service-specific status pages

## Security Considerations

- Secrets are properly scoped to workflow environment
- API tokens should have minimal required permissions
- Health check endpoints should not expose sensitive data
- Slack webhooks should be configured with appropriate channel restrictions