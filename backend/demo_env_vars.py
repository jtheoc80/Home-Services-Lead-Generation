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
from utils.launch_config import get_launch_manager
from utils.pricing_config import get_pricing_manager
from utils.schedule_config import get_schedule_manager

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
        'TWILIO_FROM',
        'LAUNCH_SCOPE',
        'DEFAULT_REGION',
        'REGISTRY_PATH',
        'CREDIT_OFFERS_JSON',
        'CRON_SCRAPE_UTC',
        'CRON_DIGEST_HOURLY',
        'CRON_DIGEST_DAILY'
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if var in ['SENDGRID_API_KEY', 'TWILIO_TOKEN']:
                display_value = value[:8] + '...' if len(value) > 8 else value
            elif var == 'CREDIT_OFFERS_JSON':
                # Show truncated JSON
                display_value = value[:50] + '...' if len(value) > 50 else value
            else:
                display_value = value
            print(f"{var:20} = {display_value}")
        else:
            print(f"{var:20} = ❌ NOT SET")


def demo_launch_config():
    """Demonstrate launch configuration functionality."""
    print("\n" + "="*60)
    print("LAUNCH CONFIGURATION DEMONSTRATION")
    print("="*60)
    
    manager = get_launch_manager()
    
    print(f"Launch Scope: {manager.get_active_scope()}")
    print(f"Default Region: {manager.get_default_region()}")
    print(f"Registry Path: {manager.get_registry_path()}")
    
    # Test region processing
    print("\nRegion Processing:")
    test_regions = ['tx-houston', 'tx-harris', 'tx-dallas', 'tx-austin']
    for region in test_regions:
        should_process = manager.should_process_region(region)
        status = "✅ PROCESS" if should_process else "❌ SKIP"
        print(f"  {region:15} -> {status}")
    
    # Show launch info
    info = manager.get_launch_info()
    print(f"\nConfiguration Valid: {info['is_valid']}")


def demo_pricing_config():
    """Demonstrate pricing configuration functionality."""
    print("\n" + "="*60)
    print("PRICING CONFIGURATION DEMONSTRATION") 
    print("="*60)
    
    manager = get_pricing_manager()
    
    # Show pricing summary
    summary = manager.get_pricing_summary()
    print(f"Available Tiers: {summary['total_tiers']}")
    print(f"Tier Names: {', '.join(summary['available_tiers'])}")
    
    print("\nPricing Details:")
    for tier, details in summary['offers'].items():
        if details:  # Handle None values
            print(f"  {tier.upper()}:")
            print(f"    Cost: ${details['usd']}")
            print(f"    Credits: {details['credits']}")
            print(f"    Cost per Credit: ${details['cost_per_credit']:.2f}")
            if details['savings_vs_oneoff'] > 0:
                print(f"    Savings vs One-off: {details['savings_vs_oneoff']:.1f}%")
    
    # Test recommendation
    print("\nRecommendation for 75 credits needed:")
    recommendation = manager.recommend_plan(75)
    print(f"Best Option: {recommendation['best_option']}")
    print(f"Best Cost per Credit: ${recommendation['best_cost_per_credit']:.2f}")
    
    print("\nAll Options (by efficiency):")
    for option in recommendation['all_options']:
        print(f"  {option['tier']:10} - ${option['total_cost']:6} "
              f"(efficiency: {option['efficiency_score']:.2f})")


def demo_schedule_config():
    """Demonstrate schedule configuration functionality."""
    print("\n" + "="*60)
    print("SCHEDULE CONFIGURATION DEMONSTRATION")
    print("="*60)
    
    manager = get_schedule_manager()
    
    # Show schedule summary
    summary = manager.get_schedule_summary()
    print(f"Total Schedules: {summary['total_schedules']}")
    print(f"All Valid: {summary['all_valid']}")
    
    if summary['errors']:
        print("Errors:")
        for error in summary['errors']:
            print(f"  ❌ {error}")
    
    print("\nSchedule Details:")
    for name, info in manager.get_all_schedule_info().items():
        print(f"  {name.upper()}:")
        print(f"    Expression: {info['expression']}")
        print(f"    Description: {info['description']}")
        print(f"    Human Readable: {info['human_readable']}")
        print(f"    Valid: {'✅' if info['is_valid'] else '❌'}")
        print()


def main():
    """Run all demonstrations."""
    print("HOME SERVICES LEAD GENERATION")
    print("Environment Variables Integration Demo")
    print("="*60)
    
    demo_environment_variables()
    demo_launch_config()
    demo_pricing_config()
    demo_schedule_config()
    demo_export_control()
    demo_notifications()
    demo_cache()
    
    print("\n" + "="*60)
    print("DEMO COMPLETED")
    print("="*60)
    print("\nTo enable all features, set these environment variables:")
    print("# Core functionality")
    print("ALLOW_EXPORTS=true")
    print("REDIS_URL=redis://localhost:6379/0")
    print("SENDGRID_API_KEY=your_sendgrid_api_key")
    print("TWILIO_SID=your_twilio_account_sid")
    print("TWILIO_TOKEN=your_twilio_auth_token")
    print("TWILIO_FROM=+1234567890")
    print("\n# Launch configuration")
    print("LAUNCH_SCOPE=houston")
    print("DEFAULT_REGION=tx-houston")
    print("REGISTRY_PATH=config/registry.yaml")
    print("\n# Pricing configuration")
    print('CREDIT_OFFERS_JSON={"starter":{"usd":199,"credits":50},"pro":{"usd":499,"credits":150},"oneoff":{"usd":25,"credits":5}}')
    print("\n# Schedule configuration")
    print("CRON_SCRAPE_UTC=0 5 * * *")
    print("CRON_DIGEST_HOURLY=0 * * * *")
    print("CRON_DIGEST_DAILY=0 13 * * *")
    print("\nNote: Some features require additional libraries to be installed:")
    print("- pip install redis (for caching)")
    print("- pip install sendgrid (for email notifications)")
    print("- pip install twilio (for SMS notifications)")


if __name__ == '__main__':
    main()