import re
from typing import Dict, Any, Optional
from datetime import datetime
from dateutil import parser as date_parser

RESIDENTIAL_KEYWORDS = [
    "residential",
    "single family",
    "sfh",
    "duplex",
    "townhome",
    "townhouse",
    "apartment",
    "multi-family",
    "remodel",
    "addition",
    "bathroom",
    "kitchen",
    "roof",
    "siding",
    "fence",
    "pool",
    "deck",
    "garage",
    "foundation",
    "window",
    "hvac",
    "plumbing",
    "electrical",
]


def _get(d: dict, keys):
    for k in keys if isinstance(keys, list) else [keys]:
        if k in d and d[k] is not None:
            return d[k]
    return ""


def normalize_record(rec: Dict[str, Any], source: str) -> Dict[str, Any]:
    """
    Attempts to map common fields; supports Socrata address composition via '__address_composed' injected by adapter.
    """
    # direct keys + fallbacks
    permit_number = str(
        _get(
            rec, ["permit_number", "permit", "permit_", "id", "permitnum", "permit_no"]
        )
    )
    issued_date = str(
        _get(
            rec,
            [
                "issue_date",
                "issued_date",
                "application_start_date",
                "date_issued",
                "issued",
            ],
        )
    )
    status = str(_get(rec, ["status", "current_status", "permit_status"]))
    address = str(
        _get(rec, ["__address_composed", "address", "full_address", "street_address"])
    )
    city = str(_get(rec, ["city", "municipality"]))
    state = str(_get(rec, ["state", "state_abbr"]))
    zipcode = str(_get(rec, ["zip", "zipcode", "postal_code"]))
    applicant = str(_get(rec, ["applicant", "applicant_name", "owner_name", "owner"]))
    contractor = str(_get(rec, ["contractor", "contractor_name", "company_name"]))
    description = str(_get(rec, ["description", "work_description", "summary"]))
    value = _get(rec, ["estimated_cost", "declared_valuation", "value"])
    work_class = str(_get(rec, ["work_class", "permit_type", "work_type", "category"]))
    category = str(_get(rec, ["category", "occupancy_type", "permit_type"]))
    lat = _get(rec, ["latitude", "lat"])
    lon = _get(rec, ["longitude", "lon", "lng"])

    return {
        "source": source,
        "permit_number": permit_number,
        "issued_date": issued_date,
        "status": status,
        "address": address,
        "city": city,
        "state": state,
        "zipcode": zipcode,
        "applicant": applicant,
        "contractor": contractor,
        "description": description,
        "value": float(value) if str(value).replace(".", "", 1).isdigit() else None,
        "work_class": work_class,
        "category": category,
        "latitude": (
            float(lat)
            if str(lat).replace(".", "", 1).replace("-", "", 1).isdigit()
            else None
        ),
        "longitude": (
            float(lon)
            if str(lon).replace(".", "", 1).replace("-", "", 1).isdigit()
            else None
        ),
        "raw_json": rec,
    }


def safe_float(value: Any) -> Optional[float]:
    """
    Safely convert a value to float, returning None if conversion fails.

    Args:
        value: Value to convert to float

    Returns:
        Float value or None if conversion fails
    """
    if value is None:
        return None

    try:
        # Handle string values with currency symbols and commas
        if isinstance(value, str):
            # Remove common currency symbols and formatting
            cleaned = re.sub(r"[$,\s]", "", value.strip())
            if not cleaned:
                return None
            return float(cleaned)

        return float(value)
    except (ValueError, TypeError):
        return None


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse date string into datetime object using flexible parsing.

    Args:
        date_str: Date string to parse

    Returns:
        Parsed datetime object or None if parsing fails
    """
    if not date_str or not isinstance(date_str, str):
        return None

    try:
        # Use dateutil parser for flexible date parsing
        return date_parser.parse(date_str.strip())
    except (ValueError, TypeError, date_parser.ParserError):
        return None


def slugify(text: str) -> str:
    """
    Convert text to URL-friendly slug format.

    Args:
        text: Text to convert to slug

    Returns:
        Slugified text
    """
    if not text:
        return ""

    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug.strip("-")


def normalize_address(address: str) -> str:
    """
    Basic address normalization.

    Args:
        address: Address string to normalize

    Returns:
        Normalized address string
    """
    if not address:
        return ""

    # Remove extra whitespace and convert to title case
    normalized = " ".join(address.split())

    # Basic abbreviation expansions
    replacements = {
        r"\bSt\b": "Street",
        r"\bAve\b": "Avenue",
        r"\bRd\b": "Road",
        r"\bDr\b": "Drive",
        r"\bLn\b": "Lane",
        r"\bBlvd\b": "Boulevard",
        r"\bCt\b": "Court",
        r"\bPl\b": "Place",
    }

    for pattern, replacement in replacements.items():
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)

    return normalized.title()
