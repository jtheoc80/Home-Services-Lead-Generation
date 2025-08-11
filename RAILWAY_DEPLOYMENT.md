# Railway Deployment Guide for Home Services Lead Generation Backend

This guide provides step-by-step commands to deploy the backend API to Railway.

## Prerequisites

1. Install Railway CLI:
```bash
npm install -g @railway/cli
```

2. Login to Railway:
```bash
railway login
```

## Step-by-Step Deployment Commands

### 1. Initialize Railway Project

Navigate to your project directory and initialize Railway:

```bash
cd /home/runner/work/Home-Services-Lead-Generation/Home-Services-Lead-Generation
railway up
```

This command will:
- Create a new Railway project (if not exists)
- Connect your local repository to Railway
- Deploy the application using the railway.json configuration

### 2. Set Required Environment Variables

Set the SENDGRID_API_KEY and REDIS_URL environment variables:

```bash
# Set SendGrid API key for email notifications
railway variables set SENDGRID_API_KEY=your_sendgrid_api_key_here

# Set Redis URL for caching
railway variables set REDIS_URL=redis://default:password@host:port

# Set DATABASE_URL (Railway will provide PostgreSQL)
railway variables set DATABASE_URL=postgresql://user:password@host:port/database

# Optional: Set CORS origins for production
railway variables set CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com

# Optional: Set port (Railway usually handles this automatically)
railway variables set PORT=8000
```

### 3. Run One-off Database Schema Application

Execute the schema application script as a one-off command:

```bash
railway run python backend/scripts/apply_schema.py
```

This command will:
- Connect to the Railway PostgreSQL database
- Apply the database schema from `backend/app/models.sql`
- Create all necessary tables and types idempotently

### 4. Verify Health Check

After deployment, verify the application is running by checking the `/healthz` endpoint:

```bash
# Get your Railway deployment URL
railway domain

# Then access the health check endpoint
curl https://your-railway-app.railway.app/healthz
```

Expected response:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "db": "connected"
}
```

## Additional Railway Commands

### View Deployment Logs
```bash
railway logs
```

### Check Service Status
```bash
railway status
```

### Open Application in Browser
```bash
railway open
```

### View Environment Variables
```bash
railway variables
```

### Connect to Database (if Railway PostgreSQL)
```bash
railway connect
```

## Troubleshooting

### If deployment fails:
1. Check logs: `railway logs`
2. Verify environment variables: `railway variables`
3. Ensure all dependencies are in `backend/requirements.txt`

### If health check fails:
1. Verify DATABASE_URL is set correctly
2. Ensure PostgreSQL database is accessible
3. Check that schema was applied successfully

### If schema application fails:
1. Verify DATABASE_URL environment variable
2. Check PostgreSQL connection
3. Ensure `backend/app/models.sql` exists and is valid

## Environment Variables Reference

Required variables:
- `DATABASE_URL`: PostgreSQL connection string
- `SENDGRID_API_KEY`: SendGrid API key for email notifications
- `REDIS_URL`: Redis connection string for caching

Optional variables:
- `CORS_ALLOWED_ORIGINS`: Comma-separated list of allowed origins
- `PORT`: Application port (default: 8000)

## Next Steps

After successful deployment:
1. Test all API endpoints
2. Configure monitoring and alerting
3. Set up continuous deployment from your Git repository
4. Configure custom domain (if needed)