# SourceAdapter Interface Documentation

## Overview

The `SourceAdapter` interface provides a unified contract for all permit data sources, eliminating the need for special-casing different jurisdictions (Houston, Dallas, Austin, San Antonio, Harris County) in runner code.

## Interface Definition

```python
from typing import Protocol, Iterable, Dict, Any

class SourceAdapter(Protocol):
    """Formal interface for permit data source adapters."""
    name: str
    
    def fetch(self, since_days: int) -> Iterable[bytes | str]:
        """Fetch raw data from the source."""
        ...
    
    def parse(self, raw: bytes | str) -> Iterable[Dict[str, Any]]:
        """Parse raw data into structured records."""
        ...
    
    def normalize(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a parsed record to standard format."""
        ...
```

## Benefits

### Before: Special-casing Required
```python
# Old approach - different code for each source
def process_permits(source_type, config):
    if source_type == "socrata":
        adapter = SocrataAdapter(config)
        records = adapter.scrape_permits(since, limit)
        # Custom normalization for Socrata
    elif source_type == "arcgis":
        adapter = ArcGISAdapter(config) 
        records = adapter.fetch_since(since, limit)
        # Custom normalization for ArcGIS
    elif source_type == "tpia":
        adapter = TPIAAdapter(config)
        # Completely different processing...
    # etc.
```

### After: Unified Interface
```python
# New approach - same code for all sources!
def process_permits(adapter: SourceAdapter, since_days: int):
    # Step 1: Fetch raw data
    for raw_chunk in adapter.fetch(since_days):
        # Step 2: Parse into records
        for record in adapter.parse(raw_chunk):
            # Step 3: Normalize
            normalized = adapter.normalize(record)
            yield normalized
```

## Available Adapters

### SimpleSocrataAdapter
For Dallas and Austin open data APIs:
```python
adapter = SimpleSocrataAdapter({
    "name": "Dallas",
    "url": "https://www.dallasopendata.com/resource/e7gq-4sah.json",
    "date_field": "issued_date",
    "field_map": {
        "permit_number": "permit_number",
        "address": "address"
    }
})
```

### ArcGISFeatureServiceAdapter
For Harris County and other ArcGIS sources:
```python
adapter = ArcGISFeatureServiceAdapter({
    "name": "Harris County",
    "url": "https://www.gis.hctx.net/.../FeatureServer/0",
    "date_field": "ISSUEDDATE",
    "mappings": {
        "permit_number": "PERMITNUMBER",
        "address": "FULLADDRESS"
    }
})
```

### TPIAAdapter
For Houston CSV files from TPIA requests:
```python
adapter = TPIAAdapter({
    "name": "Houston",
    "jurisdiction": "houston",
    "data_dir": "./data/tpia",
    "mappings": {
        "permit_number": "Permit Number",
        "address": "Address"
    }
})
```

## Usage Example

```python
from permit_leads.adapters.base import SourceAdapter

def process_any_source(adapter: SourceAdapter, days: int = 7):
    """Process permits from any source uniformly."""
    print(f"Processing {adapter.name}...")
    
    permits = []
    for raw_data in adapter.fetch(days):
        for record in adapter.parse(raw_data):
            normalized = adapter.normalize(record)
            permits.append(normalized)
    
    return permits

# Use with any adapter - same code!
dallas_permits = process_any_source(dallas_adapter, 7)
harris_permits = process_any_source(harris_adapter, 7)  
houston_permits = process_any_source(houston_adapter, 7)
```

## Standard Normalized Fields

All adapters produce records with these standard fields:

```python
{
    "source": str,           # Source name (e.g., "Dallas", "Harris County")
    "permit_number": str,    # Permit/record number
    "issued_date": str,      # Issue date
    "address": str,          # Property address
    "description": str,      # Work description
    "status": str,           # Permit status
    "work_class": str,       # Type of work/permit class
    "category": str,         # Category classification
    "applicant": str,        # Applicant/contractor name
    "value": float | None,   # Permit value (parsed)
    "raw_json": dict,        # Original raw record
}
```

## Migration Guide

### Updating Existing Runners

1. **Replace adapter-specific code** with unified interface calls
2. **Use the three-step pipeline**: `fetch()` → `parse()` → `normalize()`
3. **Handle all sources uniformly** using the `SourceAdapter` protocol

### Example Migration

```python
# OLD CODE
if source_type == "dallas":
    dallas_adapter = SocrataAdapter(config)
    raw_records = dallas_adapter.fetch_since(since)
    for record in raw_records:
        normalized = normalize_record(record, source="dallas")
        # Process normalized record

# NEW CODE  
adapter = SimpleSocrataAdapter(config)  # Any SourceAdapter
for raw_chunk in adapter.fetch(since_days):
    for record in adapter.parse(raw_chunk):
        normalized = adapter.normalize(record)
        # Process normalized record
```

## Type Safety

The interface uses Python's `typing.Protocol` for structural typing:

```python
from permit_leads.adapters.base import SourceAdapter

def runner_function(source: SourceAdapter) -> None:
    # Type checker ensures source has required methods
    assert source.name
    source.fetch(7)
    # etc.
```

## Testing

Run the interface test suite:
```bash
python test_source_adapter_interface.py
```

This verifies all adapters implement the protocol correctly and can parse/normalize sample data.