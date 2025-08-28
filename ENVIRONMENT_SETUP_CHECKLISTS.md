# Environment Setup Checklists

This document provides step-by-step checklists for setting up environments across Vercel, Railway, and Supabase.

## 🔧 Vercel Environment Checklist

### Initial Configuration
- [ ] Set **Root Directory** to `frontend` in project settings
- [ ] Verify `frontend/vercel.json` exists with correct Next.js configuration
- [ ] Ensure root `vercel.json` has proper framework settings (no `cd frontend &&` commands)

### Environment Variables
- [ ] Core Supabase variables:
  - [ ] `NEXT_PUBLIC_SUPABASE_URL`
  - [ ] `NEXT_PUBLIC_SUPABASE_ANON_KEY`
  - [ ] `SUPABASE_SERVICE_ROLE_KEY`
- [ ] Application configuration:
  - [ ] `NEXT_PUBLIC_ENVIRONMENT`
  - [ ] `NEXT_PUBLIC_DEFAULT_REGION`
  - [ ] `NEXT_PUBLIC_LAUNCH_SCOPE`
- [ ] Feature flags:
  - [ ] `NEXT_PUBLIC_FEATURE_LEAD_SCORING`
  - [ ] `NEXT_PUBLIC_FEATURE_NOTIFICATIONS`
  - [ ] `NEXT_PUBLIC_REALTIME_UPDATES`
- [ ] Billing (if enabled):
  - [ ] `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`
  - [ ] `STRIPE_WEBHOOK_SECRET`
  - [ ] `INTERNAL_BACKEND_WEBHOOK_URL`
  - [ ] `INTERNAL_WEBHOOK_TOKEN`

### Deployment Verification
- [ ] Frontend health check accessible: `/api/health`
- [ ] Environment variables pull successfully: `vercel env pull`
- [ ] Build completes without errors
- [ ] No ESLint blocking issues (production build disables ESLint)

### Automated Setup
```bash
# Use automated script for Supabase variables
./scripts/set-vercel-supabase-env.sh
```

## 🚂 Railway Environment Checklist

### Backend Configuration
- [ ] Verify `backend/Procfile` exists with correct uvicorn command
- [ ] Ensure `nixpacks.toml` is properly configured for Python-only builds
- [ ] Check `.dockerignore` excludes frontend files

### Environment Variables
- [ ] Database connection:
  - [ ] `DATABASE_URL`
  - [ ] `SUPABASE_URL`
  - [ ] `SUPABASE_SERVICE_ROLE_KEY`
  - [ ] `SUPABASE_JWT_SECRET`
- [ ] Application settings:
  - [ ] `LAUNCH_SCOPE=houston`
  - [ ] `DEFAULT_REGION=tx-houston`
  - [ ] `ALLOW_EXPORTS=false`
- [ ] External services:
  - [ ] `SENDGRID_API_KEY`
  - [ ] `REDIS_URL` (if using Redis)
- [ ] ML/Scoring:
  - [ ] `USE_ML_SCORING=false`
  - [ ] `MIN_SCORE_THRESHOLD=70.0`
- [ ] Billing integration:
  - [ ] `STRIPE_SECRET_KEY`
  - [ ] `STRIPE_PRICE_STARTER_MONTHLY`
  - [ ] `STRIPE_PRICE_PRO_MONTHLY`
  - [ ] `STRIPE_PRICE_LEAD_CREDIT_PACK`
  - [ ] `BILLING_SUCCESS_URL`
  - [ ] `BILLING_CANCEL_URL`
  - [ ] `INTERNAL_WEBHOOK_TOKEN`

### Deployment Verification
- [ ] Backend health check accessible: `/healthz`
- [ ] Database connectivity confirmed
- [ ] ETL state management working
- [ ] No Node.js auto-detection in build logs

### Automated Setup
```bash
# Use automated script for Supabase variables
./scripts/set-railway-supabase-env.sh
```

## 🗄️ Supabase Migration Checklist

### Database Setup
- [ ] Run DDL migration script: `supabase_migration.sql`
- [ ] Verify all tables created:
  - [ ] `public.leads`
  - [ ] `public.contractors`
  - [ ] `public.lead_feedback`
  - [ ] `public.contractor_engagement`
  - [ ] `public.etl_state`
  - [ ] `meta.sources`
  - [ ] `meta.ingest_state`

### Row Level Security (RLS)
- [ ] RLS enabled on all tables
- [ ] Policies configured for:
  - [ ] Authenticated users can insert/select leads
  - [ ] Contractors can only access their own data
  - [ ] Lead feedback isolated by `account_id`
  - [ ] Engagement records isolated by `contractor_id`

### Testing Migration
- [ ] Run validation queries from `supabase_migration_tests.sql`
- [ ] Verify RLS policies work correctly
- [ ] Test authenticated vs anonymous access
- [ ] Confirm foreign key constraints

### Bootstrap Process
1. **Create Tables**: Run `supabase_migration.sql` in SQL Editor
2. **Test Schema**: Use test queries to verify structure
3. **Configure RLS**: Ensure policies are working
4. **Populate Meta Tables**: Add initial source configurations
5. **Verify ETL State**: Test ETL state management

### Security Notes
- [ ] Anonymous lead insertion disabled (authenticated only)
- [ ] Service role key secured and not exposed to frontend
- [ ] User data properly isolated using `auth.uid()`
- [ ] Foreign key constraints maintain data integrity

## 🔍 Health Check Verification

### Frontend Health (`/api/health`)
- [ ] Returns 200 status
- [ ] Shows webhook configuration status
- [ ] Confirms Supabase connection
- [ ] Reports backend webhook setup

### Backend Health (`/healthz`)
- [ ] Returns 200 status with comprehensive monitoring
- [ ] Database connectivity confirmed
- [ ] Redis status (if applicable)
- [ ] Stripe configuration verified
- [ ] ETL ingestion status current
- [ ] Sources connectivity validated

### Integration Health
- [ ] Stack health script passes: `./scripts/stack-health.js`
- [ ] End-to-end smoke tests pass
- [ ] All dependent services responding

## 🚨 Troubleshooting Quick Reference

### Common Issues
- **Vercel**: Root directory must be `frontend`, not using `cd frontend &&`
- **Railway**: Ensure Nixpacks only detects Python, not Node.js
- **Supabase**: RLS policies must use `auth.uid()` for user isolation
- **ETL**: State management only updates after successful upserts

### Emergency Rollback
```bash
# Vercel rollback
vercel ls
vercel promote <previous-deployment-url>

# Railway rollback
# Use Railway dashboard to rollback to previous deployment

# Supabase schema
# Revert using backup or manual DROP statements
```