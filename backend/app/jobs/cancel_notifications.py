#!/usr/bin/env python3
"""
Cancellation notification job for processing scheduled subscription events.

This script runs daily to:
1. Send grace period reminders to users whose subscriptions are ending soon
2. Send access ended notifications to users whose grace period has expired
3. Handle any other subscription lifecycle notifications

Run this script as a cron job or scheduled task.
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add the parent directory to Python path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.subscription_notifications import (
    SubscriptionEventData, 
    get_subscription_notification_service
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/cancel_notifications.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
SEND_CANCEL_REMINDER_DAYS = int(os.getenv('SEND_CANCEL_REMINDER_DAYS', '1'))  # Days before effective date
DRY_RUN = os.getenv('DRY_RUN', 'false').lower() == 'true'


class CancellationNotificationJob:
    """Job for processing cancellation notifications."""
    
    def __init__(self):
        self.notification_service = get_subscription_notification_service()
        self.processed_count = 0
        self.error_count = 0
    
    def get_subscriptions_for_grace_reminder(self) -> List[Dict[str, Any]]:
        """
        Get subscriptions that need grace period reminders.
        
        In a real implementation, this would query the database for:
        - Subscriptions with status='canceled'
        - effective_at date = today + SEND_CANCEL_REMINDER_DAYS
        - No reminder sent yet (could track in reminder_sent_at field)
        
        Returns:
            List of subscription data dictionaries
        """
        # Mock data for demonstration
        # In real implementation, replace with database query
        reminder_date = datetime.now() + timedelta(days=SEND_CANCEL_REMINDER_DAYS)
        
        # Example mock subscriptions
        mock_subscriptions = [
            {
                'customer_id': 'cust_123',
                'customer_name': 'John Doe',
                'customer_email': 'john.doe@example.com',
                'customer_phone': '+15551234567',
                'plan_name': 'LeadLedgerPro Premium',
                'subscription_status': 'canceled',
                'effective_at': reminder_date.isoformat(),
                'canceled_at': (datetime.now() - timedelta(days=6)).isoformat(),
                'reason': 'not_using',
                'reason_codes': ['poor_results'],
                'notes': 'Not getting enough qualified leads',
                'sms_enabled': True,
                'phone_verified': True,
                'reminder_sent_at': None
            }
        ]
        
        logger.info(f"Found {len(mock_subscriptions)} subscriptions needing grace reminders")
        return mock_subscriptions
    
    def get_subscriptions_for_access_ended(self) -> List[Dict[str, Any]]:
        """
        Get subscriptions that need access ended notifications.
        
        In a real implementation, this would query the database for:
        - Subscriptions with status='canceled' 
        - effective_at date <= today
        - No access ended notification sent yet
        
        Returns:
            List of subscription data dictionaries
        """
        # Mock data for demonstration
        today = datetime.now()
        
        # Example mock subscriptions
        mock_subscriptions = [
            {
                'customer_id': 'cust_456',
                'customer_name': 'Jane Smith',
                'customer_email': 'jane.smith@example.com',
                'customer_phone': '+15559876543',
                'plan_name': 'LeadLedgerPro Premium',
                'subscription_status': 'canceled',
                'effective_at': (today - timedelta(hours=1)).isoformat(),
                'canceled_at': (today - timedelta(days=7)).isoformat(),
                'reason': 'too_expensive',
                'reason_codes': [],
                'notes': '',
                'sms_enabled': False,
                'phone_verified': True,
                'access_ended_sent_at': None
            }
        ]
        
        logger.info(f"Found {len(mock_subscriptions)} subscriptions with ended access")
        return mock_subscriptions
    
    def process_grace_reminders(self) -> None:
        """Process grace period reminder notifications."""
        logger.info("Processing grace period reminders...")
        
        subscriptions = self.get_subscriptions_for_grace_reminder()
        
        for sub_data in subscriptions:
            try:
                # Convert to SubscriptionEventData
                event_data = SubscriptionEventData(
                    customer_name=sub_data['customer_name'],
                    customer_email=sub_data['customer_email'],
                    customer_phone=sub_data.get('customer_phone'),
                    plan_name=sub_data['plan_name'],
                    reason=sub_data.get('reason'),
                    reason_codes=sub_data.get('reason_codes'),
                    notes=sub_data.get('notes'),
                    effective_at=datetime.fromisoformat(sub_data['effective_at']),
                    canceled_at=datetime.fromisoformat(sub_data['canceled_at']) if sub_data.get('canceled_at') else None,
                    sms_enabled=sub_data.get('sms_enabled', False),
                    phone_verified=sub_data.get('phone_verified', False),
                    source='scheduled_reminder'
                )
                
                if DRY_RUN:
                    logger.info(f"DRY RUN: Would send grace reminder to {event_data.customer_email}")
                    continue
                
                # Send notifications
                results = self.notification_service.send_grace_period_reminder(event_data)
                
                if results.get('email') or results.get('sms'):
                    self.processed_count += 1
                    logger.info(f"Grace reminder sent successfully to {event_data.customer_email}")
                    
                    # TODO: Update database to mark reminder as sent
                    # UPDATE subscriptions SET reminder_sent_at = NOW() WHERE customer_id = ?
                    
                else:
                    self.error_count += 1
                    logger.error(f"Failed to send grace reminder to {event_data.customer_email}")
                
            except Exception as e:
                self.error_count += 1
                logger.error(f"Error processing grace reminder for {sub_data.get('customer_email', 'unknown')}: {e}")
    
    def process_access_ended(self) -> None:
        """Process access ended notifications."""
        logger.info("Processing access ended notifications...")
        
        subscriptions = self.get_subscriptions_for_access_ended()
        
        for sub_data in subscriptions:
            try:
                # Convert to SubscriptionEventData
                event_data = SubscriptionEventData(
                    customer_name=sub_data['customer_name'],
                    customer_email=sub_data['customer_email'],
                    customer_phone=sub_data.get('customer_phone'),
                    plan_name=sub_data['plan_name'],
                    reason=sub_data.get('reason'),
                    reason_codes=sub_data.get('reason_codes'),
                    notes=sub_data.get('notes'),
                    effective_at=datetime.fromisoformat(sub_data['effective_at']),
                    canceled_at=datetime.fromisoformat(sub_data['canceled_at']) if sub_data.get('canceled_at') else None,
                    sms_enabled=sub_data.get('sms_enabled', False),
                    phone_verified=sub_data.get('phone_verified', False),
                    source='scheduled_notification'
                )
                
                if DRY_RUN:
                    logger.info(f"DRY RUN: Would send access ended notification to {event_data.customer_email}")
                    continue
                
                # Send notifications
                results = self.notification_service.send_access_ended(event_data)
                
                if results.get('email') or results.get('sms'):
                    self.processed_count += 1
                    logger.info(f"Access ended notification sent successfully to {event_data.customer_email}")
                    
                    # TODO: Update database to mark notification as sent
                    # UPDATE subscriptions SET access_ended_sent_at = NOW() WHERE customer_id = ?
                    
                else:
                    self.error_count += 1
                    logger.error(f"Failed to send access ended notification to {event_data.customer_email}")
                
            except Exception as e:
                self.error_count += 1
                logger.error(f"Error processing access ended notification for {sub_data.get('customer_email', 'unknown')}: {e}")
    
    def run(self) -> Dict[str, int]:
        """
        Run the complete cancellation notification job.
        
        Returns:
            Dictionary with job statistics
        """
        start_time = datetime.now()
        logger.info(f"Starting cancellation notification job at {start_time}")
        
        if DRY_RUN:
            logger.info("Running in DRY RUN mode - no notifications will be sent")
        
        # Process grace period reminders
        self.process_grace_reminders()
        
        # Process access ended notifications
        self.process_access_ended()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        results = {
            'processed_count': self.processed_count,
            'error_count': self.error_count,
            'duration_seconds': duration.total_seconds()
        }
        
        logger.info(f"Cancellation notification job completed in {duration.total_seconds():.2f}s")
        logger.info(f"Processed: {self.processed_count}, Errors: {self.error_count}")
        
        return results


def main():
    """Main entry point for the cancellation notification job."""
    try:
        job = CancellationNotificationJob()
        results = job.run()
        
        # Exit with error code if there were any failures
        if results['error_count'] > 0:
            logger.error(f"Job completed with {results['error_count']} errors")
            sys.exit(1)
        else:
            logger.info("Job completed successfully")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Job failed with exception: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()