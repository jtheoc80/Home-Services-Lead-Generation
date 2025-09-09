#!/usr/bin/env python3
"""
Utility script to validate ArcGIS endpoints in config/sources.yml.

According to the problem statement:
"The ArcGIS entries must point to a FeatureServer/MapServer layer, not an HTML page.
If ?f=pjson on the base doesn't return JSON, it's the wrong URL."

This script tests all ArcGIS endpoints to ensure they return valid JSON.
"""

import json
import urllib.request
import urllib.error
import yaml
from pathlib import Path


def test_arcgis_endpoint(base_url: str, key: str) -> bool:
    """Test if an ArcGIS endpoint returns valid JSON."""
    test_url = f"{base_url}?f=pjson"

    try:
        print(f"  Testing: {test_url}")

        with urllib.request.urlopen(test_url, timeout=10) as response:
            if response.status != 200:
                print(f"  ❌ HTTP {response.status}")
                return False

            content_type = response.headers.get("Content-Type", "")
            if "json" not in content_type.lower():
                print(f"  ❌ Content-Type is '{content_type}', expected JSON")
                return False

            data = response.read()
            try:
                json_data = json.loads(data)
                print(f"  ✓ Valid JSON response ({len(data)} bytes)")

                # Check if it's a valid ArcGIS service response
                if "serviceDescription" in json_data or "type" in json_data:
                    print("  ✓ Valid ArcGIS service response")
                else:
                    print("  ⚠️  JSON response but may not be ArcGIS service")

                return True

            except json.JSONDecodeError as e:
                print(f"  ❌ Invalid JSON: {e}")
                return False

    except urllib.error.HTTPError as e:
        print(f"  ❌ HTTP Error {e.code}: {e.reason}")
        return False
    except urllib.error.URLError as e:
        print(f"  ❌ URL Error: {e.reason}")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def validate_arcgis_endpoints():
    """Validate all ArcGIS endpoints in config/sources.yml."""
    print("🔍 Validating ArcGIS Endpoints")
    print("=" * 50)

    sources_file = Path("config/sources.yml")

    if not sources_file.exists():
        print(f"❌ Sources file not found: {sources_file}")
        return False

    try:
        with open(sources_file) as f:
            sources = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error parsing sources.yml: {e}")
        return False

    arcgis_sources = [s for s in sources if s.get("kind") == "arcgis"]

    if not arcgis_sources:
        print("ℹ️  No ArcGIS sources found in configuration")
        return True

    print(f"Found {len(arcgis_sources)} ArcGIS sources to validate...")
    print()

    all_valid = True

    for source in arcgis_sources:
        key = source.get("key", "unknown")
        base_url = source.get("base", "")

        print(f"🌐 Validating '{key}':")

        if not base_url:
            print("  ❌ No base URL configured")
            all_valid = False
            continue

        if test_arcgis_endpoint(base_url, key):
            print("  ✅ Endpoint validation passed")
        else:
            print("  ❌ Endpoint validation failed")
            all_valid = False

        print()

    return all_valid


if __name__ == "__main__":
    print("Note: This script requires internet access to validate endpoints.")
    print("Some endpoints may be temporarily unavailable or require VPN access.")
    print()

    if validate_arcgis_endpoints():
        print("✅ All ArcGIS endpoint validations passed!")
        exit(0)
    else:
        print("❌ Some ArcGIS endpoint validations failed.")
        print("Please check the URLs and try again.")
        exit(1)
