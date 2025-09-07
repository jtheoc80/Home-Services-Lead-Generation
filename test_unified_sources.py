#!/usr/bin/env python3
"""
Test and validate the unified config/sources.yml configuration.
"""

import yaml
from pathlib import Path


def test_unified_sources_config():
    """Test that config/sources.yml has the expected unified format."""
    print("Testing unified sources.yml configuration...")

    sources_file = Path("config/sources.yml")

    if not sources_file.exists():
        print(f"❌ Unified sources file not found: {sources_file}")
        return False

    try:
        with open(sources_file) as f:
            sources = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error parsing sources.yml: {e}")
        return False

    if not isinstance(sources, list):
        print("❌ sources.yml should contain a list of source configurations")
        return False

    print(f"✓ Found {len(sources)} source configurations")

    # Expected sources from problem statement
    expected_keys = [
        "city_of_houston_weekly",
        "city_of_houston_sold",
        "city_of_austin_permits",
        "city_of_san_antonio_permits",
        "city_of_dallas_permits",
    ]

    found_keys = [source.get("key") for source in sources]

    for expected_key in expected_keys:
        if expected_key in found_keys:
            print(f"✓ Found expected source: {expected_key}")
        else:
            print(f"❌ Missing expected source: {expected_key}")
            return False

    # Validate structure for each source
    for source in sources:
        key = source.get("key", "unknown")

        # Check required fields
        required_fields = ["key", "kind", "date_field", "auth"]
        missing_fields = [field for field in required_fields if field not in source]
        if missing_fields:
            print(f"❌ Source '{key}' missing required fields: {missing_fields}")
            return False

        # Validate kind-specific fields
        kind = source.get("kind")
        if kind == "socrata":
            if "host" not in source or "resource" not in source:
                print(f"❌ Socrata source '{key}' missing host or resource")
                return False
        elif kind == "arcgis":
            if "base" not in source:
                print(f"❌ ArcGIS source '{key}' missing base URL")
                return False
            # Validate that base URL points to FeatureServer or MapServer
            base_url = source.get("base", "")
            if not ("FeatureServer" in base_url or "MapServer" in base_url):
                print(
                    f"❌ ArcGIS source '{key}' base URL must point to FeatureServer/MapServer"
                )
                return False
        elif kind == "static_xlsx":
            if "url" not in source or "parse" not in source:
                print(f"❌ XLSX source '{key}' missing url or parse method")
                return False

        print(f"✓ Source '{key}' configuration valid")

    return True


def test_arcgis_urls_format():
    """Validate that ArcGIS URLs point to proper endpoints."""
    print("\nValidating ArcGIS URL formats...")

    sources_file = Path("config/sources.yml")
    with open(sources_file) as f:
        sources = yaml.safe_load(f)

    arcgis_sources = [s for s in sources if s.get("kind") == "arcgis"]

    for source in arcgis_sources:
        key = source.get("key")
        base_url = source.get("base", "")

        # Check URL format
        if not base_url.startswith("https://"):
            print(f"❌ ArcGIS source '{key}' should use HTTPS")
            return False

        if not (
            base_url.endswith("/FeatureServer/0") or base_url.endswith("/MapServer/0")
        ):
            print(
                f"❌ ArcGIS source '{key}' should end with /FeatureServer/0 or /MapServer/0"
            )
            return False

        print(f"✓ ArcGIS source '{key}' URL format correct: {base_url}")

    return True


def test_environment_variables():
    """Check that environment variable placeholders are properly formatted."""
    print("\nValidating environment variable usage...")

    sources_file = Path("config/sources.yml")
    with open(sources_file) as f:
        sources = yaml.safe_load(f)

    env_var_sources = []
    for source in sources:
        key = source.get("key")

        # Check for environment variables in various fields
        for field_name, field_value in source.items():
            if isinstance(field_value, str) and "${" in field_value:
                env_var_sources.append((key, field_name, field_value))
                print(f"✓ Found env var in '{key}' field '{field_name}': {field_value}")

    if env_var_sources:
        print(f"✓ Found {len(env_var_sources)} environment variable references")
    else:
        print("ℹ️  No environment variable references found (this is OK)")

    return True


if __name__ == "__main__":
    print("🔍 Validating Unified Sources Configuration")
    print("=" * 50)

    all_passed = True

    if not test_unified_sources_config():
        all_passed = False

    if not test_arcgis_urls_format():
        all_passed = False

    if not test_environment_variables():
        all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All unified sources configuration tests passed!")
    else:
        print("❌ Some tests failed. Please check the issues above.")

    exit(0 if all_passed else 1)
