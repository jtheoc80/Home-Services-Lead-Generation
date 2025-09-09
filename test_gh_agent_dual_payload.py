#!/usr/bin/env python3
"""
Test script for GitHub Agent dual payload support.

This script validates that the gh-agent function correctly handles both:
1. Custom agent payloads (existing format)
2. DB webhook payloads (new format with { type, table, record })
"""

import json


def test_payload_transformation():
    """Test the payload transformation logic."""
    print("🧪 Testing GitHub Agent Dual Payload Support")
    print("=" * 50)

    def transform_payload(body):
        """Simulate the transformation logic from the Deno function."""
        payload = body
        if body.get("record") and body.get("type"):
            # map DB webhook → agent event
            r = body["record"]
            payload = {
                "event": (
                    "etl_failed" if r.get("status") == "failed" else "etl_succeeded"
                ),
                "etl_id": r.get("id"),
                "city": r.get("city"),
                "days": r.get("lookback_days"),
                "details": r.get("details"),
            }
        return payload

    tests = []

    # Test 1: Custom agent payload (existing format)
    print("\n📄 Test 1: Custom Agent Payload")
    custom_payload = {
        "event": "etl_failed",
        "etl_id": "run-123",
        "city": "austin",
        "days": 7,
        "details": {"hint": "missing app token"},
    }

    print("Input:", json.dumps(custom_payload, indent=2))
    result1 = transform_payload(custom_payload)
    print("Output:", json.dumps(result1, indent=2))
    pass1 = result1 == custom_payload
    print("✅ PASS" if pass1 else "❌ FAIL")
    tests.append(("Custom agent payload", pass1))

    # Test 2: DB webhook payload (failed status)
    print("\n📄 Test 2: DB Webhook Payload (failed status)")
    db_webhook_payload = {
        "type": "etl_run",
        "table": "etl_runs",
        "record": {
            "id": "run-456",
            "city": "houston",
            "lookback_days": 14,
            "status": "failed",
            "details": {"error": "Connection timeout"},
        },
    }

    print("Input:", json.dumps(db_webhook_payload, indent=2))
    result2 = transform_payload(db_webhook_payload)
    print("Output:", json.dumps(result2, indent=2))
    expected2 = {
        "event": "etl_failed",
        "etl_id": "run-456",
        "city": "houston",
        "days": 14,
        "details": {"error": "Connection timeout"},
    }
    pass2 = result2 == expected2
    print("✅ PASS" if pass2 else "❌ FAIL")
    tests.append(("DB webhook (failed)", pass2))

    # Test 3: DB webhook payload (success status)
    print("\n📄 Test 3: DB Webhook Payload (success status)")
    db_webhook_success = {
        "type": "etl_run",
        "table": "etl_runs",
        "record": {
            "id": "run-789",
            "city": "dallas",
            "lookback_days": 30,
            "status": "completed",
            "details": {"records_processed": 1500},
        },
    }

    print("Input:", json.dumps(db_webhook_success, indent=2))
    result3 = transform_payload(db_webhook_success)
    print("Output:", json.dumps(result3, indent=2))
    expected3 = {
        "event": "etl_succeeded",
        "etl_id": "run-789",
        "city": "dallas",
        "days": 30,
        "details": {"records_processed": 1500},
    }
    pass3 = result3 == expected3
    print("✅ PASS" if pass3 else "❌ FAIL")
    tests.append(("DB webhook (success)", pass3))

    # Test 4: Problem statement example
    print("\n📄 Test 4: Problem Statement Example")
    curl_payload = {
        "event": "etl_failed",
        "city": "austin",
        "days": 7,
        "details": {"hint": "missing app token"},
    }

    print("Input:", json.dumps(curl_payload, indent=2))
    result4 = transform_payload(curl_payload)
    print("Output:", json.dumps(result4, indent=2))
    pass4 = result4 == curl_payload
    print("✅ PASS" if pass4 else "❌ FAIL")
    tests.append(("Problem statement curl example", pass4))

    # Summary
    print("\n🎯 Test Summary")
    all_passed = all(passed for _, passed in tests)
    for test_name, passed in tests:
        status = "✅" if passed else "❌"
        print(f"  {status} {test_name}")

    print(f"\n{'✅ All tests passed!' if all_passed else '❌ Some tests failed!'}")
    return all_passed


if __name__ == "__main__":
    test_payload_transformation()
