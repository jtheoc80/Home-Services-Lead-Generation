#!/bin/bash
# =============================================================================
# Austin Socrata Manual Testing Script
# =============================================================================
# Manual testing workflow for Austin Socrata API as described in problem statement.
# 
# Step 1 — quick HEAD + sample row
# Step 2 — download a CSV (no code)
#
# Usage: 
#   export AUSTIN_SOCRATA_APP_TOKEN=YOUR_TOKEN
#   export AUSTIN_DATASET_ID=abcd-1234   # <-- replace with the real resource id
#   ./scripts/austin-socrata-manual-test.sh
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

log_command() {
    echo -e "${YELLOW}$1${NC}"
}

# Check required environment variables
check_env_vars() {
    log_section "Environment Variable Check"
    
    if [ -z "${AUSTIN_SOCRATA_APP_TOKEN:-}" ]; then
        log_error "AUSTIN_SOCRATA_APP_TOKEN is not set"
        echo "Set it with: export AUSTIN_SOCRATA_APP_TOKEN=YOUR_TOKEN"
        return 1
    else
        log_success "AUSTIN_SOCRATA_APP_TOKEN is set"
    fi
    
    if [ -z "${AUSTIN_DATASET_ID:-}" ]; then
        log_error "AUSTIN_DATASET_ID is not set"
        echo "Set it with: export AUSTIN_DATASET_ID=abcd-1234   # <-- replace with the real resource id"
        return 1
    else
        log_success "AUSTIN_DATASET_ID is set to: $AUSTIN_DATASET_ID"
    fi
    
    return 0
}

# Step 1 — quick HEAD + sample row
step1_head_and_sample() {
    log_section "Step 1 — Quick HEAD + Sample Row"
    
    log_info "Running HEAD check (portal reachable)"
    log_command "curl -sS -I https://data.austintexas.gov | head -n1"
    
    local head_result
    head_result=$(curl -sS -I https://data.austintexas.gov | head -n1)
    echo "$head_result"
    
    if echo "$head_result" | grep -q "200"; then
        log_success "Austin data portal is reachable"
    else
        log_error "Austin data portal check failed"
        return 1
    fi
    
    echo
    log_info "Fetching 1 sample row (should print a small JSON array)"
    log_command "curl -sS \"https://data.austintexas.gov/resource/$AUSTIN_DATASET_ID.json?\\\$limit=1\" \\"
    log_command "  -H \"X-App-Token: \$AUSTIN_SOCRATA_APP_TOKEN\""
    
    local sample_result
    sample_result=$(curl -sS "https://data.austintexas.gov/resource/$AUSTIN_DATASET_ID.json?\$limit=1" \
      -H "X-App-Token: $AUSTIN_SOCRATA_APP_TOKEN")
    
    echo "$sample_result" | head -c 500
    if [ ${#sample_result} -gt 500 ]; then
        echo "... (truncated)"
    fi
    echo
    
    if echo "$sample_result" | grep -q '^\[.*\]$'; then
        log_success "Sample row fetch successful - got JSON array"
    elif echo "$sample_result" | grep -q '401\|403\|Unauthorized\|Forbidden'; then
        log_error "Authentication failed - check AUSTIN_SOCRATA_APP_TOKEN"
        return 1
    else
        log_error "Unexpected response format"
        echo "Response: $sample_result"
        return 1
    fi
}

# Step 2 — download a CSV (no code)
step2_download_csv() {
    log_section "Step 2 — Download a CSV (no code)"
    
    local start_date="2024-01-01"
    local csv_filename="austin_sample.csv"
    
    log_info "Downloading CSV with date filter"
    log_info "Start date: $start_date"
    log_info "Output file: $csv_filename"
    
    echo
    log_command "START=2024-01-01"
    log_command "curl -sS \"https://data.austintexas.gov/resource/\$AUSTIN_DATASET_ID.csv?\\"
    log_command "\\\$where=issued_date >= '\$START'&\\\$order=issued_date&\\\$limit=50000\" \\"
    log_command "  -H \"X-App-Token: \$AUSTIN_SOCRATA_APP_TOKEN\" \\"
    log_command "  -o austin_sample.csv"
    log_command "wc -l austin_sample.csv && head -5 austin_sample.csv"
    
    echo
    log_info "Executing CSV download..."
    
    # Note: Using issued_date as the default date field, but the script mentions alternatives
    local date_field="issued_date"
    
    # Check if the file exists and remove it for a clean test
    if [ -f "$csv_filename" ]; then
        rm "$csv_filename"
    fi
    
    # Execute the download
    if curl -sS "https://data.austintexas.gov/resource/$AUSTIN_DATASET_ID.csv?\$where=${date_field} >= '${start_date}'&\$order=${date_field}&\$limit=50000" \
         -H "X-App-Token: $AUSTIN_SOCRATA_APP_TOKEN" \
         -o "$csv_filename"; then
        
        if [ -f "$csv_filename" ] && [ -s "$csv_filename" ]; then
            local line_count
            line_count=$(wc -l < "$csv_filename")
            log_success "CSV download successful"
            echo "Line count: $line_count"
            echo
            log_info "First 5 lines of downloaded CSV:"
            head -5 "$csv_filename"
        else
            log_error "CSV file is empty or not created"
            return 1
        fi
    else
        log_error "CSV download failed"
        return 1
    fi
    
    echo
    log_info "Alternative date fields to try if 'issued_date' doesn't work:"
    echo "  • issue_date"
    echo "  • file_date" 
    echo "  • application_date"
    echo "  • created_date"
}

# Show usage information
show_usage() {
    cat << EOF
Austin Socrata Manual Testing Script

This script implements the manual testing workflow described in the problem statement.

REQUIRED ENVIRONMENT VARIABLES:
  AUSTIN_SOCRATA_APP_TOKEN  Your Austin Socrata API app token
  AUSTIN_DATASET_ID         The resource ID for the dataset (e.g., '3syk-w9eu')

SETUP:
  # Set your token and dataset id (find on the dataset's API page)
  export AUSTIN_SOCRATA_APP_TOKEN=YOUR_TOKEN
  export AUSTIN_DATASET_ID=abcd-1234   # <-- replace with the real resource id

USAGE:
  $0 [options]

OPTIONS:
  --help    Show this help message
  --step1   Run only Step 1 (HEAD + sample row)
  --step2   Run only Step 2 (CSV download)

EXAMPLES:
  $0                # Run both steps
  $0 --step1        # Run only HEAD + sample row test
  $0 --step2        # Run only CSV download test

WHAT THIS SCRIPT DOES:
  Step 1: Quick HEAD check + sample row
    • Verifies Austin data portal is reachable
    • Fetches 1 sample row to validate API access
  
  Step 2: Download a CSV (no code)
    • Downloads CSV with date filtering
    • Shows line count and preview of data
    • Provides alternative date field suggestions

EOF
}

# Main execution
main() {
    local run_step1=true
    local run_step2=true
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help)
                show_usage
                exit 0
                ;;
            --step1)
                run_step1=true
                run_step2=false
                shift
                ;;
            --step2)
                run_step1=false
                run_step2=true
                shift
                ;;
            *)
                echo "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    echo "============================================================================="
    echo "Austin Socrata Manual Testing Script"
    echo "============================================================================="
    
    # Check environment variables
    if ! check_env_vars; then
        echo
        log_error "Environment variables not set properly. Exiting."
        echo
        show_usage
        exit 1
    fi
    
    # Run requested steps
    local success=true
    
    if [ "$run_step1" = true ]; then
        if ! step1_head_and_sample; then
            success=false
        fi
    fi
    
    if [ "$run_step2" = true ]; then
        if ! step2_download_csv; then
            success=false
        fi
    fi
    
    echo
    log_section "Manual Testing Summary"
    if [ "$success" = true ]; then
        log_success "All manual tests completed successfully!"
    else
        log_error "Some manual tests failed. Check the output above."
        exit 1
    fi
    
    echo
    log_info "Next steps:"
    echo "  • Review the downloaded CSV data"
    echo "  • Test with different date ranges"
    echo "  • Try alternative date fields if needed"
}

# Run main function
main "$@"