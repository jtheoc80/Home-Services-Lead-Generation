#!/bin/bash

# Local Security Check Script for Home Services Lead Generation Platform
# This script runs the same security checks that are performed in CI/CD

set -e

echo "🛡️  Home Services Lead Generation - Local Security Check"
echo "======================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if required tools are installed
check_prerequisites() {
    echo "Checking prerequisites..."
    
    if ! command -v npm &> /dev/null; then
        print_error "npm is required but not installed"
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        print_error "python3 is required but not installed"
        exit 1
    fi
    
    if ! command -v license-checker &> /dev/null; then
        print_warning "license-checker not found, installing globally..."
        npm install -g license-checker
    fi
    
    if ! python3 -c "import pip_audit" &> /dev/null; then
        print_warning "pip-audit not found, installing..."
        python3 -m pip install --user pip-audit
    fi
    
    if ! python3 -c "import pip_licenses" &> /dev/null; then
        print_warning "pip-licenses not found, installing..."
        python3 -m pip install --user pip-licenses
    fi
    
    print_status "Prerequisites check complete"
}

# Run npm audit
run_npm_audit() {
    echo ""
    echo "Running npm audit..."
    
    # Check root dependencies
    echo "Checking root dependencies..."
    if npm audit --audit-level=moderate --omit=dev; then
        print_status "Root npm audit passed"
    else
        print_error "Root npm audit failed"
        return 1
    fi
    
    # Check frontend dependencies
    echo "Checking frontend dependencies..."
    cd frontend
    if npm audit --audit-level=moderate --omit=dev; then
        print_status "Frontend npm audit passed"
    else
        print_error "Frontend npm audit failed"
        cd ..
        return 1
    fi
    cd ..
}

# Run pip audit
run_pip_audit() {
    echo ""
    echo "Running pip-audit..."
    
    echo "Checking backend dependencies..."
    if python3 -m pip_audit --requirement backend/requirements.txt --vulnerability-service=pypi --format=columns; then
        print_status "Backend pip-audit passed"
    else
        print_error "Backend pip-audit failed"
        return 1
    fi
    
    echo "Checking permit_leads dependencies..."
    if python3 -m pip_audit --requirement permit_leads/requirements.txt --vulnerability-service=pypi --format=columns; then
        print_status "Permit_leads pip-audit passed"
    else
        print_error "Permit_leads pip-audit failed"
        return 1
    fi
}

# Check license compliance
check_licenses() {
    echo ""
    echo "Checking license compliance..."
    
    ALLOWED_LICENSES="MIT;Apache-2.0;BSD-2-Clause;BSD-3-Clause;ISC;Unlicense;WTFPL;CC0-1.0;CC-BY-4.0;UNLICENSED;0BSD"
    
    # Check Node.js licenses (root)
    echo "Checking root Node.js licenses..."
    if license-checker --onlyAllow "$ALLOWED_LICENSES" --production --summary; then
        print_status "Root license check passed"
    else
        print_error "Root license check failed"
        return 1
    fi
    
    # Check Node.js licenses (frontend)
    echo "Checking frontend Node.js licenses..."
    cd frontend
    if license-checker --onlyAllow "$ALLOWED_LICENSES" --production --summary; then
        print_status "Frontend license check passed"
    else
        print_error "Frontend license check failed"
        cd ..
        return 1
    fi
    cd ..
    
    # Check Python licenses
    echo "Checking Python licenses..."
    
    # Create temporary virtual environment for testing
    TEMP_VENV=$(mktemp -d)
    python3 -m venv "$TEMP_VENV/backend_env"
    source "$TEMP_VENV/backend_env/bin/activate"
    pip install -r backend/requirements.txt > /dev/null 2>&1
    if pip-licenses --fail-on 'GPL-3.0;AGPL-3.0;LGPL-3.0' --format=table; then
        print_status "Backend Python license check passed"
    else
        print_error "Backend Python license check failed"
        deactivate
        rm -rf "$TEMP_VENV"
        return 1
    fi
    deactivate
    
    python3 -m venv "$TEMP_VENV/permit_env"
    source "$TEMP_VENV/permit_env/bin/activate"
    pip install -r permit_leads/requirements.txt > /dev/null 2>&1
    if pip-licenses --fail-on 'GPL-3.0;AGPL-3.0;LGPL-3.0' --format=table; then
        print_status "Permit_leads Python license check passed"
    else
        print_error "Permit_leads Python license check failed"
        deactivate
        rm -rf "$TEMP_VENV"
        return 1
    fi
    deactivate
    
    # Clean up
    rm -rf "$TEMP_VENV"
}

# Main execution
main() {
    cd "$(dirname "$0")/.."
    
    # Ensure we have dependencies installed
    if [ ! -d "node_modules" ]; then
        echo "Installing root dependencies..."
        npm ci
    fi
    
    if [ ! -d "frontend/node_modules" ]; then
        echo "Installing frontend dependencies..."
        cd frontend && npm ci && cd ..
    fi
    
    # Run all security checks
    check_prerequisites
    
    FAILED=0
    
    if ! run_npm_audit; then
        FAILED=1
    fi
    
    if ! run_pip_audit; then
        FAILED=1
    fi
    
    if ! check_licenses; then
        FAILED=1
    fi
    
    echo ""
    echo "======================================================"
    if [ $FAILED -eq 0 ]; then
        print_status "All security checks passed! 🎉"
        echo "Your code is ready for commit."
    else
        print_error "Some security checks failed! ❌"
        echo "Please fix the issues above before committing."
        exit 1
    fi
}

# Run the main function
main