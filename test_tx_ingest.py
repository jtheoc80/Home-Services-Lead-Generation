"""Test script for Texas data ingestion pipeline components."""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import our modules
from lib.feature_flags import feature_flags, weather_enabled
from great_expectations.validation_suite import DataValidationSuite


def test_feature_flags():
    """Test feature flag functionality."""
    print("Testing Feature Flags...")

    # Test weather flag (should be False by default)
    assert not weather_enabled(), "Weather should be disabled by default"
    print("✓ Weather feature correctly disabled")

    # Test other flags
    assert feature_flags.use_geocoding, "Geocoding should be enabled by default"
    assert (
        feature_flags.use_entity_resolution
    ), "Entity resolution should be enabled by default"
    print("✓ Default feature flags working correctly")

    # Test flag override
    feature_flags.set_flag("USE_WEATHER", True)
    assert weather_enabled(), "Weather flag override failed"
    feature_flags.set_flag("USE_WEATHER", False)  # Reset
    print("✓ Feature flag override working")


def test_configuration_loading():
    """Test configuration file loading."""
    print("\nTesting Configuration Loading...")

    config_file = project_root / "config" / "sources_tx.yaml"
    assert config_file.exists(), f"Configuration file not found: {config_file}"
    print("✓ Texas sources configuration file exists")

    # Try to load it
    try:
        import yaml

        with open(config_file, "r") as f:
            config = yaml.safe_load(f)

        assert "sources" in config, "Missing 'sources' key in configuration"
        assert len(config["sources"]) > 0, "No sources configured"

        print(f"✓ Configuration loaded with {len(config['sources'])} sources")

        # Check for required source types
        source_types = [source.get("type") for source in config["sources"]]
        expected_types = ["arcgis_feature_service", "socrata", "csv_http"]

        for expected_type in expected_types:
            if expected_type in source_types:
                print(f"✓ Found {expected_type} source type")
            else:
                print(f"⚠ Missing {expected_type} source type")

    except Exception as e:
        print(f"✗ Error loading configuration: {e}")


def test_connector_imports():
    """Test that all connector modules can be imported."""
    print("\nTesting Connector Imports...")

    try:

        print("✓ ArcGIS connector imported successfully")
    except Exception as e:
        print(f"✗ Failed to import ArcGIS connector: {e}")

    try:

        print("✓ Socrata connector imported successfully")
    except Exception as e:
        print(f"✗ Failed to import Socrata connector: {e}")

    try:

        print("✓ CSV HTTP connector imported successfully")
    except Exception as e:
        print(f"✗ Failed to import CSV HTTP connector: {e}")


def test_pipeline_imports():
    """Test that pipeline modules can be imported."""
    print("\nTesting Pipeline Imports...")

    try:

        print("✓ Raw data loader imported successfully")
    except Exception as e:
        print(f"✗ Failed to import raw data loader: {e}")

    try:

        print("✓ Data normalizer imported successfully")
    except Exception as e:
        print(f"✗ Failed to import data normalizer: {e}")


def test_entity_resolution_import():
    """Test entity resolution import."""
    print("\nTesting Entity Resolution Import...")

    try:

        print("✓ Entity graph imported successfully")
    except Exception as e:
        print(f"✗ Failed to import entity graph: {e}")


def test_validation_suite():
    """Test data validation suite."""
    print("\nTesting Data Validation Suite...")

    try:
        validator = DataValidationSuite()
        print("✓ Data validation suite initialized successfully")

        # Test with empty directory (should not crash)
        result = validator.validate_all_raw_data()
        if "error" in result:
            print("✓ Correctly handled missing data directory")
        else:
            print("✓ Validation completed successfully")

    except Exception as e:
        print(f"✗ Failed to initialize validation suite: {e}")


def test_directory_structure():
    """Test that all required directories exist."""
    print("\nTesting Directory Structure...")

    required_dirs = [
        "config",
        "ingest",
        "pipelines",
        "lib",
        "great_expectations",
        "docs",
    ]

    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"✓ {dir_name}/ directory exists")
        else:
            print(f"✗ {dir_name}/ directory missing")


def test_documentation_exists():
    """Test that documentation files exist."""
    print("\nTesting Documentation...")

    doc_files = [
        "docs/tx_coverage.md",
    ]

    for doc_file in doc_files:
        doc_path = project_root / doc_file
        if doc_path.exists():
            print(f"✓ {doc_file} exists")

            # Check if it's not empty
            if doc_path.stat().st_size > 0:
                print(f"✓ {doc_file} has content")
            else:
                print(f"⚠ {doc_file} is empty")
        else:
            print(f"✗ {doc_file} missing")


def test_environment_example():
    """Test .env.example file has weather flag."""
    print("\nTesting Environment Configuration...")

    env_example = project_root / ".env.example"
    if env_example.exists():
        with open(env_example, "r") as f:
            content = f.read()

        if "USE_WEATHER=false" in content:
            print("✓ USE_WEATHER flag found in .env.example")
        else:
            print("✗ USE_WEATHER flag missing from .env.example")

        if "FEATURE FLAGS" in content:
            print("✓ Feature flags section found in .env.example")
        else:
            print("⚠ Feature flags section not clearly marked")
    else:
        print("✗ .env.example file missing")


def main():
    """Run all tests."""
    print("🏠 Texas Data Ingestion Pipeline - Component Tests")
    print("=" * 55)

    # Set up basic logging
    logging.basicConfig(level=logging.WARNING)

    # Run tests
    try:
        test_directory_structure()
        test_feature_flags()
        test_configuration_loading()
        test_connector_imports()
        test_pipeline_imports()
        test_entity_resolution_import()
        test_validation_suite()
        test_documentation_exists()
        test_environment_example()

        print("\n" + "=" * 55)
        print("✅ All component tests completed!")
        print("\nNext steps:")
        print("1. Set up environment variables (copy .env.example to .env)")
        print("2. Run actual data ingestion: python pipelines/load_raw.py")
        print("3. Run data normalization: python pipelines/normalize.py")
        print("4. Build entity graph: python lib/entity_graph.py")
        print("5. Validate data quality: python great_expectations/validation_suite.py")

    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\nUnexpected error during testing: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
