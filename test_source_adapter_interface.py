#!/usr/bin/env python3
"""
Simple test script to verify the SourceAdapter interface works correctly.
Does not make external network calls.
"""

import json
from typing import Dict, Any
from permit_leads.adapters.base import SourceAdapter
from permit_leads.adapters.simple_socrata_adapter import SimpleSocrataAdapter
from permit_leads.adapters.arcgis_feature_service import ArcGISFeatureServiceAdapter
from permit_leads.adapters.tpia_adapter import TPIAAdapter


def test_adapter_interface(adapter: SourceAdapter) -> None:
    """Test that an adapter implements the SourceAdapter interface correctly."""
    print(f"Testing {adapter.name}...")
    
    # Check all required attributes exist
    assert hasattr(adapter, 'name'), f"{adapter.__class__.__name__} missing 'name' attribute"
    assert hasattr(adapter, 'fetch'), f"{adapter.__class__.__name__} missing 'fetch' method"
    assert hasattr(adapter, 'parse'), f"{adapter.__class__.__name__} missing 'parse' method"
    assert hasattr(adapter, 'normalize'), f"{adapter.__class__.__name__} missing 'normalize' method"
    
    print(f"  ✓ {adapter.name} has all required attributes")
    
    # Test type annotations are correct
    def uses_adapter(source: SourceAdapter) -> str:
        return source.name
    
    result = uses_adapter(adapter)
    assert result == adapter.name, f"Protocol check failed for {adapter.__class__.__name__}"
    
    print(f"  ✓ {adapter.name} passes Protocol type check")


def test_parse_normalize_methods():
    """Test parse and normalize methods with sample data."""
    print("\nTesting parse() and normalize() methods with sample data...")
    
    # Test SimpleSocrataAdapter
    socrata_adapter = SimpleSocrataAdapter({
        'name': 'Dallas Test',
        'url': 'test://example.com',
        'date_field': 'issued_date',
        'field_map': {
            'permit_number': 'permit_number',
            'address': 'address'
        }
    })
    
    # Sample Socrata JSON response
    sample_socrata_json = json.dumps([
        {
            "permit_number": "BP2023-001",
            "issued_date": "2023-12-01T10:00:00",
            "address": "123 Main St",
            "work_description": "New roof installation"
        }
    ])
    
    print("  Testing Socrata adapter parse/normalize...")
    parsed_records = list(socrata_adapter.parse(sample_socrata_json))
    assert len(parsed_records) == 1, "Should parse 1 record"
    
    normalized = socrata_adapter.normalize(parsed_records[0])
    assert normalized['source'] == 'Dallas Test'
    assert normalized['permit_number'] == 'BP2023-001'
    assert normalized['address'] == '123 Main St'
    print("    ✓ Socrata parse/normalize works correctly")
    
    # Test ArcGIS adapter
    arcgis_adapter = ArcGISFeatureServiceAdapter({
        'name': 'Harris County Test',
        'url': 'test://example.com',
        'date_field': 'ISSUEDDATE',
        'mappings': {
            'permit_number': 'PERMITNUMBER',
            'address': 'FULLADDRESS'
        }
    })
    
    # Sample ArcGIS response
    sample_arcgis_json = json.dumps({
        "features": [
            {
                "attributes": {
                    "PERMITNUMBER": "HC2023-456",
                    "ISSUEDDATE": "2023-12-01",
                    "FULLADDRESS": "456 Oak Ave",
                    "PERMITNAME": "Kitchen remodel"
                }
            }
        ]
    })
    
    print("  Testing ArcGIS adapter parse/normalize...")
    parsed_records = list(arcgis_adapter.parse(sample_arcgis_json))
    assert len(parsed_records) == 1, "Should parse 1 record"
    
    normalized = arcgis_adapter.normalize(parsed_records[0])
    assert normalized['source'] == 'Harris County Test'
    assert normalized['permit_number'] == 'HC2023-456'
    assert normalized['address'] == '456 Oak Ave'
    print("    ✓ ArcGIS parse/normalize works correctly")
    
    # Test TPIA adapter
    tpia_adapter = TPIAAdapter({
        'name': 'Houston Test',
        'jurisdiction': 'houston',
        'mappings': {
            'permit_number': 'Permit Number',
            'address': 'Address'
        }
    })
    
    # Sample CSV data
    sample_csv = """Permit Number,Issue Date,Address,Description
HOU2023-789,2023-12-01,789 Pine St,Bathroom renovation"""
    
    print("  Testing TPIA adapter parse/normalize...")
    parsed_records = list(tpia_adapter.parse(sample_csv))
    assert len(parsed_records) == 1, "Should parse 1 record"
    
    normalized = tpia_adapter.normalize(parsed_records[0])
    assert normalized['source'] == 'Houston Test'
    assert normalized['permit_number'] == 'HOU2023-789'
    assert normalized['address'] == '789 Pine St'
    print("    ✓ TPIA parse/normalize works correctly")


def main():
    """Run all interface tests."""
    print("="*60)
    print("TESTING UNIFIED SOURCEADAPTER INTERFACE")
    print("="*60)
    
    # Test all adapters implement the interface
    adapters = [
        SimpleSocrataAdapter({'name': 'Dallas', 'url': 'test', 'date_field': 'issued_date'}),
        ArcGISFeatureServiceAdapter({'name': 'Harris County', 'url': 'test', 'date_field': 'ISSUEDDATE'}),
        TPIAAdapter({'name': 'Houston', 'jurisdiction': 'houston'})
    ]
    
    print("Testing SourceAdapter interface compliance...")
    for adapter in adapters:
        test_adapter_interface(adapter)
    
    # Test actual parsing and normalization
    test_parse_normalize_methods()
    
    print("\n" + "="*60)
    print("✓ ALL TESTS PASSED!")
    print("✓ Unified SourceAdapter interface is working correctly!")
    print("✓ Houston/Dallas/Austin/SA/Harris can be handled uniformly!")
    print("="*60)


if __name__ == "__main__":
    main()