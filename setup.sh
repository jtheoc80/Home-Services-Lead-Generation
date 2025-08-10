#!/bin/bash

# Setup script for Home Services Lead Generation platform
# Installs dependencies for both permit_leads and backend components

set -e  # Exit on any error

echo "🏠 Home Services Lead Generation - Setup Script"
echo "=================================================="

# Check if we're in the right directory
if [[ ! -f "permit_leads/requirements.txt" ]] || [[ ! -f "backend/requirements.txt" ]]; then
    echo "❌ Error: Requirements files not found. Please run this script from the project root directory."
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "🐍 Python version: $python_version"

# Check if Python version is 3.11 or higher
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
    echo "❌ Error: Python 3.11+ required, but found Python $python_version"
    exit 1
fi

echo "✅ Python version is compatible"

# Install permit_leads dependencies
echo ""
echo "📦 Installing permit_leads dependencies..."
pip install -r permit_leads/requirements.txt

# Install backend dependencies  
echo ""
echo "📦 Installing backend dependencies..."
pip install -r backend/requirements.txt

echo ""
echo "=================================================="
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Configure environment variables:"
echo "   - Copy backend/.env.example to backend/.env"
echo "   - Copy frontend/.env.example to frontend/.env.local"
echo "2. Setup database (see README.md)"
echo "3. Install frontend dependencies: cd frontend && npm install"