"""
Test cases for PermitNormalizer integration with normalize_trade function.
"""

from permit_leads.normalizer import PermitNormalizer


class TestPermitNormalizerTradeIntegration:
    """Test cases for trade normalization in PermitNormalizer."""

    def setup_method(self):
        """Set up test instance."""
        self.normalizer = PermitNormalizer()

    def test_normalizer_adds_trade_field(self):
        """Test that PermitNormalizer adds trade field using normalize_trade."""
        raw_record = {
            "work_description": "Roof replacement and repair",
            "permit_type": "Residential",
            "permit_number": "RP2024001",
            "address": "123 Main St",
        }

        source_config = {
            "jurisdiction": "test_city",
            "type": "test",
            "mappings": {
                "work_description": "work_description",
                "permit_type": "permit_type",
                "permit_number": "permit_number",
                "address": "address",
            },
        }

        result = self.normalizer.normalize_record(raw_record, source_config)

        assert result is not None
        assert "trade" in result
        assert result["trade"] == "Roofing"

    def test_normalizer_kitchen_trade(self):
        """Test kitchen trade detection in normalization."""
        raw_record = {
            "work_description": "Kitchen remodel with new cabinets",
            "permit_type": "Residential",
            "permit_number": "RP2024002",
        }

        source_config = {"jurisdiction": "test_city", "type": "test", "mappings": {}}

        result = self.normalizer.normalize_record(raw_record, source_config)

        assert result is not None
        assert result["trade"] == "Kitchen"

    def test_normalizer_electrical_trade(self):
        """Test electrical trade detection in normalization."""
        raw_record = {
            "work_description": "Electrical panel upgrade",
            "permit_type": "Electrical",
            "permit_number": "EP2024001",
        }

        source_config = {"jurisdiction": "test_city", "type": "test", "mappings": {}}

        result = self.normalizer.normalize_record(raw_record, source_config)

        assert result is not None
        assert result["trade"] == "Electrical"

    def test_normalizer_general_fallback(self):
        """Test fallback to General when no specific trade detected."""
        raw_record = {
            "work_description": "General construction work",
            "permit_type": "",
            "permit_number": "GP2024001",
        }

        source_config = {"jurisdiction": "test_city", "type": "test", "mappings": {}}

        result = self.normalizer.normalize_record(raw_record, source_config)

        assert result is not None
        assert result["trade"] == "General"

    def test_normalizer_permit_type_fallback(self):
        """Test fallback to permit_type when no keywords match."""
        raw_record = {
            "work_description": "General construction work",  # Changed to avoid "building" keyword
            "permit_type": "Commercial",  # Simplified to just "Commercial"
            "permit_number": "CB2024001",
        }

        source_config = {"jurisdiction": "test_city", "type": "test", "mappings": {}}

        result = self.normalizer.normalize_record(raw_record, source_config)

        assert result is not None
        assert result["trade"] == "Commercial"

    def test_normalizer_multiple_keywords_priority(self):
        """Test that highest priority trade is selected from multiple keywords."""
        raw_record = {
            "work_description": "Pool installation with electrical and plumbing",
            "permit_type": "Residential",
            "permit_number": "PP2024001",
        }

        source_config = {"jurisdiction": "test_city", "type": "test", "mappings": {}}

        result = self.normalizer.normalize_record(raw_record, source_config)

        assert result is not None
        # Pool (priority 8) should win over electrical (4) and plumbing (4)
        assert result["trade"] == "Pool"

    def test_normalizer_stats_tracking(self):
        """Test that normalization stats are tracked correctly."""
        raw_record = {
            "work_description": "HVAC installation",
            "permit_type": "Mechanical",
            "permit_number": "HV2024001",
        }

        source_config = {"jurisdiction": "test_city", "type": "test", "mappings": {}}

        initial_processed = self.normalizer.stats["processed"]
        initial_normalized = self.normalizer.stats["normalized"]

        result = self.normalizer.normalize_record(raw_record, source_config)

        assert result is not None
        assert result["trade"] == "Hvac"
        assert self.normalizer.stats["processed"] == initial_processed + 1
        assert self.normalizer.stats["normalized"] == initial_normalized + 1

    def test_normalizer_error_handling(self):
        """Test that errors in trade normalization don't break the normalizer."""
        # Create a record that might cause issues
        raw_record = {
            "work_description": None,  # None value that might cause issues
            "permit_type": None,
            "permit_number": "ER2024001",
        }

        source_config = {"jurisdiction": "test_city", "type": "test", "mappings": {}}

        result = self.normalizer.normalize_record(raw_record, source_config)

        # Should still normalize successfully with fallback trade
        assert result is not None
        assert result["trade"] == "General"
