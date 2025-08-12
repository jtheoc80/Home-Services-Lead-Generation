"""Data normalization pipeline producing gold tables for Texas data."""

import logging
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from pathlib import Path
import hashlib

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