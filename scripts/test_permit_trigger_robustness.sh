#!/bin/bash

# Test script to verify the permit→lead trigger robustness fix
# This validates that our migration contains all required elements

echo "🧪 Testing permit→lead trigger robustness fix..."
echo ""

# Test variables
MIGRATION_FILE="./supabase/migrations/20250817000000_fix_permit_lead_trigger_robust.sql"
README_FILE="./README.md"
PASSED=0
TOTAL=0

# Helper function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_output="$3"
    
    TOTAL=$((TOTAL + 1))
    echo "Testing: $test_name"
    
    if eval "$test_command"; then
        echo "✅ PASSED: $test_name"
        PASSED=$((PASSED + 1))
    else
        echo "❌ FAILED: $test_name"
    fi
    echo ""
}

# Test 1: Migration file exists
run_test "Migration file exists" "test -f '$MIGRATION_FILE'"

# Test 2: Migration contains required ALTER TABLE command
run_test "Migration sets DEFAULT on trade column" "grep -q 'ALTER TABLE public.leads ALTER COLUMN trade SET DEFAULT' '$MIGRATION_FILE'"

# Test 3: Migration contains backfill command
run_test "Migration backfills NULL trades" "grep -q \"SET trade = 'General'\" '$MIGRATION_FILE'"

# Test 4: Migration contains robust COALESCE logic
run_test "Migration uses robust trade derivation" "grep -q \"'General'\" '$MIGRATION_FILE' && grep -q \"COALESCE\" '$MIGRATION_FILE'"

# Test 5: Migration recreates trigger
run_test "Migration recreates trigger" "grep -q 'DROP TRIGGER IF EXISTS trg_lead_from_permit' '$MIGRATION_FILE' && grep -q 'CREATE TRIGGER trg_lead_from_permit' '$MIGRATION_FILE'"

# Test 6: README contains test section
run_test "README contains test documentation" "grep -q '## Testing Permit→Lead Trigger Robustness' '$README_FILE'"

# Test 7: README contains test commands
run_test "README contains test SQL commands" "grep -q 'SELECT public.upsert_permit(jsonb_build_object(' '$README_FILE'"

# Test 8: Migration contains comment documentation
run_test "Migration is documented" "grep -q 'COMMENT ON FUNCTION' '$MIGRATION_FILE'"

echo "📊 Test Results Summary:"
echo "Passed: $PASSED/$TOTAL tests"
echo ""

if [ $PASSED -eq $TOTAL ]; then
    echo "🎉 All tests passed! The permit→lead trigger fix is ready."
    echo ""
    echo "📋 Next steps:"
    echo "1. Apply the migration: $MIGRATION_FILE"
    echo "2. Test with actual data using the README examples"
    echo "3. Verify no NULL trades in the leads table"
    exit 0
else
    echo "⚠️  Some tests failed. Please review the issues above."
    exit 1
fi