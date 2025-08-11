#!/bin/bash

# Integration Test for Supabase Backup Validation System
# This script tests the backup validation system components without requiring
# real Supabase credentials by using mock/dry-run modes.

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_OUTPUT_DIR="${SCRIPT_DIR}/../test-output"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

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
        error "FAIL: $test_name"
        return 1
    fi
}

# Test 1: Script files exist and are executable
test_script_files() {
    local scripts=(
        "scripts/supabase-backup-export.sh"
        "scripts/supabase-staging-restore.sh"
        "scripts/supabase-backup-smoke-tests.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [ ! -f "$script" ]; then
            error "Script not found: $script"
            return 1
        fi
        
        if [ ! -x "$script" ]; then
            error "Script not executable: $script"
            return 1
        fi
    done
    
    return 0
}

# Test 2: Scripts show help when requested
test_help_options() {
    # Test backup export script help
    if ! ./scripts/supabase-backup-export.sh --help >/dev/null 2>&1; then
        error "Backup export script help failed"
        return 1
    fi
    
    # Test staging restore script help  
    if ! ./scripts/supabase-staging-restore.sh --help >/dev/null 2>&1; then
        error "Staging restore script help failed"
        return 1
    fi
    
    return 0
}

# Test 3: Dry run mode works for backup export
test_dry_run_mode() {
    if ! ./scripts/supabase-backup-export.sh --dry-run >/dev/null 2>&1; then
        error "Backup export dry run failed"
        return 1
    fi
    
    return 0
}

# Test 4: Required system dependencies are available
test_system_dependencies() {
    local required_commands=("curl" "jq" "bc")
    
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            error "Required command not found: $cmd"
            return 1
        fi
    done
    
    # Optional but recommended commands
    local optional_commands=("pg_dump" "psql")
    for cmd in "${optional_commands[@]}"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            warning "Optional command not found: $cmd (needed for full functionality)"
        fi
    done
    
    return 0
}

# Test 5: GitHub Actions workflow is valid YAML
test_workflow_yaml() {
    local workflow_file=".github/workflows/monthly-backup-validation.yml"
    
    if [ ! -f "$workflow_file" ]; then
        error "Workflow file not found: $workflow_file"
        return 1
    fi
    
    # Test YAML syntax
    if ! python -c "import yaml; yaml.safe_load(open('$workflow_file'))" 2>/dev/null; then
        error "Workflow YAML syntax is invalid"
        return 1
    fi
    
    return 0
}

# Test 6: Documentation exists
test_documentation() {
    local doc_file="docs/BACKUP_VALIDATION.md"
    
    if [ ! -f "$doc_file" ]; then
        error "Documentation file not found: $doc_file"
        return 1
    fi
    
    # Check that documentation contains key sections
    local required_sections=(
        "Purpose"
        "Architecture" 
        "Setup Instructions"
        "Troubleshooting"
    )
    
    for section in "${required_sections[@]}"; do
        if ! grep -q "$section" "$doc_file"; then
            error "Documentation missing section: $section"
            return 1
        fi
    done
    
    return 0
}

# Test 7: Scripts handle missing environment variables gracefully
test_environment_validation() {
    # Test that scripts properly check for required environment variables
    
    # Backup export should fail without env vars (when not in dry-run mode)
    if ./scripts/supabase-backup-export.sh 2>/dev/null; then
        error "Backup export should fail without environment variables"
        return 1
    fi
    
    # Staging restore should fail without env vars
    if ./scripts/supabase-staging-restore.sh 2>/dev/null; then
        error "Staging restore should fail without environment variables"
        return 1
    fi
    
    return 0
}

# Test 8: Create mock directories and files to simulate workflow
test_mock_workflow() {
    mkdir -p "$TEST_OUTPUT_DIR"
    
    # Create a mock backup manifest to test parsing logic
    cat > "$TEST_OUTPUT_DIR/test_manifest.json" << 'EOF'
{
  "backup_name": "test_backup_20240101_120000",
  "timestamp": "20240101_120000",
  "supabase_url": "https://test.supabase.co",
  "created_at": "2024-01-01T12:00:00.000Z",
  "backup_type": "validation",
  "purpose": "Integration test",
  "files": {
    "schema": "schema.sql",
    "data": "data.sql"
  }
}
EOF
    
    # Validate that our test JSON is valid
    if ! jq empty "$TEST_OUTPUT_DIR/test_manifest.json" >/dev/null 2>&1; then
        error "Test manifest JSON is invalid"
        return 1
    fi
    
    return 0
}

# Generate test report
generate_test_report() {
    log "Generating integration test report..."
    
    mkdir -p "$TEST_OUTPUT_DIR"
    local report_file="${TEST_OUTPUT_DIR}/integration_test_results.md"
    
    cat > "$report_file" << EOF
# Supabase Backup Validation System - Integration Test Results

**Test Run:** $(date)  
**Test Environment:** Local development

## Summary

- **Total Tests:** ${TESTS_RUN}
- **Passed:** ${TESTS_PASSED} ✅
- **Failed:** ${TESTS_FAILED} $([ $TESTS_FAILED -eq 0 ] && echo "✅" || echo "❌")
- **Success Rate:** $(echo "scale=2; $TESTS_PASSED * 100 / $TESTS_RUN" | bc 2>/dev/null || echo "N/A")%

## Overall Status: $([ $TESTS_FAILED -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")

## Test Details

1. **Script Files** - Verify all scripts exist and are executable
2. **Help Options** - Test that scripts show help when requested
3. **Dry Run Mode** - Verify backup export dry-run functionality
4. **System Dependencies** - Check required commands are available
5. **Workflow YAML** - Validate GitHub Actions workflow syntax
6. **Documentation** - Verify documentation completeness
7. **Environment Validation** - Test error handling for missing env vars
8. **Mock Workflow** - Simulate backup workflow components

## Recommendations

$([ $TESTS_FAILED -eq 0 ] && echo "✅ All integration tests passed. The backup validation system is ready for deployment." || echo "❌ Some integration tests failed. Please fix the issues before deployment.")

## Next Steps

1. Set up staging Supabase instance
2. Configure GitHub repository secrets
3. Test with real Supabase credentials
4. Schedule first monthly validation run

---
*Generated by Backup Validation Integration Test*
EOF

    success "Integration test report generated: $report_file"
}

# Main execution
main() {
    log "Starting Supabase Backup Validation System Integration Tests..."
    
    # Run all tests
    echo
    log "=== Integration Test Suite ==="
    
    run_test "Script Files" test_script_files
    run_test "Help Options" test_help_options
    run_test "Dry Run Mode" test_dry_run_mode
    run_test "System Dependencies" test_system_dependencies
    run_test "Workflow YAML" test_workflow_yaml
    run_test "Documentation" test_documentation
    run_test "Environment Validation" test_environment_validation
    run_test "Mock Workflow" test_mock_workflow
    
    echo
    log "=== Integration Test Suite Complete ==="
    
    # Generate report
    generate_test_report
    
    # Display summary
    echo
    if [ $TESTS_FAILED -eq 0 ]; then
        success "All integration tests passed!"
        success "The Supabase Backup Validation System is ready for deployment."
        log "See test results in: $TEST_OUTPUT_DIR/integration_test_results.md"
        exit 0
    else
        error "Some integration tests failed!"
        error "Please fix the issues before deployment."
        exit 1
    fi
}

# Handle script termination
trap 'error "Integration tests interrupted"; exit 1' INT TERM

# Change to repository root
cd "$(dirname "$0")/.."

# Run main function
main "$@"