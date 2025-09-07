#!/usr/bin/env python3
"""
Example of how to update main_old.py to use the unified SourceAdapter interface.

This demonstrates the migration from special-casing each adapter type
to using the unified interface.
"""

import argparse
from pathlib import Path
from typing import List, Dict, Any

from permit_leads.adapters.simple_socrata_adapter import SimpleSocrataAdapter
from permit_leads.adapters.arcgis_feature_service import ArcGISFeatureServiceAdapter
from permit_leads.adapters.tpia_adapter import TPIAAdapter
from permit_leads.adapters.html_table_adapter import HTMLTableAdapter
from permit_leads.adapters.accela_html_adapter import AccelaHTMLAdapter


# Updated adapter registry using the new interface
ADAPTERS = {
    "socrata": SimpleSocrataAdapter,  # Changed from SocrataAdapter
    "arcgis_feature_service": ArcGISFeatureServiceAdapter,
    "tpia": TPIAAdapter,
    "html_table": HTMLTableAdapter,
    "accela_html": AccelaHTMLAdapter,
}


def load_sources(config_path: Path) -> List[Dict[str, Any]]:
    """Load source configurations from YAML file."""
    import yaml

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg.get("sources", [])


def run_source_unified(
    source_cfg: Dict[str, Any], since_days: int, limit: int = 5000
) -> None:
    """
    Process a source using the unified SourceAdapter interface.

    NO MORE SPECIAL-CASING! Same code works for all sources.
    """
    name = source_cfg.get("name", "unknown")
    adapter_type = source_cfg["type"]

    # Get adapter class
    adapter_cls = ADAPTERS.get(adapter_type)
    if not adapter_cls:
        print(f"[WARN] Unsupported adapter type: {adapter_type} for {name}")
        return

    # Create adapter instance
    adapter = adapter_cls(source_cfg)

    print(f"[INFO] Processing {adapter.name} using unified interface...")

    # Unified processing pipeline - same for ALL sources!
    count_in = 0
    count_residential = 0
    count_saved = 0

    try:
        # Step 1: Fetch raw data
        print(f"[INFO] Fetching raw data from {adapter.name}...")
        raw_data_chunks = list(adapter.fetch(since_days))
        print(f"[INFO] Fetched {len(raw_data_chunks)} raw data chunks")

        # Step 2: Parse and normalize records
        print(f"[INFO] Processing records from {adapter.name}...")
        for raw_chunk in raw_data_chunks:
            for parsed_record in adapter.parse(raw_chunk):
                count_in += 1

                # Step 3: Normalize record
                normalized_record = adapter.normalize(parsed_record)

                # Residential classification (same logic for all sources)
                is_residential = is_residential_permit(normalized_record)

                if is_residential:
                    count_residential += 1

                    # Save/process the record
                    # storage.save_permit(normalized_record)  # Uncomment if using storage
                    count_saved += 1

                    # Show sample record
                    if count_saved <= 3:
                        print(
                            f"[SAMPLE] {normalized_record.get('permit_number')} - {normalized_record.get('address')}"
                        )

                # Limit processing if specified
                if count_in >= limit:
                    break

            if count_in >= limit:
                break

    except Exception as e:
        print(f"[ERROR] Error processing {adapter.name}: {e}")
        return

    print(
        f"[RESULT] {adapter.name}: {count_in} total, {count_residential} residential, {count_saved} saved"
    )


def is_residential_permit(record: Dict[str, Any]) -> bool:
    """Determine if a permit is residential (same logic for all sources)."""

    # Check category field first
    category = record.get("category", "").lower()
    if "residential" in category:
        return True

    # Check work class
    work_class = record.get("work_class", "").lower()
    if "residential" in work_class:
        return True

    # Keyword-based classification
    RESIDENTIAL_KEYWORDS = [
        "single family",
        "duplex",
        "townhouse",
        "condo",
        "residential",
        "house",
        "home",
        "dwelling",
        "apartment",
        "kitchen",
        "bathroom",
        "bedroom",
        "garage",
        "fence",
        "pool",
        "deck",
        "patio",
    ]

    description = record.get("description", "").lower()
    for keyword in RESIDENTIAL_KEYWORDS:
        if keyword in description:
            return True

    return False


def main():
    """Main entry point using unified interface."""
    parser = argparse.ArgumentParser(
        description="Process permit data using unified SourceAdapter interface"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default="config/sources.yaml",
        help="Configuration file path",
    )
    parser.add_argument(
        "--days", type=int, default=7, help="Number of days back to fetch data"
    )
    parser.add_argument(
        "--limit", type=int, default=5000, help="Maximum records to process per source"
    )
    parser.add_argument(
        "--source", type=str, help="Process only specific source by name"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("UNIFIED SOURCE ADAPTER DEMO")
    print("=" * 60)

    # Load configuration
    try:
        sources = load_sources(args.config)
        print(f"[INFO] Loaded {len(sources)} source configurations")
    except FileNotFoundError:
        print(f"[ERROR] Configuration file not found: {args.config}")
        return
    except Exception as e:
        print(f"[ERROR] Error loading configuration: {e}")
        return

    # Process sources
    for source_cfg in sources:
        source_name = source_cfg.get("name", "unknown")

        # Filter by source if specified
        if args.source and source_name.lower() != args.source.lower():
            continue

        print(f"\n{'='*40}")
        print(f"Processing: {source_name}")
        print(f"{'='*40}")

        # Use unified interface - same code for all sources!
        run_source_unified(source_cfg, args.days, args.limit)

    print(f"\n{'='*60}")
    print("BENEFITS OF UNIFIED INTERFACE:")
    print("• Single code path handles all sources")
    print("• No special-casing for Houston/Dallas/Austin/Harris")
    print("• Easy to add new jurisdictions")
    print("• Type-safe with Protocol interface")
    print("• Consistent normalize() output format")
    print("=" * 60)


if __name__ == "__main__":
    main()
