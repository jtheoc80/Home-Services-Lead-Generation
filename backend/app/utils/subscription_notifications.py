#!/usr/bin/env python3
"""
Subscription notification service for cancellation, reactivation, and related events.

This module handles sending email and SMS notifications for subscription lifecycle events.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass

from .notifications import NotificationService, NotificationConfig
from .template_renderer import render_email, render_sms

logger = logging.getLogger(__name__)


@dataclass
class SubscriptionEventData:
    """Data for subscription events."""

    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    plan_name: str = "LeadLedgerPro Premium"
    reason: Optional[str] = None
    reason_codes: Optional[List[str]] = None
    notes: Optional[str] = None
    effective_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    reactivated_at: Optional[datetime] = None
    source: str = "user_request"

    # User preferences
    sms_enabled: bool = False
    phone_verified: bool = False


class SubscriptionNotificationService:
    """Service for sending subscription-related notifications."""

    def __init__(self, notification_config: Optional[NotificationConfig] = None):
        self.notification_service = NotificationService(notification_config)
        self.email_from = os.getenv("EMAIL_FROM", "noreply@leadledgerpro.com")

    def _should_send_sms(self, event_data: SubscriptionEventData) -> bool:
        """Check if SMS should be sent based on user preferences."""
        return (
            event_data.sms_enabled
            and event_data.phone_verified
            and event_data.customer_phone
            and self.notification_service.sms.is_enabled()
        )

    def _get_template_context(
        self, event_data: SubscriptionEventData
    ) -> Dict[str, Any]:
        """Build template context from event data."""
        context = {
            "customer_name": event_data.customer_name,
            "customer_email": event_data.customer_email,
            "plan_name": event_data.plan_name,
            "source": event_data.source,
        }

        if event_data.reason:
            context["reason"] = event_data.reason

        if event_data.reason_codes:
            context["reason_codes"] = event_data.reason_codes

        if event_data.notes:
            context["notes"] = event_data.notes

        if event_data.effective_at:
            context["effective_at"] = event_data.effective_at.isoformat()

        if event_data.canceled_at:
            context["canceled_at"] = event_data.canceled_at.isoformat()

        if event_data.reactivated_at:
            context["reactivated_at"] = event_data.reactivated_at.isoformat()

        return context

    def send_cancellation_confirmation(
        self, event_data: SubscriptionEventData
    ) -> Dict[str, bool]:
        """
        Send cancellation confirmation notifications.

        Args:
            event_data: Subscription event data

        Returns:
            Dictionary with email and SMS send results
        """
        logger.info(f"Sending cancellation confirmation to {event_data.customer_email}")

        context = self._get_template_context(event_data)
        results = {"email": False, "sms": False}

        # Send email
        if self.notification_service.email.is_enabled():
            try:
                email_content = render_email("cancel_confirm", context)
                success = self.notification_service.email.send_email(
                    to_email=event_data.customer_email,
                    subject=email_content["subject"],
                    content=email_content["text_content"],
                    html_content=email_content["html_content"],
                    from_email=self.email_from,
                )
                results["email"] = success

                if success:
                    logger.info(
                        f"Cancellation confirmation email sent to {event_data.customer_email}"
                    )
                else:
                    logger.error(
                        f"Failed to send cancellation confirmation email to {event_data.customer_email}"
                    )

            except Exception as e:
                logger.error(f"Error sending cancellation confirmation email: {e}")

        # Send SMS if enabled
        if self._should_send_sms(event_data):
            try:
                sms_content = render_sms("cancel_confirm", context)
                success = self.notification_service.sms.send_sms(
                    to_number=event_data.customer_phone, message=sms_content
                )
                results["sms"] = success

                if success:
                    logger.info(
                        f"Cancellation confirmation SMS sent to {event_data.customer_phone}"
                    )
                else:
                    logger.error(
                        f"Failed to send cancellation confirmation SMS to {event_data.customer_phone}"
                    )

            except Exception as e:
                logger.error(f"Error sending cancellation confirmation SMS: {e}")

        return results

    def send_grace_period_reminder(
        self, event_data: SubscriptionEventData
    ) -> Dict[str, bool]:
        """
        Send grace period reminder notifications.

        Args:
            event_data: Subscription event data

        Returns:
            Dictionary with email and SMS send results
        """
        logger.info(f"Sending grace period reminder to {event_data.customer_email}")

        context = self._get_template_context(event_data)
        results = {"email": False, "sms": False}

        # Send email
        if self.notification_service.email.is_enabled():
            try:
                email_content = render_email("cancel_grace_reminder", context)
                success = self.notification_service.email.send_email(
                    to_email=event_data.customer_email,
                    subject=email_content["subject"],
                    content=email_content["text_content"],
                    html_content=email_content["html_content"],
                    from_email=self.email_from,
                )
                results["email"] = success

                if success:
                    logger.info(
                        f"Grace period reminder email sent to {event_data.customer_email}"
                    )
                else:
                    logger.error(
                        f"Failed to send grace period reminder email to {event_data.customer_email}"
                    )

            except Exception as e:
                logger.error(f"Error sending grace period reminder email: {e}")

        # Send SMS if enabled
        if self._should_send_sms(event_data):
            try:
                sms_content = render_sms("cancel_grace_reminder", context)
                success = self.notification_service.sms.send_sms(
                    to_number=event_data.customer_phone, message=sms_content
                )
                results["sms"] = success

                if success:
                    logger.info(
                        f"Grace period reminder SMS sent to {event_data.customer_phone}"
                    )
                else:
                    logger.error(
                        f"Failed to send grace period reminder SMS to {event_data.customer_phone}"
                    )

            except Exception as e:
                logger.error(f"Error sending grace period reminder SMS: {e}")

        return results

    def send_access_ended(self, event_data: SubscriptionEventData) -> Dict[str, bool]:
        """
        Send access ended notifications.

        Args:
            event_data: Subscription event data

        Returns:
            Dictionary with email and SMS send results
        """
        logger.info(f"Sending access ended notification to {event_data.customer_email}")

        context = self._get_template_context(event_data)
        results = {"email": False, "sms": False}

        # Send email
        if self.notification_service.email.is_enabled():
            try:
                email_content = render_email("access_ended", context)
                success = self.notification_service.email.send_email(
                    to_email=event_data.customer_email,
                    subject=email_content["subject"],
                    content=email_content["text_content"],
                    html_content=email_content["html_content"],
                    from_email=self.email_from,
                )
                results["email"] = success

                if success:
                    logger.info(
                        f"Access ended email sent to {event_data.customer_email}"
                    )
                else:
                    logger.error(
                        f"Failed to send access ended email to {event_data.customer_email}"
                    )

            except Exception as e:
                logger.error(f"Error sending access ended email: {e}")

        # Send SMS if enabled
        if self._should_send_sms(event_data):
            try:
                sms_content = render_sms("access_ended", context)
                success = self.notification_service.sms.send_sms(
                    to_number=event_data.customer_phone, message=sms_content
                )
                results["sms"] = success

                if success:
                    logger.info(f"Access ended SMS sent to {event_data.customer_phone}")
                else:
                    logger.error(
                        f"Failed to send access ended SMS to {event_data.customer_phone}"
                    )

            except Exception as e:
                logger.error(f"Error sending access ended SMS: {e}")

        return results

    def send_reactivation_confirmation(
        self, event_data: SubscriptionEventData
    ) -> Dict[str, bool]:
        """
        Send reactivation confirmation notifications.

        Args:
            event_data: Subscription event data

        Returns:
            Dictionary with email and SMS send results
        """
        logger.info(f"Sending reactivation confirmation to {event_data.customer_email}")

        context = self._get_template_context(event_data)
        results = {"email": False, "sms": False}

        # Send email
        if self.notification_service.email.is_enabled():
            try:
                email_content = render_email("reactivated", context)
                success = self.notification_service.email.send_email(
                    to_email=event_data.customer_email,
                    subject=email_content["subject"],
                    content=email_content["text_content"],
                    html_content=email_content["html_content"],
                    from_email=self.email_from,
                )
                results["email"] = success

                if success:
                    logger.info(
                        f"Reactivation confirmation email sent to {event_data.customer_email}"
                    )
                else:
                    logger.error(
                        f"Failed to send reactivation confirmation email to {event_data.customer_email}"
                    )

            except Exception as e:
                logger.error(f"Error sending reactivation confirmation email: {e}")

        # Send SMS if enabled
        if self._should_send_sms(event_data):
            try:
                sms_content = render_sms("reactivated", context)
                success = self.notification_service.sms.send_sms(
                    to_number=event_data.customer_phone, message=sms_content
                )
                results["sms"] = success

                if success:
                    logger.info(
                        f"Reactivation confirmation SMS sent to {event_data.customer_phone}"
                    )
                else:
                    logger.error(
                        f"Failed to send reactivation confirmation SMS to {event_data.customer_phone}"
                    )

            except Exception as e:
                logger.error(f"Error sending reactivation confirmation SMS: {e}")

        return results


# Global subscription notification service instance
_subscription_notification_service = None


def get_subscription_notification_service() -> SubscriptionNotificationService:
    """Get the global subscription notification service instance."""
    global _subscription_notification_service
    if _subscription_notification_service is None:
        _subscription_notification_service = SubscriptionNotificationService()
    return _subscription_notification_service
