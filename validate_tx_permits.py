#!/usr/bin/env python3
"""
Simple validation script for Texas permits integration.
Validates configuration files and basic functionality without complex dependencies.
"""

import yaml
import json
import os
from pathlib import Path


def test_sources_yaml_configuration():
    """Test that sources.yaml has been properly updated."""
    print("Testing sources.yaml configuration...")
    
    sources_file = Path("permit_leads/config/sources.yaml")
    
    if not sources_file.exists():
        print(f"❌ Sources file not found: {sources_file}")
        return False
    
    try:
        with open(sources_file) as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error parsing sources.yaml: {e}")
        return False
    
    if "sources" not in config:
        print("❌ No 'sources' key found in configuration")
        return False
    
    sources = config["sources"]
    
    # Check that we have the expected Texas sources
    source_names = [source["name"] for source in sources]
    
    expected_sources = [
        "Dallas Building Permits (Socrata)",
        "Austin Building Permits (Socrata)", 
        "Arlington Issued Permits (ArcGIS)",
        "Houston Open Records (TPIA)"
    ]
    
    found_sources = []
    missing_sources = []
    
    for expected in expected_sources:
        if expected in source_names:
            found_sources.append(expected)
        else:
            missing_sources.append(expected)
    
    print(f"✓ Found {len(found_sources)} expected sources:")
    for source in found_sources:
        print(f"  - {source}")
    
    if missing_sources:
        print(f"❌ Missing sources:")
        for source in missing_sources:
            print(f"  - {source}")
        return False
    
    # Validate individual source configurations
    for source in sources:
        name = source.get("name", "Unknown")
        
        # Check required fields
        required_fields = ["name", "type"]
        if source.get("type") != "tpia_csv":
            required_fields.extend(["updated_field", "primary_key"])
        
        missing_fields = [field for field in required_fields if field not in source]
        if missing_fields:
            print(f"❌ Source '{name}' missing required fields: {missing_fields}")
            return False
        
        # Type-specific validation
        source_type = source.get("type")
        if source_type == "socrata":
            if "domain" not in source or "dataset_id" not in source:
                print(f"❌ Socrata source '{name}' missing domain or dataset_id")
                return False
        elif source_type == "arcgis_feature_service":
            if "url" not in source:
                print(f"❌ ArcGIS source '{name}' missing url")
                return False
        elif source_type == "tpia_csv":
            if "jurisdiction" not in source:
                print(f"❌ TPIA source '{name}' missing jurisdiction")
                return False
    
    print("✓ All source configurations are valid")
    return True


def test_file_structure():
    """Test that all expected files have been created."""
    print("\nTesting file structure...")
    
    expected_files = [
        "permit_leads/config/sources.yaml",
        "permit_leads/adapters/tpia_adapter.py",
        "permit_leads/normalizer.py",
        "docs/permits_tx.md",
        "sql/permits_gold_setup.sql"
    ]
    
    all_found = True
    
    for file_path in expected_files:
        path = Path(file_path)
        if path.exists():
            size = path.stat().st_size
            print(f"✓ {file_path} ({size:,} bytes)")
        else:
            print(f"❌ Missing file: {file_path}")
            all_found = False
    
    return all_found


def test_tpia_adapter_structure():
    """Test that TPIA adapter has expected structure."""
    print("\nTesting TPIA adapter structure...")
    
    tpia_file = Path("permit_leads/adapters/tpia_adapter.py")
    
    if not tpia_file.exists():
        print("❌ TPIA adapter file not found")
        return False
    
    try:
        with open(tpia_file) as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading TPIA adapter: {e}")
        return False
    
    # Check for expected classes and methods
    expected_patterns = [
        "class TPIAAdapter",
        "def generate_tpia_request_template",
        "def fetch_since",
        "def get_status",
        "TEXAS PUBLIC INFORMATION ACT REQUEST"
    ]
    
    missing_patterns = []
    for pattern in expected_patterns:
        if pattern not in content:
            missing_patterns.append(pattern)
    
    if missing_patterns:
        print(f"❌ TPIA adapter missing expected patterns: {missing_patterns}")
        return False
    
    print("✓ TPIA adapter has expected structure")
    return True


def test_socrata_adapter_enhancements():
    """Test that Socrata adapter has been enhanced."""
    print("\nTesting Socrata adapter enhancements...")
    
    socrata_file = Path("permit_leads/adapters/socrata_adapter.py")
    
    if not socrata_file.exists():
        print("❌ Socrata adapter file not found")
        return False
    
    try:
        with open(socrata_file) as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading Socrata adapter: {e}")
        return False
    
    # Check for enhancements
    expected_enhancements = [
        "MAX_REQUESTS_PER_SECOND",
        "_rate_limit",
        "updated_field",
        "primary_key",
        "incremental updates"
    ]
    
    missing_enhancements = []
    for enhancement in expected_enhancements:
        if enhancement not in content:
            missing_enhancements.append(enhancement)
    
    if missing_enhancements:
        print(f"❌ Socrata adapter missing enhancements: {missing_enhancements}")
        return False
    
    print("✓ Socrata adapter has been enhanced")
    return True


def test_normalizer_structure():
    """Test that normalizer has expected structure."""
    print("\nTesting normalizer structure...")
    
    normalizer_file = Path("permit_leads/normalizer.py")
    
    if not normalizer_file.exists():
        print("❌ Normalizer file not found")
        return False
    
    try:
        with open(normalizer_file) as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading normalizer: {e}")
        return False
    
    # Check for expected classes and methods
    expected_patterns = [
        "class PermitNormalizer",
        "def normalize_record",
        "def normalize_batch",
        "_normalize_work_type",
        "_parse_valuation",
        "_extract_coordinates",
        "WORK_TYPE_PATTERNS"
    ]
    
    missing_patterns = []
    for pattern in expected_patterns:
        if pattern not in content:
            missing_patterns.append(pattern)
    
    if missing_patterns:
        print(f"❌ Normalizer missing expected patterns: {missing_patterns}")
        return False
    
    print("✓ Normalizer has expected structure")
    return True


def test_sql_schema():
    """Test that SQL schema file exists and has expected content."""
    print("\nTesting SQL schema...")
    
    sql_file = Path("sql/permits_gold_setup.sql")
    
    if not sql_file.exists():
        print("❌ SQL schema file not found")
        return False
    
    try:
        with open(sql_file) as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading SQL schema: {e}")
        return False
    
    # Check for expected schema elements
    expected_elements = [
        "create table if not exists public.permits_gold",
        "issued_date",
        "work_type", 
        "address",
        "valuation",
        "geom geometry(POINT, 4326)",
        "normalize_work_type",
        "categorize_valuation",
        "permits_analytics"
    ]
    
    missing_elements = []
    for element in expected_elements:
        if element not in content:
            missing_elements.append(element)
    
    if missing_elements:
        print(f"❌ SQL schema missing expected elements: {missing_elements}")
        return False
    
    print("✓ SQL schema has expected structure")
    return True


def test_documentation():
    """Test that documentation exists and covers expected topics."""
    print("\nTesting documentation...")
    
    doc_file = Path("docs/permits_tx.md")
    
    if not doc_file.exists():
        print("❌ Documentation file not found")
        return False
    
    try:
        with open(doc_file) as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading documentation: {e}")
        return False
    
    # Check for expected documentation sections
    expected_sections = [
        "# Texas Building Permits Data Integration",
        "Dallas (Socrata API)",
        "Austin (Socrata API)",
        "Arlington (ArcGIS FeatureServer)", 
        "Harris County Issued Permits (ArcGIS)",
        "Houston (Texas Public Information Act - TPIA)",
        "e7gq-4sah",  # Dallas dataset ID
        "3syk-w9eu",  # Austin dataset ID
        "Incremental Data Pulls",
        "Rate Limiting",
        "permits_gold"
    ]
    
    missing_sections = []
    for section in expected_sections:
        if section not in content:
            missing_sections.append(section)
    
    if missing_sections:
        print(f"❌ Documentation missing expected sections: {missing_sections}")
        return False
    
    print("✓ Documentation covers all expected topics")
    return True


def main():
    """Run all validation tests."""
    print("🔍 Validating Texas Permits Integration Implementation")
    print("=" * 60)
    
    tests = [
        test_file_structure,
        test_sources_yaml_configuration,
        test_tpia_adapter_structure,
        test_socrata_adapter_enhancements,
        test_normalizer_structure,
        test_sql_schema,
        test_documentation
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with error: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All validation tests passed! Texas permits integration is ready.")
        return True
    else:
        print("⚠️  Some validation tests failed. Please check the issues above.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)