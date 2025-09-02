"""
Test cases for the normalize_trade function.
"""
from permit_leads.enrich import normalize_trade


class TestNormalizeTrade:
    """Test cases for trade normalization logic."""

    def test_normalize_trade_roofing_priority(self):
        """Test that roofing gets highest priority among trades."""
        raw_permit = {
            'work_description': 'Roof replacement and electrical work',
            'permit_type': 'Residential',
            'permit_class': 'Building'
        }
        result = normalize_trade(raw_permit)
        assert result == 'Roofing'

    def test_normalize_trade_solar_priority(self):
        """Test solar gets high priority."""
        raw_permit = {
            'work_description': 'Solar panel installation with electrical',
            'permit_type': 'Residential'
        }
        result = normalize_trade(raw_permit)
        assert result == 'Solar'

    def test_normalize_trade_kitchen_priority(self):
        """Test kitchen remodel gets prioritized over basic trades."""
        raw_permit = {
            'work_description': 'Kitchen remodel with plumbing and electrical',
            'permit_type': 'Residential'
        }
        result = normalize_trade(raw_permit)
        assert result == 'Kitchen'

    def test_normalize_trade_hvac_keyword(self):
        """Test HVAC trade detection."""
        raw_permit = {
            'work_description': 'HVAC system installation',
            'permit_type': 'Mechanical'
        }
        result = normalize_trade(raw_permit)
        assert result == 'Hvac'

    def test_normalize_trade_electrical_keyword(self):
        """Test electrical trade detection."""
        raw_permit = {
            'work_description': 'Electrical panel upgrade',
            'permit_type': 'Electrical'
        }
        result = normalize_trade(raw_permit)
        assert result == 'Electrical'

    def test_normalize_trade_plumbing_keyword(self):
        """Test plumbing trade detection."""
        raw_permit = {
            'work_description': 'Water line repair and plumbing',
            'permit_type': 'Plumbing'
        }
        result = normalize_trade(raw_permit)
        assert result == 'Plumbing'

    def test_normalize_trade_permit_type_fallback(self):
        """Test fallback to permit_type when no keywords match."""
        raw_permit = {
            'work_description': 'General construction work',
            'permit_type': 'Residential Building',
            'permit_class': ''
        }
        result = normalize_trade(raw_permit)
        assert result == 'General Construction'

    def test_normalize_trade_commercial_permit_type(self):
        """Test commercial permit type mapping."""
        raw_permit = {
            'work_description': 'Office renovation',
            'permit_type': 'Commercial',
            'permit_class': ''
        }
        result = normalize_trade(raw_permit)
        assert result == 'Commercial'

    def test_normalize_trade_permit_class_fallback(self):
        """Test fallback to permit_class when permit_type is empty."""
        raw_permit = {
            'work_description': 'Construction work',
            'permit_type': '',
            'permit_class': 'Building Permit'
        }
        result = normalize_trade(raw_permit)
        assert result == 'Building Permit'

    def test_normalize_trade_general_fallback(self):
        """Test final fallback to 'General' when no information available."""
        raw_permit = {
            'work_description': '',
            'permit_type': '',
            'permit_class': ''
        }
        result = normalize_trade(raw_permit)
        assert result == 'General'

    def test_normalize_trade_none_values(self):
        """Test handling of None values."""
        raw_permit = {
            'work_description': None,
            'permit_type': None,
            'permit_class': None
        }
        result = normalize_trade(raw_permit)
        assert result == 'General'

    def test_normalize_trade_empty_dict(self):
        """Test handling of empty dictionary."""
        raw_permit = {}
        result = normalize_trade(raw_permit)
        assert result == 'General'

    def test_normalize_trade_multiple_keywords_priority(self):
        """Test that highest priority trade is selected from multiple matches."""
        raw_permit = {
            'work_description': 'Pool installation with electrical and plumbing work',
            'permit_type': 'Residential'
        }
        result = normalize_trade(raw_permit)
        # Pool (priority 8) should win over electrical (4) and plumbing (4)
        assert result == 'Pool'

    def test_normalize_trade_case_insensitive(self):
        """Test that keyword matching is case insensitive."""
        raw_permit = {
            'work_description': 'ROOF REPLACEMENT AND REPAIR',
            'permit_type': 'RESIDENTIAL'
        }
        result = normalize_trade(raw_permit)
        assert result == 'Roofing'

    def test_normalize_trade_alternative_field_names(self):
        """Test that function works with alternative field names."""
        raw_permit = {
            'description': 'Kitchen renovation project',  # Alternative to work_description
            'work_class': 'Residential'  # Alternative to permit_class
        }
        result = normalize_trade(raw_permit)
        assert result == 'Kitchen'

    def test_normalize_trade_null_string_values(self):
        """Test handling of 'null' and 'none' string values."""
        raw_permit = {
            'work_description': 'fence installation',
            'permit_type': 'null',
            'permit_class': 'none'
        }
        result = normalize_trade(raw_permit)
        assert result == 'Fence'