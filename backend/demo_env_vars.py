#!/usr/bin/env python3
"""
Demonstration script for the new environment variable functionality.

This script shows how the ALLOW_EXPORTS, REDIS_URL, SENDGRID_API_KEY,
TWILIO_SID, TWILIO_TOKEN, and TWILIO_FROM environment variables are used
in the Home Services Lead Generation application.
"""

import os
import sys
import logging

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from utils.export_control import get_export_controller, ExportType
from utils.notifications import get_notification_service
from utils.cache import get_cache_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_export_control():
    """Demonstrate export control functionality."""
    print("\n" + "="*60)
    print("EXPORT CONTROL DEMONSTRATION")
    print("="*60)
    
    controller = get_export_controller()
    
    print(f"Current ALLOW_EXPORTS setting: {os.getenv('ALLOW_EXPORTS', 'not set')}")
    print(f"Exports enabled: {controller.exports_allowed}")
    
    # Test different export types
    export_types = [ExportType.LEADS, ExportType.PERMITS, ExportType.ANALYTICS]
    
    for export_type in export_types:
        allowed, reason = controller.is_export_allowed(export_type, 'demo_user')
        status = "✅ ALLOWED" if allowed else "❌ BLOCKED"
        print(f"{export_type.value:15} -> {status}")
        if reason:
            print(f"                   Reason: {reason}")
    
    # Demonstrate export request processing
    print("\nProcessing export request...")
    request = controller.create_export_request(
        ExportType.LEADS,
        'demo_user',
        {'format': 'csv', 'date_range': '30_days'}
    )
    
    result = controller.process_export_request(request)
    print(f"Export ID: {result.export_id}")
    print(f"Success: {result.success}")
    print(f"Allowed: {result.allowed}")
    if result.reason:
        print(f"Reason: {result.reason}")


def demo_notifications():
    """Demonstrate notification functionality."""
    print("\n" + "="*60)
    print("NOTIFICATION SERVICES DEMONSTRATION")
    print("="*60)
    
    service = get_notification_service()
    
    print(f"SendGrid API Key: {'✅ Set' if service.config.sendgrid_api_key else '❌ Not set'}")
    print(f"Twilio SID: {'✅ Set' if service.config.twilio_sid else '❌ Not set'}")
    print(f"Twilio Token: {'✅ Set' if service.config.twilio_token else '❌ Not set'}")
    print(f"Twilio From: {'✅ Set' if service.config.twilio_from else '❌ Not set'}")
    
    print(f"Email notifications enabled: {service.email.is_enabled()}")
    print(f"SMS notifications enabled: {service.sms.is_enabled()}")
    
    # Test notification methods (won't actually send without libraries)
    print("\nTesting notification methods...")
    
    email_result = service.email.send_email(
        to_email="test@example.com",
        subject="Test Notification",
        content="This is a test email notification."
    )
    print(f"Email send result: {email_result}")
    
    sms_result = service.sms.send_sms(
        to_number="+1234567890",
        message="Test SMS notification"
    )
    print(f"SMS send result: {sms_result}")
    
    # Test unified notification
    notify_result = service.notify_lead_processed(
        lead_count=25,
        email_recipients=["admin@example.com"],
        sms_recipients=["+1234567890"]
    )
    print(f"Unified notification result: {notify_result}")


def demo_cache():
    """Demonstrate cache functionality."""
    print("\n" + "="*60)
    print("REDIS CACHE DEMONSTRATION")
    print("="*60)
    
    cache = get_cache_service()
    
    print(f"Redis URL: {cache.config.redis_url or 'not set'}")
    print(f"Cache enabled: {cache.is_enabled()}")
    print(f"Default TTL: {cache.config.default_ttl} seconds")
    
    # Test cache operations
    print("\nTesting cache operations...")
    
    test_data = {
        'lead_id': 123,
        'score': 85,
        'method': 'rules',
        'factors': {'recency': 25, 'trade_match': 20}
    }
    
    # Test basic operations
    set_result = cache.set('test_key', test_data, 300)
    print(f"Cache set result: {set_result}")
    
    get_result = cache.get('test_key')
    print(f"Cache get result: {get_result}")
    
    exists_result = cache.exists('test_key')
    print(f"Cache exists result: {exists_result}")
    
    # Test specialized cache methods
    score_cache_result = cache.cache_lead_scores(123, test_data)
    print(f"Lead scores cache result: {score_cache_result}")
    
    rate_limit_count = cache.increment_rate_limit('demo_user')
    print(f"Rate limit count: {rate_limit_count}")


def demo_environment_variables():
    """Show all relevant environment variables."""
    print("\n" + "="*60)
    print("ENVIRONMENT VARIABLES STATUS")
    print("="*60)
    
    required_vars = [
        'ALLOW_EXPORTS',
        'REDIS_URL',
        'SENDGRID_API_KEY',
        'TWILIO_SID',
        'TWILIO_TOKEN',
        'TWILIO_FROM'
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if var in ['SENDGRID_API_KEY', 'TWILIO_TOKEN']:
                display_value = value[:8] + '...' if len(value) > 8 else value
            else:
                display_value = value
            print(f"{var:20} = {display_value}")
        else:
            print(f"{var:20} = ❌ NOT SET")


def main():
    """Run all demonstrations."""
    print("HOME SERVICES LEAD GENERATION")
    print("Environment Variables Integration Demo")
    print("="*60)
    
    demo_environment_variables()
    demo_export_control()
    demo_notifications()
    demo_cache()
    
    print("\n" + "="*60)
    print("DEMO COMPLETED")
    print("="*60)
    print("\nTo enable all features, set these environment variables:")
    print("ALLOW_EXPORTS=true")
    print("REDIS_URL=redis://localhost:6379/0")
    print("SENDGRID_API_KEY=your_sendgrid_api_key")
    print("TWILIO_SID=your_twilio_account_sid")
    print("TWILIO_TOKEN=your_twilio_auth_token")
    print("TWILIO_FROM=+1234567890")
    print("\nNote: Some features require additional libraries to be installed:")
    print("- pip install redis (for caching)")
    print("- pip install sendgrid (for email notifications)")
    print("- pip install twilio (for SMS notifications)")


if __name__ == '__main__':
    main()