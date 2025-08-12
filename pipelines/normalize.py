
"""Data normalization pipeline producing gold tables for Texas data."""

import logging
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from pathlib import Path
import hashlib

"""
Data normalization pipeline.

This module maps raw permit data to standardized gold schemas for permits,
violations, bids, and awards. It handles field mapping, data type conversion,
and validation.
"""

import logging
import yaml
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import psycopg2
from psycopg2.extras import Json, RealDictCursor
import re


logger = logging.getLogger(__name__)



@dataclass
class NormalizedRecord:
    """Base class for normalized records."""
    id: str
    source: str
    category: str
    jurisdiction: str
    raw_data: Dict[str, Any]
    normalized_at: datetime
    quality_score: float


@dataclass
class Permit(NormalizedRecord):
    """Normalized permit record."""
    permit_number: Optional[str]
    issued_date: Optional[datetime]
    address: Optional[str]
    description: Optional[str]
    status: Optional[str]
    work_class: Optional[str]
    category: Optional[str]
    value: Optional[float]
    applicant: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]


@dataclass
class Violation(NormalizedRecord):
    """Normalized code violation record."""
    case_number: Optional[str]
    created_date: Optional[datetime]
    address: Optional[str]
    violation_type: Optional[str]
    status: Optional[str]
    description: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]


@dataclass
class Inspection(NormalizedRecord):
    """Normalized inspection record."""
    inspection_id: Optional[str]
    inspection_date: Optional[datetime]
    address: Optional[str]
    inspection_type: Optional[str]
    result: Optional[str]
    inspector: Optional[str]
    permit_number: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]


@dataclass
class Bid(NormalizedRecord):
    """Normalized procurement bid record."""
    bid_number: Optional[str]
    bid_date: Optional[datetime]
    description: Optional[str]
    agency: Optional[str]
    status: Optional[str]
    estimated_value: Optional[float]


@dataclass
class Award(NormalizedRecord):
    """Normalized contract award record."""
    contract_number: Optional[str]
    award_date: Optional[datetime]
    vendor_name: Optional[str]
    description: Optional[str]
    amount: Optional[float]
    agency: Optional[str]


@dataclass
class Contractor(NormalizedRecord):
    """Normalized contractor license record."""
    license_number: Optional[str]
    license_type: Optional[str]
    business_name: Optional[str]
    owner_name: Optional[str]
    address: Optional[str]
    city: Optional[str]
    zip_code: Optional[str]
    license_status: Optional[str]
    issue_date: Optional[datetime]
    expiration_date: Optional[datetime]
    specialty: Optional[str]


class DataNormalizer:
    """Pipeline for normalizing raw data into gold tables."""
    
    def __init__(self, raw_data_dir: str = "data/raw", output_dir: str = "data/gold"):
        """Initialize the data normalizer."""
        self.raw_data_dir = Path(raw_data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Quality checks configuration
        self.quality_thresholds = {
            "min_fields_populated": 0.5,  # At least 50% of fields must have data
            "address_required": True,      # Address is required for location-based records
            "date_required": True,         # Date fields are required
            "id_required": True           # Primary ID is required
        }
        
    def normalize_raw_files(self) -> Dict[str, int]:
        """Normalize all raw data files."""
        results = {
            "permits": 0,
            "violations": 0,
            "inspections": 0,
            "bids": 0,
            "awards": 0,
            "contractors": 0
        }
        
        # Process each raw data file
        for raw_file in self.raw_data_dir.glob("*.json"):
            logger.info(f"Processing {raw_file.name}")
            
            try:
                with open(raw_file, 'r') as f:
                    raw_records = json.load(f)
                    
                # Determine category from the records
                if raw_records:
                    category = raw_records[0].get("_category", "unknown")
                    
                    if category == "permits":
                        normalized = self._normalize_permits(raw_records)
                        self._save_normalized_data("permits", normalized)
                        results["permits"] += len(normalized)
                        
                    elif category == "violations":
                        normalized = self._normalize_violations(raw_records)
                        self._save_normalized_data("violations", normalized)
                        results["violations"] += len(normalized)
                        
                    elif category == "inspections":
                        normalized = self._normalize_inspections(raw_records)
                        self._save_normalized_data("inspections", normalized)
                        results["inspections"] += len(normalized)
                        
                    elif category == "bids":
                        normalized = self._normalize_bids(raw_records)
                        self._save_normalized_data("bids", normalized)
                        results["bids"] += len(normalized)
                        
                    elif category == "awards":
                        normalized = self._normalize_awards(raw_records)
                        self._save_normalized_data("awards", normalized)
                        results["awards"] += len(normalized)
                        
                    elif category == "contractors":
                        normalized = self._normalize_contractors(raw_records)
                        self._save_normalized_data("contractors", normalized)
                        results["contractors"] += len(normalized)
                        
                    else:
                        logger.warning(f"Unknown category: {category}")
                        
            except Exception as e:
                logger.error(f"Error processing {raw_file.name}: {e}")
                
        return results
        
    def _normalize_permits(self, raw_records: List[Dict[str, Any]]) -> List[Permit]:
        """Normalize permit records."""
        permits = []
        
        for raw in raw_records:
            try:
                permit = Permit(
                    id=self._generate_id(raw),
                    source=raw.get("_source", ""),
                    category=raw.get("_category", "permits"),
                    jurisdiction=raw.get("_jurisdiction", ""),
                    raw_data=raw,
                    normalized_at=datetime.utcnow(),
                    quality_score=0.0,
                    
                    permit_number=self._clean_string(raw.get("permit_number")),
                    issued_date=self._parse_date(raw.get("issued_date")),
                    address=self._normalize_address(raw.get("address")),
                    description=self._clean_string(raw.get("description")),
                    status=self._normalize_status(raw.get("status")),
                    work_class=self._clean_string(raw.get("work_class")),
                    value=self._parse_float(raw.get("value")),
                    applicant=self._clean_string(raw.get("applicant")),
                    latitude=self._parse_float(raw.get("latitude")),
                    longitude=self._parse_float(raw.get("longitude"))
                )
                
                # Calculate quality score
                permit.quality_score = self._calculate_quality_score(permit, "permit")
                
                # Only include high-quality records
                if permit.quality_score >= 0.5:
                    permits.append(permit)
                else:
                    logger.debug(f"Skipping low-quality permit: {permit.permit_number}")
                    
            except Exception as e:
                logger.warning(f"Error normalizing permit record: {e}")
                
        return permits
        
    def _normalize_violations(self, raw_records: List[Dict[str, Any]]) -> List[Violation]:
        """Normalize violation records."""
        violations = []
        
        for raw in raw_records:
            try:
                violation = Violation(
                    id=self._generate_id(raw),
                    source=raw.get("_source", ""),
                    category=raw.get("_category", "violations"),
                    jurisdiction=raw.get("_jurisdiction", ""),
                    raw_data=raw,
                    normalized_at=datetime.utcnow(),
                    quality_score=0.0,
                    
                    case_number=self._clean_string(raw.get("case_number")),
                    created_date=self._parse_date(raw.get("created_date")),
                    address=self._normalize_address(raw.get("address")),
                    violation_type=self._clean_string(raw.get("violation_type")),
                    status=self._normalize_status(raw.get("status")),
                    description=self._clean_string(raw.get("description")),
                    latitude=self._parse_float(raw.get("latitude")),
                    longitude=self._parse_float(raw.get("longitude"))
                )
                
                violation.quality_score = self._calculate_quality_score(violation, "violation")
                
                if violation.quality_score >= 0.5:
                    violations.append(violation)
                    
            except Exception as e:
                logger.warning(f"Error normalizing violation record: {e}")
                
        return violations
        
    def _normalize_inspections(self, raw_records: List[Dict[str, Any]]) -> List[Inspection]:
        """Normalize inspection records."""
        inspections = []
        
        for raw in raw_records:
            try:
                inspection = Inspection(
                    id=self._generate_id(raw),
                    source=raw.get("_source", ""),
                    category=raw.get("_category", "inspections"),
                    jurisdiction=raw.get("_jurisdiction", ""),
                    raw_data=raw,
                    normalized_at=datetime.utcnow(),
                    quality_score=0.0,
                    
                    inspection_id=self._clean_string(raw.get("inspection_id")),
                    inspection_date=self._parse_date(raw.get("inspection_date")),
                    address=self._normalize_address(raw.get("address")),
                    inspection_type=self._clean_string(raw.get("inspection_type")),
                    result=self._clean_string(raw.get("result")),
                    inspector=self._clean_string(raw.get("inspector")),
                    permit_number=self._clean_string(raw.get("permit_number")),
                    latitude=self._parse_float(raw.get("latitude")),
                    longitude=self._parse_float(raw.get("longitude"))
                )
                
                inspection.quality_score = self._calculate_quality_score(inspection, "inspection")
                
                if inspection.quality_score >= 0.5:
                    inspections.append(inspection)
                    
            except Exception as e:
                logger.warning(f"Error normalizing inspection record: {e}")
                
        return inspections
        
    def _normalize_bids(self, raw_records: List[Dict[str, Any]]) -> List[Bid]:
        """Normalize bid records."""
        bids = []
        
        for raw in raw_records:
            try:
                bid = Bid(
                    id=self._generate_id(raw),
                    source=raw.get("_source", ""),
                    category=raw.get("_category", "bids"),
                    jurisdiction=raw.get("_jurisdiction", ""),
                    raw_data=raw,
                    normalized_at=datetime.utcnow(),
                    quality_score=0.0,
                    
                    bid_number=self._clean_string(raw.get("bid_number")),
                    bid_date=self._parse_date(raw.get("bid_date")),
                    description=self._clean_string(raw.get("description")),
                    agency=self._clean_string(raw.get("agency")),
                    status=self._normalize_status(raw.get("status")),
                    estimated_value=self._parse_float(raw.get("estimated_value"))
                )
                
                bid.quality_score = self._calculate_quality_score(bid, "bid")
                
                if bid.quality_score >= 0.5:
                    bids.append(bid)
                    
            except Exception as e:
                logger.warning(f"Error normalizing bid record: {e}")
                
        return bids
        
    def _normalize_awards(self, raw_records: List[Dict[str, Any]]) -> List[Award]:
        """Normalize award records."""
        awards = []
        
        for raw in raw_records:
            try:
                award = Award(
                    id=self._generate_id(raw),
                    source=raw.get("_source", ""),
                    category=raw.get("_category", "awards"),
                    jurisdiction=raw.get("_jurisdiction", ""),
                    raw_data=raw,
                    normalized_at=datetime.utcnow(),
                    quality_score=0.0,
                    
                    contract_number=self._clean_string(raw.get("contract_number")),
                    award_date=self._parse_date(raw.get("award_date")),
                    vendor_name=self._clean_string(raw.get("vendor_name")),
                    description=self._clean_string(raw.get("description")),
                    amount=self._parse_float(raw.get("amount")),
                    agency=self._clean_string(raw.get("agency"))
                )
                
                award.quality_score = self._calculate_quality_score(award, "award")
                
                if award.quality_score >= 0.5:
                    awards.append(award)
                    
            except Exception as e:
                logger.warning(f"Error normalizing award record: {e}")
                
        return awards
        
    def _normalize_contractors(self, raw_records: List[Dict[str, Any]]) -> List[Contractor]:
        """Normalize contractor records."""
        contractors = []
        
        for raw in raw_records:
            try:
                contractor = Contractor(
                    id=self._generate_id(raw),
                    source=raw.get("_source", ""),
                    category=raw.get("_category", "contractors"),
                    jurisdiction=raw.get("_jurisdiction", ""),
                    raw_data=raw,
                    normalized_at=datetime.utcnow(),
                    quality_score=0.0,
                    
                    license_number=self._clean_string(raw.get("license_number")),
                    license_type=self._clean_string(raw.get("license_type")),
                    business_name=self._clean_string(raw.get("business_name")),
                    owner_name=self._clean_string(raw.get("owner_name")),
                    address=self._normalize_address(raw.get("address")),
                    city=self._clean_string(raw.get("city")),
                    zip_code=self._clean_string(raw.get("zip_code")),
                    license_status=self._normalize_status(raw.get("license_status")),
                    issue_date=self._parse_date(raw.get("issue_date")),
                    expiration_date=self._parse_date(raw.get("expiration_date")),
                    specialty=self._clean_string(raw.get("specialty"))
                )
                
                contractor.quality_score = self._calculate_quality_score(contractor, "contractor")
                
                if contractor.quality_score >= 0.5:
                    contractors.append(contractor)
                    
            except Exception as e:
                logger.warning(f"Error normalizing contractor record: {e}")
                
        return contractors
        
    def _generate_id(self, raw_record: Dict[str, Any]) -> str:
        """Generate a unique ID for a record."""
        # Use primary key if available
        primary_key = raw_record.get("_primary_key")
        source = raw_record.get("_source", "")
        
        if primary_key:
            id_string = f"{source}:{primary_key}"
        else:
            # Generate based on key fields
            key_fields = [
                raw_record.get("permit_number", ""),
                raw_record.get("case_number", ""),
                raw_record.get("license_number", ""),
                raw_record.get("contract_number", ""),
                raw_record.get("address", ""),
                raw_record.get("_loaded_at", "")
            ]
            id_string = ":".join(str(field) for field in key_fields if field)
            
        return hashlib.md5(id_string.encode()).hexdigest()
        
    def _clean_string(self, value: Any) -> Optional[str]:
        """Clean and normalize string values."""
        if not value:
            return None
            
        cleaned = str(value).strip()
        if not cleaned or cleaned.lower() in ["n/a", "na", "null", "none", ""]:
            return None
            
        return cleaned
        
    def _normalize_address(self, address: Any) -> Optional[str]:
        """Normalize address strings."""
        if not address:
            return None
            
        # Basic address cleaning
        cleaned = str(address).strip().upper()
        
        # Remove extra spaces
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Standardize direction abbreviations
        replacements = {
            ' NORTH ': ' N ',
            ' SOUTH ': ' S ',
            ' EAST ': ' E ',
            ' WEST ': ' W ',
            ' NORTHEAST ': ' NE ',
            ' NORTHWEST ': ' NW ',
            ' SOUTHEAST ': ' SE ',
            ' SOUTHWEST ': ' SW ',

class DataNormalizer:
    """Pipeline for normalizing raw permit data to gold schema."""
    
    def __init__(self, db_url: str, sources_config_path: str):
        """
        Initialize the data normalizer.
        
        Args:
            db_url: PostgreSQL connection URL
            sources_config_path: Path to sources_tx.yaml configuration
        """
        self.db_url = db_url
        self.sources_config_path = sources_config_path
        self.sources_config = self._load_sources_config()
        self.field_mappings = self._build_field_mappings()
    
    def _load_sources_config(self) -> Dict[str, Any]:
        """Load sources configuration from YAML file."""
        try:
            with open(self.sources_config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load sources config: {e}")
            raise
    
    def _build_field_mappings(self) -> Dict[str, Dict[str, str]]:
        """Build field mappings for each source."""
        mappings = {}
        
        # Process all source types
        for source_list_key in ['tier_1_sources', 'tier_2_sources', 'violations_sources']:
            for source in self.sources_config.get(source_list_key, []):
                source_id = source['id']
                field_mapping = source.get('field_mapping', {})
                mappings[source_id] = field_mapping
        
        return mappings
    
    def _get_db_connection(self):
        """Create database connection."""
        return psycopg2.connect(self.db_url)
    
    def _ensure_gold_tables_exist(self):
        """Ensure gold schema tables exist in database."""
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()
            
            # Create permits table (main gold schema)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS permits (
                    id SERIAL PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    permit_id TEXT NOT NULL,
                    permit_number TEXT,
                    permit_type TEXT,
                    permit_subtype TEXT,
                    status TEXT,
                    issue_date DATE,
                    expiration_date DATE,
                    application_date DATE,
                    finalized_date DATE,
                    
                    -- Property information
                    address TEXT,
                    street_number TEXT,
                    street_name TEXT,
                    unit TEXT,
                    city TEXT,
                    state TEXT DEFAULT 'TX',
                    zip_code TEXT,
                    latitude NUMERIC,
                    longitude NUMERIC,
                    parcel_id TEXT,
                    
                    -- Work description
                    description TEXT,
                    work_class TEXT,
                    work_type TEXT,
                    trade_types TEXT[],
                    
                    -- Value and sizing
                    estimated_cost NUMERIC,
                    square_footage NUMERIC,
                    units INTEGER,
                    stories INTEGER,
                    
                    -- Parties
                    applicant_name TEXT,
                    applicant_type TEXT,
                    contractor_name TEXT,
                    contractor_license TEXT,
                    property_owner TEXT,
                    
                    -- Property details
                    property_type TEXT,
                    occupancy_type TEXT,
                    construction_type TEXT,
                    year_built INTEGER,
                    
                    -- Normalization metadata
                    normalized_at TIMESTAMPTZ DEFAULT NOW(),
                    confidence_score NUMERIC,
                    validation_errors JSONB,
                    raw_record_id INTEGER REFERENCES raw_permits(id),
                    
                    UNIQUE(source_id, permit_id)
                )
            """)
            
            # Create violations table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS violations (
                    id SERIAL PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    case_id TEXT NOT NULL,
                    violation_type TEXT,
                    violation_category TEXT,
                    status TEXT,
                    violation_date DATE,
                    resolution_date DATE,
                    
                    -- Property information
                    address TEXT,
                    latitude NUMERIC,
                    longitude NUMERIC,
                    parcel_id TEXT,
                    
                    -- Description and details
                    description TEXT,
                    severity TEXT,
                    penalty_amount NUMERIC,
                    
                    -- Parties
                    property_owner TEXT,
                    responsible_party TEXT,
                    inspector_name TEXT,
                    
                    -- Related permit (if applicable)
                    related_permit_id TEXT,
                    
                    -- Metadata
                    normalized_at TIMESTAMPTZ DEFAULT NOW(),
                    raw_record_id INTEGER REFERENCES raw_permits(id),
                    
                    UNIQUE(source_id, case_id)
                )
            """)
            
            # Create bids table (placeholder for future procurement data)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bids (
                    id SERIAL PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    bid_id TEXT NOT NULL,
                    project_name TEXT,
                    bid_type TEXT,
                    status TEXT,
                    bid_date DATE,
                    opening_date DATE,
                    
                    -- Project details
                    description TEXT,
                    estimated_value NUMERIC,
                    project_category TEXT,
                    
                    -- Location
                    address TEXT,
                    city TEXT,
                    latitude NUMERIC,
                    longitude NUMERIC,
                    
                    -- Metadata
                    normalized_at TIMESTAMPTZ DEFAULT NOW(),
                    raw_record_id INTEGER REFERENCES raw_permits(id),
                    
                    UNIQUE(source_id, bid_id)
                )
            """)
            
            # Create awards table (placeholder for future contract awards)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS awards (
                    id SERIAL PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    award_id TEXT NOT NULL,
                    bid_id TEXT,
                    project_name TEXT,
                    award_date DATE,
                    
                    -- Award details
                    awarded_amount NUMERIC,
                    contractor_name TEXT,
                    contractor_id TEXT,
                    contract_duration_days INTEGER,
                    
                    -- Project details
                    description TEXT,
                    project_category TEXT,
                    
                    -- Location
                    address TEXT,
                    city TEXT,
                    
                    -- Metadata
                    normalized_at TIMESTAMPTZ DEFAULT NOW(),
                    raw_record_id INTEGER REFERENCES raw_permits(id),
                    
                    UNIQUE(source_id, award_id)
                )
            """)
            
            # Create indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_permits_source_id ON permits(source_id)",
                "CREATE INDEX IF NOT EXISTS idx_permits_issue_date ON permits(issue_date)",
                "CREATE INDEX IF NOT EXISTS idx_permits_location ON permits(latitude, longitude)",
                "CREATE INDEX IF NOT EXISTS idx_permits_address ON permits(address)",
                "CREATE INDEX IF NOT EXISTS idx_violations_source_id ON violations(source_id)",
                "CREATE INDEX IF NOT EXISTS idx_violations_violation_date ON violations(violation_date)",
                "CREATE INDEX IF NOT EXISTS idx_violations_location ON violations(latitude, longitude)",
            ]
            
            for index_sql in indexes:
                cur.execute(index_sql)
            
            conn.commit()
            logger.info("Gold schema tables initialized")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to create gold tables: {e}")
            raise
        finally:
            conn.close()
    
    def _normalize_permit_record(self, raw_record: Dict[str, Any], source_config: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a single raw permit record to gold schema."""
        source_id = source_config['id']
        field_mapping = source_config.get('field_mapping', {})
        raw_data = raw_record.get('raw_data', {})
        
        # Start with empty normalized record
        normalized = {
            'source_id': source_id,
            'raw_record_id': raw_record.get('id')
        }
        
        # Apply field mappings
        for standard_field, source_field in field_mapping.items():
            if source_field in raw_data:
                value = raw_data[source_field]
                normalized[standard_field] = self._normalize_field_value(
                    standard_field, value, source_config
                )
        
        # Handle additional fields from raw data
        self._map_additional_fields(normalized, raw_data, source_config)
        
        # Validate and enrich
        self._validate_normalized_record(normalized)
        self._enrich_record(normalized)
        
        return normalized
    
    def _normalize_field_value(self, field_name: str, value: Any, source_config: Dict[str, Any]) -> Any:
        """Normalize a specific field value based on its type."""
        if value is None or value == '':
            return None
        
        # Date fields
        if field_name in ['issue_date', 'expiration_date', 'application_date', 'finalized_date', 'violation_date']:
            return self._parse_date(value)
        
        # Numeric fields
        elif field_name in ['estimated_cost', 'square_footage', 'latitude', 'longitude', 'penalty_amount']:
            return self._parse_number(value)
        
        # Integer fields
        elif field_name in ['units', 'stories', 'year_built']:
            return self._parse_integer(value)
        
        # Address field (clean and standardize)
        elif field_name == 'address':
            return self._normalize_address(value)
        
        # Status field (standardize)
        elif field_name == 'status':
            return self._normalize_status(value)
        
        # Work class/type (standardize)
        elif field_name in ['work_class', 'work_type', 'permit_type']:
            return self._normalize_work_type(value)
        
        # Text fields (clean)
        else:
            return self._clean_text(value)
    
    def _parse_date(self, value: Any) -> Optional[datetime]:
        """Parse various date formats."""
        if isinstance(value, datetime):
            return value.date()
        
        if not isinstance(value, str):
            return None
        
        # Common date formats
        date_formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%m/%d/%y',
            '%Y-%m-%d %H:%M:%S',
            '%m/%d/%Y %H:%M:%S',
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        
        return None
    
    def _parse_number(self, value: Any) -> Optional[float]:
        """Parse numeric values."""
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Remove formatting
            clean_value = re.sub(r'[,$%]', '', value.strip())
            try:
                return float(clean_value)
            except ValueError:
                return None
        
        return None
    
    def _parse_integer(self, value: Any) -> Optional[int]:
        """Parse integer values."""
        if isinstance(value, int):
            return value
        
        if isinstance(value, float):
            return int(value)
        
        if isinstance(value, str):
            clean_value = re.sub(r'[,]', '', value.strip())
            try:
                return int(float(clean_value))
            except ValueError:
                return None
        
        return None
    
    def _normalize_address(self, value: str) -> str:
        """Normalize address format."""
        if not value:
            return None
        
        # Basic address cleaning
        address = str(value).strip().upper()
        
        # Remove extra whitespace
        address = re.sub(r'\s+', ' ', address)
        
        # Common abbreviations
        replacements = {

            ' STREET': ' ST',
            ' AVENUE': ' AVE',
            ' BOULEVARD': ' BLVD',
            ' DRIVE': ' DR',

            ' ROAD': ' RD'
        }
        
        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)
            
        return cleaned if cleaned else None
        
    def _normalize_status(self, status: Any) -> Optional[str]:
        """Normalize status values."""
        if not status:
            return None
            
        cleaned = str(status).strip().upper()
        
        # Standardize common status values
        if cleaned in ["ISSUED", "ACTIVE", "APPROVED", "OPEN"]:
            return "ACTIVE"
        elif cleaned in ["CLOSED", "COMPLETED", "FINALIZED", "EXPIRED"]:
            return "CLOSED"
        elif cleaned in ["PENDING", "IN PROGRESS", "UNDER REVIEW"]:
            return "PENDING"
        elif cleaned in ["CANCELLED", "CANCELED", "VOID", "REJECTED"]:
            return "CANCELLED"
            
        return cleaned if cleaned else None
        
    def _parse_date(self, date_value: Any) -> Optional[datetime]:
        """Parse various date formats."""
        if not date_value:
            return None
            
        if isinstance(date_value, datetime):
            return date_value
            
        date_str = str(date_value).strip()
        if not date_str:
            return None
            
        # Common date formats
        date_formats = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%m/%d/%Y",
            "%m/%d/%Y %H:%M:%S",
            "%m-%d-%Y",
            "%d-%m-%Y",
            "%Y%m%d"
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
                
        logger.warning(f"Could not parse date: {date_value}")
        return None
        
    def _parse_float(self, value: Any) -> Optional[float]:
        """Parse numeric values."""
        if not value:
            return None
            
        try:
            # Remove currency symbols and commas
            if isinstance(value, str):
                cleaned = re.sub(r'[$,]', '', value.strip())
                if not cleaned:
                    return None
                return float(cleaned)
            else:
                return float(value)
        except (ValueError, TypeError):
            return None
            
    def _calculate_quality_score(self, record: NormalizedRecord, record_type: str) -> float:
        """Calculate quality score for a normalized record."""
        score = 0.0
        total_checks = 0
        
        # Check for required ID field
        id_field_map = {
            "permit": "permit_number",
            "violation": "case_number", 
            "inspection": "inspection_id",
            "bid": "bid_number",
            "award": "contract_number",
            "contractor": "license_number"
        }
        
        id_field = id_field_map.get(record_type)
        if id_field and hasattr(record, id_field):
            if getattr(record, id_field):
                score += 0.3
            total_checks += 0.3
            
        # Check for address (location-based records)
        if hasattr(record, "address"):
            if getattr(record, "address"):
                score += 0.2
            total_checks += 0.2
            
        # Check for date fields
        date_fields = ["issued_date", "created_date", "inspection_date", "bid_date", "award_date", "issue_date"]
        for field in date_fields:
            if hasattr(record, field):
                if getattr(record, field):
                    score += 0.2
                total_checks += 0.2
                break
                
        # Check for geographic coordinates
        if hasattr(record, "latitude") and hasattr(record, "longitude"):
            if getattr(record, "latitude") and getattr(record, "longitude"):
                score += 0.15
            total_checks += 0.15
            
        # Check for other key fields
        other_fields = ["description", "status", "business_name", "vendor_name"]
        for field in other_fields:
            if hasattr(record, field):
                if getattr(record, field):
                    score += 0.05
                total_checks += 0.05
                
        return score / total_checks if total_checks > 0 else 0.0
        
    def _save_normalized_data(self, category: str, records: List[NormalizedRecord]):
        """Save normalized data to JSON files."""
        if not records:
            return
            
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{category}_{timestamp}.json"
        filepath = self.output_dir / filename
        
        # Convert records to dictionaries
        data = []
        for record in records:
            record_dict = {
                "id": record.id,
                "source": record.source,
                "category": record.category,
                "jurisdiction": record.jurisdiction,
                "normalized_at": record.normalized_at.isoformat(),
                "quality_score": record.quality_score
            }
            
            # Add specific fields
            for field_name in record.__dict__:
                if not field_name.startswith("_") and field_name not in record_dict:
                    value = getattr(record, field_name)
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    record_dict[field_name] = value
                    
            data.append(record_dict)
            
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Saved {len(records)} {category} records to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save normalized data: {e}")


def main():
    """Example usage of the data normalizer."""
    # Set up logging

            ' ROAD': ' RD',
            ' LANE': ' LN',
            ' COURT': ' CT',
            ' PLACE': ' PL',
        }
        
        for full, abbrev in replacements.items():
            address = address.replace(full, abbrev)
        
        return address
    
    def _normalize_status(self, value: str) -> str:
        """Normalize permit status values."""
        if not value:
            return None
        
        status = str(value).strip().upper()
        
        # Map common status variations
        status_mapping = {
            'ISSUED': 'ISSUED',
            'ACTIVE': 'ACTIVE',
            'APPROVED': 'APPROVED',
            'PENDING': 'PENDING',
            'EXPIRED': 'EXPIRED',
            'CANCELLED': 'CANCELLED',
            'CANCELED': 'CANCELLED',
            'COMPLETE': 'COMPLETE',
            'COMPLETED': 'COMPLETE',
            'FINALIZED': 'COMPLETE',
            'CLOSED': 'COMPLETE',
            'VOIDED': 'VOIDED',
            'VOID': 'VOIDED',
        }
        
        return status_mapping.get(status, status)
    
    def _normalize_work_type(self, value: str) -> str:
        """Normalize work type/class values."""
        if not value:
            return None
        
        work_type = str(value).strip().upper()
        
        # Map common work type variations
        type_mapping = {
            'BUILDING': 'BUILDING',
            'ELECTRICAL': 'ELECTRICAL',
            'PLUMBING': 'PLUMBING',
            'MECHANICAL': 'MECHANICAL',
            'HVAC': 'MECHANICAL',
            'ROOFING': 'ROOFING',
            'ROOF': 'ROOFING',
            'ADDITION': 'ADDITION',
            'ALTERATION': 'ALTERATION',
            'RENOVATION': 'RENOVATION',
            'REPAIR': 'REPAIR',
            'DEMOLITION': 'DEMOLITION',
            'DEMO': 'DEMOLITION',
            'NEW CONSTRUCTION': 'NEW_CONSTRUCTION',
            'NEW': 'NEW_CONSTRUCTION',
        }
        
        return type_mapping.get(work_type, work_type)
    
    def _clean_text(self, value: Any) -> Optional[str]:
        """Clean text fields."""
        if not value:
            return None
        
        text = str(value).strip()
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove null-like values
        if text.upper() in ['NULL', 'N/A', 'NA', 'NONE', 'UNKNOWN']:
            return None
        
        return text if text else None
    
    def _map_additional_fields(self, normalized: Dict[str, Any], raw_data: Dict[str, Any], source_config: Dict[str, Any]):
        """Map additional fields that aren't in the explicit field mapping."""
        # Try to extract common fields by name similarity
        for raw_key, raw_value in raw_data.items():
            if not raw_value:
                continue
            
            raw_key_lower = raw_key.lower()
            
            # Skip already mapped fields
            if any(raw_key == mapped_field for mapped_field in source_config.get('field_mapping', {}).values()):
                continue
            
            # Map based on key patterns
            if 'lat' in raw_key_lower and 'latitude' not in normalized:
                normalized['latitude'] = self._parse_number(raw_value)
            elif 'lon' in raw_key_lower and 'longitude' not in normalized:
                normalized['longitude'] = self._parse_number(raw_value)
            elif 'zip' in raw_key_lower and 'zip_code' not in normalized:
                normalized['zip_code'] = self._clean_text(raw_value)
            elif 'state' in raw_key_lower and 'state' not in normalized:
                normalized['state'] = self._clean_text(raw_value) or 'TX'
    
    def _validate_normalized_record(self, record: Dict[str, Any]):
        """Validate normalized record and track validation errors."""
        errors = []
        
        # Required fields
        if not record.get('permit_id'):
            errors.append("Missing permit_id")
        
        # Date validation
        issue_date = record.get('issue_date')
        if issue_date:
            if issue_date.year < 1990 or issue_date.year > datetime.now().year + 1:
                errors.append(f"Invalid issue_date: {issue_date}")
        
        # Coordinate validation
        lat = record.get('latitude')
        lon = record.get('longitude')
        if lat is not None and (lat < 25.0 or lat > 37.0):  # Texas bounds
            errors.append(f"Invalid latitude: {lat}")
        if lon is not None and (lon < -107.0 or lon > -93.0):  # Texas bounds
            errors.append(f"Invalid longitude: {lon}")
        
        # Store validation errors
        if errors:
            record['validation_errors'] = errors
            record['confidence_score'] = max(0, 1.0 - len(errors) * 0.2)
        else:
            record['confidence_score'] = 1.0
    
    def _enrich_record(self, record: Dict[str, Any]):
        """Enrich record with derived fields."""
        # Parse address components if full address exists
        address = record.get('address')
        if address and not record.get('street_name'):
            self._parse_address_components(record, address)
        
        # Derive trade types from work description
        if not record.get('trade_types'):
            record['trade_types'] = self._extract_trade_types(
                record.get('description', '') + ' ' + record.get('work_class', '')
            )
        
        # Set property type based on indicators
        if not record.get('property_type'):
            record['property_type'] = self._infer_property_type(record)
    
    def _parse_address_components(self, record: Dict[str, Any], address: str):
        """Parse address into components."""
        # Simple address parsing (could be enhanced with address parsing library)
        address_parts = address.split()
        
        if address_parts:
            # Try to extract street number (first numeric part)
            for i, part in enumerate(address_parts):
                if part.isdigit():
                    record['street_number'] = part
                    # Rest is street name (simplified)
                    if i + 1 < len(address_parts):
                        record['street_name'] = ' '.join(address_parts[i+1:])
                    break
    
    def _extract_trade_types(self, text: str) -> List[str]:
        """Extract trade types from description text."""
        if not text:
            return []
        
        text_upper = text.upper()
        trades = []
        
        trade_keywords = {
            'ELECTRICAL': ['ELECTRICAL', 'ELECTRIC', 'WIRING'],
            'PLUMBING': ['PLUMBING', 'PLUMBER', 'WATER', 'SEWER'],
            'HVAC': ['HVAC', 'AIR CONDITIONING', 'HEATING', 'VENTILATION'],
            'ROOFING': ['ROOF', 'ROOFING', 'SHINGLE'],
            'CONCRETE': ['CONCRETE', 'FOUNDATION', 'SLAB'],
            'FRAMING': ['FRAMING', 'FRAME', 'STRUCTURAL'],
            'FLOORING': ['FLOORING', 'FLOOR', 'TILE', 'CARPET'],
            'PAINTING': ['PAINT', 'PAINTING'],
            'FENCING': ['FENCE', 'FENCING'],
            'POOL': ['POOL', 'SPA'],
        }
        
        for trade, keywords in trade_keywords.items():
            if any(keyword in text_upper for keyword in keywords):
                trades.append(trade)
        
        return trades
    
    def _infer_property_type(self, record: Dict[str, Any]) -> Optional[str]:
        """Infer property type from available fields."""
        description = (record.get('description', '') + ' ' + record.get('work_class', '')).upper()
        
        if any(word in description for word in ['RESIDENTIAL', 'HOUSE', 'HOME', 'SINGLE FAMILY']):
            return 'RESIDENTIAL'
        elif any(word in description for word in ['COMMERCIAL', 'OFFICE', 'RETAIL', 'STORE']):
            return 'COMMERCIAL'
        elif any(word in description for word in ['INDUSTRIAL', 'WAREHOUSE', 'FACTORY']):
            return 'INDUSTRIAL'
        elif any(word in description for word in ['APARTMENT', 'MULTI-FAMILY', 'CONDO']):
            return 'MULTI_FAMILY'
        
        return None
    
    def normalize_permits(self, source_id: Optional[str] = None, batch_size: int = 1000) -> Dict[str, Any]:
        """Normalize raw permit records to gold schema."""
        self._ensure_gold_tables_exist()
        
        conn = self._get_db_connection()
        try:
            # Build query
            where_clause = ""
            params = []
            
            if source_id:
                where_clause = "WHERE r.source_id = %s"
                params.append(source_id)
            
            # Get source config for field mappings
            source_configs = {}
            for source_list in ['tier_1_sources', 'tier_2_sources']:
                for source in self.sources_config.get(source_list, []):
                    source_configs[source['id']] = source
            
            # Process in batches
            total_processed = 0
            total_errors = 0
            
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get raw records to normalize
                cur.execute(f"""
                    SELECT r.id, r.source_id, r.source_type, r.raw_data, r.extracted_at
                    FROM raw_permits r
                    LEFT JOIN permits p ON r.id = p.raw_record_id
                    {where_clause}
                    AND p.id IS NULL  -- Only unnormalized records
                    ORDER BY r.extracted_at DESC
                    LIMIT %s
                """, params + [batch_size])
                
                raw_records = cur.fetchall()
                
                if not raw_records:
                    logger.info("No raw records to normalize")
                    return {'processed': 0, 'errors': 0}
                
                logger.info(f"Normalizing {len(raw_records)} raw records")
                
                # Process each record
                normalized_records = []
                for raw_record in raw_records:
                    try:
                        source_config = source_configs.get(raw_record['source_id'])
                        if not source_config:
                            logger.warning(f"No source config for {raw_record['source_id']}")
                            continue
                        
                        normalized = self._normalize_permit_record(dict(raw_record), source_config)
                        normalized_records.append(normalized)
                        
                    except Exception as e:
                        logger.error(f"Error normalizing record {raw_record['id']}: {e}")
                        total_errors += 1
                
                # Batch insert normalized records
                if normalized_records:
                    insert_sql = """
                        INSERT INTO permits (
                            source_id, permit_id, permit_number, permit_type, status,
                            issue_date, address, description, work_class, estimated_cost,
                            latitude, longitude, applicant_name, property_owner,
                            confidence_score, validation_errors, raw_record_id
                        ) VALUES (
                            %(source_id)s, %(permit_id)s, %(permit_number)s, %(permit_type)s, %(status)s,
                            %(issue_date)s, %(address)s, %(description)s, %(work_class)s, %(estimated_cost)s,
                            %(latitude)s, %(longitude)s, %(applicant_name)s, %(property_owner)s,
                            %(confidence_score)s, %(validation_errors)s, %(raw_record_id)s
                        )
                        ON CONFLICT (source_id, permit_id) DO UPDATE SET
                            permit_number = EXCLUDED.permit_number,
                            permit_type = EXCLUDED.permit_type,
                            status = EXCLUDED.status,
                            issue_date = EXCLUDED.issue_date,
                            address = EXCLUDED.address,
                            description = EXCLUDED.description,
                            work_class = EXCLUDED.work_class,
                            estimated_cost = EXCLUDED.estimated_cost,
                            latitude = EXCLUDED.latitude,
                            longitude = EXCLUDED.longitude,
                            applicant_name = EXCLUDED.applicant_name,
                            property_owner = EXCLUDED.property_owner,
                            confidence_score = EXCLUDED.confidence_score,
                            validation_errors = EXCLUDED.validation_errors,
                            normalized_at = NOW()
                    """
                    
                    # Convert validation_errors to JSON for PostgreSQL
                    for record in normalized_records:
                        if 'validation_errors' in record:
                            record['validation_errors'] = Json(record['validation_errors'])
                    
                    cur.executemany(insert_sql, normalized_records)
                    total_processed = len(normalized_records)
                    
                    conn.commit()
                    logger.info(f"Successfully normalized {total_processed} records")
            
            return {
                'processed': total_processed,
                'errors': total_errors,
                'success_rate': total_processed / (total_processed + total_errors) if total_processed + total_errors > 0 else 0
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to normalize permits: {e}")
            raise
        finally:
            conn.close()


def main():
    """CLI entry point for data normalization."""
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description='Normalize raw permit data to gold schema')
    parser.add_argument('--source-id', help='Normalize only specific source')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for processing')
    parser.add_argument('--sources-config', default='config/sources_tx.yaml',
                       help='Path to sources configuration file')
    parser.add_argument('--db-url', help='PostgreSQL connection URL (or set DATABASE_URL env var)')
    
    args = parser.parse_args()
    
    # Setup logging

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    

    # Initialize normalizer
    normalizer = DataNormalizer()
    
    # Normalize all raw data
    results = normalizer.normalize_raw_files()
    
    # Print results
    print("Normalization Results:")
    for category, count in results.items():
        if count > 0:
            print(f"  {category}: {count} records")
            
    total = sum(results.values())
    print(f"\nTotal normalized records: {total}")


if __name__ == "__main__":
    main()

    # Get database URL
    db_url = args.db_url or os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("Database URL required (--db-url or DATABASE_URL env var)")
        return 1
    
    try:
        normalizer = DataNormalizer(db_url, args.sources_config)
        result = normalizer.normalize_permits(
            source_id=args.source_id,
            batch_size=args.batch_size
        )
        
        print(json.dumps(result, indent=2))
        return 0
        
    except Exception as e:
        logger.error(f"Normalization failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())

