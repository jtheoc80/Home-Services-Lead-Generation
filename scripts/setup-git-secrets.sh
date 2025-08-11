#!/bin/bash

# Git Secrets Setup Script for Home Services Lead Generation
# This script installs and configures git-secrets to prevent committing sensitive data

set -e

echo "🔐 Setting up git-secrets for Home Services Lead Generation..."

# Check if git-secrets is installed
if ! command -v git-secrets &> /dev/null; then
    echo "Installing git-secrets..."
    
    # Install git-secrets from source
    cd /tmp
    git clone https://github.com/awslabs/git-secrets.git
    cd git-secrets
    make install
    cd -
    echo "✅ git-secrets installed successfully"
else
    echo "✅ git-secrets is already installed"
fi

# Navigate to repository root
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# Install git-secrets hooks
echo "Installing git-secrets hooks..."
git secrets --install --force

# Register AWS patterns (baseline)
echo "Registering AWS patterns..."
git secrets --register-aws

# Add custom patterns for Supabase
echo "Adding Supabase secret patterns..."
git secrets --add 'sb-[A-Za-z0-9_-]{32,}'  # Supabase service role keys
git secrets --add 'ey[A-Za-z0-9_-]{40,}'   # JWT tokens (start with 'ey')
git secrets --add 'supabase_[A-Za-z0-9_-]{32,}'  # Supabase API keys

# Add custom patterns for Vercel
echo "Adding Vercel secret patterns..."
git secrets --add 'vercel_[A-Za-z0-9_-]{24,}'    # Vercel API tokens
git secrets --add '[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12}_[A-Za-z0-9_-]{32,}'  # Vercel deploy hooks

# Add custom patterns for Railway
echo "Adding Railway secret patterns..."
git secrets --add 'railway_[A-Za-z0-9_-]{32,}'   # Railway API keys
git secrets --add 'dapi_[A-Za-z0-9_-]{40,}'      # Railway Deploy API keys
git secrets --add 'rw_[A-Za-z0-9_-]{32,}'        # Railway tokens

# Add allowed patterns for placeholder values
echo "Adding allowed patterns for placeholder values..."
git secrets --add --allowed 'your_supabase_jwt_secret_here'
git secrets --add --allowed 'your_mapbox_token_here'
git secrets --add --allowed 'your_google_api_key_here'
git secrets --add --allowed 'your_sendgrid_api_key_here'
git secrets --add --allowed 'your_twilio_account_sid_here'
git secrets --add --allowed 'your_twilio_auth_token_here'
git secrets --add --allowed 'sb-example-key-placeholder'
git secrets --add --allowed 'vercel_example_token'
git secrets --add --allowed 'railway_example_key'

# Add allowed patterns for test values (used in documentation and tests)
echo "Adding allowed patterns for test/documentation examples..."
git secrets --add --allowed 'sb-1234567890abcdef1234567890abcdef12345678'
git secrets --add --allowed 'test_jwt_token_placeholder'
git secrets --add --allowed 'vercel_1234567890abcdef1234567890'
# echo "Adding allowed patterns for test/documentation examples..."
# If you need to allow test/documentation secrets, add them only in test-specific setup or local configuration.

echo ""
echo "🎉 Git-secrets setup complete!"
echo ""
echo "The following patterns are now being monitored:"
echo "  ✓ Supabase service role keys (sb-*)"
echo "  ✓ JWT tokens (ey*)"
echo "  ✓ Vercel API tokens (vercel_*)"
echo "  ✓ Vercel deploy hooks"
echo "  ✓ Railway API keys (railway_*, dapi_*, rw_*)"
echo "  ✓ AWS credentials (default patterns)"
echo ""
echo "To test the setup, try running:"
echo "  git secrets --scan"
echo ""
echo "To test a specific file:"
echo "  git secrets --scan path/to/file"
echo ""
echo "If you need to add more patterns:"
echo "  git secrets --add 'pattern'"
echo ""
echo "If you need to allow a specific string:"
echo "  git secrets --add --allowed 'allowed_string'"