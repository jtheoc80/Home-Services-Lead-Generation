#!/usr/bin/env python3
"""
Unit tests for TX permits integration components.

Tests the key normalizer and scoring functions with fixture data
from each of the three TX permit sources.
"""

import unittest
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from normalizers.permits import normalize, validate_normalized_record
from normalizers.field_aliases import PERMIT_ALIASES
from scoring.v0 import score_v0, validate_lead_input

# Use relative imports for project modules
from ..normalizers.permits import normalize, validate_normalized_record
from ..normalizers.field_aliases import PERMIT_ALIASES
from ..scoring.v0 import score_v0, validate_lead_input
class TestTXPermitsIntegration(unittest.TestCase):
    """Test suite for TX permits integration."""

    def setUp(self):
        """Set up test fixtures."""
        # Dallas permit fixture (Socrata format)
        self.dallas_permit = {
            'permit_number': 'DL2024-001',
            'issued_date': '2024-01-15T10:30:00.000',
            'work_description': 'Residential roofing replacement',
            'permit_status': 'Issued',
            'estimated_cost': '15000',
            'address': '123 Main St, Dallas, TX 75201',
            'contractor_name': 'ABC Roofing Co',
            'permit_type': 'Building'
        }
        
        # Austin permit fixture (Socrata format)  
        self.austin_permit = {
            'permit_num': 'AUS-2024-456',
            'issued_date': '2024-01-10T14:20:00.000',
            'description': 'Kitchen renovation',
            'status_current': 'Active',
            'declared_value': '45000',
            'project_address': '456 Oak Ave, Austin, TX 78701',
            'permit_class': 'Commercial'
        }
        
        # Arlington permit fixture (ArcGIS format)
        self.arlington_permit = {
            'OBJECTID': 12345,
            'PERMIT_NUM': 'ARL-24-789',
            'ISSUE_DATE': 1705507200000,  # Unix timestamp in milliseconds
            'DESCRIPTION': 'Pool installation with electrical',
            'STATUS': 'APPROVED',
            'VALUATION': 25000,
            'ADDRESS': '789 Elm St, Arlington, TX 76001',
            'X': -97.108,  # Longitude
            'Y': 32.736    # Latitude
        }

    def test_dallas_permit_normalization(self):
        """Test normalization of Dallas permit data."""
        source_meta = {
            'id': 'dallas_permits',
            'jurisdiction': 'Dallas',
            'city': 'Dallas',
            'county': 'Dallas'
        }
        
        normalized = normalize(source_meta, self.dallas_permit)
        
        # Verify key fields
        self.assertEqual(normalized['source_id'], 'dallas_permits')
        self.assertEqual(normalized['permit_id'], 'DL2024-001')
        self.assertEqual(normalized['city'], 'Dallas')
        self.assertEqual(normalized['description'], 'Residential roofing replacement')
        self.assertEqual(normalized['valuation'], 15000.0)
        self.assertEqual(normalized['contractor_name'], 'ABC Roofing Co')
        
        # Verify normalization worked
        self.assertIsInstance(normalized['issued_at'], datetime)
        self.assertIsNotNone(normalized['record_hash'])
        
        # Validate the normalized record
        errors = validate_normalized_record(normalized)
        self.assertEqual(len(errors), 0, f"Validation errors: {errors}")

    def test_austin_permit_normalization(self):
        """Test normalization of Austin permit data."""
        source_meta = {
            'id': 'austin_permits',
            'jurisdiction': 'Austin',
            'city': 'Austin',
            'county': 'Travis'
        }
        
        normalized = normalize(source_meta, self.austin_permit)
        
        # Verify key fields
        self.assertEqual(normalized['source_id'], 'austin_permits')
        self.assertEqual(normalized['permit_id'], 'AUS-2024-456')
        self.assertEqual(normalized['city'], 'Austin')
        self.assertEqual(normalized['description'], 'Kitchen renovation')
        self.assertEqual(normalized['valuation'], 45000.0)
        
        # Validate the normalized record
        errors = validate_normalized_record(normalized)
        self.assertEqual(len(errors), 0, f"Validation errors: {errors}")

    def test_arlington_permit_normalization(self):
        """Test normalization of Arlington permit data.""" 
        source_meta = {
            'id': 'arlington_permits',
            'jurisdiction': 'Arlington',
            'city': 'Arlington',
            'county': 'Tarrant'
        }
        
        normalized = normalize(source_meta, self.arlington_permit)
        
        # Verify key fields
        self.assertEqual(normalized['source_id'], 'arlington_permits')
        self.assertEqual(normalized['permit_id'], str(self.arlington_permit['OBJECTID']))
        self.assertEqual(normalized['city'], 'Arlington')
        self.assertEqual(normalized['description'], 'Pool installation with electrical')
        self.assertEqual(normalized['valuation'], 25000.0)
        self.assertEqual(normalized['longitude'], -97.108)
        self.assertEqual(normalized['latitude'], 32.736)
        
        # Validate the normalized record
        errors = validate_normalized_record(normalized)
        self.assertEqual(len(errors), 0, f"Validation errors: {errors}")

    def test_scoring_v0_roofing_permit(self):
        """Test v0 scoring algorithm with roofing permit."""
        lead_data = {
            'created_at': '2024-01-15T10:30:00Z',
            'trade_tags': ['roofing'],
            'value': 15000,
            'year_built': 1995,
            'owner_kind': 'individual'
        }
        
        # Validate input
        errors = validate_lead_input(lead_data)
        self.assertEqual(len(errors), 0, f"Input validation errors: {errors}")
        
        # Score the lead
        result = score_v0(lead_data)
        
        # Verify response structure
        self.assertIn('score', result)
        self.assertIn('reasons', result)
        self.assertIsInstance(result['score'], int)
        self.assertIsInstance(result['reasons'], list)
        
        # Verify scoring logic
        self.assertGreaterEqual(result['score'], 0)
        self.assertLessEqual(result['score'], 100)
        
        # Roofing should get high trade score
        self.assertGreater(result['score'], 70, "Roofing leads should score high")
        
        # Verify reasons include key components
        reasons_text = ' '.join(result['reasons'])
        self.assertIn('roofing', reasons_text.lower())
        self.assertIn('individual owner', reasons_text.lower())

    def test_scoring_v0_kitchen_permit(self):
        """Test v0 scoring algorithm with kitchen permit."""
        lead_data = {
            'created_at': '2024-01-10T14:20:00Z',
            'trade_tags': ['kitchen'],
            'value': 45000,
            'year_built': 2010,
            'owner_kind': 'llc'
        }
        
        result = score_v0(lead_data)
        
        # Kitchen + high value should score well
        self.assertGreater(result['score'], 60, "Kitchen renovations should score well")
        
        # Verify high value project scoring
        reasons_text = ' '.join(result['reasons'])
        self.assertIn('kitchen', reasons_text.lower())
        self.assertIn('$15k-50k', reasons_text)

    def test_scoring_v0_pool_permit(self):
        """Test v0 scoring algorithm with pool permit."""
        lead_data = {
            'created_at': '2024-01-12T09:00:00Z',
            'trade_tags': ['pool'],
            'value': 25000,
            'year_built': 1988,
            'owner_kind': 'individual'
        }
        
        result = score_v0(lead_data)
        
        # Pool + individual owner should score reasonably well
        self.assertGreater(result['score'], 50, "Pool installations should score moderately")
        
        # Verify pool trade match
        reasons_text = ' '.join(result['reasons'])
        self.assertIn('pool', reasons_text.lower())

    def test_field_aliases_coverage(self):
        """Test that field aliases cover expected permit fields."""
        required_fields = [
            'permit_id', 'issued_at', 'status', 'permit_type', 
            'description', 'address_full', 'valuation'
        ]
        
        for field in required_fields:
            self.assertIn(field, PERMIT_ALIASES, 
                         f"Missing alias configuration for {field}")
            self.assertIsInstance(PERMIT_ALIASES[field], list,
                                f"Aliases for {field} should be a list")
            self.assertGreater(len(PERMIT_ALIASES[field]), 0,
                             f"No aliases defined for {field}")

    def test_coordinate_validation(self):
        """Test that Texas coordinate validation works."""
        # Valid Texas coordinates (Arlington)
        source_meta = {
            'id': 'test_source',
            'jurisdiction': 'Test',
            'city': 'Test',
            'county': 'Test'
        }
        
        valid_record = {
            'permit_number': 'TEST123',
            'latitude': '32.736',
            'longitude': '-97.108'
        }
        
        normalized = normalize(source_meta, valid_record)
        self.assertIsNotNone(normalized['geom'], "Valid TX coordinates should create geometry")
        
        # Invalid coordinates (outside Texas)
        invalid_record = {
            'permit_number': 'TEST456', 
            'latitude': '40.7128',  # New York latitude
            'longitude': '-74.0060'  # New York longitude
        }
        
        normalized_invalid = normalize(source_meta, invalid_record)
        self.assertIsNone(normalized_invalid['geom'], "Invalid coordinates should not create geometry")


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)