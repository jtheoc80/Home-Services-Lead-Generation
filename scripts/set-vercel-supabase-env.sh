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

echo "🚀 Setting up Supabase environment variables for Vercel project..."
echo ""

# Pre-defined Supabase URL
# Get Supabase URL from environment variable or first command line argument
if [ -n "$SUPABASE_URL" ]; then
    echo "Using SUPABASE_URL from environment variable."
elif [ -n "$1" ]; then
    SUPABASE_URL="$1"
    echo "Using SUPABASE_URL from command line argument."
else
    echo "❌ Error: SUPABASE_URL is not set. Please set the SUPABASE_URL environment variable or pass it as the first argument to this script."
    exit 1
fi

echo "📝 Setting NEXT_PUBLIC_SUPABASE_URL for all environments..."
echo "   URL: $SUPABASE_URL"
echo ""

# Set NEXT_PUBLIC_SUPABASE_URL for all environments
echo "🔧 Adding NEXT_PUBLIC_SUPABASE_URL to production environment..."
vercel env add NEXT_PUBLIC_SUPABASE_URL production --value="$SUPABASE_URL"

echo "🔧 Adding NEXT_PUBLIC_SUPABASE_URL to preview environment..."
vercel env add NEXT_PUBLIC_SUPABASE_URL preview --value="$SUPABASE_URL"

echo "🔧 Adding NEXT_PUBLIC_SUPABASE_URL to development environment..."
vercel env add NEXT_PUBLIC_SUPABASE_URL development --value="$SUPABASE_URL"

echo ""
echo "🔑 Now setting NEXT_PUBLIC_SUPABASE_ANON_KEY for all environments..."
echo "   You will be prompted to enter the anonymous key for each environment."
echo "   Get this key from your Supabase project settings > API > anon public key"
echo ""

# Set NEXT_PUBLIC_SUPABASE_ANON_KEY for all environments (user will be prompted)
echo "🔧 Adding NEXT_PUBLIC_SUPABASE_ANON_KEY to production environment..."
echo "   Please paste your Supabase anonymous key when prompted:"
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production

echo ""
echo "🔧 Adding NEXT_PUBLIC_SUPABASE_ANON_KEY to preview environment..."
echo "   Please paste your Supabase anonymous key when prompted:"
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY preview

echo ""
echo "🔧 Adding NEXT_PUBLIC_SUPABASE_ANON_KEY to development environment..."
echo "   Please paste your Supabase anonymous key when prompted:"
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY development

echo ""
echo "📥 Pulling environment variables to local .env.local file..."
vercel env pull .env.local

echo ""
echo "✅ Supabase environment variables have been successfully configured!"
echo "   - NEXT_PUBLIC_SUPABASE_URL: $SUPABASE_URL"
echo "   - NEXT_PUBLIC_SUPABASE_ANON_KEY: [configured for all environments]"
echo "   - Local .env.local file has been updated"
echo ""
echo "🎉 Setup complete! Your Vercel project is now configured with Supabase environment variables."