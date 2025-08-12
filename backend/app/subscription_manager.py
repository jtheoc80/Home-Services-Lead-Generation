#!/usr/bin/env python3
"""
Subscription management module for handling user subscriptions and cancellations.

This module provides the core logic for managing subscription lifecycle including:
- Trial vs paid subscription cancellation workflows
- Grace period management for paid subscriptions
- Notification sending for cancellation events
- Reactivation handling
- Quiet hours respect for notifications
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from .utils.notifications import NotificationService, get_notification_service

# Configure logging
logger = logging.getLogger(__name__)


class SubscriptionStatus(Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    CANCELLED = "cancelled"
    GRACE_PERIOD = "grace_period"
    EXPIRED = "expired"


class SubscriptionPlan(Enum):
    TRIAL = "trial"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class CancellationType(Enum):
    TRIAL = "trial"
    PAID = "paid"


@dataclass
class SubscriptionInfo:
    """Subscription information for a user."""
    id: int
    user_id: str
    plan: SubscriptionPlan
    status: SubscriptionStatus
    trial_start_date: Optional[datetime] = None
    trial_end_date: Optional[datetime] = None
    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None
    grace_period_end_date: Optional[datetime] = None
    billing_cycle: Optional[str] = None
    amount_cents: Optional[int] = None
    payment_method: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class CancellationRequest:
    """Cancellation request details."""
    user_id: str
    reason_category: Optional[str] = None
    reason_notes: Optional[str] = None
    processed_by: Optional[str] = None  # Admin user ID if applicable


@dataclass
class QuietHoursConfig:
    """Configuration for quiet hours when notifications should not be sent."""
    enabled: bool = True
    start_hour: int = 22  # 10 PM
    end_hour: int = 8     # 8 AM
    timezone: str = "UTC"  # Default timezone


class SubscriptionManager:
    """Manager for subscription lifecycle operations."""
    
    def __init__(self, 
                 notification_service: Optional[NotificationService] = None,
                 quiet_hours_config: Optional[QuietHoursConfig] = None):
        """
        Initialize subscription manager.
        
        Args:
            notification_service: Service for sending notifications
            quiet_hours_config: Configuration for quiet hours
        """
        self.notification_service = notification_service or get_notification_service()
        self.quiet_hours = quiet_hours_config or QuietHoursConfig()
        
    def is_quiet_hours(self, now: Optional[datetime] = None) -> bool:
        """
        Check if current time is within quiet hours.
        
        Args:
            now: Current time (defaults to datetime.utcnow())
            
        Returns:
            True if within quiet hours, False otherwise
        """
        if not self.quiet_hours.enabled:
            return False
            
        if now is None:
            now = datetime.utcnow()
            
        current_hour = now.hour
        
        # Handle cases where quiet hours span midnight
        if self.quiet_hours.start_hour > self.quiet_hours.end_hour:
            # e.g., 22:00 to 08:00
            return (current_hour >= self.quiet_hours.start_hour or 
                   current_hour < self.quiet_hours.end_hour)
        else:
            # e.g., 01:00 to 06:00
            return (current_hour >= self.quiet_hours.start_hour and 
                   current_hour < self.quiet_hours.end_hour)
    
    def schedule_notification_respecting_quiet_hours(self, 
                                                   notification_func,
                                                   *args, **kwargs) -> bool:
        """
        Send notification immediately if outside quiet hours, or log for later sending.
        
        Args:
            notification_func: Function to call for sending notification
            *args, **kwargs: Arguments to pass to notification function
            
        Returns:
            True if notification was sent, False if deferred
        """
        if self.is_quiet_hours():
            logger.info("Currently in quiet hours. Notification would be deferred for later sending.")
            # In a real implementation, you'd queue this for later
            # For this demo, we'll just log it
            return False
        else:
            return notification_func(*args, **kwargs)
    
    def cancel_subscription(self, 
                          subscription: SubscriptionInfo, 
                          request: CancellationRequest) -> Dict[str, Any]:
        """
        Cancel a user subscription with appropriate workflow.
        
        Args:
            subscription: Current subscription information
            request: Cancellation request details
            
        Returns:
            Dictionary with cancellation result and details
        """
        now = datetime.utcnow()
        
        # Determine cancellation type
        if subscription.status == SubscriptionStatus.TRIAL:
            return self._cancel_trial_subscription(subscription, request, now)
        else:
            return self._cancel_paid_subscription(subscription, request, now)
    
    def _cancel_trial_subscription(self, 
                                 subscription: SubscriptionInfo,
                                 request: CancellationRequest,
                                 now: datetime) -> Dict[str, Any]:
        """
        Cancel trial subscription - immediate termination.
        
        Args:
            subscription: Trial subscription to cancel
            request: Cancellation request details
            now: Current timestamp
            
        Returns:
            Cancellation result dictionary
        """
        logger.info(f"Processing trial cancellation for user {subscription.user_id}")
        
        # Update subscription status to cancelled immediately
        updated_subscription = SubscriptionInfo(
            id=subscription.id,
            user_id=subscription.user_id,
            plan=subscription.plan,
            status=SubscriptionStatus.CANCELLED,
            trial_start_date=subscription.trial_start_date,
            trial_end_date=subscription.trial_end_date,
            subscription_start_date=subscription.subscription_start_date,
            subscription_end_date=now,  # End immediately
            grace_period_end_date=None,
            billing_cycle=subscription.billing_cycle,
            amount_cents=subscription.amount_cents,
            payment_method=subscription.payment_method,
            created_at=subscription.created_at,
            updated_at=now
        )
        
        # Send cancel confirmation notification
        notification_sent = self.schedule_notification_respecting_quiet_hours(
            self._send_cancel_confirm_notification,
            subscription.user_id,
            CancellationType.TRIAL,
            immediate_termination=True
        )
        
        # Create cancellation record
        cancellation_record = {
            'user_id': subscription.user_id,
            'subscription_id': subscription.id,
            'cancellation_type': CancellationType.TRIAL.value,
            'reason_category': request.reason_category,
            'reason_notes': request.reason_notes,
            'cancelled_at': now,
            'effective_date': now,  # Immediate
            'grace_period_days': 0,
            'processed_by': request.processed_by,
            'refund_issued': False,
            'refund_amount_cents': None
        }
        
        return {
            'success': True,
            'cancellation_type': CancellationType.TRIAL.value,
            'effective_date': now,
            'grace_period_days': 0,
            'notification_sent': notification_sent,
            'updated_subscription': updated_subscription,
            'cancellation_record': cancellation_record,
            'message': 'Trial subscription cancelled immediately'
        }
    
    def _cancel_paid_subscription(self, 
                                subscription: SubscriptionInfo,
                                request: CancellationRequest,
                                now: datetime) -> Dict[str, Any]:
        """
        Cancel paid subscription - grace period until end of billing cycle.
        
        Args:
            subscription: Paid subscription to cancel
            request: Cancellation request details  
            now: Current timestamp
            
        Returns:
            Cancellation result dictionary
        """
        logger.info(f"Processing paid cancellation for user {subscription.user_id}")
        
        # Calculate grace period end (subscription end date or billing cycle end)
        grace_end_date = subscription.subscription_end_date
        if grace_end_date is None:
            # Calculate next billing cycle end
            if subscription.billing_cycle == 'monthly':
                grace_end_date = now + timedelta(days=30)
            elif subscription.billing_cycle == 'yearly':
                grace_end_date = now + timedelta(days=365)
            else:
                # Default to 30 days if unknown billing cycle
                grace_end_date = now + timedelta(days=30)
                
        grace_period_days = (grace_end_date - now).days
        
        # Update subscription status to grace period
        updated_subscription = SubscriptionInfo(
            id=subscription.id,
            user_id=subscription.user_id,
            plan=subscription.plan,
            status=SubscriptionStatus.GRACE_PERIOD,
            trial_start_date=subscription.trial_start_date,
            trial_end_date=subscription.trial_end_date,
            subscription_start_date=subscription.subscription_start_date,
            subscription_end_date=grace_end_date,
            grace_period_end_date=grace_end_date,
            billing_cycle=subscription.billing_cycle,
            amount_cents=subscription.amount_cents,
            payment_method=subscription.payment_method,
            created_at=subscription.created_at,
            updated_at=now
        )
        
        # Send cancel confirmation notification
        notification_sent = self.schedule_notification_respecting_quiet_hours(
            self._send_cancel_confirm_notification,
            subscription.user_id,
            CancellationType.PAID,
            grace_end_date=grace_end_date
        )
        
        # Schedule grace reminder for T-3 days
        grace_reminder_date = grace_end_date - timedelta(days=3)
        if grace_reminder_date > now:
            # In a real implementation, you'd schedule this in a job queue
            logger.info(f"Grace reminder scheduled for {grace_reminder_date} for user {subscription.user_id}")
        
        # Create cancellation record
        cancellation_record = {
            'user_id': subscription.user_id,
            'subscription_id': subscription.id,
            'cancellation_type': CancellationType.PAID.value,
            'reason_category': request.reason_category,
            'reason_notes': request.reason_notes,
            'cancelled_at': now,
            'effective_date': grace_end_date,
            'grace_period_days': grace_period_days,
            'processed_by': request.processed_by,
            'refund_issued': False,
            'refund_amount_cents': None
        }
        
        return {
            'success': True,
            'cancellation_type': CancellationType.PAID.value,
            'effective_date': grace_end_date,
            'grace_period_days': grace_period_days,
            'notification_sent': notification_sent,
            'updated_subscription': updated_subscription,
            'cancellation_record': cancellation_record,
            'message': f'Paid subscription cancelled. Access continues until {grace_end_date.strftime("%Y-%m-%d")}'
        }
    
    def reactivate_subscription(self, 
                              subscription: SubscriptionInfo) -> Dict[str, Any]:
        """
        Reactivate a cancelled subscription.
        
        Args:
            subscription: Cancelled subscription to reactivate
            
        Returns:
            Reactivation result dictionary
        """
        now = datetime.utcnow()
        
        logger.info(f"Processing reactivation for user {subscription.user_id}")
        
        # Update subscription status to active
        updated_subscription = SubscriptionInfo(
            id=subscription.id,
            user_id=subscription.user_id,
            plan=subscription.plan,
            status=SubscriptionStatus.ACTIVE,
            trial_start_date=subscription.trial_start_date,
            trial_end_date=subscription.trial_end_date,
            subscription_start_date=subscription.subscription_start_date,
            subscription_end_date=None,  # Remove end date
            grace_period_end_date=None,  # Remove grace period
            billing_cycle=subscription.billing_cycle,
            amount_cents=subscription.amount_cents,
            payment_method=subscription.payment_method,
            created_at=subscription.created_at,
            updated_at=now
        )
        
        # Send reactivation notification
        notification_sent = self.schedule_notification_respecting_quiet_hours(
            self._send_reactivation_notification,
            subscription.user_id
        )
        
        return {
            'success': True,
            'notification_sent': notification_sent,
            'updated_subscription': updated_subscription,
            'message': 'Subscription reactivated successfully'
        }
    
    def send_grace_reminder(self, subscription: SubscriptionInfo) -> bool:
        """
        Send grace period reminder notification.
        
        Args:
            subscription: Subscription in grace period
            
        Returns:
            True if notification was sent successfully
        """
        return self.schedule_notification_respecting_quiet_hours(
            self._send_grace_reminder_notification,
            subscription.user_id,
            subscription.grace_period_end_date
        )
    
    def send_access_ended(self, subscription: SubscriptionInfo) -> bool:
        """
        Send access ended notification.
        
        Args:
            subscription: Subscription that has ended
            
        Returns:
            True if notification was sent successfully
        """
        return self.schedule_notification_respecting_quiet_hours(
            self._send_access_ended_notification,
            subscription.user_id
        )
    
    def _send_cancel_confirm_notification(self, 
                                        user_id: str, 
                                        cancellation_type: CancellationType,
                                        immediate_termination: bool = False,
                                        grace_end_date: Optional[datetime] = None) -> bool:
        """Send cancellation confirmation notification."""
        
        if cancellation_type == CancellationType.TRIAL:
            subject = "Trial Cancellation Confirmed - LeadLedgerPro"
            message = ("Your LeadLedgerPro trial has been cancelled and access has ended immediately. "
                      "We're sorry to see you go! If you change your mind, you can sign up again anytime.")
        else:
            grace_date_str = grace_end_date.strftime("%B %d, %Y") if grace_end_date else "your billing period end"
            subject = "Subscription Cancellation Confirmed - LeadLedgerPro"
            message = (f"Your LeadLedgerPro subscription has been cancelled. "
                      f"You'll continue to have access until {grace_date_str}. "
                      f"You can reactivate your subscription anytime before then.")
        
        # Send email notification (assuming we have user email from user_id)
        # In a real implementation, you'd look up the user's email and phone
        logger.info(f"Sending cancel confirmation to user {user_id}: {message}")
        
        # This would be the actual notification sending logic
        # return self.notification_service.email.send_email(
        #     to_email=user_email,
        #     subject=subject,
        #     content=message
        # )
        
        # For demo purposes, just return True
        return True
    
    def _send_grace_reminder_notification(self, 
                                        user_id: str, 
                                        grace_end_date: datetime) -> bool:
        """Send grace period reminder notification."""
        
        grace_date_str = grace_end_date.strftime("%B %d, %Y")
        subject = "Your LeadLedgerPro Access Ends Soon"
        message = (f"This is a reminder that your LeadLedgerPro access will end on {grace_date_str}. "
                  f"Reactivate your subscription now to continue enjoying uninterrupted service.")
        
        logger.info(f"Sending grace reminder to user {user_id}: {message}")
        
        # This would be the actual notification sending logic
        return True
    
    def _send_access_ended_notification(self, user_id: str) -> bool:
        """Send access ended notification."""
        
        subject = "Your LeadLedgerPro Access Has Ended"
        message = ("Your LeadLedgerPro subscription has ended and access has been terminated. "
                  "Thank you for using our service! You can reactivate anytime to restore access.")
        
        logger.info(f"Sending access ended notification to user {user_id}: {message}")
        
        # This would be the actual notification sending logic
        return True
    
    def _send_reactivation_notification(self, user_id: str) -> bool:
        """Send reactivation confirmation notification."""
        
        subject = "Welcome Back to LeadLedgerPro!"
        message = ("Great news! Your LeadLedgerPro subscription has been reactivated. "
                  "You now have full access to all features again. Welcome back!")
        
        logger.info(f"Sending reactivation notification to user {user_id}: {message}")
        
        # This would be the actual notification sending logic
        return True


# Global subscription manager instance
_subscription_manager = None

def get_subscription_manager() -> SubscriptionManager:
    """Get the global subscription manager instance."""
    global _subscription_manager
    if _subscription_manager is None:
        _subscription_manager = SubscriptionManager()
    return _subscription_manager