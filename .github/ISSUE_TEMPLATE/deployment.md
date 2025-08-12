---
name: Deployment Issue
about: Report issues with deployment, infrastructure, or DevOps
title: '[DEPLOY] '
labels: ['deployment', 'infrastructure', 'devops']
assignees: ['jtheoc80']

---

## Deployment Environment
**Platform:**
- [ ] Railway
- [ ] Vercel
- [ ] Local development
- [ ] CI/CD pipeline
- [ ] Other: ___________

**Service Affected:**
- [ ] Frontend (Next.js)
- [ ] Backend (FastAPI)
- [ ] Database (Supabase)
- [ ] ETL/Scraping service
- [ ] Multiple services

## Issue Description
A clear and concise description of the deployment issue.

## Steps to Reproduce
1. Deploy to '...'
2. Access '....'
3. Check '....'
4. See error

## Expected Behavior
What should happen during/after deployment.

## Actual Behavior
What actually happened during/after deployment.

## Error Messages/Logs
```bash
# Paste deployment logs, error messages, or relevant output here
```

## Environment Variables
**Missing/Incorrect Environment Variables:**
- [ ] SUPABASE_URL
- [ ] SUPABASE_SERVICE_ROLE_KEY
- [ ] SUPABASE_JWT_SECRET
- [ ] STRIPE_SECRET_KEY
- [ ] NEXT_PUBLIC_SUPABASE_URL
- [ ] NEXT_PUBLIC_SUPABASE_ANON_KEY
- [ ] Other: ___________

## Configuration Files
**Files that may need updates:**
- [ ] nixpacks.toml
- [ ] vercel.json
- [ ] railway.json
- [ ] Dockerfile
- [ ] docker-compose.yml
- [ ] package.json
- [ ] pyproject.toml
- [ ] GitHub Actions workflows

## Health Checks
**Service Status:**
- Frontend: [ ] Working [ ] Down [ ] Degraded
- Backend: [ ] Working [ ] Down [ ] Degraded
- Database: [ ] Working [ ] Down [ ] Degraded
- ETL: [ ] Working [ ] Down [ ] Degraded

**URLs to Test:**
- Frontend: [URL]
- Backend health: [URL/health]
- Backend API docs: [URL/docs]
- Supabase check: [URL/api/supa-env-check]

## Build Information
**Build Status:**
- [ ] Build successful
- [ ] Build failed
- [ ] Build warnings
- [ ] Build not triggered

**Deployment Timing:**
- Build time: [e.g. 5 minutes]
- Deploy time: [e.g. 2 minutes]
- Total time: [e.g. 7 minutes]

## Rollback Plan
- [ ] Can rollback to previous version
- [ ] Need manual intervention
- [ ] Database migration required
- [ ] No rollback needed

## Impact Assessment
**User Impact:**
- [ ] Service completely down
- [ ] Degraded performance
- [ ] Some features unavailable
- [ ] No user impact

**Business Impact:**
- [ ] Critical (revenue/customer impact)
- [ ] High (major feature down)
- [ ] Medium (some functionality lost)
- [ ] Low (internal tools only)

## Additional Context
Any other relevant information about the deployment issue.