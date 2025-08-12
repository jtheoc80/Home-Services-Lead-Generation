"""
Unit tests for scoring v0 algorithm.

These tests validate that the v0 scoring algorithm produces exact matches
with the expected scores from our golden fixture dataset.
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, Any

from scoring.v0 import score_v0, validate_lead_input
from tests.scoring.fixtures import (
    GOLDEN_LEAD_FIXTURES,
    get_lead_by_id,
    get_leads_by_score_range,
    get_high_score_leads,
    get_low_score_leads
)


class TestScoreV0:
    """Test cases for the v0 scoring algorithm."""

    def test_score_v0_golden_fixtures(self):
        """
        Test that scoring v0 produces exact matches with golden fixture scores.
        
        This is the critical test that ensures the scoring algorithm produces
        deterministic and expected results for all 50 test cases.
        """
        failures = []
        
        for fixture in GOLDEN_LEAD_FIXTURES:
            # Extract lead data (excluding expected_score)
            lead_data = {k: v for k, v in fixture.items() if k != 'expected_score'}
            expected_score = fixture['expected_score']
            
            # Score the lead
            result = score_v0(lead_data)
            actual_score = result['score']
            
            # Check exact match
            if actual_score != expected_score:
                failures.append({
                    'lead_id': fixture['lead_id'],
                    'expected': expected_score,
                    'actual': actual_score,
                    'diff': actual_score - expected_score,
                    'reasons': result['reasons']
                })
        
        # Report all failures
        if failures:
            failure_report = "\n".join([
                f"Lead {f['lead_id']}: expected {f['expected']}, got {f['actual']} (diff: {f['diff']:+d})"
                for f in failures
            ])
            pytest.fail(f"Scoring mismatches found:\n{failure_report}")

    def test_score_v0_returns_valid_structure(self):
        """Test that score_v0 returns the expected data structure."""
        lead = get_lead_by_id("lead-001")
        result = score_v0(lead)
        
        # Check return structure
        assert isinstance(result, dict)
        assert 'score' in result
        assert 'reasons' in result
        assert isinstance(result['score'], int)
        assert isinstance(result['reasons'], list)
        assert all(isinstance(reason, str) for reason in result['reasons'])
        
        # Check score range
        assert 0 <= result['score'] <= 100
        
        # Check that reasons are provided
        assert len(result['reasons']) > 0

    def test_score_v0_recency_scoring(self):
        """Test recency scoring component."""
        base_lead = get_lead_by_id("lead-001")
        
        # Test very recent lead (today)
        recent_lead = base_lead.copy()
        recent_lead['created_at'] = datetime.now(timezone.utc).isoformat()
        result = score_v0(recent_lead)
        
        # Should get maximum recency points (25 * 3 = 75)
        assert any("Very recent lead" in reason for reason in result['reasons'])
        
        # Test older lead
        older_lead = base_lead.copy()
        older_lead['created_at'] = "2024-01-01T00:00:00Z"  # Much older
        result = score_v0(older_lead)
        
        # Should get minimal or no recency points
        assert any("Older lead" in reason for reason in result['reasons'])

    def test_score_v0_trade_scoring(self):
        """Test trade matching scoring component."""
        base_lead = get_lead_by_id("lead-001")
        
        # Test high-value trade (roofing)
        roofing_lead = base_lead.copy()
        roofing_lead['trade_tags'] = ['roofing']
        result = score_v0(roofing_lead)
        
        assert any("roofing" in reason for reason in result['reasons'])
        
        # Test low-value trade (fence)
        fence_lead = base_lead.copy()
        fence_lead['trade_tags'] = ['fence']
        result = score_v0(fence_lead)
        
        fence_score = result['score']
        roofing_score = score_v0(roofing_lead)['score']
        
        # Roofing should score higher than fence
        assert roofing_score > fence_score
        
        # Test no trade tags
        no_trade_lead = base_lead.copy()
        no_trade_lead['trade_tags'] = []
        result = score_v0(no_trade_lead)
        
        assert any("No trade categories identified" in reason for reason in result['reasons'])

    def test_score_v0_value_scoring(self):
        """Test project value scoring component."""
        base_lead = get_lead_by_id("lead-001")
        
        # Test high value ($50k+)
        high_value_lead = base_lead.copy()
        high_value_lead['value'] = 75000
        result_high = score_v0(high_value_lead)
        
        # Test medium value ($15k-50k)
        medium_value_lead = base_lead.copy()
        medium_value_lead['value'] = 25000
        result_medium = score_v0(medium_value_lead)
        
        # Test low value (under $5k)
        low_value_lead = base_lead.copy()
        low_value_lead['value'] = 3000
        result_low = score_v0(low_value_lead)
        
        # Higher values should score higher
        assert result_high['score'] > result_medium['score'] > result_low['score']
        
        # Check reason strings
        assert any("$50k+" in reason for reason in result_high['reasons'])
        assert any("$15k-50k" in reason for reason in result_medium['reasons'])
        assert any("Under $5k" in reason for reason in result_low['reasons'])

    def test_score_v0_property_age_scoring(self):
        """Test property age scoring component."""
        base_lead = get_lead_by_id("lead-001")
        
        # Test very old property (25+ years)
        old_lead = base_lead.copy()
        old_lead['year_built'] = 1990  # 34+ years old
        result_old = score_v0(old_lead)
        
        # Test newer property (under 10 years)
        new_lead = base_lead.copy()
        new_lead['year_built'] = 2020  # 4 years old
        result_new = score_v0(new_lead)
        
        # Older properties should score higher (more likely to need work)
        assert result_old['score'] > result_new['score']
        
        # Check reason strings contain age information
        assert any("years old" in reason for reason in result_old['reasons'])
        assert any("years old" in reason for reason in result_new['reasons'])

    def test_score_v0_owner_type_scoring(self):
        """Test owner type scoring component."""
        base_lead = get_lead_by_id("lead-001")
        
        # Test individual owner (highest score)
        individual_lead = base_lead.copy()
        individual_lead['owner_kind'] = 'individual'
        result_individual = score_v0(individual_lead)
        
        # Test LLC owner (medium score)
        llc_lead = base_lead.copy()
        llc_lead['owner_kind'] = 'llc'
        result_llc = score_v0(llc_lead)
        
        # Test corporate owner (lower score)
        corp_lead = base_lead.copy()
        corp_lead['owner_kind'] = 'corporation'
        result_corp = score_v0(corp_lead)
        
        # Individual should score highest
        assert result_individual['score'] >= result_llc['score'] >= result_corp['score']
        
        # Check reason strings
        assert any("Individual owner" in reason for reason in result_individual['reasons'])
        assert any("LLC owner" in reason for reason in result_llc['reasons'])

    def test_score_v0_missing_data_handling(self):
        """Test handling of missing or invalid data."""
        # Test completely minimal lead
        minimal_lead = {
            'lead_id': 'test-minimal'
        }
        result = score_v0(minimal_lead)
        
        # Should still return valid structure with low score
        assert isinstance(result, dict)
        assert 'score' in result and 'reasons' in result
        assert 0 <= result['score'] <= 100
        assert len(result['reasons']) > 0
        
        # Test lead with some missing fields
        partial_lead = {
            'lead_id': 'test-partial',
            'created_at': '2024-12-15T10:00:00Z',
            'trade_tags': ['roofing'],
            # Missing value, year_built, owner_kind
        }
        result = score_v0(partial_lead)
        
        assert result['score'] > 0  # Should still get points for recency and trade
        assert any("unknown" in reason.lower() for reason in result['reasons'])

    def test_score_v0_edge_cases(self):
        """Test edge cases and boundary conditions."""
        base_lead = get_lead_by_id("lead-001")
        
        # Test exact value boundaries
        boundary_tests = [
            (4999, "Under $5k"),
            (5000, "$5k-15k"),
            (14999, "$5k-15k"),
            (15000, "$15k-50k"),
            (49999, "$15k-50k"), 
            (50000, "$50k+")
        ]
        
        for value, expected_desc in boundary_tests:
            test_lead = base_lead.copy()
            test_lead['value'] = value
            result = score_v0(test_lead)
            
            assert any(expected_desc in reason for reason in result['reasons']), \
                f"Value {value} should produce '{expected_desc}' description"

    def test_score_v0_multiple_trade_tags(self):
        """Test handling of multiple trade tags (should pick highest scoring)."""
        base_lead = get_lead_by_id("lead-001")
        
        # Mix high and low value trades
        multi_trade_lead = base_lead.copy()
        multi_trade_lead['trade_tags'] = ['fence', 'roofing', 'electrical']  # roofing should win
        result = score_v0(multi_trade_lead)
        
        # Should use roofing (highest scoring trade)
        assert any("roofing" in reason for reason in result['reasons'])
        assert not any("fence" in reason for reason in result['reasons'])

    def test_score_v0_score_capping(self):
        """Test that scores are properly capped at 100."""
        # Create a lead that would theoretically score very high
        perfect_lead = {
            'lead_id': 'test-perfect',
            'created_at': datetime.now(timezone.utc).isoformat(),  # Maximum recency
            'trade_tags': ['roofing'],  # Highest trade score
            'value': 100000,  # Very high value
            'year_built': 1970,  # Very old property
            'owner_kind': 'individual'  # Best owner type
        }
        
        result = score_v0(perfect_lead)
        
        # Score should be capped at 100
        assert result['score'] <= 100


class TestValidateLeadInput:
    """Test cases for lead input validation."""

    def test_validate_lead_input_valid_lead(self):
        """Test validation with a valid lead."""
        valid_lead = get_lead_by_id("lead-001")
        errors = validate_lead_input(valid_lead)
        
        assert len(errors) == 0

    def test_validate_lead_input_missing_fields(self):
        """Test validation with missing fields."""
        minimal_lead = {'lead_id': 'test'}
        errors = validate_lead_input(minimal_lead)
        
        # Should have no errors (missing fields are warnings, not errors)
        assert len(errors) == 0

    def test_validate_lead_input_invalid_types(self):
        """Test validation with invalid data types."""
        invalid_lead = {
            'lead_id': 'test',
            'value': 'not-a-number',  # Should be numeric
            'year_built': 'not-a-year',  # Should be integer
            'trade_tags': 'not-a-list'  # Should be list
        }
        errors = validate_lead_input(invalid_lead)
        
        assert len(errors) > 0
        assert any('value' in error for error in errors)
        assert any('year_built' in error for error in errors)
        assert any('trade_tags' in error for error in errors)

    def test_validate_lead_input_invalid_ranges(self):
        """Test validation with values outside valid ranges."""
        invalid_lead = {
            'lead_id': 'test',
            'year_built': 1500,  # Too old
        }
        errors = validate_lead_input(invalid_lead)
        
        assert len(errors) > 0
        assert any('year_built' in error for error in errors)


class TestScoringConsistency:
    """Test scoring consistency and determinism."""

    def test_scoring_is_deterministic(self):
        """Test that scoring the same lead multiple times gives same result."""
        lead = get_lead_by_id("lead-001")
        
        # Score the same lead multiple times
        results = [score_v0(lead) for _ in range(5)]
        
        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result['score'] == first_result['score']
            assert result['reasons'] == first_result['reasons']

    def test_score_distribution(self):
        """Test that fixture scores have reasonable distribution."""
        all_scores = [fixture['expected_score'] for fixture in GOLDEN_LEAD_FIXTURES]
        
        # Check we have good distribution across score ranges
        low_scores = len([s for s in all_scores if s < 40])
        medium_scores = len([s for s in all_scores if 40 <= s < 80])
        high_scores = len([s for s in all_scores if s >= 80])
        
        # Should have leads in all score ranges
        assert low_scores > 0, "Should have some low-scoring leads"
        assert medium_scores > 0, "Should have some medium-scoring leads"
        assert high_scores > 0, "Should have some high-scoring leads"
        
        # Most leads should be in medium to high range (realistic for quality leads)
        assert medium_scores + high_scores > low_scores

    def test_high_score_leads_characteristics(self):
        """Test that high-scoring leads have expected characteristics."""
        high_score_leads = get_high_score_leads(80)
        
        for lead in high_score_leads:
            # High-scoring leads should generally be recent
            created_at = datetime.fromisoformat(lead['created_at'].replace('Z', '+00:00'))
            days_old = (datetime.now(timezone.utc) - created_at).days
            
            # Most high-scoring leads should be relatively recent (within 30 days)
            # or have other very strong factors
            if days_old > 30:
                # If not recent, should have high-value trade or very high project value
                assert (
                    any(tag in ['roofing', 'kitchen', 'bath', 'foundation'] for tag in lead.get('trade_tags', [])) or
                    (lead.get('value', 0) > 40000)
                ), f"Lead {lead['lead_id']} is old but lacks other high-value factors"

    def test_low_score_leads_characteristics(self):
        """Test that low-scoring leads have expected characteristics."""
        low_score_leads = get_low_score_leads(50)
        
        for lead in low_score_leads:
            # Low-scoring leads should have limiting factors
            created_at = datetime.fromisoformat(lead['created_at'].replace('Z', '+00:00'))
            days_old = (datetime.now(timezone.utc) - created_at).days
            
            # Should be old, low value, bad trade match, or new property
            limiting_factors = [
                days_old > 20,  # Old lead
                (lead.get('value') or 0) < 15000,  # Low value (handle None)
                not lead.get('trade_tags') or lead['trade_tags'] == [] or 'fence' in lead.get('trade_tags', []),  # Poor trade match
                lead.get('year_built', 1900) > 2010,  # New property
                lead.get('owner_kind') in ['corporation', 'llc']  # Non-individual owner
            ]
            
            assert any(limiting_factors), \
                f"Lead {lead['lead_id']} has low score but no obvious limiting factors"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])