# Operations Runbook - LeadLedgerPro

This runbook provides operational guidance for maintaining and troubleshooting the LeadLedgerPro platform.

## Table of Contents

1. [System Overview](#system-overview)
2. [Monitoring and Logs](#monitoring-and-logs)
3. [ETL Operations](#etl-operations)
4. [Key Rotation](#key-rotation)
5. [Troubleshooting](#troubleshooting)
6. [Emergency Procedures](#emergency-procedures)
7. [Maintenance Tasks](#maintenance-tasks)

## System Overview

LeadLedgerPro consists of multiple services:
- **Frontend**: Next.js application (Vercel)
- **Backend API**: FastAPI application (Railway)
- **ETL Service**: Python scraping service (Railway/Cron)
- **Database**: Supabase PostgreSQL
- **Authentication**: Supabase Auth
- **Payments**: Stripe

## Monitoring and Logs

### Where Logs Live

#### GitHub Actions Logs
- **Location**: GitHub repository → Actions tab
- **Retention**: 30 days for public repos, 90 days for private
- **Accessing**:
  1. Go to repository → Actions
  2. Select workflow run
  3. Click on job to see logs
  4. Download logs using "Download logs" button

#### Supabase Logs
- **Location**: Supabase Dashboard → Project → Logs
- **Types**:
  - Database logs: Query performance, errors
  - API logs: Authentication, API calls
  - Realtime logs: WebSocket connections
- **Accessing**:
  1. Login to Supabase Dashboard
  2. Select project
  3. Navigate to Logs section
  4. Filter by service (Database, API, Auth, etc.)

#### Railway Logs
- **Location**: Railway Dashboard → Service → Deploy Logs
- **Real-time access**: `railway logs --follow`
- **Accessing**:
  1. Login to Railway Dashboard
  2. Select project and service
  3. Go to Deployments tab
  4. Click on deployment to see logs

#### Vercel Logs
- **Location**: Vercel Dashboard → Project → Functions
- **Real-time access**: Vercel CLI `vercel logs`
- **Accessing**:
  1. Login to Vercel Dashboard
  2. Select project
  3. Go to Functions tab for API routes
  4. View logs in real-time or download

### Log Analysis Commands

```bash
# Search for errors in GitHub Actions artifacts
grep -i "error\|fail\|exception" workflow-logs.txt

# Filter Supabase logs by date
# (Use Supabase Dashboard filters)

# Railway logs with CLI
railway logs --follow --service backend
railway logs --since 1h --service etl-scraper

# Vercel logs with CLI
vercel logs --follow
vercel logs --since 1h
```

## ETL Operations

### How to Replay a Failed ETL

#### 1. Identify the Failed Run
```bash
# Check ETL state
python scripts/etl_state_helper.py list

# Get last run details for specific source
python scripts/etl_state_helper.py get --source harris_issued_permits
```

#### 2. Manual ETL Replay with Custom Time Range
```bash
# Replay last 24 hours
poetry run python -m permit_leads --since 24h --formats csv

# Replay specific date range  
poetry run python -m permit_leads --since 2024-01-15 --until 2024-01-16 --formats csv

# Replay last week (be careful with rate limits)
poetry run python -m permit_leads --since 7d --formats csv --delay 2
```

#### 3. Reset ETL State (if needed)
```bash
# Mark source as failed to force full replay
python scripts/etl_state_helper.py update --source harris_issued_permits --status failure --error "Manual reset for replay"

# Initialize new source
python scripts/etl_state_helper.py init --source new_county_permits
```

#### 4. Monitor Replay Progress
```bash
# Check logs in real-time
tail -f etl_output.log

# Monitor ETL state updates
while true; do
  python scripts/etl_state_helper.py get --source harris_issued_permits
  sleep 30
done
```

### ETL Troubleshooting Common Issues

#### Zero Records Issue
1. Check data source availability:
   ```bash
   curl -I "$HC_ISSUED_PERMITS_URL"
   ```
2. Verify robots.txt compliance
3. Check for website structure changes
4. Review rate limiting settings

#### Rate Limiting
- Default delays are built into scrapers
- Increase delays with `--delay` flag
- Check scraper logs for HTTP 429 responses

#### Data Quality Issues
- Review normalization rules in scraper configs
- Check for new data fields or format changes
- Validate against expected schema

## Key Rotation

### How to Rotate Keys/Secrets Without Downtime

#### 1. Supabase Keys
```bash
# 1. Generate new keys in Supabase Dashboard
# 2. Update in multiple places simultaneously:

# GitHub Secrets
gh secret set SUPABASE_URL --body "new-url"
gh secret set SUPABASE_SERVICE_ROLE_KEY --body "new-key"
gh secret set SUPABASE_JWT_SECRET --body "new-secret"

# Railway Environment Variables
railway variables set SUPABASE_URL="new-url"
railway variables set SUPABASE_SERVICE_ROLE_KEY="new-key"

# Vercel Environment Variables  
vercel env add SUPABASE_URL production
vercel env add SUPABASE_SERVICE_ROLE_KEY production
```

#### 2. Stripe Keys
```bash
# 1. Generate new keys in Stripe Dashboard
# 2. Update in environments:

gh secret set STRIPE_SECRET_KEY --body "sk_live_new_key"
gh secret set STRIPE_WEBHOOK_SECRET --body "whsec_new_secret"

railway variables set STRIPE_SECRET_KEY="sk_live_new_key"
vercel env add STRIPE_SECRET_KEY production
```

#### 3. Database Credentials
1. Create new database user in Supabase
2. Update connection strings
3. Test connectivity
4. Remove old user

#### 4. Rotation Checklist
- [ ] Update GitHub repository secrets
- [ ] Update Railway environment variables
- [ ] Update Vercel environment variables
- [ ] Update local .env files
- [ ] Test all services after rotation
- [ ] Verify health checks pass
- [ ] Monitor logs for auth errors
- [ ] Remove old keys from providers

## Troubleshooting

### Service Health Checks

#### Quick Health Check Script
```bash
#!/bin/bash
# health-check.sh

echo "🔍 LeadLedgerPro Health Check"
echo "================================"

# Frontend
echo "Frontend (Vercel):"
curl -s -o /dev/null -w "%{http_code}" https://your-frontend.vercel.app/ || echo "FAILED"

# Backend API
echo "Backend API (Railway):"
curl -s -o /dev/null -w "%{http_code}" https://your-backend.railway.app/health || echo "FAILED"

# Database connectivity
echo "Database Check:"
curl -s https://your-backend.railway.app/api/supa-env-check | jq '.database_status' || echo "FAILED"

# ETL Status
echo "ETL Status:"
python scripts/etl_state_helper.py list | grep -E "(success|failure|running)"
```

### Common Issues

#### 1. Database Connection Issues
```bash
# Check Supabase status
curl -s https://status.supabase.com/api/v2/status.json

# Test connection from backend
poetry run python -c "
from supabase import create_client
import os
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))
print('Connection successful')
"
```

#### 2. Authentication Issues
- Check JWT secrets match between Supabase and application
- Verify token expiration settings
- Review user permissions in Supabase Auth

#### 3. Payment Processing Issues
- Check Stripe webhook endpoint health
- Verify webhook secret matches
- Review Stripe Dashboard for failed payments
- Check idempotency in billing events table

#### 4. ETL Service Issues
- Review scraper rate limits
- Check data source availability
- Verify normalization rules
- Monitor for schema drift

### Performance Issues

#### Database Performance
```sql
-- Check slow queries
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;

-- Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

#### API Performance
- Check Railway resource usage
- Review FastAPI endpoint performance
- Monitor database connection pool
- Check for N+1 query issues

## Emergency Procedures

### Service Outage Response

#### 1. Immediate Assessment (5 minutes)
```bash
# Run health checks
./scripts/health-check.sh

# Check status pages
curl -s https://status.railway.com/api/v2/status.json
curl -s https://status.supabase.com/api/v2/status.json  
curl -s https://status.vercel.com/api/v2/status.json
```

#### 2. Communication (10 minutes)
- Update status page (if available)
- Notify stakeholders
- Document issue in GitHub issue

#### 3. Mitigation (30 minutes)
- Rollback recent deployments if needed
- Switch to backup services if available
- Implement temporary workarounds

#### 4. Resolution
- Fix root cause
- Test thoroughly
- Deploy fix
- Monitor post-deployment

### Data Recovery

#### Database Backup Recovery
```bash
# List available backups in Supabase
# (Use Supabase Dashboard → Settings → Backups)

# Point-in-time recovery
# (Contact Supabase support for enterprise features)
```

#### ETL Data Recovery
```bash
# Re-run ETL for specific time range
poetry run python -m permit_leads --since "2024-01-15 00:00:00" --until "2024-01-15 23:59:59"

# Restore from archived CSV files
python scripts/restore_from_csv.py --file archived_permits_20240115.csv
```

## Maintenance Tasks

### Daily
- [ ] Review error logs
- [ ] Check ETL success rates
- [ ] Monitor API response times
- [ ] Verify payment processing

### Weekly
- [ ] Review GitHub Actions usage
- [ ] Check database performance
- [ ] Update dependencies (via Dependabot)
- [ ] Review user feedback

### Monthly
- [ ] Rotate sensitive credentials
- [ ] Update documentation
- [ ] Review and archive logs
- [ ] Performance optimization review
- [ ] Security audit

### Quarterly
- [ ] Disaster recovery testing
- [ ] Full system health assessment
- [ ] Cost optimization review
- [ ] Architecture review

## Contacts and Escalation

### Primary Contacts
- **Development Team**: GitHub @jtheoc80
- **Infrastructure**: Railway, Vercel, Supabase support
- **Security Issues**: security@company.com

### Escalation Matrix
1. **Low Impact**: GitHub issue, normal response
2. **Medium Impact**: Email notification, 4-hour response
3. **High Impact**: Immediate notification, 1-hour response
4. **Critical**: Page on-call, immediate response

### Service Providers
- **Railway**: support@railway.app
- **Vercel**: support@vercel.com  
- **Supabase**: support@supabase.com
- **Stripe**: support@stripe.com

## Useful Commands Reference

```bash
# Poetry commands
poetry install                    # Install dependencies
poetry update                     # Update dependencies
poetry run pytest               # Run tests
poetry run ruff check .         # Lint code

# Railway commands
railway login                    # Authenticate
railway environment             # Switch environments  
railway logs --follow          # Watch logs
railway variables              # Manage environment variables

# Vercel commands  
vercel login                    # Authenticate
vercel logs --follow           # Watch logs
vercel env ls                  # List environment variables

# Docker commands (if using containers)
docker logs container_name     # View container logs
docker exec -it container_name bash  # Shell into container

# Database commands
psql $DATABASE_URL             # Connect to database
pg_dump $DATABASE_URL > backup.sql  # Create backup
```

---

**Last Updated**: $(date '+%Y-%m-%d')
**Version**: 1.0
**Maintained By**: Development Team