"""
Tests for Texas permits data integration functionality.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import json
import sys
import os

# Add project root to path so we can import modules
from pathlib import Path
# Add project root to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Test the Socrata adapter enhancements
def test_socrata_adapter_dallas():
    """Test Dallas Socrata configuration and basic functionality."""
    from permit_leads.adapters.socrata_adapter import SocrataAdapter
    
    config = {
        "domain": "www.dallasopendata.com",
        "dataset_id": "e7gq-4sah",
        "updated_field": "issued_date",
        "primary_key": "permit_number",
        "mappings": {
            "permit_number": "permit_number",
            "issued_date": "issued_date",
            "address": "address",
            "work_description": "work_description"
        }
    }
    
    adapter = SocrataAdapter(config)
    assert adapter.cfg["domain"] == "www.dallasopendata.com"
    assert adapter.cfg["dataset_id"] == "e7gq-4sah"
    assert adapter.MAX_REQUESTS_PER_SECOND == 5


def test_socrata_adapter_austin():
    """Test Austin Socrata configuration."""
    from permit_leads.adapters.socrata_adapter import SocrataAdapter
    
    config = {
        "domain": "data.austintexas.gov",
        "dataset_id": "3syk-w9eu",
        "updated_field": "issued_date",
        "primary_key": "permit_number",
        "mappings": {
            "permit_number": "permit_number",
            "issued_date": "issued_date",
            "address": "original_address1"
        }
    }
    
    adapter = SocrataAdapter(config)
    assert adapter.cfg["domain"] == "data.austintexas.gov"
    assert adapter.cfg["dataset_id"] == "3syk-w9eu"


def test_tpia_adapter_houston():
    """Test Houston TPIA adapter functionality."""
    from permit_leads.adapters.tpia_adapter import TPIAAdapter
    
    config = {
        "jurisdiction": "houston",
        "data_dir": "/tmp/test_tpia_data",
        "template_dir": "/tmp/test_tpia_templates"
    }
    
    adapter = TPIAAdapter(config)
    assert adapter.jurisdiction == "houston"
    
    # Test template generation
    template = adapter.generate_tpia_request_template()
    assert "TEXAS PUBLIC INFORMATION ACT REQUEST" in template
    assert "houston" in template.lower()
    assert "building permit records" in template.lower()
    
    # Test status
    status = adapter.get_status()
    assert status["jurisdiction"] == "houston"
    assert "instructions" in status


def test_permit_normalizer():
    """Test permit data normalization."""
    from permit_leads.normalizer import PermitNormalizer
    
    normalizer = PermitNormalizer()
    
    # Test Dallas raw record
    dallas_raw = {
        "permit_number": "BLD2024-001234",
        "issued_date": "2024-01-15T10:30:00",
        "address": "123 Main St, Dallas, TX 75201",
        "work_description": "Residential addition - kitchen remodel",
        "permit_status": "Issued",
        "estimated_cost": "25000",
        "contractor_name": "ABC Construction Inc"
    }
    
    dallas_config = {
        "jurisdiction": "dallas",
        "type": "socrata",
        "url": "https://www.dallasopendata.com/resource/e7gq-4sah.json",
        "mappings": {
            "permit_number": "permit_number",
            "issued_date": "issued_date",
            "address": "address",
            "work_description": "work_description",
            "value": "estimated_cost",
            "applicant_name": "contractor_name"
        }
    }
    
    normalized = normalizer.normalize_record(dallas_raw, dallas_config)
    
    assert normalized is not None
    assert normalized["jurisdiction"] == "dallas"
    assert normalized["source_type"] == "socrata"
    assert normalized["permit_id"] == "BLD2024-001234"
    assert normalized["work_type"] == "residential"  # Should detect from description
    assert normalized["valuation"] == 25000.0
    assert normalized["project_value_band"] == "tier_15k_50k"


def test_work_type_normalization():
    """Test work type classification logic."""
    from permit_leads.normalizer import PermitNormalizer
    
    normalizer = PermitNormalizer()
    
    # Test residential patterns
    assert normalizer._normalize_work_type("Kitchen remodel", "Residential") == "residential"
    assert normalizer._normalize_work_type("Single family dwelling", None) == "residential"
    assert normalizer._normalize_work_type("Garage addition", "Building") == "residential"
    
    # Test commercial patterns
    assert normalizer._normalize_work_type("Office building", "Commercial") == "commercial"
    assert normalizer._normalize_work_type("Retail store renovation", None) == "commercial"
    
    # Test multi-family
    assert normalizer._normalize_work_type("Apartment complex", None) == "multi_family"
    assert normalizer._normalize_work_type("Condo renovation", "Multi-family") == "multi_family"
    
    # Test default
    assert normalizer._normalize_work_type("Unknown work", None) == "mixed_use"


def test_valuation_parsing():
    """Test valuation parsing from various formats."""
    from permit_leads.normalizer import PermitNormalizer
    
    normalizer = PermitNormalizer()
    
    # Test various formats
    assert normalizer._parse_valuation("25000") == 25000.0
    assert normalizer._parse_valuation("$25,000") == 25000.0
    assert normalizer._parse_valuation("25000.50") == 25000.5
    assert normalizer._parse_valuation(25000) == 25000.0
    assert normalizer._parse_valuation("") is None
    assert normalizer._parse_valuation("NULL") is None
    
    # Test categorization
    assert normalizer._categorize_valuation(500) == "under_1k"
    assert normalizer._categorize_valuation(25000) == "tier_15k_50k"
    assert normalizer._categorize_valuation(75000) == "tier_50k_100k"
    assert normalizer._categorize_valuation(1500000) == "tier_1m_plus"


def test_coordinate_extraction():
    """Test coordinate parsing and validation."""
    from permit_leads.normalizer import PermitNormalizer
    
    normalizer = PermitNormalizer()
    
    raw_record = {
        "latitude": "32.7767",
        "longitude": "-96.7970"  # Dallas coordinates
    }
    
    mappings = {
        "latitude": "latitude",
        "longitude": "longitude"
    }
    
    lat, lon = normalizer._extract_coordinates(raw_record, mappings)
    assert lat == 32.7767
    assert lon == -96.7970
    
    # Test invalid coordinates (outside Texas)
    invalid_record = {
        "latitude": "40.7589",  # NYC latitude
        "longitude": "-73.9851"  # NYC longitude
    }
    
    lat, lon = normalizer._extract_coordinates(invalid_record, mappings)
    assert lat is None
    assert lon is None


def test_sources_yaml_configuration():
    """Test that sources.yaml has been properly updated."""
    import yaml
    from pathlib import Path
    
    sources_file = Path("permit_leads/config/sources.yaml")
    
    with open(sources_file) as f:
        config = yaml.safe_load(f)
    
    sources = config["sources"]
    
    # Check that we have the expected Texas sources
    source_names = [source["name"] for source in sources]
    
    assert "Dallas Building Permits (Socrata)" in source_names
    assert "Austin Building Permits (Socrata)" in source_names
    assert "Arlington Issued Permits (ArcGIS)" in source_names
    assert "Houston Open Records (TPIA)" in source_names
    
    # Check Dallas configuration
    dallas_source = next(s for s in sources if "Dallas" in s["name"])
    assert dallas_source["type"] == "socrata"
    assert dallas_source["domain"] == "www.dallasopendata.com"
    assert dallas_source["dataset_id"] == "e7gq-4sah"
    assert "updated_field" in dallas_source
    assert "primary_key" in dallas_source
    
    # Check Austin configuration
    austin_source = next(s for s in sources if "Austin" in s["name"])
    assert austin_source["type"] == "socrata"
    assert austin_source["domain"] == "data.austintexas.gov"
    assert austin_source["dataset_id"] == "3syk-w9eu"
    
    # Check Arlington configuration
    arlington_source = next(s for s in sources if "Arlington" in s["name"])
    assert arlington_source["type"] == "arcgis_feature_service"
    assert "gis.arlingtontx.gov" in arlington_source["url"]
    
    # Check Houston configuration
    houston_source = next(s for s in sources if "Houston" in s["name"])
    assert houston_source["type"] == "tpia_csv"
    assert houston_source["jurisdiction"] == "houston"


if __name__ == "__main__":
    # Run basic functionality tests
    print("Testing Texas permits integration...")
    
    test_socrata_adapter_dallas()
    print("✓ Dallas Socrata adapter configuration")
    
    test_socrata_adapter_austin()
    print("✓ Austin Socrata adapter configuration")
    
    test_tpia_adapter_houston()
    print("✓ Houston TPIA adapter functionality")
    
    test_permit_normalizer()
    print("✓ Permit data normalization")
    
    test_work_type_normalization()
    print("✓ Work type classification")
    
    test_valuation_parsing()
    print("✓ Valuation parsing and categorization")
    
    test_coordinate_extraction()
    print("✓ Coordinate extraction and validation")
    
    test_sources_yaml_configuration()
    print("✓ Sources configuration validation")
    
    print("\nAll tests passed! Texas permits integration is ready.")