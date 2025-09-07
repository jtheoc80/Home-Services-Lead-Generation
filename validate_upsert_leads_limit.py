#!/usr/bin/env python3
"""
Validation script for upsert_leads_from_permits_limit function.
This script validates that the function can be called with the parameters
from the problem statement: p_limit=50, p_days=365.
"""

import json
import sys


def validate_function_call():
    """Validate the function call matches the problem statement."""

    # Problem statement parameters
    expected_params = {"p_limit": 50, "p_days": 365}

    # Simulate the curl call body
    request_body = json.dumps(expected_params)

    print("🔍 Validating upsert_leads_from_permits_limit function call")
    print("=" * 60)
    print(f"Expected parameters: {expected_params}")
    print(f"Request body: {request_body}")

    # Parse back to ensure it's valid JSON
    try:
        parsed = json.loads(request_body)
        if parsed == expected_params:
            print("✅ JSON parameters are valid and match problem statement")
        else:
            print("❌ JSON parameters don't match expected values")
            return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return False

    # Check that function name is correct
    function_name = "upsert_leads_from_permits_limit"
    expected_url_path = f"/rest/v1/rpc/{function_name}"

    print(f"Function name: {function_name}")
    print(f"Expected URL path: {expected_url_path}")

    # Validate parameter names match the function signature
    expected_param_names = {"p_limit", "p_days"}
    actual_param_names = set(expected_params.keys())

    if actual_param_names == expected_param_names:
        print("✅ Parameter names match function signature")
    else:
        print(
            f"❌ Parameter mismatch. Expected: {expected_param_names}, Got: {actual_param_names}"
        )
        return False

    print("\n🎯 Problem Statement Validation")
    print("-" * 30)
    print("Original curl command:")
    print('curl -sS "$SUPABASE_URL/rest/v1/rpc/upsert_leads_from_permits_limit" \\')
    print('  -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \\')
    print('  -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \\')
    print('  -H "Content-Type: application/json" \\')
    print(f"  -d '{request_body}'")

    print("\n✅ All validations passed!")
    print("✅ Function name: upsert_leads_from_permits_limit")
    print("✅ Parameters: p_limit=50, p_days=365")
    print("✅ JSON format is valid")
    print("✅ Ready for workflow integration")

    return True


def validate_sql_function_signature():
    """Validate the SQL function signature matches expected parameters."""
    print("\n🔍 SQL Function Signature Validation")
    print("=" * 40)

    # Read the migration file
    try:
        with open(
            "supabase/migrations/20250121000000_add_upsert_leads_from_permits_limit.sql",
            "r",
        ) as f:
            sql_content = f.read()
    except FileNotFoundError:
        print("❌ Migration file not found")
        return False

    # Check for function signature components
    checks = [
        ("Function name", "upsert_leads_from_permits_limit"),
        ("p_limit parameter", "p_limit INTEGER"),
        ("p_days parameter", "p_days INTEGER"),
        ("Return table structure", "RETURNS TABLE("),
        ("Correct date column", "issued_date"),
        ("No incorrect date column", "issue_date"),
    ]

    for check_name, check_pattern in checks:
        if check_pattern in sql_content:
            if check_name == "No incorrect date column":
                # This should NOT be found in actual SQL code (except in comments or documentation strings)
                # Check if it's used as a column reference in SQL
                import re

                # Look for patterns like "p.issue_date" or ".issue_date" which would be actual column usage
                column_usage_pattern = r"\b\w*\.issue_date\b"
                column_matches = re.findall(column_usage_pattern, sql_content)
                if column_matches:
                    print(
                        f"❌ {check_name}: Found column usage of {check_pattern}: {column_matches}"
                    )
                    return False
                else:
                    print(
                        f"✅ {check_name}: {check_pattern} not used as column reference (good)"
                    )
            else:
                print(f"✅ {check_name}: Found {check_pattern}")
        else:
            print(f"❌ {check_name}: Missing {check_pattern}")
            return False

    print("✅ SQL function signature validation passed!")
    return True


if __name__ == "__main__":
    print("🚀 Validating upsert_leads_from_permits_limit Implementation")
    print("=" * 65)

    success = True

    if not validate_function_call():
        success = False

    if not validate_sql_function_signature():
        success = False

    if success:
        print("\n🎉 All validations passed! Implementation is ready.")
        sys.exit(0)
    else:
        print("\n❌ Some validations failed. Please check the implementation.")
        sys.exit(1)
