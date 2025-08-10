#!/bin/bash

# Vercel Supabase Environment Setup Script
# This script sets up Supabase environment variables for production, preview, and development environments

set -e  # Exit on any error

echo "🚀 Setting up Supabase environment variables for Vercel project..."
echo ""

# Pre-defined Supabase URL
SUPABASE_URL="https://wsbnbncapkrdovrrghlh.supabase.co"

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