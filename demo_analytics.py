#!/usr/bin/env python3
"""
Demo script showing analytics tracking functionality.

This script demonstrates how to use the analytics service to track
cancellation and reactivation events.
"""

import os
import sys
import time

# Add the backend app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'app'))

from utils.analytics import (
    AnalyticsConfig,
    AnalyticsService,
    track_cancellation_event,
    track_reactivation_event
)


def demo_analytics_tracking():
    """Demonstrate analytics tracking functionality."""
    print("Analytics Tracking Demo")
    print("=" * 50)
    
    # Show current configuration
    config = AnalyticsConfig.from_env()
    print(f"Analytics Provider: {config.provider}")
    print(f"API Key configured: {'Yes' if config.api_key else 'No'}")
    print(f"Analytics enabled: {config.is_enabled()}")
    print()
    
    # Test cancellation tracking
    print("1. Testing Cancellation Event Tracking")
    print("-" * 40)
    
    success = track_cancellation_event(
        account_id='demo_account_123',
        user_id='demo_user_123',
        cancellation_reason='demo_test',
        subscription_type='premium',
        event_type='user_intent'
    )
    
    print(f"Cancellation event tracked: {'✓' if success else '✗'}")
    time.sleep(1)
    
    # Test reactivation tracking
    print("\n2. Testing Reactivation Event Tracking")
    print("-" * 40)
    
    success = track_reactivation_event(
        account_id='demo_account_123',
        user_id='demo_user_123',
        reactivation_source='demo_script',
        subscription_type='premium',
        event_type='system_driven'
    )
    
    print(f"Reactivation event tracked: {'✓' if success else '✗'}")
    time.sleep(1)
    
    # Test custom event tracking
    print("\n3. Testing Custom Event Tracking")
    print("-" * 40)
    
    analytics = AnalyticsService()
    success = analytics.track_event(
        event_name='demo_custom_event',
        event_type='user_intent',
        account_id='demo_account_123',
        user_id='demo_user_123',
        properties={
            'demo_property': 'test_value',
            'script_version': '1.0',
            'timestamp': time.time()
        }
    )
    
    print(f"Custom event tracked: {'✓' if success else '✗'}")
    
    print("\n" + "=" * 50)
    print("Demo completed successfully!")
    print("\nTo enable analytics tracking:")
    print("1. Set ANALYTICS_PROVIDER in your .env file")
    print("2. Set ANALYTICS_API_KEY in your .env file")
    print("3. Install the appropriate analytics library")
    print("\nExample:")
    print("  ANALYTICS_PROVIDER=posthog")
    print("  ANALYTICS_API_KEY=your_api_key_here")


if __name__ == '__main__':
    demo_analytics_tracking()