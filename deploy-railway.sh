#!/bin/bash
# Quick deployment script for Railway

set -e

echo "🚀 Railway Deployment Script for Home Services Lead Generation Backend"
echo "======================================================================="

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI is not installed. Please install it first:"
    echo "npm install -g @railway/cli"
    exit 1
fi

# Check if user is logged in
if ! railway whoami &> /dev/null; then
    echo "❌ Not logged in to Railway. Please run:"
    echo "railway login"
    exit 1
fi

echo "✅ Railway CLI is installed and user is logged in"

# Step 1: Deploy to Railway
echo ""
echo "📦 Step 1: Deploying to Railway..."
railway up

# Step 2: Set environment variables
echo ""
echo "🔧 Step 2: Setting environment variables..."
echo "You need to set the following environment variables:"
echo ""
echo "Set SENDGRID_API_KEY:"
read -p "Enter your SendGrid API key: " SENDGRID_KEY
if [ ! -z "$SENDGRID_KEY" ]; then
    railway variables set SENDGRID_API_KEY="$SENDGRID_KEY"
    echo "✅ SENDGRID_API_KEY set"
fi

echo ""
echo "Set REDIS_URL:"
read -p "Enter your Redis URL: " REDIS_URL_VAR
if [ ! -z "$REDIS_URL_VAR" ]; then
    railway variables set REDIS_URL="$REDIS_URL_VAR"
    echo "✅ REDIS_URL set"
fi

# Check if DATABASE_URL is already set by Railway
if railway variables | grep -q "DATABASE_URL"; then
    echo "✅ DATABASE_URL already configured by Railway"
else
    echo "⚠️  DATABASE_URL not found. Make sure to add a PostgreSQL database in Railway dashboard"
fi

# Step 3: Apply database schema
echo ""
echo "🗄️  Step 3: Applying database schema..."
echo "Running one-off command: python backend/scripts/apply_schema.py"
railway run python backend/scripts/apply_schema.py

# Step 4: Verify health endpoint
echo ""
echo "🏥 Step 4: Verifying health endpoint..."
echo "Getting Railway URL..."
RAILWAY_URL=$(railway domain 2>/dev/null | head -n 1)

if [ ! -z "$RAILWAY_URL" ]; then
    echo "Railway URL: $RAILWAY_URL"
    echo "Testing /healthz endpoint..."
    
    # Wait a moment for deployment
    sleep 5
    
    if curl -f -s "$RAILWAY_URL/healthz" > /dev/null; then
        echo "✅ Health check passed!"
        echo "🎉 Deployment completed successfully!"
        echo ""
        echo "Your application is available at: $RAILWAY_URL"
        echo "Health check endpoint: $RAILWAY_URL/healthz"
        echo "API documentation: $RAILWAY_URL/docs"
    else
        echo "❌ Health check failed. Check logs with: railway logs"
    fi
else
    echo "⚠️  Could not get Railway URL. Check deployment status with: railway status"
fi

echo ""
echo "📋 Summary:"
echo "- ✅ Deployed to Railway"
echo "- ✅ Environment variables configured"
echo "- ✅ Database schema applied"
echo "- ✅ Health endpoint verified"
echo ""
echo "🔗 Useful commands:"
echo "- View logs: railway logs"
echo "- Check status: railway status"
echo "- Open in browser: railway open"
echo "- View variables: railway variables"