"""
Test cases for registry configuration.
"""

import yaml
from pathlib import Path


def test_registry_yaml_valid():
    """Test that registry.yaml is valid YAML and has expected structure."""
    registry_path = Path(__file__).parent.parent / "config" / "registry.yaml"
    assert registry_path.exists(), "registry.yaml should exist"

    with open(registry_path, "r") as f:
        registry = yaml.safe_load(f)

    # Verify top-level structure
    assert "regions" in registry, "registry should have 'regions' section"
    assert "jurisdictions" in registry, "registry should have 'jurisdictions' section"

    # Verify regions structure
    regions = registry["regions"]
    assert len(regions) == 3, "Should have 3 regions"

    # Check for expected regions
    region_slugs = {r["slug"] for r in regions}
    expected_regions = {"usa", "tx", "tx-houston"}
    assert (
        region_slugs == expected_regions
    ), f"Expected regions {expected_regions}, got {region_slugs}"

    # Verify hierarchical structure
    usa_region = next(r for r in regions if r["slug"] == "usa")
    tx_region = next(r for r in regions if r["slug"] == "tx")
    houston_region = next(r for r in regions if r["slug"] == "tx-houston")

    assert usa_region["parent"] is None, "USA should be top-level"
    assert tx_region["parent"] == "usa", "Texas should be under USA"
    assert houston_region["parent"] == "tx", "Houston Metro should be under Texas"

    # Verify jurisdictions structure
    jurisdictions = registry["jurisdictions"]
    active_jurisdictions = [j for j in jurisdictions if j.get("active", False)]
    assert len(active_jurisdictions) == 4, "Should have 4 active jurisdictions"

    # Check for expected active jurisdictions
    active_slugs = {j["slug"] for j in active_jurisdictions}
    expected_active = {"tx-harris", "tx-fort-bend", "tx-brazoria", "tx-galveston"}
    assert (
        active_slugs == expected_active
    ), f"Expected active jurisdictions {expected_active}, got {active_slugs}"

    # Verify all active jurisdictions have required fields
    for jurisdiction in active_jurisdictions:
        assert (
            "name" in jurisdiction
        ), f"Jurisdiction {jurisdiction['slug']} missing name"
        assert (
            "state" in jurisdiction
        ), f"Jurisdiction {jurisdiction['slug']} missing state"
        assert (
            "region" in jurisdiction
        ), f"Jurisdiction {jurisdiction['slug']} missing region"
        assert (
            "provider" in jurisdiction
        ), f"Jurisdiction {jurisdiction['slug']} missing provider"
        assert (
            "source_config" in jurisdiction
        ), f"Jurisdiction {jurisdiction['slug']} missing source_config"

        # Verify source_config structure
        source_config = jurisdiction["source_config"]
        assert (
            "url" in source_config
        ), f"Jurisdiction {jurisdiction['slug']} missing source URL"
        assert (
            "date_field" in source_config
        ), f"Jurisdiction {jurisdiction['slug']} missing date_field"
        assert (
            "field_map" in source_config
        ), f"Jurisdiction {jurisdiction['slug']} missing field_map"

        # All active jurisdictions should be in Houston Metro
        assert (
            jurisdiction["region"] == "tx-houston"
        ), f"Active jurisdiction {jurisdiction['slug']} should be in tx-houston region"
        assert (
            jurisdiction["state"] == "TX"
        ), f"Active jurisdiction {jurisdiction['slug']} should be in TX"
        assert (
            jurisdiction["provider"] == "arcgis"
        ), f"Active jurisdiction {jurisdiction['slug']} should use arcgis provider"


def test_registry_yaml_field_mappings():
    """Test that field mappings are consistent across jurisdictions."""
    registry_path = Path(__file__).parent.parent / "config" / "registry.yaml"

    with open(registry_path, "r") as f:
        registry = yaml.safe_load(f)

    active_jurisdictions = [
        j for j in registry["jurisdictions"] if j.get("active", False)
    ]

    # All active jurisdictions should have the same field mapping structure
    expected_fields = {
        "permit_id",
        "issue_date",
        "work_class",
        "value",
        "applicant",
        "address",
    }

    for jurisdiction in active_jurisdictions:
        field_map = jurisdiction["source_config"]["field_map"]
        mapped_fields = set(field_map.keys())
        assert (
            mapped_fields == expected_fields
        ), f"Jurisdiction {jurisdiction['slug']} has inconsistent field mapping: {mapped_fields} vs {expected_fields}"
