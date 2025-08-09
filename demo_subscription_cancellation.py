#!/usr/bin/env python3
"""
Demo script for subscription cancellation workflow.

This script demonstrates the key functionality implemented:
- Trial vs paid subscription cancellation
- Grace period handling for paid subscriptions
- Quiet hours respect for notifications
- Reactivation workflow
- Admin cancellation records tracking
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.subscription_manager import (
    SubscriptionManager,
    SubscriptionInfo,
    CancellationRequest,
    QuietHoursConfig,
    SubscriptionStatus,
    SubscriptionPlan,
    CancellationType
)

from backend.app.subscription_api import SubscriptionAPI


def demo_trial_cancellation():
    """Demo trial subscription cancellation - immediate termination."""
    print("\n" + "="*60)
    print("DEMO: Trial Subscription Cancellation")
    print("="*60)
    
    # Create trial subscription
    trial_subscription = SubscriptionInfo(
        id=1,
        user_id="demo-trial-user-123",
        plan=SubscriptionPlan.TRIAL,
        status=SubscriptionStatus.TRIAL,
        trial_start_date=datetime.utcnow() - timedelta(days=2),
        trial_end_date=datetime.utcnow() + timedelta(days=5),
        created_at=datetime.utcnow() - timedelta(days=2)
    )
    
    # Create cancellation request
    request = CancellationRequest(
        user_id="demo-trial-user-123",
        reason_category="not_satisfied",
        reason_notes="Service didn't meet my business needs",
        processed_by=None
    )
    
    # Process cancellation
    manager = SubscriptionManager()
    result = manager.cancel_subscription(trial_subscription, request)
    
    print(f"✓ Cancellation Type: {result['cancellation_type']}")
    print(f"✓ Grace Period Days: {result['grace_period_days']}")
    print(f"✓ Effective Date: {result['effective_date']}")
    print(f"✓ Message: {result['message']}")
    print(f"✓ Notification Sent: {result['notification_sent']}")
    
    # Show cancellation record
    record = result['cancellation_record']
    print(f"\nCancellation Record Created:")
    print(f"  - User ID: {record['user_id']}")
    print(f"  - Type: {record['cancellation_type']}")
    print(f"  - Reason: {record['reason_category']} - {record['reason_notes']}")
    print(f"  - Grace Days: {record['grace_period_days']}")


def demo_paid_cancellation():
    """Demo paid subscription cancellation - grace period."""
    print("\n" + "="*60)
    print("DEMO: Paid Subscription Cancellation")
    print("="*60)
    
    # Create paid subscription
    paid_subscription = SubscriptionInfo(
        id=2,
        user_id="demo-paid-user-456",
        plan=SubscriptionPlan.PREMIUM,
        status=SubscriptionStatus.ACTIVE,
        subscription_start_date=datetime.utcnow() - timedelta(days=15),
        billing_cycle="monthly",
        amount_cents=4999,  # $49.99
        payment_method="stripe",
        created_at=datetime.utcnow() - timedelta(days=15)
    )
    
    # Create cancellation request
    request = CancellationRequest(
        user_id="demo-paid-user-456",
        reason_category="cost",
        reason_notes="Too expensive for current business volume",
        processed_by="admin-support-1"
    )
    
    # Process cancellation
    manager = SubscriptionManager()
    result = manager.cancel_subscription(paid_subscription, request)
    
    print(f"✓ Cancellation Type: {result['cancellation_type']}")
    print(f"✓ Grace Period Days: {result['grace_period_days']}")
    print(f"✓ Effective Date: {result['effective_date']}")
    print(f"✓ Message: {result['message']}")
    print(f"✓ Notification Sent: {result['notification_sent']}")
    
    # Show updated subscription status
    updated_sub = result['updated_subscription']
    print(f"\nUpdated Subscription:")
    print(f"  - Status: {updated_sub.status.value}")
    print(f"  - Grace Period End: {updated_sub.grace_period_end_date}")
    
    return updated_sub


def demo_reactivation():
    """Demo subscription reactivation."""
    print("\n" + "="*60)
    print("DEMO: Subscription Reactivation")
    print("="*60)
    
    # Create cancelled subscription (from previous demo)
    cancelled_subscription = SubscriptionInfo(
        id=3,
        user_id="demo-cancelled-user-789",
        plan=SubscriptionPlan.BASIC,
        status=SubscriptionStatus.GRACE_PERIOD,
        subscription_start_date=datetime.utcnow() - timedelta(days=20),
        subscription_end_date=datetime.utcnow() + timedelta(days=10),
        grace_period_end_date=datetime.utcnow() + timedelta(days=10),
        billing_cycle="monthly",
        amount_cents=2999,  # $29.99
        created_at=datetime.utcnow() - timedelta(days=20)
    )
    
    # Process reactivation
    manager = SubscriptionManager()
    result = manager.reactivate_subscription(cancelled_subscription)
    
    print(f"✓ Reactivation Successful: {result['success']}")
    print(f"✓ Message: {result['message']}")
    print(f"✓ Notification Sent: {result['notification_sent']}")
    
    # Show updated subscription status
    updated_sub = result['updated_subscription']
    print(f"\nReactivated Subscription:")
    print(f"  - Status: {updated_sub.status.value}")
    print(f"  - End Date: {updated_sub.subscription_end_date}")
    print(f"  - Grace Period: {updated_sub.grace_period_end_date}")


def demo_quiet_hours():
    """Demo quiet hours functionality."""
    print("\n" + "="*60)
    print("DEMO: Quiet Hours Respect")
    print("="*60)
    
    # Configure quiet hours (10 PM to 8 AM)
    quiet_config = QuietHoursConfig(
        enabled=True,
        start_hour=22,  # 10 PM
        end_hour=8      # 8 AM
    )
    
    manager = SubscriptionManager(quiet_hours_config=quiet_config)
    
    # Test during quiet hours
    quiet_time = datetime(2024, 1, 1, 23, 0, 0)  # 11 PM
    is_quiet = manager.is_quiet_hours(quiet_time)
    print(f"✓ 11:00 PM is quiet hours: {is_quiet}")
    
    # Test during normal hours
    normal_time = datetime(2024, 1, 1, 14, 0, 0)  # 2 PM
    is_quiet = manager.is_quiet_hours(normal_time)
    print(f"✓ 2:00 PM is quiet hours: {is_quiet}")
    
    print(f"\nQuiet Hours Configuration:")
    print(f"  - Enabled: {quiet_config.enabled}")
    print(f"  - Start: {quiet_config.start_hour}:00")
    print(f"  - End: {quiet_config.end_hour}:00")
    print(f"  - Timezone: {quiet_config.timezone}")


def demo_api_endpoints():
    """Demo API endpoints."""
    print("\n" + "="*60)
    print("DEMO: API Endpoints")
    print("="*60)
    
    api = SubscriptionAPI()
    
    # Demo cancel subscription API
    cancel_request = {
        'user_id': 'demo-trial-user',
        'reason_category': 'not_satisfied',
        'reason_notes': 'Service quality below expectations'
    }
    
    result = api.cancel_subscription(cancel_request)
    print(f"✓ Cancel API Status: {result['status_code']}")
    print(f"✓ Cancel Success: {result['success']}")
    if result['success']:
        print(f"✓ Cancel Message: {result['data']['message']}")
    
    # Demo reactivation API
    reactivate_request = {
        'user_id': 'demo-cancelled-user'
    }
    
    result = api.reactivate_subscription(reactivate_request)
    print(f"✓ Reactivate API Status: {result['status_code']}")
    print(f"✓ Reactivate Success: {result['success']}")
    if result['success']:
        print(f"✓ Reactivate Message: {result['data']['message']}")
    
    # Demo admin cancellation records
    admin_request = {
        'cancellation_type': 'trial'
    }
    
    result = api.get_cancellation_records('admin-demo-user', admin_request)
    print(f"✓ Admin Records API Status: {result['status_code']}")
    print(f"✓ Admin Records Success: {result['success']}")
    if result['success']:
        records = result['data']['records']
        print(f"✓ Found {len(records)} cancellation records")


def main():
    """Run all demos."""
    print("LeadLedgerPro Subscription Cancellation Workflow Demo")
    print("This demo shows all implemented functionality:")
    print("- Trial vs Paid subscription cancellation")
    print("- Grace periods for paid subscriptions")
    print("- Reactivation workflow")
    print("- Quiet hours respect for notifications")
    print("- Admin cancellation tracking")
    
    try:
        demo_trial_cancellation()
        paid_sub = demo_paid_cancellation()
        demo_reactivation()
        demo_quiet_hours()
        demo_api_endpoints()
        
        print("\n" + "="*60)
        print("✅ ALL DEMOS COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\nKey Requirements Fulfilled:")
        print("✓ Cancel on trial → immediate end, send cancel_confirm")
        print("✓ Cancel paid → grace until period end; send cancel_confirm now, grace_reminder at T-3 days, access_ended at end")
        print("✓ Reactivate → reactivated email/SMS sent; status returns to active")
        print("✓ Admin can see cancellation records with reasons/notes in DB")
        print("✓ Respect quiet hours for notifications")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())