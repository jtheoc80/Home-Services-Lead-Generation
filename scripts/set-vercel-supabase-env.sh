#!/bin/bash

# --- Interpreter and Permission Checks ---

# Check if running under Bash
if [ -z "$BASH_VERSION" ]; then
  echo "Error: This script must be run with Bash." >&2
  exit 1
fi

# Check if /bin/bash exists and is executable
if [ ! -x "/bin/bash" ]; then
  echo "Error: /bin/bash not found or not executable." >&2
  exit 1
fi

# Check if the script itself is executable
if [ ! -x "$0" ]; then
  echo "Warning: Script '$0' is not marked as executable. Consider running 'chmod +x $0'." >&2
fi

# Vercel Supabase Environment Setup Script
# This script sets up Supabase environment variables for production, preview, and development environments

set -e  # Exit on any error

# Error handler function
error_handler() {
    echo ""
    echo "❌ Error occurred on line $1."
    echo "   Please check the previous output for details."
    echo "   If you need help, refer to the README or contact support."
    exit 1
}

# Trap errors and call error_handler with the line number
trap 'error_handler $LINENO' ERR

echo "🚀 Setting up Supabase environment variables for Vercel project..."
echo ""

# Pre-defined Supabase URL (hardcoded as per requirements)
SUPABASE_URL="https://wsbnbncapkrdovrrghlh.supabase.co"

echo "📝 Setting NEXT_PUBLIC_SUPABASE_URL for all environments..."
echo "   URL: $SUPABASE_URL"
echo ""

# Helper function to set environment variable
set_env_var() {
    local var_name="$1"
    local environment="$2"
    local value="$3"
    
    echo "🔧 Setting $var_name for $environment environment..."
    if vercel env ls "$environment" | grep -q "^$var_name "; then
        echo "   Variable already exists. Updating value..."
        vercel env edit "$var_name" "$environment" --value="$value"
    else
        echo "   Adding new variable..."
        vercel env add "$var_name" "$environment" --value="$value"
    fi
}

# Set NEXT_PUBLIC_SUPABASE_URL for all environments
set_env_var "NEXT_PUBLIC_SUPABASE_URL" "production" "$SUPABASE_URL"
set_env_var "NEXT_PUBLIC_SUPABASE_URL" "preview" "$SUPABASE_URL"
set_env_var "NEXT_PUBLIC_SUPABASE_URL" "development" "$SUPABASE_URL"

echo ""
echo "🔑 Now setting NEXT_PUBLIC_SUPABASE_ANON_KEY for all environments..."
echo "   You will be prompted to enter the anonymous key for each environment."
echo "   Get this key from your Supabase project settings > API > anon public key"
echo ""

# Securely prompt for the Supabase anonymous key
echo "🔐 Please enter your Supabase anonymous key:"
echo "   (input will be hidden for security)"
read -s -p "   Key: " SUPABASE_ANON_KEY
echo ""

if [ -z "$SUPABASE_ANON_KEY" ]; then
    echo "❌ Error: No anonymous key provided. Exiting."
    exit 1
fi

echo "   ✅ Anonymous key received securely."
echo ""

# Helper function to set anon key for environment
set_anon_key() {
    local environment="$1"
    echo "🔧 Setting NEXT_PUBLIC_SUPABASE_ANON_KEY for $environment environment..."
    if vercel env ls "$environment" | grep -q "^NEXT_PUBLIC_SUPABASE_ANON_KEY "; then
        echo "   Variable already exists. Updating value..."
        vercel env edit "NEXT_PUBLIC_SUPABASE_ANON_KEY" "$environment" --value="$SUPABASE_ANON_KEY"
    else
        echo "   Adding new variable..."
        vercel env add "NEXT_PUBLIC_SUPABASE_ANON_KEY" "$environment" --value="$SUPABASE_ANON_KEY"
    fi
}

# Set NEXT_PUBLIC_SUPABASE_ANON_KEY for all environments
set_anon_key "production"
set_anon_key "preview"
set_anon_key "development"

echo ""
echo "📥 Pulling environment variables to local .env.local file..."
vercel env pull .env.local

echo ""
echo "✅ Supabase environment variables have been successfully configured!"
echo "   - NEXT_PUBLIC_SUPABASE_URL: $SUPABASE_URL"
echo "   - NEXT_PUBLIC_SUPABASE_ANON_KEY: [configured securely for all environments]"
echo "   - Local .env.local file has been updated"
echo ""
echo "📋 What was done:"
echo "   ✓ Set NEXT_PUBLIC_SUPABASE_URL for production, preview, and development"
echo "   ✓ Set NEXT_PUBLIC_SUPABASE_ANON_KEY for production, preview, and development"
echo "   ✓ Pulled environment variables to .env.local"
echo ""
echo "🎉 Setup complete! Your Vercel project is now configured with Supabase environment variables."
echo ""
echo "💡 Next steps:"
echo "   1. Verify your environment variables: vercel env ls"
echo "   2. Deploy your changes: vercel --prod"
echo "   3. Check your local .env.local file for the pulled variables"