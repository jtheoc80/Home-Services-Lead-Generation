#!/usr/bin/env python3
"""
Example usage of cancellation feedback integration.

This script demonstrates how the cancellation feedback system integrates
with lead scoring to provide both global and personalized adjustments.
"""

import json


def example_cancellation_data():
    """Example cancellation data that would be inserted into the database."""
    return {
        "cancellation_record": {
            "account_id": "contractor-123",
            "canceled_at": "2024-01-15T10:30:00Z",
            "primary_reason": "poor_lead_quality",
            "secondary_reasons": ["leads_not_qualified", "wrong_lead_type"],
            "feedback_text": "Leads were mostly for commercial projects, but I only do residential work",
            "total_leads_purchased": 25,
            "leads_contacted": 20,
            "leads_quoted": 3,
            "leads_won": 1,
            "avg_lead_score": 72.5,
            "preferred_service_areas": ["houston", "katy", "sugar_land"],
            "preferred_trade_types": ["roofing", "siding"],
        }
    }


def example_global_adjustments():
    """Example of how global cancellation adjustments would be calculated."""
    return {
        "city_of_houston": {
            "cancellation_rate": 0.18,  # 18% of contractors cancel
            "avg_canceled_score": 68.5,  # Average score of leads that led to cancellations
            "score_adjustment": -7.2,  # Negative adjustment due to high cancellation rate
            "quality_complaint_rate": 0.35,  # 35% cite poor quality as reason
        },
        "harris_county": {
            "cancellation_rate": 0.12,  # 12% cancellation rate - better
            "avg_canceled_score": 75.0,
            "score_adjustment": -4.8,  # Smaller negative adjustment
            "quality_complaint_rate": 0.20,
        },
    }


def example_personalized_adjustment():
    """Example of personalized adjustment calculation."""
    contractor_history = {
        "account_id": "contractor-123",
        "cancellation_reason": "poor_lead_quality",
        "preferred_trades": ["roofing"],
        "preferred_areas": ["houston"],
    }

    lead_to_score = {
        "id": 456,
        "jurisdiction": "city_of_houston",
        "trade_tags": ["electrical"],  # Doesn't match preference
        "value": 8000,
        "address": "1234 Main St, Dallas, TX",  # Wrong area
    }

    # Calculation logic:
    adjustment = 0.0
    adjustment -= 15.0  # Primary reason was poor_lead_quality
    adjustment -= 5.0  # Trade mismatch (electrical vs roofing)
    adjustment -= 8.0  # Geographic mismatch (Dallas vs Houston)

    return {
        "lead_id": lead_to_score["id"],
        "base_score": 78.5,
        "personalized_adjustment": adjustment,  # -28.0
        "final_score": max(0, 78.5 + adjustment),  # 50.5
        "reasoning": [
            "Contractor previously canceled due to poor lead quality (-15 pts)",
            "Lead trade type doesn't match contractor preference (-5 pts)",
            "Lead location outside contractor's preferred areas (-8 pts)",
        ],
    }


def example_ml_features():
    """Example of how cancellation data becomes ML features."""
    return {
        "training_features": {
            # Original features
            "rating_numeric": 2,  # not_qualified = 2
            "estimated_deal_value": 10000,
            "feedback_age_days": 5,
            "has_contact_issues": False,
            "has_qualification_issues": True,
            # New cancellation features
            "source_cancellation_rate": 0.18,
            "source_avg_cancellation_score": 68.5,
            "contractor_canceled": True,
            "canceled_for_quality": True,
            "canceled_for_wrong_type": False,
            "contractor_win_rate": 0.04,  # 1 win / 25 leads
            "lead_value_log": 9.21,  # log(10000+1)
        },
        "expected_impact": "Lower probability prediction due to high cancellation features",
    }


def example_api_integration():
    """Example of how the API would use the enhanced scoring."""
    return {
        "request": {
            "account_id": "contractor-123",
            "leads": [
                {
                    "id": 789,
                    "jurisdiction": "city_of_houston",
                    "trade_tags": ["roofing"],  # Matches preference
                    "value": 15000,
                    "features": {
                        "source_cancellation_rate": 0.18,
                        "contractor_canceled": True,
                        "contractor_win_rate": 0.04,
                    },
                }
            ],
        },
        "response": {
            "predictions": [
                {
                    "lead_id": 789,
                    "win_probability": 0.65,  # Base ML prediction
                    "adjusted_probability": 0.52,  # After personalization
                    "calibrated_score": 52.0,
                    "personalized_adjustment": -13.0,  # Moderate penalty
                    "predicted_success": True,
                    "confidence": "medium",
                    "reasoning": "Good trade match (+2) but contractor history suggests risk (-15)",
                }
            ]
        },
    }


def main():
    """Print example usage scenarios."""
    print("Cancellation Feedback Integration - Usage Examples")
    print("=" * 55)

    print("\n1. Cancellation Data Collection:")
    print(json.dumps(example_cancellation_data(), indent=2))

    print("\n2. Global Source Adjustments:")
    print(json.dumps(example_global_adjustments(), indent=2))

    print("\n3. Personalized Adjustment Calculation:")
    print(json.dumps(example_personalized_adjustment(), indent=2))

    print("\n4. ML Training Features:")
    print(json.dumps(example_ml_features(), indent=2))

    print("\n5. API Integration Example:")
    print(json.dumps(example_api_integration(), indent=2))

    print("\n" + "=" * 55)
    print("Integration Benefits:")
    print("- Global scoring identifies problematic lead sources")
    print("- Personalized scoring matches contractors to better leads")
    print("- ML model learns from cancellation patterns")
    print("- Reduces churn by improving lead quality over time")


if __name__ == "__main__":
    main()
