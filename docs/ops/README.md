# Operations Documentation

This directory contains operational documentation for the Home Services Lead Generation platform.

## Environment Variables Management

This platform uses different environment variable locations depending on where the code runs:

### 1. Vercel Environment (Frontend/Browser-Exposed)

**Location:** Vercel Dashboard → Project Settings → Environment Variables

**Variables:** These are browser-exposed and safe to include in frontend builds
```bash
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key_here
NEXT_PUBLIC_API_BASE=https://your-backend.railway.app
```

**Setting via CLI:**
```bash
vercel env add NEXT_PUBLIC_SUPABASE_URL production
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production  
vercel env add NEXT_PUBLIC_API_BASE production
```

**Important:** Do NOT store `NEXT_PUBLIC_*` variables in GitHub Secrets - they belong in Vercel env.

### 2. GitHub Secrets (Server/Workflow-Only)

**Location:** GitHub Repository → Settings → Secrets and Variables → Actions → Secrets

**Variables:** These are server-side only and never exposed to browsers
```bash
DATABASE_URL=postgresql://user:pass@host/db
SENDGRID_API_KEY=SG.xxx
REDIS_URL=redis://user:pass@host:port
VERCEL_TOKEN=xxx (for workflow automation)
SUPABASE_SERVICE_ROLE=xxx (bypasses RLS, server-side only)
SLACK_WEBHOOK=https://hooks.slack.com/xxx
RAILWAY_TOKEN=xxx (for workflow automation)
```

**Setting via CLI:**
```bash
gh secret set DATABASE_URL
gh secret set SENDGRID_API_KEY
gh secret set REDIS_URL
gh secret set VERCEL_TOKEN
gh secret set SUPABASE_SERVICE_ROLE
gh secret set SLACK_WEBHOOK
gh secret set RAILWAY_TOKEN
```

### 3. GitHub Actions Variables (Public Build-Time)

**Location:** GitHub Repository → Settings → Secrets and Variables → Actions → Variables

**Variables:** These are safe for public workflows but not browser-exposed
```bash
AUTO_REMEDIATE=false
FRONTEND_URL=https://your-vercel-domain.vercel.app
SUPABASE_URL=https://your-project.supabase.co
VERCEL_PROJECT_ID=prj_xxx
RAILWAY_PROJECT_ID=xxx
RAILWAY_SERVICE_ID=xxx
```

**Setting via CLI:**
```bash
gh variable set AUTO_REMEDIATE --body false
gh variable set FRONTEND_URL --body https://your-domain.vercel.app
gh variable set SUPABASE_URL --body https://your-project.supabase.co
gh variable set VERCEL_PROJECT_ID --body prj_xxx
gh variable set RAILWAY_PROJECT_ID --body xxx
gh variable set RAILWAY_SERVICE_ID --body xxx
```

### 4. Local Development

**Location:** `.env.local` (frontend) and `.env` (backend/root)

**Frontend `.env.local`:**
```bash
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key_here
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

**Backend/Root `.env`:**
```bash
DATABASE_URL=postgresql://localhost/lead_db
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE=your_service_role_key_here
```

## Security Guidelines

### ✅ Safe to Expose (Browser/Public)
- `NEXT_PUBLIC_*` variables
- GitHub Actions Variables
- Public URLs and project IDs

### ❌ Never Expose (Server-Only)
- `DATABASE_URL`
- `SUPABASE_SERVICE_ROLE` 
- API keys (`SENDGRID_API_KEY`, etc.)
- Authentication tokens
- Private keys and secrets

## Quick Reference

| Environment | Purpose | Location | CLI Tool |
|-------------|---------|----------|----------|
| **Vercel** | Frontend runtime | Vercel Dashboard | `vercel env` |
| **GitHub Secrets** | Workflow secrets | Repo Settings | `gh secret` |
| **GitHub Variables** | Workflow config | Repo Settings | `gh variable` |
| **Local Dev** | Development | `.env.local`/`.env` | Direct edit |

## Troubleshooting

### Missing Environment Variables
1. Check the correct location for the variable type
2. Verify spelling and case sensitivity
3. Redeploy after adding new environment variables
4. Use the health check endpoints to verify configuration

### Health Check Endpoints
- **Frontend:** `GET /api/health` - checks frontend + backend + Supabase
- **Backend:** `GET /healthz` - checks backend + database connectivity
- **Stack Monitor:** `node scripts/stack-health.js` - comprehensive check

## Related Documentation

- [runbooks.md](./runbooks.md) - Troubleshooting guides for each platform
- [stack-monitor-bot.md](./stack-monitor-bot.md) - Automated monitoring details
- [../DEPLOYMENT.md](../../DEPLOYMENT.md) - Deployment procedures