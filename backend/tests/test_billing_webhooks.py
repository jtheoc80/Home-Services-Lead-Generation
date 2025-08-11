"""
Tests for Stripe webhook handling functionality.

This module tests the webhook processing logic using sample Stripe events
without making external API calls.
"""

import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from app.billing_api import (
    handle_checkout_completed,
    handle_invoice_paid,
    handle_invoice_failed,
    handle_subscription_updated
)

# Sample Stripe webhook payloads for testing
SAMPLE_CHECKOUT_COMPLETED = {
    "id": "cs_test_123",
    "object": "checkout.session",
    "mode": "subscription",
    "customer": "cus_test_123",
    "subscription": "sub_test_123",
    "metadata": {
        "user_id": "550e8400-e29b-41d4-a716-446655440000"
    }
}

SAMPLE_CHECKOUT_COMPLETED_CREDITS = {
    "id": "cs_test_456",
    "object": "checkout.session",
    "mode": "payment",
    "customer": "cus_test_123",
    "metadata": {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "type": "credit_pack"
    }
}

SAMPLE_INVOICE_PAID = {
    "id": "in_test_123",
    "object": "invoice",
    "amount_due": 1990,
    "amount_paid": 1990,
    "status": "paid",
    "hosted_invoice_url": "https://invoice.stripe.com/test",
    "metadata": {
        "user_id": "550e8400-e29b-41d4-a716-446655440000"
    }
}

SAMPLE_INVOICE_FAILED = {
    "id": "in_test_456",
    "object": "invoice",
    "amount_due": 1990,
    "amount_paid": 0,
    "status": "payment_failed",
    "subscription": "sub_test_123",
    "metadata": {
        "user_id": "550e8400-e29b-41d4-a716-446655440000"
    }
}

SAMPLE_SUBSCRIPTION_UPDATED = {
    "id": "sub_test_123",
    "object": "subscription",
    "status": "active",
    "current_period_end": 1640995200,  # Jan 1, 2022
    "cancel_at_period_end": False,
    "items": {
        "data": [{
            "price": {
                "id": "price_test_123"
            },
            "quantity": 1
        }]
    }
}

class TestWebhookHandlers:
    """Test webhook event handlers."""

    @pytest.mark.asyncio
    @patch('app.billing_api.get_supabase_client')
    @patch('app.billing_api.stripe.Subscription.retrieve')
    async def test_handle_checkout_completed_subscription(self, mock_stripe_sub, mock_supabase):
        """Test handling successful subscription checkout."""
        # Mock Stripe subscription response
        mock_subscription = Mock()
        mock_subscription.status = "active"
        mock_subscription.current_period_end = 1640995200
        mock_subscription.cancel_at_period_end = False
        mock_subscription.__getitem__ = lambda self, key: {
            "items": {
                "data": [{
                    "price": {"id": "price_test_123"},
                    "quantity": 1
                }]
            }
        }[key]
        mock_stripe_sub.return_value = mock_subscription

        # Mock Supabase client
        mock_client = Mock()
        mock_client.table.return_value.upsert.return_value.execute.return_value = None
        mock_supabase.return_value = mock_client

        # Test the function
        await handle_checkout_completed(SAMPLE_CHECKOUT_COMPLETED)

        # Verify customer update was called
        mock_client.table.assert_any_call("billing_customers")
        
        # Verify subscription upsert was called
        mock_client.table.assert_any_call("billing_subscriptions")

    @pytest.mark.asyncio
    @patch('app.billing_api.get_supabase_client')
    @patch('app.billing_api.grant_credits')
    async def test_handle_checkout_completed_credits(self, mock_grant_credits, mock_supabase):
        """Test handling successful credit pack checkout."""
        # Mock Supabase client
        mock_client = Mock()
        mock_client.table.return_value.upsert.return_value.execute.return_value = None
        mock_supabase.return_value = mock_client
        
        # Mock credit granting
        mock_grant_credits.return_value = True

        # Test the function
        await handle_checkout_completed(SAMPLE_CHECKOUT_COMPLETED_CREDITS)

        # Verify credits were granted
        mock_grant_credits.assert_called_once_with(
            "550e8400-e29b-41d4-a716-446655440000", 
            50
        )

    @pytest.mark.asyncio
    @patch('app.billing_api.get_supabase_client')
    async def test_handle_invoice_paid(self, mock_supabase):
        """Test handling successful invoice payment."""
        # Mock Supabase client
        mock_client = Mock()
        mock_client.table.return_value.upsert.return_value.execute.return_value = None
        mock_supabase.return_value = mock_client

        # Test the function
        await handle_invoice_paid(SAMPLE_INVOICE_PAID)

        # Verify invoice record was created
        mock_client.table.assert_called_with("billing_invoices")

    @pytest.mark.asyncio
    @patch('app.billing_api.get_supabase_client')
    async def test_handle_invoice_failed(self, mock_supabase):
        """Test handling failed invoice payment."""
        # Mock Supabase client
        mock_client = Mock()
        mock_client.table.return_value.upsert.return_value.execute.return_value = None
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = None
        mock_supabase.return_value = mock_client

        # Test the function
        await handle_invoice_failed(SAMPLE_INVOICE_FAILED)

        # Verify invoice record was created
        mock_client.table.assert_any_call("billing_invoices")
        
        # Verify subscription status was updated
        mock_client.table.assert_any_call("billing_subscriptions")

    @pytest.mark.asyncio
    @patch('app.billing_api.get_supabase_client')
    async def test_handle_subscription_updated(self, mock_supabase):
        """Test handling subscription updates."""
        # Mock Supabase client
        mock_client = Mock()
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = None
        mock_supabase.return_value = mock_client

        # Test the function
        await handle_subscription_updated(SAMPLE_SUBSCRIPTION_UPDATED)

        # Verify subscription was updated
        mock_client.table.assert_called_with("billing_subscriptions")

    @pytest.mark.asyncio
    @patch('app.billing_api.get_supabase_client')
    async def test_handle_checkout_completed_no_user_id(self, mock_supabase):
        """Test handling checkout with missing user_id in metadata."""
        session_no_user = {**SAMPLE_CHECKOUT_COMPLETED}
        del session_no_user["metadata"]["user_id"]

        # Should not raise an exception, just log a warning
        await handle_checkout_completed(session_no_user)

        # No database calls should be made
        mock_supabase.assert_not_called()

class TestCreditManagement:
    """Test credit management functions."""

    @pytest.mark.asyncio
    @patch('app.billing_api.get_supabase_client')
    async def test_grant_credits_new_user(self, mock_supabase):
        """Test granting credits to a new user."""
        from app.billing_api import grant_credits
        
        # Mock Supabase client
        mock_client = Mock()
        mock_client.table.return_value.upsert.return_value.execute.return_value = None
        mock_supabase.return_value = mock_client

        # Test the function
        result = await grant_credits("test-user-id", 50)

        # Verify success
        assert result is True
        mock_client.table.assert_called_with("lead_credits")

    @pytest.mark.asyncio
    @patch('app.billing_api.get_supabase_client')
    async def test_use_credits_sufficient_balance(self, mock_supabase):
        """Test using credits when user has sufficient balance."""
        from app.billing_api import use_credits
        
        # Mock Supabase client
        mock_client = Mock()
        
        # Mock select response (user has 100 credits)
        mock_select_response = Mock()
        mock_select_response.data = [{"balance": 100}]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_select_response
        
        # Mock update response
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = None
        
        mock_supabase.return_value = mock_client

        # Test using 1 credit
        result = await use_credits("test-user-id", 1)

        # Verify success
        assert result is True

    @pytest.mark.asyncio
    @patch('app.billing_api.get_supabase_client')
    async def test_use_credits_insufficient_balance(self, mock_supabase):
        """Test using credits when user has insufficient balance."""
        from app.billing_api import use_credits
        
        # Mock Supabase client
        mock_client = Mock()
        
        # Mock select response (user has 0 credits)
        mock_select_response = Mock()
        mock_select_response.data = [{"balance": 0}]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_select_response
        
        mock_supabase.return_value = mock_client

        # Test using 1 credit
        result = await use_credits("test-user-id", 1)

        # Verify failure
        assert result is False

    @pytest.mark.asyncio
    @patch('app.billing_api.get_supabase_client')
    async def test_use_credits_no_record(self, mock_supabase):
        """Test using credits when user has no credit record."""
        from app.billing_api import use_credits
        
        # Mock Supabase client
        mock_client = Mock()
        
        # Mock select response (no records)
        mock_select_response = Mock()
        mock_select_response.data = []
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_select_response
        
        mock_supabase.return_value = mock_client

        # Test using 1 credit
        result = await use_credits("test-user-id", 1)

        # Verify failure
        assert result is False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])