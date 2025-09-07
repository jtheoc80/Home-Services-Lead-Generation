"""
Stripe client singleton for secure payment processing.

This module provides a singleton Stripe client configured with the secret key
from environment variables. All Stripe API operations should use this client.
"""

import os
import stripe
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class StripeClient:
    """Singleton Stripe client with configuration management."""

    _instance: Optional["StripeClient"] = None
    _client_initialized: bool = False

    def __new__(cls) -> "StripeClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._client_initialized:
            self._configure_stripe()
            self._client_initialized = True

    def _configure_stripe(self):
        """Configure Stripe with API key and settings."""
        self.secret_key = os.getenv("STRIPE_SECRET_KEY")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        self.publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY")

        if not self.secret_key:
            raise ValueError("Stripe configuration error: missing required secret key")

        # Set the global Stripe API key
        stripe.api_key = self.secret_key

        # Store price IDs from environment
        self.price_starter_monthly = os.getenv("STRIPE_PRICE_STARTER_MONTHLY")
        self.price_pro_monthly = os.getenv("STRIPE_PRICE_PRO_MONTHLY")
        self.price_lead_credit_pack = os.getenv("STRIPE_PRICE_LEAD_CREDIT_PACK")
        self.tax_rate_id = os.getenv("STRIPE_TAX_RATE_ID")

        # Billing URLs
        self.success_url = os.getenv(
            "BILLING_SUCCESS_URL", "https://localhost:3000/billing/success"
        )
        self.cancel_url = os.getenv(
            "BILLING_CANCEL_URL", "https://localhost:3000/billing/cancel"
        )

    @property
    def is_configured(self) -> bool:
        """Check if Stripe is properly configured."""
        return bool(self.secret_key and self.webhook_secret)

    def test_connection(self) -> bool:
        """Test Stripe API connection with a safe GET request."""
        try:
            # Use a safe GET request to test the API key
            stripe.Product.list(limit=1)
            return True
        except Exception:
            return False

    def get_price_ids(self) -> dict:
        """Get all configured price IDs."""
        return {
            "starter_monthly": self.price_starter_monthly,
            "pro_monthly": self.price_pro_monthly,
            "lead_credit_pack": self.price_lead_credit_pack,
        }


# Global instance
_stripe_client: Optional[StripeClient] = None


def get_stripe_client() -> StripeClient:
    """Get the singleton Stripe client instance."""
    global _stripe_client
    if _stripe_client is None:
        _stripe_client = StripeClient()
    return _stripe_client
