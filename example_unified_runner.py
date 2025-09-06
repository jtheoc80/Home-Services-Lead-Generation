#!/usr/bin/env python3
"""
Example runner script demonstrating the unified SourceAdapter interface.

This shows how Houston/Dallas/Austin/SA/Harris can now be handled uniformly
without special-casing each source in the runner code.
"""

import logging
from typing import List, Dict, Any
from permit_leads.adapters.base import SourceAdapter
from permit_leads.adapters.simple_socrata_adapter import SimpleSocrataAdapter
from permit_leads.adapters.arcgis_feature_service import ArcGISFeatureServiceAdapter
from permit_leads.adapters.tpia_adapter import TPIAAdapter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_permits_unified(adapter: SourceAdapter, since_days: int = 7) -> List[Dict[str, Any]]:
    """
    Process permits from any source using the unified SourceAdapter interface.
    
    No special-casing needed - all sources work the same way!
    """
    logger.info(f"Processing permits from {adapter.name} for last {since_days} days")
    
    permits = []
    
    # Step 1: Fetch raw data
    logger.info(f"Fetching raw data from {adapter.name}...")
    raw_data_chunks = list(adapter.fetch(since_days))
    logger.info(f"Fetched {len(raw_data_chunks)} raw data chunks")
    
    # Step 2: Parse raw data into records
    logger.info(f"Parsing raw data from {adapter.name}...")
    for raw_chunk in raw_data_chunks:
        for parsed_record in adapter.parse(raw_chunk):
            # Step 3: Normalize each record
            normalized_record = adapter.normalize(parsed_record)
            permits.append(normalized_record)
    
    logger.info(f"Processed {len(permits)} permits from {adapter.name}")
    return permits


def main():
    """Demonstrate unified interface with different Texas jurisdictions."""
    
    # Configure different adapters for Texas jurisdictions
    adapters_config = [
        {
            "name": "Dallas",
            "adapter_class": SimpleSocrataAdapter,
            "config": {
                "name": "Dallas",
                "url": "https://www.dallasopendata.com/resource/e7gq-4sah.json",
                "date_field": "issued_date",
                "field_map": {
                    "permit_number": "permit_number",
                    "issued_date": "issued_date", 
                    "address": "address",
                    "description": "work_description"
                }
            }
        },
        {
            "name": "Austin", 
            "adapter_class": SimpleSocrataAdapter,
            "config": {
                "name": "Austin",
                "url": "https://data.austintexas.gov/resource/3syk-w9eu.json",
                "date_field": "issued_date",
                "field_map": {
                    "permit_number": "permit_number",
                    "issued_date": "issued_date",
                    "address": "original_address1" 
                }
            }
        },
        {
            "name": "Harris County",
            "adapter_class": ArcGISFeatureServiceAdapter, 
            "config": {
                "name": "Harris County",
                "url": "https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0",
                "date_field": "ISSUEDDATE",
                "mappings": {
                    "permit_number": "PERMITNUMBER",
                    "issued_date": "ISSUEDDATE",
                    "address": "FULLADDRESS",
                    "description": "PERMITNAME",
                    "status": "STATUS"
                }
            }
        },
        {
            "name": "Houston",
            "adapter_class": TPIAAdapter,
            "config": {
                "name": "Houston", 
                "jurisdiction": "houston",
                "data_dir": "./data/tpia",
                "mappings": {
                    "permit_number": "Permit Number",
                    "issued_date": "Issue Date",
                    "address": "Address",
                    "description": "Description"
                }
            }
        }
    ]
    
    print("="*60)
    print("UNIFIED SOURCE ADAPTER INTERFACE DEMONSTRATION")
    print("="*60)
    print()
    
    # Process each jurisdiction using the SAME code!
    for adapter_info in adapters_config:
        print(f"Processing {adapter_info['name']}...")
        print("-" * 40)
        
        try:
            # Create adapter instance
            adapter = adapter_info["adapter_class"](adapter_info["config"])
            
            # Use the unified interface - same code for all sources!
            permits = process_permits_unified(adapter, since_days=1)
            
            print(f"✓ Successfully processed {len(permits)} permits from {adapter.name}")
            
            # Show sample normalized record
            if permits:
                sample = permits[0]
                print(f"Sample normalized record:")
                for key in ["source", "permit_number", "issued_date", "address", "description"]:
                    value = sample.get(key, "N/A")
                    print(f"  {key}: {value}")
                    
        except Exception as e:
            print(f"⚠ Error processing {adapter_info['name']}: {e}")
            
        print()
    
    print("="*60) 
    print("KEY BENEFITS OF UNIFIED INTERFACE:")
    print("• No special-casing needed for different sources")
    print("• Same code handles Houston, Dallas, Austin, Harris County") 
    print("• Consistent fetch() -> parse() -> normalize() pipeline")
    print("• Easy to add new jurisdictions")
    print("• Type-safe with Protocol interface")
    print("="*60)


if __name__ == "__main__":
    main()