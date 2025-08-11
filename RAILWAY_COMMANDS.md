# Railway Deployment Commands Summary

## Quick Start Commands

```bash
# 1. Deploy to Railway
railway up

# 2. Set environment variables
railway variables set SENDGRID_API_KEY=your_sendgrid_api_key_here
railway variables set REDIS_URL=redis://default:password@host:port/database

# 3. Run one-off schema application
railway run python backend/scripts/apply_schema.py

# 4. Verify health endpoint
curl $(railway domain)/healthz
```

## Detailed Command Walkthrough

### Prerequisites
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login
```

### Step 1: Deploy Application
```bash
# Navigate to project directory
cd /path/to/Home-Services-Lead-Generation

# Deploy to Railway (creates project if needed)
railway up
```

### Step 2: Configure Environment Variables
```bash
# Set SendGrid API key for email notifications
railway variables set SENDGRID_API_KEY=your_sendgrid_api_key_here

# Set Redis URL for caching
railway variables set REDIS_URL=redis://username:password@host:port/database

# Optional: Set CORS origins (if different from default)
railway variables set CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com

# View all variables to confirm
railway variables
```

### Step 3: Apply Database Schema
```bash
# Run the schema application script as a one-off command
railway run python backend/scripts/apply_schema.py
```

This command will:
- Connect to the Railway PostgreSQL database using DATABASE_URL
- Apply the complete database schema from `backend/app/models.sql`
- Create tables: leads, lead_feedback, lead_outcomes, notifications, etc.
- Create custom types: lead_rating, subscription_status, subscription_plan
- Handle idempotent operations (won't fail if tables already exist)

### Step 4: Verify Deployment
```bash
# Get your Railway deployment URL
railway domain

# Test the health endpoint
curl https://your-app.railway.app/healthz

# Expected response:
# {
#   "status": "ok",
#   "version": "1.0.0", 
#   "db": "connected"
# }
```

## Alternative: Automated Deployment Script

Use the provided deployment script for guided setup:

```bash
# Make script executable
chmod +x deploy-railway.sh

# Run automated deployment
./deploy-railway.sh
```

## Verification Commands

```bash
# View deployment logs
railway logs

# Check service status
railway status

# Open application in browser
railway open

# Connect to database (if needed)
railway connect

# View all environment variables
railway variables

# Restart the service
railway restart
```

## API Endpoints Available After Deployment

- `GET /` - Root endpoint
- `GET /healthz` - Health check with database connectivity
- `GET /health` - Simple health check
- `GET /docs` - API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation
- `POST /api/subscription/cancel` - Cancel subscription
- `POST /api/subscription/reactivate` - Reactivate subscription
- `GET /api/subscription/status/{user_id}` - Get subscription status

## Environment Variables Reference

### Required Variables
- `SENDGRID_API_KEY` - SendGrid API key for email notifications
- `REDIS_URL` - Redis connection string for caching
- `DATABASE_URL` - PostgreSQL connection (automatically set by Railway)

### Optional Variables
- `CORS_ALLOWED_ORIGINS` - Comma-separated list of allowed CORS origins
- `PORT` - Application port (default: 8000, Railway usually overrides)

## Troubleshooting

### If deployment fails:
1. Check logs: `railway logs`
2. Verify nixpacks.toml configuration
3. Ensure backend/requirements.txt is complete

### If health check fails:
1. Verify DATABASE_URL is set: `railway variables | grep DATABASE_URL`
2. Check if PostgreSQL service is added in Railway dashboard
3. Verify schema was applied: `railway run python -c "import psycopg2; print('DB accessible')"`

### If schema application fails:
1. Check if models.sql exists: `ls backend/app/models.sql`
2. Verify database connection: `railway run python -c "import os; print(os.getenv('DATABASE_URL'))"`
3. Check for SQL syntax errors in models.sql

## Production Checklist

- [ ] Railway project deployed successfully
- [ ] SENDGRID_API_KEY environment variable set
- [ ] REDIS_URL environment variable set  
- [ ] DATABASE_URL automatically configured by Railway
- [ ] Database schema applied via `railway run python backend/scripts/apply_schema.py`
- [ ] Health endpoint returns `"db": "connected"` at `/healthz`
- [ ] API documentation accessible at `/docs`
- [ ] Custom domain configured (if needed)
- [ ] Monitoring and alerts configured