#!/bin/bash
# =============================================================================
# Source-Agnostic Health Checks
# =============================================================================
# Quick, copy/paste health checks for various data sources.
# Run these from your laptop or a GH Action shell step.
# They'll fail fast with clear reasons.
#
# Usage: ./scripts/source-health-checks.sh [--verbose] [--test-urls]
# 
# Options:
#   --verbose    Show detailed curl output
#   --test-urls  Use test URLs instead of production URLs
#   --help       Show this help message
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
VERBOSE=false
TEST_URLS=false
USER_AGENT="LeadLedgerETL/1.0 (+github-actions)"

# Function to print usage
usage() {
    cat << EOF
Quick, source-agnostic health checks for data sources.

Usage: $0 [OPTIONS]

OPTIONS:
    --verbose       Show detailed curl output
    --test-urls     Use test URLs instead of production URLs  
    --help          Show this help message

EXAMPLES:
    $0                    # Run standard health checks
    $0 --verbose          # Run with detailed output
    $0 --test-urls        # Use test URLs for safe testing

WHAT TO LOOK FOR:
    ✅ HTTP/1.1 200 OK on HEAD requests
    ✅ ArcGIS ?f=pjson returns JSON with service info
    ✅ ArcGIS query returns JSON with count field
    ✅ Socrata returns JSON array (401/403 = missing/invalid App Token)
    ✅ XLSX has Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet

EOF
}

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_section() {
    echo
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}======================================${NC}"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --test-urls)
            TEST_URLS=true
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# =============================================================================
# 1) DNS + TLS + HEAD (connectivity & status)
# =============================================================================
check_dns_tls_head() {
    log_section "1. DNS + TLS + HEAD Connectivity Checks"
    
    if [ "$TEST_URLS" = true ]; then
        urls=(
            "https://httpbin.org/status/200"
            "https://httpbin.org/status/301"
            "https://www.google.com"
        )
    else
        urls=(
            "https://www.houstontx.gov/planning/DevelopRegs/dev_reports.html"
            "https://data.austintexas.gov"
            "https://services.arcgis.com"
            "https://opendata.sanantonio.gov"
            "https://dallascityhall.com"
        )
    fi
    
    for url in "${urls[@]}"; do
        echo
        log_info "Checking: $url"
        
        # Extract hostname for DNS check
        hostname=$(echo "$url" | awk -F/ '{print $3}')
        
        # DNS resolution check
        echo -n "  DNS: "
        if getent ahosts "$hostname" >/dev/null 2>&1; then
            log_success "DNS resolution successful for $hostname"
            if [ "$VERBOSE" = true ]; then
                getent ahosts "$hostname" | head -3
            fi
        else
            log_error "DNS resolution failed for $hostname"
            continue
        fi
        
        # HTTP HEAD check
        echo -n "  HEAD: "
        if [ "$VERBOSE" = true ]; then
            curl_output=$(curl -sS -I -A "$USER_AGENT" "$url" 2>&1)
            echo "$curl_output"
            status_line=$(echo "$curl_output" | head -n 1)
        else
            status_line=$(curl -sS -I -A "$USER_AGENT" "$url" 2>/dev/null | head -n 1)
        fi
        
        if echo "$status_line" | grep -q "200\|301\|302"; then
            log_success "$status_line"
        else
            log_error "$status_line"
        fi
    done
}

# =============================================================================
# 2) ArcGIS service root sanity (returns JSON service info if correct base)
# =============================================================================
check_arcgis_service_root() {
    log_section "2. ArcGIS Service Root Sanity Checks"
    
    if [ "$TEST_URLS" = true ]; then
        # Using a known working ArcGIS service for testing
        arcgis_urls=(
            "https://sampleserver6.arcgisonline.com/arcgis/rest/services/Wildfire/FeatureServer/0"
        )
    else
        arcgis_urls=(
            "https://gis2.arlingtontx.gov/agsext2/rest/services/OpenData/OD_Property/MapServer/1"
            # Add more ArcGIS service URLs here as needed
        )
    fi
    
    for arc_url in "${arcgis_urls[@]}"; do
        echo
        log_info "Checking ArcGIS service: $arc_url"
        
        # Check service root with f=pjson
        json_url="${arc_url}?f=pjson"
        echo -n "  Service Info: "
        
        if [ "$VERBOSE" = true ]; then
            response=$(curl -sS "$json_url" 2>&1)
            echo "$response" | head -c 300
            echo
        else
            response=$(curl -sS "$json_url" 2>/dev/null | head -c 300)
        fi
        
        if echo "$response" | grep -q '"name":\|"type":\|"geometryType":'; then
            log_success "Valid ArcGIS service - JSON response with service metadata"
        else
            log_error "Invalid response - not a proper ArcGIS service or service unavailable"
            if [ "$VERBOSE" = false ]; then
                echo "    Response preview: $response"
            fi
        fi
    done
}

# =============================================================================
# 3) ArcGIS count probe (date filter optional)
# =============================================================================
check_arcgis_count() {
    log_section "3. ArcGIS Count Probe Checks"
    
    if [ "$TEST_URLS" = true ]; then
        arcgis_urls=(
            "https://sampleserver6.arcgisonline.com/arcgis/rest/services/Wildfire/FeatureServer/0"
        )
    else
        arcgis_urls=(
            "https://gis2.arlingtontx.gov/agsext2/rest/services/OpenData/OD_Property/MapServer/1"
        )
    fi
    
    for arc_url in "${arcgis_urls[@]}"; do
        echo
        log_info "Checking count for: $arc_url"
        
        # Count query
        count_url="${arc_url}/query?where=1%3D1&returnCountOnly=true&f=json"
        echo -n "  Count Query: "
        
        if [ "$VERBOSE" = true ]; then
            response=$(curl -sS "$count_url" 2>&1)
            echo "$response"
        else
            response=$(curl -sS "$count_url" 2>/dev/null)
        fi
        
        if echo "$response" | grep -q '"count":[0-9]'; then
            count=$(echo "$response" | grep -o '"count":[0-9]*' | cut -d: -f2)
            log_success "Count query successful - found $count records"
        else
            log_error "Count query failed or returned invalid JSON"
            if [ "$VERBOSE" = false ]; then
                echo "    Response: $response"
            fi
        fi
    done
}

# =============================================================================
# 4) Socrata probe (Austin / San Antonio) – needs App Tokens
# =============================================================================
check_socrata() {
    log_section "4. Socrata API Probe Checks"
    
    # Check for app tokens
    if [ -z "${AUSTIN_SOCRATA_APP_TOKEN:-}" ]; then
        log_warning "AUSTIN_SOCRATA_APP_TOKEN not set - skipping Austin Socrata check"
    fi
    
    if [ -z "${SA_SOCRATA_APP_TOKEN:-}" ]; then
        log_warning "SA_SOCRATA_APP_TOKEN not set - skipping San Antonio Socrata check"
    fi
    
    # Austin Socrata check
    if [ -n "${AUSTIN_SOCRATA_APP_TOKEN:-}" ]; then
        echo
        log_info "Checking Austin Socrata API"
        
        if [ "$TEST_URLS" = true ]; then
            austin_url="https://data.austintexas.gov/resource/3syk-w9eu.json?\$limit=1"
        else
            austin_url="https://data.austintexas.gov/resource/3syk-w9eu.json?\$limit=1"
        fi
        
        echo -n "  Austin API: "
        if [ "$VERBOSE" = true ]; then
            response=$(curl -sS "$austin_url" -H "X-App-Token: $AUSTIN_SOCRATA_APP_TOKEN" 2>&1)
            echo "$response" | head -c 500
            echo
        else
            response=$(curl -sS "$austin_url" -H "X-App-Token: $AUSTIN_SOCRATA_APP_TOKEN" 2>/dev/null)
        fi
        
        if echo "$response" | grep -q '^\[.*\]$'; then
            log_success "Austin Socrata API responding with JSON array"
        elif echo "$response" | grep -q '401\|403\|Unauthorized\|Forbidden'; then
            log_error "Austin Socrata API authentication failed - check AUSTIN_SOCRATA_APP_TOKEN"
        else
            log_error "Austin Socrata API returned unexpected response"
            if [ "$VERBOSE" = false ]; then
                echo "    Response: $response"
            fi
        fi
    fi
    
    # San Antonio Socrata check
    if [ -n "${SA_SOCRATA_APP_TOKEN:-}" ]; then
        echo
        log_info "Checking San Antonio Socrata API"
        
        if [ "$TEST_URLS" = true ]; then
            sa_url="https://data.sanantonio.gov/resource/sample.json?\$limit=1"
        else
            sa_url="https://data.sanantonio.gov/resource/sample.json?\$limit=1"  # Replace with actual resource ID
        fi
        
        echo -n "  San Antonio API: "
        if [ "$VERBOSE" = true ]; then
            response=$(curl -sS "$sa_url" -H "X-App-Token: $SA_SOCRATA_APP_TOKEN" 2>&1)
            echo "$response" | head -c 500
            echo
        else
            response=$(curl -sS "$sa_url" -H "X-App-Token: $SA_SOCRATA_APP_TOKEN" 2>/dev/null)
        fi
        
        if echo "$response" | grep -q '^\[.*\]$'; then
            log_success "San Antonio Socrata API responding with JSON array"
        elif echo "$response" | grep -q '401\|403\|Unauthorized\|Forbidden'; then
            log_error "San Antonio Socrata API authentication failed - check SA_SOCRATA_APP_TOKEN"
        else
            log_error "San Antonio Socrata API returned unexpected response"
            if [ "$VERBOSE" = false ]; then
                echo "    Response: $response"
            fi
        fi
    fi
    
    if [ -z "${AUSTIN_SOCRATA_APP_TOKEN:-}" ] && [ -z "${SA_SOCRATA_APP_TOKEN:-}" ]; then
        log_info "To test Socrata APIs, set environment variables:"
        log_info "  export AUSTIN_SOCRATA_APP_TOKEN='your-austin-token'"
        log_info "  export SA_SOCRATA_APP_TOKEN='your-sa-token'"
    fi
}

# =============================================================================
# 5) Static XLSX probe (Houston Weekly) – verify it's a real file
# =============================================================================
check_static_xlsx() {
    log_section "5. Static XLSX File Probe Checks"
    
    if [ "$TEST_URLS" = true ]; then
        xlsx_urls=(
            "https://httpbin.org/response-headers?Content-Type=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet&Content-Length=12345"
        )
    else
        xlsx_urls=(
            # Replace with actual Houston Weekly XLSX URL
            "https://example.com/houston-weekly-permits.xlsx"
        )
    fi
    
    for xlsx_url in "${xlsx_urls[@]}"; do
        echo
        log_info "Checking XLSX file: $xlsx_url"
        
        echo -n "  File Check: "
        if [ "$VERBOSE" = true ]; then
            headers=$(curl -sSI "$xlsx_url" 2>&1)
            echo "$headers"
        else
            headers=$(curl -sSI "$xlsx_url" 2>/dev/null)
        fi
        
        # Extract key headers
        http_status=$(echo "$headers" | grep -i '^HTTP/' | head -1)
        content_type=$(echo "$headers" | grep -i '^content-type:' | head -1)
        content_length=$(echo "$headers" | grep -i '^content-length:' | head -1)
        
        echo "    Status: $http_status"
        echo "    Type: $content_type"
        echo "    Length: $content_length"
        
        if echo "$http_status" | grep -q "200"; then
            if echo "$content_type" | grep -q "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\|application/octet-stream"; then
                log_success "XLSX file is accessible and has correct content type"
            else
                log_warning "File accessible but content type may not be XLSX"
            fi
        else
            log_error "XLSX file not accessible - check URL"
        fi
    done
}

# =============================================================================
# Main execution
# =============================================================================
main() {
    echo "============================================================================="
    echo "Source-Agnostic Health Checks for Data Sources"
    echo "============================================================================="
    echo "User-Agent: $USER_AGENT"
    if [ "$TEST_URLS" = true ]; then
        echo "Mode: TEST URLS (safe for testing)"
    else
        echo "Mode: PRODUCTION URLS"
    fi
    echo "Verbose: $VERBOSE"
    echo "============================================================================="
    
    # Run all checks
    check_dns_tls_head
    check_arcgis_service_root
    check_arcgis_count
    check_socrata
    check_static_xlsx
    
    echo
    log_section "Health Check Summary"
    log_info "All health checks completed!"
    log_info "Look for ✓ (success), ⚠ (warning), or ✗ (error) indicators above"
    echo
    log_info "Expected success indicators:"
    echo "  • HTTP/1.1 200 OK on HEAD requests"
    echo "  • ArcGIS ?f=pjson returns JSON with service metadata"
    echo "  • ArcGIS query returns JSON with count field"
    echo "  • Socrata returns JSON array (401/403 = missing/invalid App Token)"
    echo "  • XLSX has Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
}

# Run main function
main "$@"