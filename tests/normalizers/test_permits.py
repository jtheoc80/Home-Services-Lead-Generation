"""
Unit tests for permit normalization functionality.

This module contains fixtures for sample records from each source (Dallas, Austin, Arlington)
and tests to ensure the normalization pipeline correctly processes them.
"""

import pytest
from datetime import datetime
from normalizers.permits import normalize, pick, validate_normalized_record


# Test fixtures for sample records from each source


@pytest.fixture
def dallas_permit_sample():
    """Sample permit record from Dallas Socrata API."""
    return {
        "permit_number": "BLD2024-00123",
        "issued_date": "2024-01-15T10:30:00.000",
        "address": "123 Main St, Dallas, TX 75201",
        "work_description": "Single family residence - new construction",
        "permit_status": "Issued",
        "permit_type_desc": "Building - New Construction",
        "estimated_cost": "450000",
        "contractor_name": "ABC Construction LLC",
        "license_no": "TX123456",
        "latitude": "32.776664",
        "longitude": "-96.796988",
    }


@pytest.fixture
def austin_permit_sample():
    """Sample permit record from Austin Socrata API."""
    return {
        "permit_num": "2024-001234-RES",
        "issued_date": "2024-01-20T14:15:30.000",
        "project_address": "456 Oak Avenue, Austin, TX 78701",
        "description": "Kitchen and bathroom remodel",
        "status_current": "Active",
        "permit_class": "Residential",
        "declared_value": "75000",
        "contractor_company": "Home Renovations Inc",
        "location": {"latitude": "30.267153", "longitude": "-97.743061"},
    }


@pytest.fixture
def arlington_permit_sample():
    """Sample permit record from Arlington ArcGIS API."""
    return {
        "OBJECTID": 98765,
        "PERMIT_NUM": "P2024-0567",
        "ISSUE_DATE": 1705651200000,  # Unix timestamp in milliseconds
        "ADDRESS": "789 Elm Street, Arlington, TX 76010",
        "DESCRIPTION": "HVAC system replacement",
        "STATUS": "APPROVED",
        "PERMIT_TYPE": "Mechanical",
        "JOB_VALUE": 15000,
        "CONTRACTOR": "Cool Air Systems",
        "geometry": {"x": -97.10806, "y": 32.735687},
    }


@pytest.fixture
def dallas_source_meta():
    """Source metadata for Dallas."""
    return {
        "id": "dallas_permits",
        "jurisdiction": "Dallas",
        "city": "Dallas",
        "county": "Dallas",
    }


@pytest.fixture
def austin_source_meta():
    """Source metadata for Austin."""
    return {
        "id": "austin_permits",
        "jurisdiction": "Austin",
        "city": "Austin",
        "county": "Travis",
    }


@pytest.fixture
def arlington_source_meta():
    """Source metadata for Arlington."""
    return {
        "id": "arlington_permits",
        "jurisdiction": "Arlington",
        "city": "Arlington",
        "county": "Tarrant",
    }


class TestPickFunction:
    """Test the pick() helper function."""

    def test_pick_first_available_field(self):
        """Test picking the first available field from aliases."""
        record = {"permit_number": "123", "permit_id": "456", "id": "789"}
        aliases = ["permit_num", "permit_number", "permit_id", "id"]

        result = pick(record, aliases)
        assert result == "123"  # First available field

    def test_pick_skips_null_values(self):
        """Test that pick skips null and empty values."""
        record = {
            "permit_num": None,
            "permit_number": "",
            "permit_id": "N/A",
            "id": "123",
        }
        aliases = ["permit_num", "permit_number", "permit_id", "id"]

        result = pick(record, aliases)
        assert result == "123"  # Skips nulls, empty strings, and N/A

    def test_pick_returns_none_when_no_match(self):
        """Test pick returns None when no aliases match."""
        record = {"other_field": "value"}
        aliases = ["permit_id", "permit_number"]

        result = pick(record, aliases)
        assert result is None


class TestNormalizeDallasPermit:
    """Test normalization of Dallas permit records."""

    def test_dallas_normalization(self, dallas_permit_sample, dallas_source_meta):
        """Test complete normalization of Dallas permit."""
        result = normalize(dallas_source_meta, dallas_permit_sample)

        # Check core fields
        assert result["source_id"] == "dallas_permits"
        assert result["permit_id"] == "BLD2024-00123"
        assert result["jurisdiction"] == "Dallas"
        assert result["city"] == "Dallas"
        assert result["county"] == "Dallas"
        assert result["state"] == "TX"

        # Check normalized fields
        assert result["status"] == "ISSUED"  # Should be normalized
        assert result["permit_type"] == "BUILDING"  # Should be normalized
        assert result["description"] == "Single family residence - new construction"
        assert result["address_full"] == "123 Main St, Dallas, TX 75201"
        assert result["valuation"] == 450000.0
        assert result["contractor_name"] == "ABC Construction LLC"
        assert result["contractor_license"] == "TX123456"

        # Check geography
        assert result["latitude"] == 32.776664
        assert result["longitude"] == -96.796988
        assert result["geom"] is not None
        assert "POINT(-96.796988 32.776664)" in result["geom"]

        # Check dates
        assert isinstance(result["issued_at"], datetime)
        assert result["issued_at"].year == 2024
        assert result["issued_at"].month == 1
        assert result["issued_at"].day == 15

        # Check metadata
        assert result["record_hash"] is not None
        assert len(result["record_hash"]) == 40  # SHA1 hash length
        assert isinstance(result["updated_at"], datetime)
        assert result["provenance"]["source"] == "dallas_permits"


class TestNormalizeAustinPermit:
    """Test normalization of Austin permit records."""

    def test_austin_normalization(self, austin_permit_sample, austin_source_meta):
        """Test complete normalization of Austin permit."""
        result = normalize(austin_source_meta, austin_permit_sample)

        # Check core fields
        assert result["source_id"] == "austin_permits"
        assert result["permit_id"] == "2024-001234-RES"
        assert result["jurisdiction"] == "Austin"
        assert result["city"] == "Austin"
        assert result["county"] == "Travis"

        # Check field mapping
        assert result["address_full"] == "456 Oak Avenue, Austin, TX 78701"
        assert result["description"] == "Kitchen and bathroom remodel"
        assert result["status"] == "ACTIVE"
        assert result["valuation"] == 75000.0
        assert result["contractor_name"] == "Home Renovations Inc"

        # Check geography from nested location object
        assert result["latitude"] == 30.267153
        assert result["longitude"] == -97.743061
        assert result["geom"] is not None

        # Check dates
        assert isinstance(result["issued_at"], datetime)


class TestNormalizeArlingtonPermit:
    """Test normalization of Arlington permit records."""

    def test_arlington_normalization(
        self, arlington_permit_sample, arlington_source_meta
    ):
        """Test complete normalization of Arlington permit."""
        result = normalize(arlington_source_meta, arlington_permit_sample)

        # Check core fields
        assert result["source_id"] == "arlington_permits"
        assert result["permit_id"] == "P2024-0567"
        assert result["jurisdiction"] == "Arlington"
        assert result["city"] == "Arlington"
        assert result["county"] == "Tarrant"

        # Check field mapping for ArcGIS format
        assert result["address_full"] == "789 Elm Street, Arlington, TX 76010"
        assert result["description"] == "HVAC system replacement"
        assert result["status"] == "APPROVED"
        assert result["permit_type"] == "MECHANICAL"
        assert result["valuation"] == 15000.0
        assert result["contractor_name"] == "Cool Air Systems"

        # Check geometry extraction from ArcGIS format
        assert result["latitude"] == 32.735687
        assert result["longitude"] == -97.10806
        assert result["geom"] is not None

        # Check timestamp conversion (ArcGIS uses milliseconds)
        assert isinstance(result["issued_at"], datetime)
        assert result["issued_at"].year == 2024


class TestValidation:
    """Test validation of normalized records."""

    def test_valid_record_passes_validation(
        self, dallas_permit_sample, dallas_source_meta
    ):
        """Test that a valid normalized record passes validation."""
        normalized = normalize(dallas_source_meta, dallas_permit_sample)
        errors = validate_normalized_record(normalized)

        assert len(errors) == 0

    def test_missing_permit_id_fails_validation(self):
        """Test that missing permit_id fails validation."""
        record = {
            "source_id": "test",
            "permit_id": None,  # Missing
            "latitude": 32.0,
            "longitude": -96.0,
        }

        errors = validate_normalized_record(record)
        assert any("permit_id" in error for error in errors)

    def test_invalid_coordinates_fail_validation(self):
        """Test that coordinates outside Texas bounds fail validation."""
        record = {
            "source_id": "test",
            "permit_id": "123",
            "latitude": 45.0,  # Outside Texas
            "longitude": -120.0,  # Outside Texas
        }

        errors = validate_normalized_record(record)
        assert any("latitude" in error for error in errors)
        assert any("longitude" in error for error in errors)

    def test_negative_valuation_fails_validation(self):
        """Test that negative valuation fails validation."""
        record = {
            "source_id": "test",
            "permit_id": "123",
            "valuation": -1000,  # Invalid
        }

        errors = validate_normalized_record(record)
        assert any("valuation" in error for error in errors)


class TestFieldAliasSystem:
    """Test the field alias system works correctly."""

    def test_jurisdiction_specific_aliases(self):
        """Test that jurisdiction-specific aliases are used when available."""
        # This would require looking at the actual normalization logic
        # to see if Dallas-specific aliases are being used

        # Test record with Dallas-specific field names
        dallas_record = {
            "permit_number": "123",  # Dallas uses this
            "issued_date": "2024-01-01",
        }

        dallas_meta = {
            "id": "dallas_permits",
            "jurisdiction": "Dallas",
            "city": "Dallas",
            "county": "Dallas",
        }

        result = normalize(dallas_meta, dallas_record)
        assert result["permit_id"] == "123"

    def test_fallback_to_generic_aliases(self):
        """Test fallback to generic aliases when jurisdiction-specific ones don't match."""
        # Test with an unknown jurisdiction that should fall back to generic aliases
        unknown_record = {
            "record_id": "456",  # Generic field name
            "issue_date": "2024-01-01",
        }

        unknown_meta = {
            "id": "unknown_source",
            "jurisdiction": "Unknown",
            "city": "Unknown",
            "county": "Unknown",
        }

        result = normalize(unknown_meta, unknown_record)
        assert result["permit_id"] == "456"


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_record(self):
        """Test normalization of empty record."""
        result = normalize({"id": "test", "jurisdiction": "Test"}, {})

        # Should still have basic metadata
        assert result["source_id"] == "test"
        assert result["jurisdiction"] == "Test"
        assert result["state"] == "TX"
        assert result["record_hash"] is not None

    def test_malformed_dates(self):
        """Test handling of malformed date strings."""
        record = {
            "permit_id": "123",
            "issued_date": "not-a-date",
            "applied_date": "2024-99-99",  # Invalid date
        }

        meta = {"id": "test", "jurisdiction": "Test"}
        result = normalize(meta, record)

        # Should handle gracefully with None values
        assert result["issued_at"] is None
        assert result["applied_at"] is None

    def test_malformed_coordinates(self):
        """Test handling of malformed coordinate values."""
        record = {
            "permit_id": "123",
            "latitude": "not-a-number",
            "longitude": "also-not-a-number",
        }

        meta = {"id": "test", "jurisdiction": "Test"}
        result = normalize(meta, record)

        # Should handle gracefully
        assert result["latitude"] is None
        assert result["longitude"] is None
        assert result["geom"] is None


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
