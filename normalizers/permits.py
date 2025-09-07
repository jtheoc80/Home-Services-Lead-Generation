"""
Permit data normalization utilities.

This module provides functions to normalize raw permit data from various
sources into the standardized gold.permits schema.
"""

import hashlib
import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from .field_aliases import (
    PERMIT_ALIASES,
    JURISDICTION_SPECIFIC_ALIASES,
    STATUS_MAPPINGS,
    PERMIT_TYPE_MAPPINGS,
)

logger = logging.getLogger(__name__)

# Texas coordinate bounds for validation
TEXAS_MIN_LATITUDE = 25.5
TEXAS_MAX_LATITUDE = 36.5
TEXAS_MIN_LONGITUDE = -107.0
TEXAS_MAX_LONGITUDE = -93.0


def pick(record: Dict[str, Any], aliases: List[str]) -> Any:
    """
    Pick the first present field from a list of aliases.

    Args:
        record: Source record dictionary
        aliases: List of field names to try in order

    Returns:
        Value of the first found field, or None if none found
    """
    for alias in aliases:
        if alias in record and record[alias] is not None:
            value = record[alias]
            # Skip empty strings and common null values
            if value not in ["", "null", "NULL", "N/A", "n/a"]:
                return value
    return None


def normalize_date(value: Any) -> Optional[datetime]:
    """
    Parse various date formats to datetime.

    Args:
        value: Date value in various formats

    Returns:
        Parsed datetime in UTC or None if unparseable
    """
    if not value:
        return None

    if isinstance(value, datetime):
        return value

    if not isinstance(value, str):
        return None

    # Clean the date string
    date_str = str(value).strip()
    if not date_str:
        return None

    # Common date formats
    date_formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%m/%d/%Y",
        "%m/%d/%Y %H:%M:%S",
        "%m-%d-%Y",
        "%d-%m-%Y",
        "%Y%m%d",
    ]

    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    logger.warning(f"Could not parse date: {value}")
    return None


def normalize_numeric(value: Any) -> Optional[float]:
    """
    Parse numeric values, handling currency and formatting.

    Args:
        value: Numeric value in various formats

    Returns:
        Parsed float or None if unparseable
    """
    if not value:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        # Remove currency symbols, commas, and whitespace
        cleaned = re.sub(r"[$,\s]", "", value.strip())
        if not cleaned:
            return None

        try:
            return float(cleaned)
        except ValueError:
            return None

    return None


def normalize_text(value: Any) -> Optional[str]:
    """
    Clean and normalize text values.

    Args:
        value: Text value to clean

    Returns:
        Cleaned text or None if empty
    """
    if not value:
        return None

    text = str(value).strip()

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)

    # Skip null-like values
    if text.upper() in ["NULL", "N/A", "NA", "NONE", "UNKNOWN", ""]:
        return None

    return text if text else None


def normalize_status(status: Any) -> Optional[str]:
    """
    Normalize permit status to standard values.

    Args:
        status: Raw status value

    Returns:
        Standardized status or original if not mapped
    """
    if not status:
        return None

    normalized = str(status).strip().lower()
    return STATUS_MAPPINGS.get(normalized, str(status).upper())


def normalize_permit_type(permit_type: Any) -> Optional[str]:
    """
    Normalize permit type to standard values.

    Args:
        permit_type: Raw permit type value

    Returns:
        Standardized permit type or original if not mapped
    """
    if not permit_type:
        return None

    normalized = str(permit_type).strip().lower()
    return PERMIT_TYPE_MAPPINGS.get(normalized, str(permit_type).upper())


def compute_record_hash(canonical: Dict[str, Any]) -> str:
    """
    Compute a hash of the canonical record for change detection.

    Args:
        canonical: Normalized record dictionary

    Returns:
        SHA1 hash of the sorted JSON representation
    """
    # Create a copy with only the data fields (exclude metadata)
    hashable = {
        k: v for k, v in canonical.items() if not k.startswith("_") and v is not None
    }

    # Convert to sorted JSON for consistent hashing
    json_str = json.dumps(hashable, sort_keys=True, default=str)
    return hashlib.sha1(json_str.encode()).hexdigest()


def build_geometry(
    latitude: Optional[float], longitude: Optional[float]
) -> Optional[str]:
    """
    Build PostGIS geometry from lat/long coordinates.

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate

    Returns:
        PostGIS point geometry WKT or None if coordinates missing
    """
    if latitude is None or longitude is None:
        return None

    # Basic validation for Texas coordinates
    if not (
        TEXAS_MIN_LATITUDE <= latitude <= TEXAS_MAX_LATITUDE
        and TEXAS_MIN_LONGITUDE <= longitude <= TEXAS_MAX_LONGITUDE
    ):
        logger.warning(f"Coordinates outside Texas bounds: {latitude}, {longitude}")
        return None

    return f"POINT({longitude} {latitude})"


def normalize(source_meta: Dict[str, Any], record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a raw permit record to canonical gold.permits schema.

    Args:
        source_meta: Source metadata (jurisdiction, city, etc.)
        record: Raw permit record from data source

    Returns:
        Normalized permit record ready for gold.permits table
    """
    source_id = source_meta.get("id", "unknown")
    jurisdiction = source_meta.get("jurisdiction", "unknown").lower()

    # Use jurisdiction-specific aliases if available
    aliases = JURISDICTION_SPECIFIC_ALIASES.get(jurisdiction, PERMIT_ALIASES)
    if jurisdiction not in JURISDICTION_SPECIFIC_ALIASES:
        aliases = PERMIT_ALIASES

    # Build canonical record
    canonical = {}

    # Core identification
    canonical["source_id"] = source_id
    canonical["permit_id"] = normalize_text(pick(record, aliases.get("permit_id", [])))

    # Jurisdiction information
    canonical["jurisdiction"] = source_meta.get("jurisdiction")
    canonical["city"] = source_meta.get("city")
    canonical["county"] = source_meta.get("county")
    canonical["state"] = "TX"  # Fixed for Texas

    # Dates (parse to UTC datetime)
    canonical["applied_at"] = normalize_date(
        pick(record, aliases.get("applied_at", []))
    )
    canonical["issued_at"] = normalize_date(pick(record, aliases.get("issued_at", [])))
    canonical["finaled_at"] = normalize_date(
        pick(record, aliases.get("finaled_at", []))
    )

    # Status and classification
    canonical["status"] = normalize_status(pick(record, aliases.get("status", [])))
    canonical["permit_type"] = normalize_permit_type(
        pick(record, aliases.get("permit_type", []))
    )
    canonical["subtype"] = normalize_text(pick(record, aliases.get("subtype", [])))
    canonical["work_class"] = normalize_text(
        pick(record, aliases.get("work_class", []))
    )

    # Description
    canonical["description"] = normalize_text(
        pick(record, aliases.get("description", []))
    )

    # Location
    canonical["address_full"] = normalize_text(
        pick(record, aliases.get("address_full", []))
    )
    canonical["postal_code"] = normalize_text(
        pick(record, aliases.get("postal_code", []))
    )
    canonical["parcel_id"] = normalize_text(pick(record, aliases.get("parcel_id", [])))

    # Project details
    canonical["valuation"] = normalize_numeric(
        pick(record, aliases.get("valuation", []))
    )

    # Parties
    canonical["contractor_name"] = normalize_text(
        pick(record, aliases.get("contractor_name", []))
    )
    canonical["contractor_license"] = normalize_text(
        pick(record, aliases.get("contractor_license", []))
    )

    # Geography
    canonical["latitude"] = normalize_numeric(pick(record, aliases.get("latitude", [])))
    canonical["longitude"] = normalize_numeric(
        pick(record, aliases.get("longitude", []))
    )

    # Build PostGIS geometry if coordinates are available
    canonical["geom"] = build_geometry(canonical["latitude"], canonical["longitude"])

    # Additional fields
    canonical["url"] = normalize_text(pick(record, aliases.get("url", [])))

    # Provenance information
    canonical["provenance"] = {
        "source": source_id,
        "raw_keys": list(record.keys()),
        "processed_at": datetime.utcnow().isoformat(),
        "normalizer_version": "1.0",
    }

    # Compute record hash for change detection
    canonical["record_hash"] = compute_record_hash(canonical)

    # Set update timestamp
    canonical["updated_at"] = datetime.utcnow()

    return canonical


def validate_normalized_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate a normalized permit record.

    Args:
        record: Normalized permit record

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Required fields
    if not record.get("permit_id"):
        errors.append("Missing permit_id")

    if not record.get("source_id"):
        errors.append("Missing source_id")

    # Date validation
    issued_at = record.get("issued_at")
    if issued_at and isinstance(issued_at, datetime):
        current_year = datetime.now().year
        if issued_at.year < 1990 or issued_at.year > current_year + 2:
            errors.append(f"Invalid issued_at year: {issued_at.year}")

    # Coordinate validation
    lat = record.get("latitude")
    lon = record.get("longitude")
    if lat is not None:
        if not isinstance(lat, (int, float)) or not (25.0 <= lat <= 37.0):
            errors.append(f"Invalid latitude for Texas: {lat}")
    if lon is not None:
        if not isinstance(lon, (int, float)) or not (-107.0 <= lon <= -93.0):
            errors.append(f"Invalid longitude for Texas: {lon}")

    # Valuation validation
    valuation = record.get("valuation")
    if valuation is not None:
        if not isinstance(valuation, (int, float)) or valuation < 0:
            errors.append(f"Invalid valuation: {valuation}")

    return errors
