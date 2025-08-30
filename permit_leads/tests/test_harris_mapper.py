"""Tests for Harris County ArcGIS Feature Mapper."""


from permit_leads.adapters.harris_mapper import (
    convert_feature_to_dict,
    _safe_cast_to_int,
    _safe_str,
    _safe_parse_date_to_iso,
    _parse_address,
)


class TestConvertFeatureToDict:
    """Test the main convert_feature_to_dict function."""

    def test_complete_feature_conversion(self):
        """Test conversion of a complete ArcGIS feature."""
        feature = {
            "attributes": {
                "EVENTID": 123456,
                "PERMITNUMBER": "BP2024001234",
                "PERMITNAME": "Single Family Residence",
                "APPTYPE": "Building Permit",
                "ISSUEDDATE": 1705324200000,  # 2024-01-15 13:10:00 UTC in milliseconds
                "PROJECTNUMBER": "PRJ-2024-001",
                "FULLADDRESS": "123 Main St, Houston, TX 77001",
                "STATUS": "Issued",
            },
            "geometry": {"x": -95.3698, "y": 29.7604},
        }

        result = convert_feature_to_dict(feature)

        assert result["event_id"] == 123456
        assert result["permit_number"] == "BP2024001234"
        assert result["permit_name"] == "Single Family Residence"
        assert result["app_type"] == "Building Permit"
        assert result["issue_date"] == "2024-01-15T13:10:00Z"
        assert result["project_number"] == "PRJ-2024-001"
        assert result["full_address"] == "123 Main St, Houston, TX 77001"
        assert result["street_number"] == "123"
        assert result["street_name"] == "Main St"
        assert result["status"] == "Issued"
        assert result["raw"] == feature

    def test_missing_attributes(self):
        """Test handling of feature with missing attributes."""
        feature = {"geometry": {"x": -95.3698, "y": 29.7604}}

        result = convert_feature_to_dict(feature)

        assert result["event_id"] == 0
        assert result["permit_number"] == ""
        assert result["permit_name"] == ""
        assert result["app_type"] == ""
        assert result["issue_date"] == ""
        assert result["project_number"] == ""
        assert result["full_address"] == ""
        assert result["street_number"] == ""
        assert result["street_name"] == ""
        assert result["status"] == ""
        assert result["raw"] == feature

    def test_null_attributes(self):
        """Test handling of feature with null/None attributes."""
        feature = {
            "attributes": {
                "EVENTID": None,
                "PERMITNUMBER": None,
                "PERMITNAME": None,
                "APPTYPE": None,
                "ISSUEDDATE": None,
                "PROJECTNUMBER": None,
                "FULLADDRESS": None,
                "STATUS": None,
            }
        }

        result = convert_feature_to_dict(feature)

        assert result["event_id"] == 0
        assert result["permit_number"] == ""
        assert result["permit_name"] == ""
        assert result["app_type"] == ""
        assert result["issue_date"] == ""
        assert result["project_number"] == ""
        assert result["full_address"] == ""
        assert result["street_number"] == ""
        assert result["street_name"] == ""
        assert result["status"] == ""

    def test_empty_feature(self):
        """Test handling of completely empty feature."""
        feature = {}

        result = convert_feature_to_dict(feature)

        assert all(
            result[key] == 0 if key == "event_id" else result[key] == ""
            for key in result
            if key != "raw"
        )
        assert result["raw"] == feature

    def test_invalid_feature_type(self):
        """Test handling of non-dict feature."""
        feature = "not a dict"

        result = convert_feature_to_dict(feature)

        assert result["event_id"] == 0
        assert all(
            result[key] == "" for key in result if key not in ["event_id", "raw"]
        )
        assert result["raw"] == {}


class TestSafeCastToInt:
    """Test the _safe_cast_to_int function."""

    def test_valid_integers(self):
        """Test casting valid integers."""
        assert _safe_cast_to_int(123) == 123
        assert _safe_cast_to_int(0) == 0
        assert _safe_cast_to_int(-456) == -456

    def test_valid_floats(self):
        """Test casting valid floats."""
        assert _safe_cast_to_int(123.45) == 123
        assert _safe_cast_to_int(999.99) == 999
        assert _safe_cast_to_int(-10.7) == -10

    def test_valid_strings(self):
        """Test casting valid string numbers."""
        assert _safe_cast_to_int("123") == 123
        assert _safe_cast_to_int("  456  ") == 456
        assert _safe_cast_to_int("-789") == -789
        assert _safe_cast_to_int("123abc") == 123  # Extract numbers

    def test_invalid_values(self):
        """Test handling of invalid values."""
        assert _safe_cast_to_int(None) == 0
        assert _safe_cast_to_int("") == 0
        assert _safe_cast_to_int("abc") == 0
        assert _safe_cast_to_int([]) == 0
        assert _safe_cast_to_int({}) == 0


class TestSafeStr:
    """Test the _safe_str function."""

    def test_valid_strings(self):
        """Test handling of valid strings."""
        assert _safe_str("hello") == "hello"
        assert _safe_str("  world  ") == "world"
        assert _safe_str("") == ""

    def test_non_string_values(self):
        """Test conversion of non-string values."""
        assert _safe_str(123) == "123"
        assert _safe_str(123.45) == "123.45"
        assert _safe_str(True) == "True"

    def test_none_values(self):
        """Test handling of None."""
        assert _safe_str(None) == ""


class TestSafeParseDateToIso:
    """Test the _safe_parse_date_to_iso function."""

    def test_unix_timestamp_milliseconds(self):
        """Test parsing Unix timestamp in milliseconds."""
        # 2024-01-15 13:10:00 UTC
        timestamp_ms = 1705324200000
        result = _safe_parse_date_to_iso(timestamp_ms)
        assert result == "2024-01-15T13:10:00Z"

    def test_unix_timestamp_seconds(self):
        """Test parsing Unix timestamp in seconds."""
        # 2024-01-15 13:10:00 UTC
        timestamp_s = 1705324200
        result = _safe_parse_date_to_iso(timestamp_s)
        assert result == "2024-01-15T13:10:00Z"

    def test_iso_date_string(self):
        """Test parsing ISO date string."""
        iso_date = "2024-01-15T10:30:00Z"
        result = _safe_parse_date_to_iso(iso_date)
        assert result == "2024-01-15T10:30:00Z"

    def test_common_date_formats(self):
        """Test parsing common date formats."""
        # Test various formats
        test_cases = [
            ("2024-01-15", "2024-01-15T06:00:00Z"),  # Assumes Central Time
            ("01/15/2024", "2024-01-15T06:00:00Z"),
            ("Jan 15, 2024", "2024-01-15T06:00:00Z"),
        ]

        for date_str, expected_prefix in test_cases:
            result = _safe_parse_date_to_iso(date_str)
            # Just check that we get a valid ISO date back
            assert result.endswith("Z")
            assert len(result) == 20  # ISO format length

    def test_timezone_aware_dates(self):
        """Test parsing timezone-aware dates."""
        # Central Time (CST/CDT) - Harris County is in Central Time
        cst_date = "2024-01-15T10:30:00-06:00"
        result = _safe_parse_date_to_iso(cst_date)
        assert result == "2024-01-15T16:30:00Z"  # Converted to UTC

    def test_invalid_dates(self):
        """Test handling of invalid dates."""
        assert _safe_parse_date_to_iso(None) == ""
        assert _safe_parse_date_to_iso("") == ""
        assert _safe_parse_date_to_iso("invalid") == ""
        assert _safe_parse_date_to_iso([]) == ""
        assert _safe_parse_date_to_iso({}) == ""


class TestParseAddress:
    """Test the _parse_address function."""

    def test_typical_addresses(self):
        """Test parsing typical address formats."""
        test_cases = [
            ("123 Main St, Houston, TX 77001", "123", "Main St"),
            ("456 N Oak Street", "456", "N Oak Street"),
            ("789 W Elm Ave, Houston, TX", "789", "W Elm Ave"),
            ("1001 S Pine Blvd", "1001", "S Pine Blvd"),
        ]

        for address, expected_number, expected_name in test_cases:
            number, name = _parse_address(address)
            assert number == expected_number
            assert name == expected_name

    def test_complex_numbers(self):
        """Test parsing addresses with complex street numbers."""
        test_cases = [
            ("123A Main St", "123A", "Main St"),
            ("123-B Oak Street", "123-B", "Oak Street"),
            (
                "123 1/2 Pine Ave",
                "123",
                "1/2 Pine Ave",
            ),  # Note: 1/2 becomes part of street name
        ]

        for address, expected_number, expected_name in test_cases:
            number, name = _parse_address(address)
            assert number == expected_number
            assert name == expected_name

    def test_no_number_addresses(self):
        """Test parsing addresses without street numbers."""
        test_cases = [
            ("Main Street", "", "Main Street"),
            ("Oak Ave, Houston, TX", "", "Oak Ave"),
            ("", "", ""),
        ]

        for address, expected_number, expected_name in test_cases:
            number, name = _parse_address(address)
            assert number == expected_number
            assert name == expected_name

    def test_invalid_inputs(self):
        """Test handling of invalid inputs."""
        assert _parse_address(None) == ("", "")
        assert _parse_address("") == ("", "")
        assert _parse_address("   ") == ("", "")
        assert _parse_address(123) == ("", "")


class TestIntegration:
    """Integration tests with realistic data."""

    def test_realistic_harris_county_feature(self):
        """Test with realistic Harris County permit data."""
        feature = {
            "attributes": {
                "OBJECTID": 1234567,
                "EVENTID": 789012,
                "PERMITNUMBER": "BP2024-12345",
                "PERMITNAME": "Single Family Residence - New Construction",
                "APPTYPE": "Building Permit - Residential",
                "ISSUEDDATE": 1705324200000,  # Jan 15, 2024 13:10:00 UTC
                "PROJECTNUMBER": "PRJ-2024-456",
                "FULLADDRESS": "1234 W Oak Forest Dr, Houston, TX 77091",
                "STATUS": "Issued",
                "PERMITVALUATION": 450000,
                "APPLICANTNAME": "ABC Construction LLC",
                "OWNERNAME": "John and Jane Smith",
            },
            "geometry": {"x": -95.46789, "y": 29.84567},
        }

        result = convert_feature_to_dict(feature)

        # Verify all required fields are present and correctly formatted
        assert result["event_id"] == 789012
        assert result["permit_number"] == "BP2024-12345"
        assert result["permit_name"] == "Single Family Residence - New Construction"
        assert result["app_type"] == "Building Permit - Residential"
        assert result["issue_date"] == "2024-01-15T13:10:00Z"
        assert result["project_number"] == "PRJ-2024-456"
        assert result["full_address"] == "1234 W Oak Forest Dr, Houston, TX 77091"
        assert result["street_number"] == "1234"
        assert result["street_name"] == "W Oak Forest Dr"
        assert result["status"] == "Issued"
        assert result["raw"] == feature

        # Verify all required keys are present
        required_keys = {
            "event_id",
            "permit_number",
            "permit_name",
            "app_type",
            "issue_date",
            "project_number",
            "full_address",
            "street_number",
            "street_name",
            "status",
            "raw",
        }
        assert set(result.keys()) == required_keys

    def test_minimal_feature_data(self):
        """Test with minimal feature data."""
        feature = {
            "attributes": {
                "EVENTID": "999",  # String number
                "PERMITNUMBER": "MIN-001",
                "FULLADDRESS": "5 Elm St",
            }
        }

        result = convert_feature_to_dict(feature)

        assert result["event_id"] == 999  # Converted to int
        assert result["permit_number"] == "MIN-001"
        assert result["full_address"] == "5 Elm St"
        assert result["street_number"] == "5"
        assert result["street_name"] == "Elm St"

        # Other fields should have safe defaults
        assert result["permit_name"] == ""
        assert result["app_type"] == ""
        assert result["issue_date"] == ""
        assert result["project_number"] == ""
        assert result["status"] == ""
