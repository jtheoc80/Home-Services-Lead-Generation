#!/usr/bin/env python3
"""
Test subscription cancellation and reactivation workflows.

Tests cover:
- Trial subscription cancellation (immediate termination)
- Paid subscription cancellation (grace period)
- Reactivation workflow
- Quiet hours respect for notifications
- Cancellation record creation
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.subscription_manager import (
    SubscriptionManager,
    SubscriptionInfo,
    CancellationRequest,
    QuietHoursConfig,
    SubscriptionStatus,
    SubscriptionPlan,
    CancellationType,
)


class TestSubscriptionCancellation(unittest.TestCase):
    """Test subscription cancellation workflows."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_notification_service = Mock()
        self.quiet_hours_config = QuietHoursConfig(
            enabled=True, start_hour=22, end_hour=8  # 10 PM  # 8 AM
        )
        self.manager = SubscriptionManager(
            notification_service=self.mock_notification_service,
            quiet_hours_config=self.quiet_hours_config,
        )

        # Base test subscription
        self.base_subscription = SubscriptionInfo(
            id=1,
            user_id="test-user-123",
            plan=SubscriptionPlan.TRIAL,
            status=SubscriptionStatus.TRIAL,
            trial_start_date=datetime.utcnow() - timedelta(days=2),
            trial_end_date=datetime.utcnow() + timedelta(days=5),
            created_at=datetime.utcnow() - timedelta(days=2),
            updated_at=datetime.utcnow() - timedelta(days=1),
        )

        # Base cancellation request
        self.base_request = CancellationRequest(
            user_id="test-user-123",
            reason_category="not_satisfied",
            reason_notes="Service didn't meet expectations",
            processed_by="admin-123",
        )

    def test_trial_cancellation_immediate_termination(self):
        """Test trial subscription cancellation results in immediate termination."""
        result = self.manager.cancel_subscription(
            self.base_subscription, self.base_request
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["cancellation_type"], CancellationType.TRIAL.value)
        self.assertEqual(result["grace_period_days"], 0)
        self.assertIn("immediate", result["message"].lower())

        # Check updated subscription
        updated_sub = result["updated_subscription"]
        self.assertEqual(updated_sub.status, SubscriptionStatus.CANCELLED)
        self.assertIsNotNone(updated_sub.subscription_end_date)
        self.assertIsNone(updated_sub.grace_period_end_date)

        # Check cancellation record
        record = result["cancellation_record"]
        self.assertEqual(record["cancellation_type"], CancellationType.TRIAL.value)
        self.assertEqual(record["grace_period_days"], 0)
        self.assertEqual(record["effective_date"], record["cancelled_at"])
        self.assertEqual(record["reason_category"], "not_satisfied")
        self.assertEqual(record["reason_notes"], "Service didn't meet expectations")

    def test_paid_cancellation_grace_period(self):
        """Test paid subscription cancellation includes grace period."""
        # Create paid subscription
        paid_subscription = SubscriptionInfo(
            id=2,
            user_id="test-user-456",
            plan=SubscriptionPlan.PREMIUM,
            status=SubscriptionStatus.ACTIVE,
            subscription_start_date=datetime.utcnow() - timedelta(days=10),
            billing_cycle="monthly",
            amount_cents=4999,
            payment_method="stripe",
            created_at=datetime.utcnow() - timedelta(days=10),
        )

        request = CancellationRequest(
            user_id="test-user-456",
            reason_category="cost",
            reason_notes="Too expensive for current needs",
        )

        result = self.manager.cancel_subscription(paid_subscription, request)

        self.assertTrue(result["success"])
        self.assertEqual(result["cancellation_type"], CancellationType.PAID.value)
        self.assertGreater(result["grace_period_days"], 0)
        self.assertIn("access continues", result["message"].lower())

        # Check updated subscription
        updated_sub = result["updated_subscription"]
        self.assertEqual(updated_sub.status, SubscriptionStatus.GRACE_PERIOD)
        self.assertIsNotNone(updated_sub.grace_period_end_date)
        self.assertIsNotNone(updated_sub.subscription_end_date)

        # Check cancellation record
        record = result["cancellation_record"]
        self.assertEqual(record["cancellation_type"], CancellationType.PAID.value)
        self.assertGreater(record["grace_period_days"], 0)
        self.assertNotEqual(record["effective_date"], record["cancelled_at"])
        self.assertEqual(record["reason_category"], "cost")

    def test_reactivation_workflow(self):
        """Test subscription reactivation workflow."""
        # Create cancelled subscription
        cancelled_subscription = SubscriptionInfo(
            id=3,
            user_id="test-user-789",
            plan=SubscriptionPlan.BASIC,
            status=SubscriptionStatus.GRACE_PERIOD,
            subscription_start_date=datetime.utcnow() - timedelta(days=15),
            subscription_end_date=datetime.utcnow() + timedelta(days=5),
            grace_period_end_date=datetime.utcnow() + timedelta(days=5),
            billing_cycle="monthly",
            amount_cents=2999,
            created_at=datetime.utcnow() - timedelta(days=15),
        )

        result = self.manager.reactivate_subscription(cancelled_subscription)

        self.assertTrue(result["success"])
        self.assertIn("reactivated successfully", result["message"].lower())

        # Check updated subscription
        updated_sub = result["updated_subscription"]
        self.assertEqual(updated_sub.status, SubscriptionStatus.ACTIVE)
        self.assertIsNone(updated_sub.subscription_end_date)
        self.assertIsNone(updated_sub.grace_period_end_date)

    def test_quiet_hours_detection(self):
        """Test quiet hours detection logic."""
        # Test during quiet hours (23:00 - within quiet period)
        quiet_time = datetime(2024, 1, 1, 23, 0, 0)  # 11 PM
        self.assertTrue(self.manager.is_quiet_hours(quiet_time))

        # Test during quiet hours (03:00 - within quiet period)
        quiet_time_early = datetime(2024, 1, 1, 3, 0, 0)  # 3 AM
        self.assertTrue(self.manager.is_quiet_hours(quiet_time_early))

        # Test outside quiet hours (14:00 - normal hours)
        normal_time = datetime(2024, 1, 1, 14, 0, 0)  # 2 PM
        self.assertFalse(self.manager.is_quiet_hours(normal_time))

        # Test disabled quiet hours
        self.manager.quiet_hours.enabled = False
        self.assertFalse(self.manager.is_quiet_hours(quiet_time))

    @patch("app.subscription_manager.datetime")
    def test_quiet_hours_notification_deferral(self, mock_datetime):
        """Test that notifications are deferred during quiet hours."""
        # Mock current time to be during quiet hours
        mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 23, 0, 0)  # 11 PM

        mock_notification_func = Mock(return_value=True)

        # Should defer notification during quiet hours
        result = self.manager.schedule_notification_respecting_quiet_hours(
            mock_notification_func, "test-arg"
        )

        self.assertFalse(result)  # Notification deferred
        mock_notification_func.assert_not_called()

    @patch("app.subscription_manager.datetime")
    def test_quiet_hours_notification_immediate_send(self, mock_datetime):
        """Test that notifications are sent immediately outside quiet hours."""
        # Mock current time to be outside quiet hours
        mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 14, 0, 0)  # 2 PM

        mock_notification_func = Mock(return_value=True)

        # Should send notification immediately outside quiet hours
        result = self.manager.schedule_notification_respecting_quiet_hours(
            mock_notification_func, "test-arg"
        )

        self.assertTrue(result)  # Notification sent
        mock_notification_func.assert_called_once_with("test-arg")

    def test_grace_reminder_notification(self):
        """Test grace reminder notification sending."""
        subscription = SubscriptionInfo(
            id=4,
            user_id="test-user-reminder",
            plan=SubscriptionPlan.PREMIUM,
            status=SubscriptionStatus.GRACE_PERIOD,
            grace_period_end_date=datetime.utcnow() + timedelta(days=3),
        )

        # Mock outside quiet hours
        with patch("app.subscription_manager.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 14, 0, 0)
            result = self.manager.send_grace_reminder(subscription)

        self.assertTrue(result)

    def test_access_ended_notification(self):
        """Test access ended notification sending."""
        subscription = SubscriptionInfo(
            id=5,
            user_id="test-user-ended",
            plan=SubscriptionPlan.BASIC,
            status=SubscriptionStatus.EXPIRED,
        )

        # Mock outside quiet hours
        with patch("app.subscription_manager.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 14, 0, 0)
            result = self.manager.send_access_ended(subscription)

        self.assertTrue(result)


class TestSubscriptionDataStructures(unittest.TestCase):
    """Test subscription data structures and enums."""

    def test_subscription_status_enum(self):
        """Test subscription status enum values."""
        self.assertEqual(SubscriptionStatus.TRIAL.value, "trial")
        self.assertEqual(SubscriptionStatus.ACTIVE.value, "active")
        self.assertEqual(SubscriptionStatus.CANCELLED.value, "cancelled")
        self.assertEqual(SubscriptionStatus.GRACE_PERIOD.value, "grace_period")
        self.assertEqual(SubscriptionStatus.EXPIRED.value, "expired")

    def test_cancellation_type_enum(self):
        """Test cancellation type enum values."""
        self.assertEqual(CancellationType.TRIAL.value, "trial")
        self.assertEqual(CancellationType.PAID.value, "paid")

    def test_subscription_info_creation(self):
        """Test SubscriptionInfo dataclass creation."""
        subscription = SubscriptionInfo(
            id=1,
            user_id="test-user",
            plan=SubscriptionPlan.PREMIUM,
            status=SubscriptionStatus.ACTIVE,
        )

        self.assertEqual(subscription.id, 1)
        self.assertEqual(subscription.user_id, "test-user")
        self.assertEqual(subscription.plan, SubscriptionPlan.PREMIUM)
        self.assertEqual(subscription.status, SubscriptionStatus.ACTIVE)

    def test_cancellation_request_creation(self):
        """Test CancellationRequest dataclass creation."""
        request = CancellationRequest(
            user_id="test-user",
            reason_category="cost",
            reason_notes="Service too expensive",
            processed_by="admin-user",
        )

        self.assertEqual(request.user_id, "test-user")
        self.assertEqual(request.reason_category, "cost")
        self.assertEqual(request.reason_notes, "Service too expensive")
        self.assertEqual(request.processed_by, "admin-user")

    def test_quiet_hours_config(self):
        """Test QuietHoursConfig dataclass."""
        config = QuietHoursConfig(
            enabled=True, start_hour=22, end_hour=8, timezone="UTC"
        )

        self.assertTrue(config.enabled)
        self.assertEqual(config.start_hour, 22)
        self.assertEqual(config.end_hour, 8)
        self.assertEqual(config.timezone, "UTC")


if __name__ == "__main__":
    unittest.main()
