"""Harris County ArcGIS Feature Mapper.

Converts ArcGIS features from Harris County permit data into standardized dictionaries
with specific keys required for permit processing.
"""

import logging
import re
from datetime import datetime
from typing import Dict, Any
from dateutil import parser as date_parser
import pytz

logger = logging.getLogger(__name__)


def convert_feature_to_dict(feature: Dict[str, Any]) -> Dict[str, Any]:
    """Convert ArcGIS feature to standardized dictionary format.

    Args:
        feature: ArcGIS feature dictionary with 'attributes' and optional 'geometry'

    Returns:
        Dictionary with standardized keys:
        {
            'event_id': int,
            'permit_number': str,
            'permit_name': str,
            'app_type': str,
            'issue_date': str,  # UTC ISO format
            'project_number': str,
            'full_address': str,
            'street_number': str,
            'street_name': str,
            'status': str,
            'raw': dict  # Original feature
        }
    """
    if not isinstance(feature, dict):
        logger.warning("Feature is not a dictionary, using empty feature")
        feature = {}

    attributes = feature.get("attributes", {})
    if not isinstance(attributes, dict):
        logger.warning("Feature attributes is not a dictionary, using empty attributes")
        attributes = {}

    # Extract and convert fields with safe defaults
    result = {
        "event_id": _safe_cast_to_int(attributes.get("EVENTID")),
        "permit_number": _safe_str(attributes.get("PERMITNUMBER")),
        "permit_name": _safe_str(attributes.get("PERMITNAME")),
        "app_type": _safe_str(attributes.get("APPTYPE")),
        "issue_date": _safe_parse_date_to_iso(attributes.get("ISSUEDDATE")),
        "project_number": _safe_str(attributes.get("PROJECTNUMBER")),
        "full_address": _safe_str(attributes.get("FULLADDRESS")),
        "status": _safe_str(attributes.get("STATUS")),
        "raw": feature,
    }

    # Parse street number and name from full address
    street_number, street_name = _parse_address(result["full_address"])
    result["street_number"] = street_number
    result["street_name"] = street_name

    return result


def _safe_cast_to_int(value: Any) -> int:
    """Safely cast value to integer with fallback to 0."""
    if value is None:
        return 0

    try:
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            # Remove any non-numeric characters except minus sign
            cleaned = re.sub(r"[^\d-]", "", value.strip())
            if cleaned:
                return int(cleaned)
        return 0
    except (ValueError, TypeError, OverflowError):
        logger.warning(f"Could not convert '{value}' to int, using 0")
        return 0


def _safe_str(value: Any) -> str:
    """Safely convert value to string with fallback to empty string."""
    if value is None:
        return ""

    try:
        if isinstance(value, str):
            return value.strip()
        return str(value).strip()
    except (TypeError, AttributeError):
        logger.warning(f"Could not convert '{value}' to string, using empty string")
        return ""


def _safe_parse_date_to_iso(value: Any) -> str:
    """Safely parse date value to UTC ISO format string.

    Handles various date formats including:
    - Unix timestamps (milliseconds and seconds)
    - ISO date strings
    - Common date formats

    Returns:
        UTC ISO format string (YYYY-MM-DDTHH:MM:SSZ) or empty string if parsing fails
    """
    if value is None or value == "":
        return ""

    try:
        parsed_date = None

        # Handle numeric timestamps (common in ArcGIS)
        if isinstance(value, (int, float)):
            # ArcGIS often uses milliseconds since epoch
            if value > 1e10:  # Likely milliseconds
                parsed_date = datetime.fromtimestamp(value / 1000, tz=pytz.UTC)
            elif value > 0:  # Likely seconds
                parsed_date = datetime.fromtimestamp(value, tz=pytz.UTC)

        # Handle string values
        elif isinstance(value, str):
            value = value.strip()
            if value:
                # Try to parse with dateutil which handles many formats
                parsed_date = date_parser.parse(value)

                # Convert to UTC if timezone-naive
                if parsed_date.tzinfo is None:
                    # Assume local time is Central Time (Harris County is in Texas)
                    central = pytz.timezone("America/Chicago")
                    parsed_date = central.localize(parsed_date)

                # Convert to UTC
                parsed_date = parsed_date.astimezone(pytz.UTC)

        if parsed_date:
            # Return ISO format with Z suffix for UTC
            return parsed_date.strftime("%Y-%m-%dT%H:%M:%SZ")

    except (ValueError, TypeError, OverflowError) as e:
        logger.warning(f"Could not parse date '{value}': {e}")

    return ""


def _parse_address(full_address: str) -> tuple[str, str]:
    """Parse street number and street name from full address.

    Args:
        full_address: Complete address string

    Returns:
        Tuple of (street_number, street_name)
    """
    if not full_address or not isinstance(full_address, str):
        return "", ""

    address = full_address.strip()
    if not address:
        return "", ""

    try:
        # Common patterns for Texas addresses:
        # "123 Main St, Houston, TX 77001"
        # "123 N Main Street"
        # "123-A Main St"

        # Split on comma to get the street portion
        street_part = address.split(",")[0].strip()

        # Match street number at the beginning
        # Handles patterns like: 123, 123A, 123-A, 123 1/2
        number_match = re.match(r"^(\d+[\w\-/]*)\s+(.+)", street_part)

        if number_match:
            street_number = number_match.group(1).strip()
            street_name = number_match.group(2).strip()
            return street_number, street_name

        # If no number found, return empty number and full street part as name
        return "", street_part

    except (AttributeError, IndexError) as e:
        logger.warning(f"Error parsing address '{full_address}': {e}")
        return "", address
