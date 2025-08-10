#!/usr/bin/env bash

#
# Vercel Latest Deployment URL Script
#
# This script fetches the latest READY deployment from Vercel and checks its status.
# 
# Requirements:
# - Vercel CLI (npm install -g vercel)
# - jq (for JSON parsing)
# - curl (for HTTP status checking)
#
# Usage:
#   ./scripts/vercel-latest-url.sh
#
# Environment Variables:
#   VERCEL_ORG_ID     - Vercel organization ID (optional, will be prompted if needed)
#   VERCEL_PROJECT_ID - Vercel project ID (optional, will be prompted if needed)
#
# Exit Codes:
#   0 - Success: Found READY deployment with acceptable HTTP status
#   1 - Error: Missing dependencies, no deployments found, or HTTP error
#

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}" >&2
}

# Function to check if command exists
check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_error "Required command '$1' not found"
        return 1
    fi
}

# Function to ensure project is linked
ensure_project_linked() {
    print_info "Ensuring Vercel project is linked..."
    
    # Check if user is authenticated first
    if ! vercel whoami &>/dev/null; then
        print_error "Not authenticated with Vercel"
        print_error "Please run 'vercel login' first to authenticate"
        exit 1
    fi
    
    # Check if project is already linked by testing vercel ls
    if vercel ls --json &>/dev/null; then
        print_success "Project is already linked to Vercel"
        return 0
    fi
    
    print_warning "Project not linked. Running 'vercel pull' to link..."
    
    # Try to pull/link the project
    if ! vercel pull --yes; then
        print_error "Failed to link project with 'vercel pull'"
        print_error "Please run 'vercel link' in this directory to link your project first"
        exit 1
    fi
    
    print_success "Project linked successfully"
}

# Function to get latest READY deployment
get_latest_deployment() {
    print_info "Fetching deployments from Vercel..."
    
    # Get deployments as JSON
    local deployments_json
    if ! deployments_json=$(vercel ls --json); then
        print_error "Failed to fetch deployments from Vercel"
        print_error "Make sure you're authenticated with 'vercel login' and the project is linked"
        exit 1
    fi
    
    # Parse and filter for READY deployments, sort by created date (newest first)
    local latest_ready_deployment
    latest_ready_deployment=$(echo "$deployments_json" | jq -r '
        .deployments 
        | map(select(.readyState == "READY"))
        | sort_by(.createdAt)
        | reverse
        | first
        | select(. != null)
    ')
    
    if [[ "$latest_ready_deployment" == "null" || -z "$latest_ready_deployment" ]]; then
        print_error "No READY deployments found"
        print_error "Please ensure you have at least one successful deployment on Vercel"
        exit 1
    fi
    
    # Extract the URL
    local deployment_url
    deployment_url=$(echo "$latest_ready_deployment" | jq -r '.url')
    
    if [[ -z "$deployment_url" || "$deployment_url" == "null" ]]; then
        print_error "Could not extract URL from deployment data"
        exit 1
    fi
    
    # Ensure URL has https:// prefix
    if [[ "$deployment_url" != https://* ]]; then
        deployment_url="https://$deployment_url"
    fi
    
    echo "$deployment_url"
}

# Function to check HTTP status
check_http_status() {
    local url="$1"
    print_info "Checking HTTP status for: $url"
    
    # Get HTTP status code using curl
    local http_status
    if ! http_status=$(curl -I -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null); then
        print_error "Failed to check HTTP status for $url"
        return 1
    fi
    
    print_info "HTTP Status: $http_status"
    
    # Check if status is acceptable (200, 301, 302, 308)
    case "$http_status" in
        200)
            print_success "Status 200 OK - Page is accessible"
            return 0
            ;;
        301)
            print_success "Status 301 Moved Permanently - Redirect is working"
            return 0
            ;;
        302)
            print_success "Status 302 Found - Temporary redirect is working"
            return 0
            ;;
        308)
            print_success "Status 308 Permanent Redirect - Redirect is working"
            return 0
            ;;
        *)
            print_error "Unacceptable HTTP status: $http_status"
            print_error "Expected one of: 200, 301, 302, 308"
            return 1
            ;;
    esac
}

# Main execution
main() {
    # Check for help flag first, before any other operations
    if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
        echo "Vercel Latest Deployment URL Script"
        echo
        echo "This script fetches the latest READY deployment from Vercel and checks its status."
        echo
        echo "Requirements:"
        echo "  - Vercel CLI (npm install -g vercel)"
        echo "  - jq (for JSON parsing)"
        echo "  - curl (for HTTP status checking)"
        echo
        echo "Usage:"
        echo "  ./scripts/vercel-latest-url.sh"
        echo "  ./scripts/vercel-latest-url.sh --help"
        echo
        echo "Prerequisites:"
        echo "  1. Run 'vercel login' to authenticate with Vercel"
        echo "  2. Run 'vercel link' to link your project (or let the script do it)"
        echo "  3. Have at least one successful deployment"
        echo
        echo "Environment Variables:"
        echo "  VERCEL_ORG_ID     - Vercel organization ID (optional)"
        echo "  VERCEL_PROJECT_ID - Vercel project ID (optional)"
        echo
        echo "Exit Codes:"
        echo "  0 - Success: Found READY deployment with acceptable HTTP status"
        echo "  1 - Error: Missing dependencies, no deployments found, or HTTP error"
        echo
        echo "Acceptable HTTP Status Codes: 200, 301, 302, 308"
        echo
        exit 0
    fi
    
    # Check dependencies
    print_info "Checking dependencies..."
    check_command "vercel" || {
        print_error "Vercel CLI is required. Install with: npm install -g vercel"
        exit 1
    }

    check_command "jq" || {
        print_error "jq is required. Install with: apt-get install jq (Ubuntu/Debian) or brew install jq (macOS)"
        exit 1
    }

    check_command "curl" || {
        print_error "curl is required. Install with: apt-get install curl (Ubuntu/Debian) or brew install curl (macOS)"
        exit 1
    }

    print_success "All dependencies are available"
    
    echo
    print_info "Vercel Latest Deployment URL Checker"
    echo
    
    # Ensure project is linked
    ensure_project_linked
    echo
    
    # Get the latest deployment URL
    local deployment_url
    deployment_url=$(get_latest_deployment)
    
    if [[ -z "$deployment_url" ]]; then
        print_error "Failed to get deployment URL"
        exit 1
    fi
    
    echo
    print_success "Latest READY deployment URL:"
    echo "$deployment_url"
    echo
    
    # Check HTTP status
    if check_http_status "$deployment_url"; then
        echo
        print_success "Deployment is accessible and working correctly!"
        echo
        exit 0
    else
        echo
        print_error "Deployment has issues - HTTP status check failed"
        echo
        exit 1
    fi
}

# Run main function
main "$@"