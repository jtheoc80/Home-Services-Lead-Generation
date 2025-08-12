# Harris County ArcGIS Feature Mapper

The `harris_mapper.py` module provides functionality to convert ArcGIS features from Harris County permit data into standardized dictionaries with specific keys required for permit processing.

## Installation

No additional installation required - uses standard Python libraries and dependencies already in the project.

## Usage

```python
from permit_leads.adapters.harris_mapper import convert_feature_to_dict

# Example ArcGIS feature from Harris County
feature = {
    'attributes': {
        'EVENTID': 123456,
        'PERMITNUMBER': 'BP2024001234',
        'PERMITNAME': 'Single Family Residence',
        'APPTYPE': 'Building Permit',
        'ISSUEDDATE': 1705324200000,  # Unix timestamp in milliseconds
        'PROJECTNUMBER': 'PRJ-2024-001',
        'FULLADDRESS': '123 Main St, Houston, TX 77001',
        'STATUS': 'Issued'
    },
    'geometry': {'x': -95.3698, 'y': 29.7604}
}

# Convert to standardized format
result = convert_feature_to_dict(feature)
print(result)
```

## Output Format

The mapper returns a dictionary with these standardized keys:

```python
{
    'event_id': int,           # Cast from EVENTID (safe default: 0)
    'permit_number': str,      # From PERMITNUMBER (safe default: "")
    'permit_name': str,        # From PERMITNAME (safe default: "")
    'app_type': str,           # From APPTYPE (safe default: "")
    'issue_date': str,         # From ISSUEDDATE -> UTC ISO format (safe default: "")
    'project_number': str,     # From PROJECTNUMBER (safe default: "")
    'full_address': str,       # From FULLADDRESS (safe default: "")
    'street_number': str,      # Parsed from FULLADDRESS (safe default: "")
    'street_name': str,        # Parsed from FULLADDRESS (safe default: "")
    'status': str,             # From STATUS (safe default: "")
    'raw': dict                # Original feature data
}
```

## Field Mapping

| Harris County Field | Output Key | Processing |
|-------------------|------------|------------|
| `EVENTID` | `event_id` | Cast to integer with safe default 0 |
| `PERMITNUMBER` | `permit_number` | String with safe default "" |
| `PERMITNAME` | `permit_name` | String with safe default "" |
| `APPTYPE` | `app_type` | String with safe default "" |
| `ISSUEDDATE` | `issue_date` | Parsed to UTC ISO format |
| `PROJECTNUMBER` | `project_number` | String with safe default "" |
| `FULLADDRESS` | `full_address` | String with safe default "" |
| `FULLADDRESS` | `street_number` | Parsed from address |
| `FULLADDRESS` | `street_name` | Parsed from address |
| `STATUS` | `status` | String with safe default "" |
| (entire feature) | `raw` | Original feature preserved |

## Features

### Date Parsing
- Supports Unix timestamps in milliseconds and seconds
- Handles ISO date strings and common date formats
- Converts timezone-naive dates assuming Central Time (Harris County)
- Always outputs UTC ISO format with Z suffix
- Safe default: empty string for invalid dates

### Address Parsing
- Extracts street number and name from full address
- Handles complex numbers like "123A", "123-B", "123 1/2"
- Gracefully handles addresses without numbers
- Safe defaults: empty strings when parsing fails

### Error Handling
- Never throws exceptions - always returns expected structure
- Uses safe defaults for all fields when data is missing or invalid
- Comprehensive logging for debugging
- Preserves original data in 'raw' field for reference

## Testing

Run the comprehensive test suite:

```bash
cd /path/to/Home-Services-Lead-Generation
python -m pytest permit_leads/tests/test_harris_mapper.py -v
```

The test suite includes:
- 24 comprehensive test cases
- Tests for all functions and edge cases
- Realistic Harris County permit data validation
- Error handling and safe defaults validation

## Examples

### Complete Feature
```python
feature = {
    'attributes': {
        'EVENTID': 789012345,
        'PERMITNUMBER': 'BP2024-123456',
        'PERMITNAME': 'Single Family Residence - New Construction',
        'APPTYPE': 'Building Permit - Residential',
        'ISSUEDDATE': 1705324200000,
        'PROJECTNUMBER': 'PRJ-2024-HARRIS-456',
        'FULLADDRESS': '12345 W Oak Forest Dr, Houston, TX 77091',
        'STATUS': 'Issued'
    }
}

result = convert_feature_to_dict(feature)
# Returns fully populated dictionary with all fields
```

### Minimal Data
```python
feature = {'attributes': {'EVENTID': '999'}}
result = convert_feature_to_dict(feature)
# Returns dictionary with safe defaults for missing fields
```

### Invalid Data
```python
feature = {'attributes': {'EVENTID': 'invalid', 'ISSUEDDATE': 'bad_date'}}
result = convert_feature_to_dict(feature)
# Returns dictionary with safe defaults, never crashes
```

## Integration

This mapper is designed to integrate with the existing Harris County ArcGIS adapter pipeline:

1. ArcGIS adapter fetches features from Harris County FeatureServer
2. Features are passed through `convert_feature_to_dict()`
3. Standardized dictionaries are used for permit processing
4. Original data preserved in 'raw' field for audit/debugging