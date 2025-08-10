#!/bin/bash
#
# Railway Supabase Environment Variables Setup Script
#
# This script uses the Railway CLI to set SUPABASE_URL and SUPABASE_SERVICE_ROLE
# environment variables for a backend service in Railway.
#

set -e  # Exit on any error

# Pre-filled Supabase URL
SUPABASE_URL="https://wsbnbncapkrdovrrghlh.supabase.co"

echo "🚀 Railway Supabase Environment Setup"
echo "======================================"
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Error: Railway CLI is not installed"
    echo "Please install it from: https://docs.railway.app/develop/cli#install"
    exit 1
fi

echo "✅ Railway CLI is available"
echo ""

# Check if user is logged in to Railway
echo "🔐 Checking Railway authentication..."
if ! railway whoami &> /dev/null; then
    echo "❌ Error: You are not logged in to Railway"
    echo "Please run: railway login"
    exit 1
fi

RAILWAY_USER=$(railway whoami 2>/dev/null)
echo "✅ Logged in as: $RAILWAY_USER"
echo ""

# Get Railway service ID - offer selection or manual input
echo "📋 Railway Service Selection"
echo "Choose how to specify the Railway service:"
echo "1) Select from available services"
echo "2) Enter service ID manually"
echo ""

read -p "Enter your choice (1 or 2): " choice

case $choice in
    1)
        echo ""
        echo "📋 Available Railway services:"
        echo ""
        
        # List available services
        if ! railway services; then
            echo "❌ Error: Failed to list Railway services"
            exit 1
        fi
        
        echo ""
        read -p "Enter the Service ID from the list above: " SERVICE_ID
        ;;
    2)
        echo ""
        read -p "Enter Railway Service ID: " SERVICE_ID
        ;;
    *)
        echo "❌ Error: Invalid choice. Please select 1 or 2."
        exit 1
        ;;
esac

# Validate service ID is not empty
if [ -z "$SERVICE_ID" ]; then
    echo "❌ Error: Service ID cannot be empty"
    exit 1
fi

echo ""
echo "🎯 Selected Service ID: $SERVICE_ID"
echo ""

# Get Supabase Service Role Key securely
echo "🔑 Supabase Service Role Key Setup"
echo "Please paste your Supabase Service Role Key below."
echo "This key will be set securely and not displayed in the terminal."
echo ""

read -s -p "Enter SUPABASE_SERVICE_ROLE key: " SUPABASE_SERVICE_ROLE
echo ""

# Validate service role key is not empty
if [ -z "$SUPABASE_SERVICE_ROLE" ]; then
    echo "❌ Error: SUPABASE_SERVICE_ROLE cannot be empty"
    exit 1
fi

echo ""
echo "⚙️  Setting Railway environment variables..."
echo ""

# Set SUPABASE_URL
echo "🔗 Setting SUPABASE_URL..."
if railway variables set SUPABASE_URL="$SUPABASE_URL" --service="$SERVICE_ID"; then
    echo "✅ SUPABASE_URL set successfully: $SUPABASE_URL"
else
    echo "❌ Error: Failed to set SUPABASE_URL"
    exit 1
fi

echo ""

# Set SUPABASE_SERVICE_ROLE
echo "🔑 Setting SUPABASE_SERVICE_ROLE..."
if railway variables set SUPABASE_SERVICE_ROLE="$SUPABASE_SERVICE_ROLE" --service="$SERVICE_ID"; then
    echo "✅ SUPABASE_SERVICE_ROLE set successfully (key hidden for security)"
else
    echo "❌ Error: Failed to set SUPABASE_SERVICE_ROLE"
    exit 1
fi

echo ""
echo "🎉 Environment variables configured successfully!"
echo ""
echo "Summary:"
echo "--------"
echo "Service ID: $SERVICE_ID"
echo "SUPABASE_URL: $SUPABASE_URL"
echo "SUPABASE_SERVICE_ROLE: [HIDDEN]"
echo ""
echo "💡 You can verify the variables are set by running:"
echo "   railway variables --service=$SERVICE_ID"
echo ""
echo "🔄 Don't forget to redeploy your service if needed:"
echo "   railway redeploy --service=$SERVICE_ID"