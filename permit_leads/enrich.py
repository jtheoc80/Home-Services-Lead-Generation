"""
Data enrichment pipeline for permit records.

Provides functions to enrich scraped permit data with:
- Address normalization and geocoding
- Parcel/assessor data from ArcGIS FeatureServer
- Trade tagging and categorization
- Owner classification
- Budget bands and project start predictions
"""

from __future__ import annotations
import os
import re
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import yaml

logger = logging.getLogger(__name__)

# Trade keywords for classification
TRADE_KEYWORDS = {
    "roofing": ["roof", "roofing", "shingle", "gutter", "eave"],
    "bath": ["bath", "bathroom", "shower", "toilet", "vanity", "tub"],
    "kitchen": ["kitchen", "cabinet", "countertop", "appliance"],
    "pool": ["pool", "spa", "jacuzzi", "hot tub", "swimming"],
    "fence": ["fence", "fencing", "gate", "barrier"],
    "windows": ["window", "glazing", "glass", "sash"],
    "foundation": ["foundation", "slab", "footing", "pier", "basement"],
    "solar": ["solar", "photovoltaic", "pv", "renewable"],
    "hvac": ["hvac", "heating", "cooling", "air condition", "furnace", "heat pump"],
    "electrical": ["electrical", "electric", "wiring", "panel", "outlet"],
    "plumbing": ["plumb", "water", "sewer", "pipe", "drain"],
}

# Budget bands
BUDGET_BANDS = [
    (0, 5000, "$0–5k"),
    (5000, 15000, "$5–15k"),
    (15000, 50000, "$15–50k"),
    (50000, float("inf"), "$50k+"),
]

# Default median days to first inspection by jurisdiction
DEFAULT_INSPECTION_DAYS = {"city_of_houston": 14, "harris_county": 10, "default": 7}


def normalize_address(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize and clean address field.

    Args:
        record: Permit record dictionary

    Returns:
        Updated record with normalized address
    """
    address = record.get("address", "")
    if not address:
        return record

    # Basic cleanup
    address = " ".join(str(address).split())  # Remove extra whitespace
    address = address.strip()

    # Standardize common abbreviations
    replacements = {
        r"\bSt\.?\b": "St",
        r"\bAve\.?\b": "Ave",
        r"\bRd\.?\b": "Rd",
        r"\bDr\.?\b": "Dr",
        r"\bLn\.?\b": "Ln",
        r"\bCt\.?\b": "Ct",
        r"\bBlvd\.?\b": "Blvd",
        r"\bPkwy\.?\b": "Pkwy",
        r"\bN\.?\b": "N",
        r"\bS\.?\b": "S",
        r"\bE\.?\b": "E",
        r"\bW\.?\b": "W",
    }

    for pattern, replacement in replacements.items():
        address = re.sub(pattern, replacement, address, flags=re.IGNORECASE)

    record["address"] = address
    return record


def geocode(
    record: Dict[str, Any], provider: str = None, api_key: str = None
) -> Dict[str, Any]:
    """
    Geocode address to lat/lon coordinates.

    Args:
        record: Permit record dictionary
        provider: Geocoding provider ('nominatim', 'mapbox', 'google')
        api_key: API key for commercial providers

    Returns:
        Updated record with latitude/longitude fields
    """
    if not provider:
        provider = os.getenv("GEOCODER", "nominatim")

    address = record.get("address", "")
    if not address:
        return record

    try:
        if provider == "nominatim":
            lat, lon = _geocode_nominatim(address)
        elif provider == "mapbox":
            api_key = api_key or os.getenv("MAPBOX_TOKEN")
            lat, lon = _geocode_mapbox(address, api_key)
        elif provider == "google":
            api_key = api_key or os.getenv("GOOGLE_MAPS_API_KEY")
            lat, lon = _geocode_google(address, api_key)
        else:
            logger.warning(f"Unknown geocoding provider: {provider}")
            return record

        if lat and lon:
            record["latitude"] = lat
            record["longitude"] = lon

    except Exception as e:
        logger.warning(f"Geocoding failed for {address}: {e}")

    return record


def _geocode_nominatim(address: str) -> Tuple[Optional[float], Optional[float]]:
    """Geocode using Nominatim (OpenStreetMap)."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1}

    headers = {"User-Agent": "permit-leads-enrichment/1.0"}

    response = requests.get(url, params=params, headers=headers, timeout=10)
    response.raise_for_status()

    data = response.json()
    if data:
        return float(data[0]["lat"]), float(data[0]["lon"])
    return None, None


def _geocode_mapbox(
    address: str, api_key: str
) -> Tuple[Optional[float], Optional[float]]:
    """Geocode using Mapbox."""
    if not api_key:
        raise ValueError("Mapbox API key required")

    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{address}.json"
    params = {"access_token": api_key, "limit": 1}

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()
    if data.get("features"):
        coords = data["features"][0]["geometry"]["coordinates"]
        return coords[1], coords[0]  # lat, lon
    return None, None


def _geocode_google(
    address: str, api_key: str
) -> Tuple[Optional[float], Optional[float]]:
    """Geocode using Google Maps."""
    if not api_key:
        raise ValueError("Google Maps API key required")

    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": api_key}

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()
    if data.get("results"):
        location = data["results"][0]["geometry"]["location"]
        return location["lat"], location["lng"]
    return None, None


def fetch_parcel(
    record: Dict[str, Any], config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Fetch parcel/assessor data from ArcGIS FeatureServer.

    Args:
        record: Permit record dictionary
        config: Configuration dict with ArcGIS endpoints

    Returns:
        Updated record with parcel fields (apn, year_built, heated_sqft, lot_size, land_use)
    """
    if not config:
        config = _load_config()

    lat = record.get("latitude")
    lon = record.get("longitude")
    jurisdiction = record.get("jurisdiction", "").lower().replace(" ", "_")

    if not lat or not lon:
        return record

    parcel_config = config.get("parcels", {}).get(jurisdiction)
    if not parcel_config:
        logger.debug(f"No parcel config for jurisdiction: {jurisdiction}")
        return record

    try:
        parcel_data = _query_arcgis_parcel(lat, lon, parcel_config)
        if parcel_data:
            # Map fields based on configuration
            field_mapping = parcel_config.get("field_mapping", {})

            if "apn" in field_mapping and field_mapping["apn"] in parcel_data:
                record["apn"] = parcel_data[field_mapping["apn"]]
            if (
                "year_built" in field_mapping
                and field_mapping["year_built"] in parcel_data
            ):
                record["year_built"] = parcel_data[field_mapping["year_built"]]
            if (
                "heated_sqft" in field_mapping
                and field_mapping["heated_sqft"] in parcel_data
            ):
                record["heated_sqft"] = parcel_data[field_mapping["heated_sqft"]]
            if "lot_size" in field_mapping and field_mapping["lot_size"] in parcel_data:
                record["lot_size"] = parcel_data[field_mapping["lot_size"]]
            if "land_use" in field_mapping and field_mapping["land_use"] in parcel_data:
                record["land_use"] = parcel_data[field_mapping["land_use"]]

    except Exception as e:
        logger.warning(f"Parcel lookup failed for {lat}, {lon}: {e}")

    return record


def _query_arcgis_parcel(
    lat: float, lon: float, config: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Query ArcGIS FeatureServer for parcel data."""
    url = config["endpoint"]

    # Create point geometry for spatial query
    params = {
        "f": "json",
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "*",
        "returnGeometry": "false",
    }

    response = requests.get(url + "/query", params=params, timeout=15)
    response.raise_for_status()

    data = response.json()
    features = data.get("features", [])

    if features:
        return features[0]["attributes"]
    return None


def derive_owner_kind(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify owner as 'individual' or 'llc' based on owner name.

    Args:
        record: Permit record dictionary

    Returns:
        Updated record with owner_kind field
    """
    owner = record.get("owner", "")
    if not owner:
        record["owner_kind"] = None
        return record

    owner_lower = owner.lower()

    # LLC indicators
    llc_patterns = [
        "llc",
        "l.l.c",
        "inc",
        "corp",
        "corporation",
        "company",
        "co.",
        "partners",
        "partnership",
        "trust",
        "estate",
        "properties",
        "investments",
        "holdings",
        "group",
        "enterprises",
    ]

    if any(pattern in owner_lower for pattern in llc_patterns):
        record["owner_kind"] = "llc"
    else:
        record["owner_kind"] = "individual"

    return record


def normalize_trade(raw_permit: Dict[str, Any]) -> str:
    """
    Normalize trade value from raw permit dictionary using prioritized logic.

    Infers a single trade classification from permit data using the following priority:
    1. Most specific/high-value trade from work description keywords
    2. Permit type mapping
    3. Permit class/category mapping
    4. Default fallback to 'General'

    Args:
        raw_permit: Raw permit data dictionary

    Returns:
        Single trade classification string
    """
    # Priority mapping for trade types (higher number = higher priority)
    TRADE_PRIORITY = {
        "roofing": 10,  # High-value specialty trade
        "solar": 9,  # High-value specialty trade
        "pool": 8,  # High-value specialty trade
        "kitchen": 7,  # High-value remodel
        "bath": 6,  # High-value remodel
        "hvac": 5,  # Important mechanical trade
        "electrical": 4,  # Important trade
        "plumbing": 4,  # Important trade
        "foundation": 3,  # Structural work
        "windows": 2,  # Common improvement
        "fence": 1,  # Lower-value work
    }

    # Extract relevant text fields for analysis
    description = str(
        raw_permit.get("work_description", "") or raw_permit.get("description", "")
    ).lower()
    permit_type = str(raw_permit.get("permit_type", "")).lower()
    permit_class = str(
        raw_permit.get("permit_class", "") or raw_permit.get("work_class", "")
    ).lower()

    # Combine all text for comprehensive analysis
    combined_text = f"{description} {permit_type} {permit_class}"

    # Find matching trades from keywords
    matching_trades = []
    for trade, keywords in TRADE_KEYWORDS.items():
        if any(keyword in combined_text for keyword in keywords):
            priority = TRADE_PRIORITY.get(trade, 0)
            matching_trades.append((trade, priority))

    # Return highest priority trade if any matches found
    if matching_trades:
        # Sort by priority (descending) and return the highest priority trade
        matching_trades.sort(key=lambda x: x[1], reverse=True)
        return matching_trades[0][0].title()

    # Fallback to permit_type or permit_class if no keyword matches
    if permit_type and permit_type not in ["", "null", "none"]:
        # Basic permit type mapping
        if any(word in permit_type for word in ["residential", "building", "house"]):
            return "General Construction"
        elif any(word in permit_type for word in ["commercial", "office"]):
            return "Commercial"
        elif any(word in permit_type for word in ["electrical", "electric"]):
            return "Electrical"
        elif any(word in permit_type for word in ["plumbing", "plumb"]):
            return "Plumbing"
        elif any(word in permit_type for word in ["mechanical", "hvac"]):
            return "HVAC"
        else:
            return permit_type.title()

    if permit_class and permit_class not in ["", "null", "none"]:
        return permit_class.title()

    # Final fallback
    return "General"


def tag_trades(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tag record with relevant trade categories based on description.

    Args:
        record: Permit record dictionary

    Returns:
        Updated record with trade_tags field (list of strings)
    """
    description = (
        record.get("description", "") + " " + record.get("work_class", "")
    ).lower()

    trade_tags = []
    for trade, keywords in TRADE_KEYWORDS.items():
        if any(keyword in description for keyword in keywords):
            trade_tags.append(trade)

    record["trade_tags"] = trade_tags
    return record


def budget_band(value: float) -> str:
    """
    Categorize project value into budget bands.

    Args:
        value: Project value in dollars

    Returns:
        Budget band string
    """
    if not value or value <= 0:
        return "$0–5k"

    for min_val, max_val, band in BUDGET_BANDS:
        if min_val <= value < max_val:
            return band

    return "$50k+"


def start_by_prediction(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Predict project start date based on issue date and jurisdiction.

    Args:
        record: Permit record dictionary

    Returns:
        Updated record with start_by_estimate field
    """
    issue_date = record.get("issue_date")
    if not issue_date:
        return record

    try:
        # Parse issue date
        if isinstance(issue_date, str):
            issue_dt = datetime.fromisoformat(issue_date.replace("Z", "+00:00"))
        else:
            issue_dt = issue_date

        jurisdiction = record.get("jurisdiction", "").lower().replace(" ", "_")
        days_to_start = DEFAULT_INSPECTION_DAYS.get(
            jurisdiction, DEFAULT_INSPECTION_DAYS["default"]
        )

        start_estimate = issue_dt + timedelta(days=days_to_start)
        record["start_by_estimate"] = start_estimate.date().isoformat()

    except Exception as e:
        logger.warning(f"Start date prediction failed: {e}")

    return record


def enrich_record(
    record: Dict[str, Any], config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Apply all enrichment functions to a permit record.

    Args:
        record: Permit record dictionary
        config: Optional configuration override

    Returns:
        Fully enriched record
    """
    # Make a copy to avoid mutating input
    enriched = record.copy()

    # Apply enrichment functions in sequence
    enriched = normalize_address(enriched)
    enriched = geocode(enriched)
    enriched = fetch_parcel(enriched, config)
    enriched = derive_owner_kind(enriched)
    enriched = tag_trades(enriched)

    # Add budget band and start prediction
    value = enriched.get("value", 0)
    enriched["budget_band"] = budget_band(value)
    enriched = start_by_prediction(enriched)

    return enriched


def _load_config() -> Dict[str, Any]:
    """Load enrichment configuration from YAML file."""
    config_path = os.path.join(os.path.dirname(__file__), "enrich_config.yaml")

    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f)

    # Return default config if file doesn't exist
    return {
        "parcels": {
            "harris_county": {
                "endpoint": "https://services.arcgis.com/sample/parcels/FeatureServer/0",
                "field_mapping": {
                    "apn": "ACCOUNT_NUM",
                    "year_built": "YEAR_BUILT",
                    "heated_sqft": "BUILDING_SQFT",
                    "lot_size": "LOT_SIZE",
                    "land_use": "LAND_USE_CODE",
                },
            }
        }
    }
