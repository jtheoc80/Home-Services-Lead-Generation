#!/usr/bin/env python3
"""
Pricing configuration utility for managing credit offers and pricing tiers.

This module provides configuration for pricing tiers, credit offers,
and payment-related settings from environment variables.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class CreditOffer:
    """Individual credit offer configuration."""

    usd: int
    credits: int

    def __post_init__(self):
        """Validate credit offer data."""
        if self.usd <= 0:
            raise ValueError("USD amount must be positive")
        if self.credits <= 0:
            raise ValueError("Credits amount must be positive")

    @property
    def cost_per_credit(self) -> float:
        """Calculate cost per credit."""
        return self.usd / self.credits

    def savings_vs_oneoff(self, oneoff_cost_per_credit: float) -> float:
        """Calculate savings percentage vs one-off pricing."""
        if oneoff_cost_per_credit <= 0:
            return 0.0
        return max(
            0.0,
            (oneoff_cost_per_credit - self.cost_per_credit)
            / oneoff_cost_per_credit
            * 100,
        )


@dataclass
class PricingConfig:
    """Configuration for pricing and credit offers."""

    credit_offers: Dict[str, CreditOffer]

    @classmethod
    def from_env(cls) -> "PricingConfig":
        """Create configuration from environment variables."""
        # Default credit offers
        default_offers = {
            "starter": {"usd": 199, "credits": 50},
            "pro": {"usd": 499, "credits": 150},
            "oneoff": {"usd": 25, "credits": 5},
        }

        # Load from environment variable if provided
        offers_json = os.getenv("CREDIT_OFFERS_JSON")
        if offers_json:
            try:
                offers_data = json.loads(offers_json)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in CREDIT_OFFERS_JSON: {e}")
                offers_data = default_offers
        else:
            offers_data = default_offers

        # Convert to CreditOffer objects
        credit_offers = {}
        for tier, data in offers_data.items():
            try:
                credit_offers[tier] = CreditOffer(
                    usd=data["usd"], credits=data["credits"]
                )
            except (KeyError, TypeError, ValueError) as e:
                logger.error(f"Invalid credit offer data for tier '{tier}': {e}")
                # Skip invalid offers

        return cls(credit_offers=credit_offers)

    def get_offer(self, tier: str) -> Optional[CreditOffer]:
        """Get credit offer for a specific tier."""
        return self.credit_offers.get(tier)

    def get_all_offers(self) -> Dict[str, CreditOffer]:
        """Get all credit offers."""
        return self.credit_offers.copy()

    def get_pricing_tiers(self) -> list:
        """Get list of available pricing tiers."""
        return list(self.credit_offers.keys())

    def calculate_best_value(self, needed_credits: int) -> Dict[str, Any]:
        """Calculate the best value option for a given number of credits."""
        best_option = None
        best_cost_per_credit = float("inf")
        recommendations = []

        for tier, offer in self.credit_offers.items():
            cost_per_credit = offer.cost_per_credit
            total_cost = needed_credits * cost_per_credit

            # Handle cases where you need fewer credits than the minimum
            if needed_credits <= offer.credits:
                actual_cost = offer.usd
                waste_credits = offer.credits - needed_credits
            else:
                # Need multiple packages
                packages_needed = (needed_credits + offer.credits - 1) // offer.credits
                actual_cost = packages_needed * offer.usd
                total_credits = packages_needed * offer.credits
                waste_credits = total_credits - needed_credits

            recommendations.append(
                {
                    "tier": tier,
                    "cost_per_credit": cost_per_credit,
                    "total_cost": actual_cost,
                    "waste_credits": waste_credits,
                    "efficiency_score": needed_credits
                    / (needed_credits + waste_credits),
                }
            )

            if cost_per_credit < best_cost_per_credit:
                best_cost_per_credit = cost_per_credit
                best_option = tier

        return {
            "best_option": best_option,
            "best_cost_per_credit": best_cost_per_credit,
            "all_options": sorted(
                recommendations, key=lambda x: x["efficiency_score"], reverse=True
            ),
        }


class PricingManager:
    """Manager for pricing configuration and calculations."""

    def __init__(self, config: Optional[PricingConfig] = None):
        self.config = config or PricingConfig.from_env()

    def get_offer_details(self, tier: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a pricing tier."""
        offer = self.config.get_offer(tier)
        if not offer:
            return None

        oneoff_offer = self.config.get_offer("oneoff")
        oneoff_cost_per_credit = oneoff_offer.cost_per_credit if oneoff_offer else 0

        return {
            "tier": tier,
            "usd": offer.usd,
            "credits": offer.credits,
            "cost_per_credit": offer.cost_per_credit,
            "savings_vs_oneoff": (
                offer.savings_vs_oneoff(oneoff_cost_per_credit) if oneoff_offer else 0
            ),
        }

    def get_pricing_summary(self) -> Dict[str, Any]:
        """Get a summary of all pricing options."""
        offers = {}
        for tier in self.config.get_pricing_tiers():
            offers[tier] = self.get_offer_details(tier)

        return {
            "offers": offers,
            "total_tiers": len(offers),
            "available_tiers": list(offers.keys()),
        }

    def recommend_plan(self, monthly_credits_needed: int) -> Dict[str, Any]:
        """Recommend the best pricing plan for monthly credit needs."""
        return self.config.calculate_best_value(monthly_credits_needed)

    def validate_pricing(self) -> bool:
        """Validate pricing configuration."""
        if not self.config.credit_offers:
            logger.error("No credit offers configured")
            return False

        required_tiers = ["starter", "pro", "oneoff"]
        for tier in required_tiers:
            if tier not in self.config.credit_offers:
                logger.warning(f"Recommended tier '{tier}' not found in configuration")

        return True


# Global instance for easy access
_pricing_manager: Optional[PricingManager] = None


def get_pricing_manager() -> PricingManager:
    """Get global pricing manager instance."""
    global _pricing_manager
    if _pricing_manager is None:
        _pricing_manager = PricingManager()
    return _pricing_manager


def get_pricing_config() -> PricingConfig:
    """Get pricing configuration."""
    return get_pricing_manager().config
