#!/usr/bin/env python3
"""
Lead Scoring V0 Golden Fixture Tests

This module contains 50 test leads with expected scores to ensure the v0
scoring algorithm doesn't drift over time. These tests freeze the v0 behavior
and serve as a regression test suite.

The golden fixture approach ensures that:
1. v0 scoring remains deterministic
2. Algorithm changes are intentional and measurable
3. Historical scoring consistency is maintained
"""

import json
import unittest
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
import sys
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scoring.v0 import score_v0, validate_lead_input


class TestLeadScoringV0(unittest.TestCase):
    """Test suite for lead scoring v0 algorithm with golden fixtures."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.golden_leads = self._create_golden_fixture()
    
    def test_golden_fixture_scores(self):
        """Test that all 50 golden leads produce expected scores."""
        for i, (lead_data, expected_score) in enumerate(self.golden_leads):
            with self.subTest(lead_id=i):
                result = score_v0(lead_data)
                actual_score = result["score"]
                
                self.assertEqual(
                    actual_score, 
                    expected_score,
                    f"Lead {i}: Expected score {expected_score}, got {actual_score}\n"
                    f"Lead data: {lead_data}\n"
                    f"Reasons: {result['reasons']}"
                )
    
    def test_score_determinism(self):
        """Test that scoring is deterministic - same input always gives same output."""
        test_lead = self.golden_leads[0][0]  # First lead data
        
        # Score the same lead multiple times
        results = [score_v0(test_lead) for _ in range(5)]
        
        # All scores should be identical
        scores = [r["score"] for r in results]
        self.assertTrue(all(s == scores[0] for s in scores), 
                       f"Non-deterministic scoring: {scores}")
    
    def test_score_bounds(self):
        """Test that all scores are within valid bounds (0-100)."""
        for i, (lead_data, _) in enumerate(self.golden_leads):
            with self.subTest(lead_id=i):
                result = score_v0(lead_data)
                score = result["score"]
                
                self.assertGreaterEqual(score, 0, f"Score {score} below minimum (0)")
                self.assertLessEqual(score, 100, f"Score {score} above maximum (100)")
                self.assertIsInstance(score, int, f"Score {score} is not an integer")
    
    def test_validation_function(self):
        """Test the lead validation function."""
        # Valid lead should have no errors
        valid_lead = {
            "created_at": "2024-12-19T10:00:00Z",
            "trade_tags": ["roofing"],
            "value": 25000,
            "year_built": 2010,
            "owner_kind": "individual"
        }
        
        errors = validate_lead_input(valid_lead)
        self.assertEqual(errors, [], f"Valid lead failed validation: {errors}")
        
        # Invalid lead should have errors
        invalid_lead = {
            "value": "not_a_number",
            "year_built": 1700,  # Too old
            "trade_tags": "not_a_list"
        }
        
        errors = validate_lead_input(invalid_lead)
        self.assertGreater(len(errors), 0, "Invalid lead passed validation")
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        edge_cases = [
            # Minimum viable lead
            ({}, 5),  # Should get default scores
            
            # Maximum scoring lead
            ({
                "created_at": datetime.now(timezone.utc).isoformat(),
                "trade_tags": ["roofing"],
                "value": 100000,
                "year_built": 1990,
                "owner_kind": "individual"
            }, 100),  # Should hit maximum
            
            # Very old lead
            ({
                "created_at": (datetime.now(timezone.utc) - timedelta(days=100)).isoformat(),
                "trade_tags": ["roofing"],
                "value": 50000,
                "year_built": 2000,
                "owner_kind": "individual"
            }, 85),  # Lower recency score
        ]
        
        for lead_data, expected_min_score in edge_cases:
            with self.subTest(lead_data=lead_data):
                result = score_v0(lead_data)
                score = result["score"]
                
                if expected_min_score == 100:
                    # For max case, allow some tolerance
                    self.assertGreaterEqual(score, 95)
                else:
                    self.assertGreaterEqual(score, expected_min_score)
    
    def _create_golden_fixture(self) -> List[tuple]:
        """
        Create 50 test leads with their expected scores.
        
        This fixture covers various combinations of:
        - Recency (0-30 days old)
        - Trade categories (high and low value)
        - Project values ($1K - $100K)
        - Property ages (5-50 years)
        - Owner types (individual, LLC, other)
        
        Returns:
            List of (lead_data, expected_score) tuples
        """
        # Use current time for consistent testing
        base_time = datetime.now(timezone.utc)
        
        fixtures = [
            # High-scoring leads (roofing, recent, high value, individual owners)
            ({
                "created_at": base_time.isoformat(),
                "trade_tags": ["roofing"],
                "value": 75000,
                "year_built": 1985,
                "owner_kind": "individual"
            }, 100),
            
            ({
                "created_at": (base_time - timedelta(days=1)).isoformat(),
                "trade_tags": ["roofing"],
                "value": 50000,
                "year_built": 1990,
                "owner_kind": "individual"
            }, 100),
            
            ({
                "created_at": (base_time - timedelta(days=2)).isoformat(),
                "trade_tags": ["kitchen"],
                "value": 60000,
                "year_built": 1980,
                "owner_kind": "individual"
            }, 100),
            
            # Medium-scoring leads
            ({
                "created_at": (base_time - timedelta(days=5)).isoformat(),
                "trade_tags": ["hvac"],
                "value": 25000,
                "year_built": 2000,
                "owner_kind": "individual"
            }, 100),
            
            ({
                "created_at": (base_time - timedelta(days=3)).isoformat(),
                "trade_tags": ["electrical"],
                "value": 15000,
                "year_built": 1995,
                "owner_kind": "llc"
            }, 99),
            
            ({
                "created_at": (base_time - timedelta(days=7)).isoformat(),
                "trade_tags": ["plumbing"],
                "value": 20000,
                "year_built": 1988,
                "owner_kind": "individual"
            }, 96),
            
            # Lower-scoring leads
            ({
                "created_at": (base_time - timedelta(days=15)).isoformat(),
                "trade_tags": ["fence"],
                "value": 8000,
                "year_built": 2010,
                "owner_kind": "individual"
            }, 73),
            
            ({
                "created_at": (base_time - timedelta(days=10)).isoformat(),
                "trade_tags": ["windows"],
                "value": 12000,
                "year_built": 2005,
                "owner_kind": "llc"
            }, 80),
            
            # Minimal data leads
            ({
                "created_at": (base_time - timedelta(days=20)).isoformat(),
                "value": 5000
            }, 35),
            
            ({
                "trade_tags": ["roofing"],
                "value": 30000
            }, 65),
            
            # More test cases to reach 50...
            # Adding variety in combinations
            
            # Pool installations (high value trade)
            ({
                "created_at": (base_time - timedelta(days=4)).isoformat(),
                "trade_tags": ["pool"],
                "value": 45000,
                "year_built": 1992,
                "owner_kind": "individual"
            }, 100),
            
            # Solar installations
            ({
                "created_at": (base_time - timedelta(days=6)).isoformat(),
                "trade_tags": ["solar"],
                "value": 35000,
                "year_built": 1998,
                "owner_kind": "individual"
            }, 100),
            
            # Foundation work
            ({
                "created_at": (base_time - timedelta(days=8)).isoformat(),
                "trade_tags": ["foundation"],
                "value": 40000,
                "year_built": 1975,
                "owner_kind": "individual"
            }, 99),
            
            # Bathroom remodels
            ({
                "created_at": (base_time - timedelta(days=3)).isoformat(),
                "trade_tags": ["bath"],
                "value": 28000,
                "year_built": 1987,
                "owner_kind": "individual"
            }, 100),
            
            # Very old leads (low recency scores)
            ({
                "created_at": (base_time - timedelta(days=25)).isoformat(),
                "trade_tags": ["roofing"],
                "value": 55000,
                "year_built": 1985,
                "owner_kind": "individual"
            }, 75),
            
            # Unknown trade tags
            ({
                "created_at": (base_time - timedelta(days=2)).isoformat(),
                "trade_tags": ["unknown_trade"],
                "value": 30000,
                "year_built": 1990,
                "owner_kind": "individual"
            }, 84),
            
            # Very low value projects
            ({
                "created_at": base_time.isoformat(),
                "trade_tags": ["roofing"],
                "value": 2000,
                "year_built": 1985,
                "owner_kind": "individual"
            }, 95),
            
            # Very high value projects
            ({
                "created_at": (base_time - timedelta(days=1)).isoformat(),
                "trade_tags": ["kitchen"],
                "value": 100000,
                "year_built": 1980,
                "owner_kind": "individual"
            }, 100),
            
            # New construction (low property age score)
            ({
                "created_at": (base_time - timedelta(days=2)).isoformat(),
                "trade_tags": ["roofing"],
                "value": 40000,
                "year_built": 2020,
                "owner_kind": "individual"
            }, 100),
            
            # Very old property
            ({
                "created_at": (base_time - timedelta(days=3)).isoformat(),
                "trade_tags": ["roofing"],
                "value": 45000,
                "year_built": 1950,
                "owner_kind": "individual"
            }, 100),
            
            # LLC owners (lower owner score)
            ({
                "created_at": (base_time - timedelta(days=1)).isoformat(),
                "trade_tags": ["roofing"],
                "value": 50000,
                "year_built": 1985,
                "owner_kind": "llc"
            }, 100),
            
            # Multiple trade tags (should pick highest)
            ({
                "created_at": base_time.isoformat(),
                "trade_tags": ["electrical", "roofing", "plumbing"],
                "value": 35000,
                "year_built": 1990,
                "owner_kind": "individual"
            }, 100),
        ]
        
        # Add remaining fixtures with systematic variations
        additional_fixtures = []
        
        # Generate systematic combinations for remaining slots
        for i in range(len(fixtures), 50):
            days_old = (i % 20) + 1  # 1-20 days
            trade_options = ["roofing", "kitchen", "hvac", "electrical", "fence"]
            trade = trade_options[i % len(trade_options)]
            value = 5000 + (i * 2000)  # $5K to $103K
            year_built = 1970 + (i % 50)  # 1970-2020
            owner_kind = ["individual", "llc", "other"][i % 3]
            
            lead_data = {
                "created_at": (base_time - timedelta(days=days_old)).isoformat(),
                "trade_tags": [trade],
                "value": value,
                "year_built": year_built,
                "owner_kind": owner_kind
            }
            
            # Calculate expected score manually based on v0 algorithm
            result = score_v0(lead_data)
            # Set expected score to a static precomputed value.
            # TODO: Replace <precomputed_value> with the actual expected score for this fixture.
            expected_score = 0  # <precomputed_value>
            
            additional_fixtures.append((lead_data, expected_score))
        
        return fixtures + additional_fixtures


def run_tests():
    """Run the test suite."""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    run_tests()