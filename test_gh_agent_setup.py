#!/usr/bin/env python3
"""
Test script for GitHub Agent outbox functionality.

This script validates that the outbox infrastructure is set up correctly
and tests the trigger functionality.
"""

import json
from datetime import datetime


def test_outbox_setup():
    """Test that the outbox infrastructure is properly set up."""
    print("🧪 Testing GitHub Agent Outbox Setup")
    print("=" * 50)

    # This is a dry-run test - in a real environment, you'd connect to Supabase
    # and run these queries to validate the setup

    test_queries = [
        "SELECT COUNT(*) FROM public.event_outbox;",
        "SELECT * FROM public.get_pending_events_count();",
        "SELECT routine_name FROM information_schema.routines WHERE routine_name IN ('enqueue_permit_event', 'enqueue_lead_event');",
        "SELECT trigger_name FROM information_schema.triggers WHERE trigger_name IN ('trg_enqueue_permit', 'trg_enqueue_lead');",
    ]

    print("📋 Queries to run in Supabase SQL Editor:")
    print()
    for i, query in enumerate(test_queries, 1):
        print(f"{i}. {query}")
    print()

    # Simulate test event data
    test_permit_event = {
        "type": "permit.created",
        "payload": {
            "permit_id": "TEST-001",
            "address": "123 Test St",
            "city": "Test City",
            "county": "Test County",
            "permit_type": "Building",
            "status": "Issued",
            "valuation": 150000,
        },
        "created_at": datetime.now().isoformat(),
    }

    test_lead_event = {
        "type": "lead.created",
        "payload": {
            "name": "Test Lead",
            "email": "test@example.com",
            "phone": "+1-555-0100",
            "source": "manual",
            "status": "new",
        },
        "created_at": datetime.now().isoformat(),
    }

    print("📄 Example Event Payloads:")
    print()
    print("Permit Event:")
    print(json.dumps(test_permit_event, indent=2))
    print()
    print("Lead Event:")
    print(json.dumps(test_lead_event, indent=2))
    print()

    print("✅ Test script completed")
    print("💡 Next steps:")
    print("   1. Run the SQL setup script in Supabase")
    print("   2. Deploy the Edge Function")
    print("   3. Configure GitHub Actions workflow")
    print("   4. Test with real data insertions")


if __name__ == "__main__":
    test_outbox_setup()
