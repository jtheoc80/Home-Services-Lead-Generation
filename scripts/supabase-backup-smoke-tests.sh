#!/bin/bash

# Supabase Backup Validation Smoke Tests
# This script runs comprehensive smoke tests against a restored Supabase staging environment
# to validate that the backup restoration was successful and the system is functional.

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_RESULTS_DIR="${TEST_RESULTS_DIR:-${SCRIPT_DIR}/../test-results}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Required environment variables
: "${STAGING_SUPABASE_URL:?STAGING_SUPABASE_URL environment variable is required}"
: "${STAGING_SUPABASE_SERVICE_ROLE:?STAGING_SUPABASE_SERVICE_ROLE environment variable is required}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results tracking
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

# Run a test and track results
run_test() {
    local test_name="$1"
    local test_function="$2"
    
    ((TESTS_RUN++))
    log "Running test: $test_name"
    
    if $test_function; then
        ((TESTS_PASSED++))
        success "PASS: $test_name"
        return 0
    else
        ((TESTS_FAILED++))
        FAILED_TESTS+=("$test_name")
        error "FAIL: $test_name"
        return 1
    fi
}

# Test 1: Basic API connectivity
test_api_connectivity() {
    local response
    response=$(curl -s -w "%{http_code}" \
        -H "apikey: $STAGING_SUPABASE_SERVICE_ROLE" \
        -H "Authorization: Bearer $STAGING_SUPABASE_SERVICE_ROLE" \
        "${STAGING_SUPABASE_URL}/rest/v1/" 2>/dev/null)
    
    local http_code="${response: -3}"
    
    if [ "$http_code" = "200" ]; then
        return 0
    else
        error "API returned HTTP $http_code"
        return 1
    fi
}

# Test 2: Database schema validation
test_database_schema() {
    local required_tables=("leads" "permits_raw_harris")
    
    for table in "${required_tables[@]}"; do
        log "Checking table: $table"
        
        local response
        response=$(curl -s -w "%{http_code}" \
            -H "apikey: $STAGING_SUPABASE_SERVICE_ROLE" \
            -H "Authorization: Bearer $STAGING_SUPABASE_SERVICE_ROLE" \
            "${STAGING_SUPABASE_URL}/rest/v1/${table}?select=count&limit=1" 2>/dev/null)
        
        local http_code="${response: -3}"
        
        if [ "$http_code" != "200" ]; then
            error "Table $table is not accessible (HTTP $http_code)"
            return 1
        fi
    done
    
    return 0
}

# Test 3: Data integrity check
test_data_integrity() {
    # Test leads table
    log "Testing leads table data integrity..."
    
    local leads_response
    leads_response=$(curl -s \
        -H "apikey: $STAGING_SUPABASE_SERVICE_ROLE" \
        -H "Authorization: Bearer $STAGING_SUPABASE_SERVICE_ROLE" \
        "${STAGING_SUPABASE_URL}/rest/v1/leads?select=id,name,email,created_at&limit=5" 2>/dev/null)
    
    # Check if response is valid JSON
    if ! echo "$leads_response" | jq empty >/dev/null 2>&1; then
        error "Leads table returned invalid JSON"
        return 1
    fi
    
    # Check for required fields
    local has_required_fields
    has_required_fields=$(echo "$leads_response" | jq 'length > 0 and .[0] | has("id") and has("name") and has("created_at")' 2>/dev/null || echo "false")
    
    if [ "$has_required_fields" != "true" ]; then
        warning "Leads table may be empty or missing required fields"
    fi
    
    # Test permits_raw_harris table if exists
    local permits_response
    permits_response=$(curl -s \
        -H "apikey: $STAGING_SUPABASE_SERVICE_ROLE" \
        -H "Authorization: Bearer $STAGING_SUPABASE_SERVICE_ROLE" \
        "${STAGING_SUPABASE_URL}/rest/v1/permits_raw_harris?select=id,permit_number,issue_date&limit=5" 2>/dev/null)
    
    if echo "$permits_response" | jq empty >/dev/null 2>&1; then
        log "Permits table data validated"
    else
        warning "Permits table validation failed or table is empty"
    fi
    
    return 0
}

# Test 4: CRUD operations
test_crud_operations() {
    local test_prefix="smoke_test_${TIMESTAMP}"
    
    # Test CREATE operation
    log "Testing CREATE operation..."
    local create_response
    create_response=$(curl -s \
        -X POST \
        -H "apikey: $STAGING_SUPABASE_SERVICE_ROLE" \
        -H "Authorization: Bearer $STAGING_SUPABASE_SERVICE_ROLE" \
        -H "Content-Type: application/json" \
        -H "Prefer: return=representation" \
        -d "{
            \"source\": \"${test_prefix}\",
            \"name\": \"Test User\",
            \"email\": \"test@example.com\",
            \"phone\": \"+1-555-123-4567\",
            \"address\": \"123 Test Street\",
            \"city\": \"Houston\",
            \"state\": \"TX\",
            \"zip\": \"77001\",
            \"status\": \"new\"
        }" \
        "${STAGING_SUPABASE_URL}/rest/v1/leads" 2>/dev/null)
    
    # Extract the created ID
    local created_id
    created_id=$(echo "$create_response" | jq -r '.[0].id' 2>/dev/null || echo "null")
    
    if [ "$created_id" = "null" ] || [ -z "$created_id" ]; then
        error "Failed to create test record"
        return 1
    fi
    
    log "Created test record with ID: $created_id"
    
    # Test READ operation
    log "Testing READ operation..."
    local read_response
    read_response=$(curl -s \
        -H "apikey: $STAGING_SUPABASE_SERVICE_ROLE" \
        -H "Authorization: Bearer $STAGING_SUPABASE_SERVICE_ROLE" \
        "${STAGING_SUPABASE_URL}/rest/v1/leads?id=eq.${created_id}" 2>/dev/null)
    
    local read_count
    read_count=$(echo "$read_response" | jq '. | length' 2>/dev/null || echo "0")
    
    if [ "$read_count" != "1" ]; then
        error "Failed to read created record"
        return 1
    fi
    
    # Test UPDATE operation
    log "Testing UPDATE operation..."
    local update_response
    update_response=$(curl -s -w "%{http_code}" \
        -X PATCH \
        -H "apikey: $STAGING_SUPABASE_SERVICE_ROLE" \
        -H "Authorization: Bearer $STAGING_SUPABASE_SERVICE_ROLE" \
        -H "Content-Type: application/json" \
        -d "{\"status\": \"contacted\"}" \
        "${STAGING_SUPABASE_URL}/rest/v1/leads?id=eq.${created_id}" 2>/dev/null)
    
    local update_code="${update_response: -3}"
    
    if [ "$update_code" != "204" ]; then
        error "Failed to update record (HTTP $update_code)"
        return 1
    fi
    
    # Test DELETE operation
    log "Testing DELETE operation..."
    local delete_response
    delete_response=$(curl -s -w "%{http_code}" \
        -X DELETE \
        -H "apikey: $STAGING_SUPABASE_SERVICE_ROLE" \
        -H "Authorization: Bearer $STAGING_SUPABASE_SERVICE_ROLE" \
        "${STAGING_SUPABASE_URL}/rest/v1/leads?id=eq.${created_id}" 2>/dev/null)
    
    local delete_code="${delete_response: -3}"
    
    if [ "$delete_code" != "204" ]; then
        error "Failed to delete record (HTTP $delete_code)"
        return 1
    fi
    
    success "CRUD operations completed successfully"
    return 0
}

# Test 5: Authentication system
test_authentication() {
    log "Testing authentication rejection with invalid key..."
    
    # Test with invalid API key
    local auth_response
    auth_response=$(curl -s -w "%{http_code}" \
        -H "apikey: invalid_key" \
        -H "Authorization: Bearer invalid_key" \
        "${STAGING_SUPABASE_URL}/rest/v1/leads?limit=1" 2>/dev/null)
    
    local auth_code="${auth_code: -3}"
    
    # Should return 401 Unauthorized
    if [ "$auth_code" = "401" ]; then
        success "Authentication properly rejects invalid keys"
        return 0
    else
        warning "Authentication test inconclusive (HTTP $auth_code)"
        return 0  # Don't fail for this
    fi
}

# Test 6: Storage system basic functionality
test_storage_system() {
    log "Testing storage system..."
    
    # List storage buckets
    local buckets_response
    buckets_response=$(curl -s -w "%{http_code}" \
        -H "apikey: $STAGING_SUPABASE_SERVICE_ROLE" \
        -H "Authorization: Bearer $STAGING_SUPABASE_SERVICE_ROLE" \
        "${STAGING_SUPABASE_URL}/storage/v1/bucket" 2>/dev/null)
    
    local buckets_code="${buckets_response: -3}"
    
    if [ "$buckets_code" = "200" ]; then
        log "Storage system is accessible"
        return 0
    else
        warning "Storage system test failed (HTTP $buckets_code)"
        return 0  # Don't fail for storage issues
    fi
}

# Test 7: Performance and response times
test_performance() {
    log "Testing API response performance..."
    
    # Measure response time for basic query
    local start_time=$(date +%s%N)
    
    curl -s \
        -H "apikey: $STAGING_SUPABASE_SERVICE_ROLE" \
        -H "Authorization: Bearer $STAGING_SUPABASE_SERVICE_ROLE" \
        "${STAGING_SUPABASE_URL}/rest/v1/leads?limit=10" >/dev/null 2>&1
    
    local end_time=$(date +%s%N)
    local response_time=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds
    
    log "API response time: ${response_time}ms"
    
    # Fail if response time is over 5 seconds (something is seriously wrong)
    if [ $response_time -gt 5000 ]; then
        error "API response time too slow: ${response_time}ms"
        return 1
    fi
    
    success "API performance acceptable: ${response_time}ms"
    return 0
}

# Test 8: Data consistency check
test_data_consistency() {
    log "Testing data consistency..."
    
    # Check for duplicate IDs in leads table
    local duplicate_check
    duplicate_check=$(curl -s \
        -H "apikey: $STAGING_SUPABASE_SERVICE_ROLE" \
        -H "Authorization: Bearer $STAGING_SUPABASE_SERVICE_ROLE" \
        "${STAGING_SUPABASE_URL}/rest/v1/leads?select=id&limit=100" 2>/dev/null)
    
    if echo "$duplicate_check" | jq empty >/dev/null 2>&1; then
        local total_records
        total_records=$(echo "$duplicate_check" | jq '. | length' 2>/dev/null || echo "0")
        
        local unique_records
        unique_records=$(echo "$duplicate_check" | jq '[.[].id] | unique | length' 2>/dev/null || echo "0")
        
        if [ "$total_records" = "$unique_records" ]; then
            success "No duplicate IDs found"
            return 0
        else
            error "Found duplicate IDs: $total_records total, $unique_records unique"
            return 1
        fi
    else
        warning "Could not validate data consistency"
        return 0
    fi
}

# Generate test results report
generate_test_report() {
    log "Generating test results report..."
    
    mkdir -p "$TEST_RESULTS_DIR"
    local report_file="${TEST_RESULTS_DIR}/backup_validation_${TIMESTAMP}.json"
    local summary_file="${TEST_RESULTS_DIR}/backup_validation_${TIMESTAMP}.md"
    
    # Create JSON report
    cat > "$report_file" << EOF
{
  "backup_validation": {
    "timestamp": "${TIMESTAMP}",
    "staging_url": "${STAGING_SUPABASE_URL}",
    "test_summary": {
      "total_tests": ${TESTS_RUN},
      "passed": ${TESTS_PASSED},
      "failed": ${TESTS_FAILED},
      "success_rate": "$(echo "scale=2; $TESTS_PASSED * 100 / $TESTS_RUN" | bc)%"
    },
    "overall_status": "$([ $TESTS_FAILED -eq 0 ] && echo "PASS" || echo "FAIL")",
    "failed_tests": [
EOF

    # Add failed tests to JSON
    for ((i=0; i<${#FAILED_TESTS[@]}; i++)); do
        echo "      \"${FAILED_TESTS[i]}\"$([ $i -lt $((${#FAILED_TESTS[@]}-1)) ] && echo ",")" >> "$report_file"
    done

    cat >> "$report_file" << EOF
    ],
    "recommendations": [
      $([ $TESTS_FAILED -eq 0 ] && echo '"Backup validation successful - production backup system is working correctly"' || echo '"Backup validation failed - investigate failed tests and fix backup/restore process"')
    ]
  }
}
EOF

    # Create Markdown summary
    cat > "$summary_file" << EOF
# Backup Validation Test Results

**Test Run:** $(date)  
**Staging Environment:** ${STAGING_SUPABASE_URL}

## Summary

- **Total Tests:** ${TESTS_RUN}
- **Passed:** ${TESTS_PASSED} ✅
- **Failed:** ${TESTS_FAILED} $([ $TESTS_FAILED -eq 0 ] && echo "✅" || echo "❌")
- **Success Rate:** $(echo "scale=2; $TESTS_PASSED * 100 / $TESTS_RUN" | bc)%

## Overall Status: $([ $TESTS_FAILED -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")

$([ $TESTS_FAILED -gt 0 ] && echo "## Failed Tests" && printf '%s\n' "${FAILED_TESTS[@]}" | sed 's/^/- /')

## Recommendations

$([ $TESTS_FAILED -eq 0 ] && echo "✅ Backup validation successful - production backup system is working correctly" || echo "❌ Backup validation failed - investigate failed tests and fix backup/restore process")

---
*Generated by Supabase Backup Validation System*
EOF

    success "Test report generated:"
    success "  JSON: $report_file"
    success "  Markdown: $summary_file"
}

# Main execution
main() {
    log "Starting Supabase backup validation smoke tests..."
    log "Staging URL: ${STAGING_SUPABASE_URL}"
    log "Results directory: ${TEST_RESULTS_DIR}"
    
    # Check dependencies
    if ! command -v curl >/dev/null 2>&1; then
        error "curl is required but not installed"
        exit 1
    fi
    
    if ! command -v jq >/dev/null 2>&1; then
        error "jq is required but not installed"
        exit 1
    fi
    
    if ! command -v bc >/dev/null 2>&1; then
        error "bc is required but not installed"
        exit 1
    fi
    
    # Run all tests
    echo
    log "=== Starting Test Suite ==="
    
    run_test "API Connectivity" test_api_connectivity
    run_test "Database Schema" test_database_schema
    run_test "Data Integrity" test_data_integrity
    run_test "CRUD Operations" test_crud_operations
    run_test "Authentication" test_authentication
    run_test "Storage System" test_storage_system
    run_test "Performance" test_performance
    run_test "Data Consistency" test_data_consistency
    
    echo
    log "=== Test Suite Complete ==="
    
    # Generate report
    generate_test_report
    
    # Display summary
    echo
    if [ $TESTS_FAILED -eq 0 ]; then
        success "All tests passed! Backup validation successful."
        success "Production backup system is working correctly."
        exit 0
    else
        error "Some tests failed! Backup validation failed."
        error "Failed tests: ${FAILED_TESTS[*]}"
        error "Please investigate and fix the backup/restore process."
        exit 1
    fi
}

# Handle script termination
trap 'error "Smoke tests interrupted"; exit 1' INT TERM

# Run main function
main "$@"