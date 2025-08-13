"""
Permit data normalization for Texas multi-jurisdiction data sources.
Transforms raw permit data from Dallas, Austin, Arlington, Houston, and Harris County
into standardized permits_gold format.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from decimal import Decimal
import re

logger = logging.getLogger(__name__)


class PermitNormalizer:
    """
    Normalizes permit data from multiple Texas data sources into permits_gold format.
    
    Supports:
    - Dallas Socrata (e7gq-4sah)
    - Austin Socrata (3syk-w9eu) 
    - Arlington ArcGIS FeatureServer
    - Harris County ArcGIS FeatureServer
    - Houston TPIA CSV files
    """
    
    # Jurisdiction mapping for consistent naming
    JURISDICTION_MAP = {
        'dallas': 'dallas',
        'austin': 'austin', 
        'arlington': 'arlington',
        'houston': 'houston',
        'harris': 'harris_county',
        'harris_county': 'harris_county',
    }
    
    # Work type normalization patterns
    WORK_TYPE_PATTERNS = {
        'residential': [
            r'residential', r'single.?family', r'duplex', r'house', r'home',
            r'addition', r'remodel', r'renovation', r'kitchen', r'bathroom',  # Added 'renovation' for residential
            r'garage', r'deck', r'porch', r'fence', r'pool', r'shed',
            r'single.?family.?dwelling', r'accessory.?dwelling', r'dwelling'
        ],
        'commercial': [
            r'commercial', r'office', r'retail', r'store', r'warehouse',
            r'industrial', r'manufacturing', r'factory', r'business',
            r'industrial', r'manufacturing', r'factory', r'business'
        ],
        'multi_family': [
            r'apartment', r'condo', r'townhouse', r'multi.?family',
            r'condominium', r'multifamily', r'complex'
        ],
        'infrastructure': [
            r'utility', r'infrastructure', r'sewer', r'water',
            r'electrical.?service', r'gas.?line', r'utility.?line'
        ]
    }
    
    def __init__(self):
        self.stats = {
            'processed': 0,
            'normalized': 0,
            'errors': 0,
            'by_jurisdiction': {},
            'by_source_type': {}
        }
    
    def normalize_record(self, raw_record: Dict[str, Any], source_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a single permit record to permits_gold format.
        
        Args:
            raw_record: Raw permit data from source API/CSV
            source_config: Configuration including mappings and metadata
            
        Returns:
            Normalized permit record ready for permits_gold table
        """
        try:
            # Extract source metadata
            jurisdiction = self._normalize_jurisdiction(source_config.get('jurisdiction'))
            source_type = source_config.get('type', 'unknown')
            mappings = source_config.get('mappings', {})
            
            # Build normalized record
            normalized = {
                'jurisdiction': jurisdiction,
                'source_type': source_type,
                'raw_data': raw_record,
                'ingested_at': datetime.now().isoformat(),
                'source_url': source_config.get('url')
            }
            
            # Apply field mappings
            normalized.update(self._apply_field_mappings(raw_record, mappings))
            
            # Normalize specific fields
            normalized['permit_id'] = self._extract_permit_id(raw_record, mappings, jurisdiction)
            normalized['issued_date'] = self._parse_date(
                self._get_mapped_value(raw_record, mappings, 'issued_date')
            )
            normalized['work_type'] = self._normalize_work_type(
                normalized.get('description') or normalized.get('work_description'),
                normalized.get('category') or normalized.get('permit_category') or normalized.get('work_class')
            )
            normalized['valuation'] = self._parse_valuation(
                self._get_mapped_value(raw_record, mappings, 'value')
            )
            normalized['project_value_band'] = self._categorize_valuation(
                normalized.get('valuation')
            )
            
            # Handle coordinates
            lat, lon = self._extract_coordinates(raw_record, mappings)
            if lat and lon:
                normalized['latitude'] = lat
                normalized['longitude'] = lon
            
            # Clean and normalize text fields
            normalized['address'] = self._clean_address(normalized.get('address'))
            normalized['work_description'] = self._clean_text(normalized.get('work_description'))
            normalized['applicant_name'] = self._clean_name(normalized.get('applicant_name'))
            normalized['contractor_name'] = self._clean_name(normalized.get('contractor_name'))
            
            # Update stats
            self.stats['processed'] += 1
            self.stats['normalized'] += 1
            self.stats['by_jurisdiction'][jurisdiction] = self.stats['by_jurisdiction'].get(jurisdiction, 0) + 1
            self.stats['by_source_type'][source_type] = self.stats['by_source_type'].get(source_type, 0) + 1
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing permit record: {e}")
            logger.debug(f"Raw record: {raw_record}")
            self.stats['processed'] += 1
            self.stats['errors'] += 1
            return None
    
    def normalize_batch(self, raw_records: List[Dict[str, Any]], source_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize a batch of permit records."""
        normalized_records = []
        
        for raw_record in raw_records:
            normalized = self.normalize_record(raw_record, source_config)
            if normalized:
                normalized_records.append(normalized)
        
        logger.info(f"Normalized {len(normalized_records)} out of {len(raw_records)} records")
        return normalized_records
    
    def _normalize_jurisdiction(self, jurisdiction: str) -> str:
        """Normalize jurisdiction name to standard format."""
        if not jurisdiction:
            return 'unknown'
        
        jurisdiction_lower = jurisdiction.lower().strip()
        return self.JURISDICTION_MAP.get(jurisdiction_lower, jurisdiction_lower)
    
    def _apply_field_mappings(self, raw_record: Dict[str, Any], mappings: Dict[str, str]) -> Dict[str, Any]:
        """Apply configured field mappings."""
        mapped = {}
        
        for target_field, source_field in mappings.items():
            if source_field in raw_record:
                mapped[target_field] = raw_record[source_field]
        
        return mapped
    
    def _get_mapped_value(self, raw_record: Dict[str, Any], mappings: Dict[str, str], field: str) -> Any:
        """Get value using field mapping."""
        source_field = mappings.get(field)
        if source_field and source_field in raw_record:
            return raw_record[source_field]
        return raw_record.get(field)
    
    def _extract_permit_id(self, raw_record: Dict[str, Any], mappings: Dict[str, str], jurisdiction: str) -> str:
        """Extract and normalize permit ID."""
        permit_id = self._get_mapped_value(raw_record, mappings, 'permit_number') or \
                   self._get_mapped_value(raw_record, mappings, 'permit_id')
        
        if permit_id:
            return str(permit_id).strip()
        
        # Fallback: generate ID from jurisdiction and other fields
        fallback_fields = []
        for field in ['address', 'issued_date', 'description']:
            value = self._get_mapped_value(raw_record, mappings, field)
            if value:
                fallback_fields.append(str(value)[:50])
        
        if fallback_fields:
            import hashlib
            composite = f"{jurisdiction}:{':'.join(fallback_fields)}"
            return hashlib.sha256(composite.encode()).hexdigest()[:16]
        
        return f"{jurisdiction}_unknown_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def _parse_date(self, date_value: Any) -> Optional[str]:
        """Parse date from various formats to ISO format."""
        if not date_value:
            return None
        
        # Already a datetime object
        if isinstance(date_value, datetime):
            return date_value.isoformat()
        
        # Handle Unix timestamps (both seconds and milliseconds)
        if isinstance(date_value, (int, float)):
            try:
                # If value is very large, it's likely milliseconds
                if date_value > 1e10:
                    timestamp = date_value / 1000
                else:
                    timestamp = date_value
                return datetime.fromtimestamp(timestamp).isoformat()
            except (ValueError, OSError):
                pass
        
        date_str = str(date_value).strip()
        if not date_str or date_str.lower() in ('null', 'none', ''):
            return None
        
        # Try to parse as Unix timestamp string
        try:
            timestamp = float(date_str)
            if timestamp > 1e10:
                timestamp = timestamp / 1000
            return datetime.fromtimestamp(timestamp).isoformat()
        except (ValueError, OSError):
            pass
        
        # Common date formats in permit data
        formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%m-%d-%Y",
            "%Y-%m-%d %H:%M:%S",
            "%m/%d/%Y %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).isoformat()
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_str}")
        return None
    
    def _normalize_work_type(self, description: str, category: str) -> str:
        """Normalize work type using description and category."""
        text = ' '.join(filter(None, [str(description or ''), str(category or '')])).lower()
        
        # Score each work type by pattern matches
        scores = {}
        for work_type, patterns in self.WORK_TYPE_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                if matches > 0:
                    # Give higher weight to more specific patterns
                    if pattern in ['commercial', 'retail', 'office', 'store', 'business']:
                        score += matches * 3  # Commercial patterns get higher weight
                    elif pattern in ['apartment', 'condo', 'multi.?family', 'complex']:
                        score += matches * 3  # Multi-family patterns get higher weight
                    elif pattern in ['single.?family', 'dwelling', 'residential']:
                        score += matches * 2  # Residential patterns get medium weight
                    else:
                        score += matches
            scores[work_type] = score
        
        # Return the work type with the highest score
        if scores:
            best_type = max(scores.items(), key=lambda x: x[1])
            if best_type[1] > 0:
                return best_type[0]
        
        return 'mixed_use'
    
    def _parse_valuation(self, value: Any) -> Optional[float]:
        """Parse monetary valuation from various formats."""
        if not value:
            return None
        
        try:
            # Handle numeric types
            if isinstance(value, (int, float, Decimal)):
                return float(value)
            
            # Clean string representation
            value_str = str(value).strip()
            if not value_str or value_str.lower() in ('null', 'none', '', '0'):
                return None
            
            # Remove currency symbols and commas
            clean_value = re.sub(r'[$,]', '', value_str)
            
            # Extract numeric part
            match = re.search(r'[\d.]+', clean_value)
            if match:
                return float(match.group())
            
        except (ValueError, TypeError) as e:
            logger.debug(f"Could not parse valuation '{value}': {e}")
        
        return None
    
    def _categorize_valuation(self, valuation: Optional[float]) -> str:
        """Categorize valuation into bands for analytics."""
        if not valuation:
            return 'unknown'
        
        if valuation < 1000:
            return 'under_1k'
        elif valuation < 5000:
            return 'tier_1k_5k'
        elif valuation < 15000:
            return 'tier_5k_15k'
        elif valuation < 50000:
            return 'tier_15k_50k'
        elif valuation < 100000:
            return 'tier_50k_100k'
        elif valuation < 250000:
            return 'tier_100k_250k'
        elif valuation < 500000:
            return 'tier_250k_500k'
        elif valuation < 1000000:
            return 'tier_500k_1m'
        else:
            return 'tier_1m_plus'
    
    def _extract_coordinates(self, raw_record: Dict[str, Any], mappings: Dict[str, str]) -> tuple:
        """Extract latitude and longitude coordinates."""
        lat = self._get_mapped_value(raw_record, mappings, 'latitude')
        lon = self._get_mapped_value(raw_record, mappings, 'longitude')
        
        try:
            if lat and lon:
                lat_float = float(lat)
                lon_float = float(lon)
                
                # Basic validation for Texas coordinates
                if 25.0 <= lat_float <= 37.0 and -107.0 <= lon_float <= -93.0:
                    return lat_float, lon_float
        except (ValueError, TypeError):
            pass
        
        return None, None
    
    def _clean_address(self, address: str) -> Optional[str]:
        """Clean and standardize address format."""
        if not address:
            return None
        
        # Basic cleaning
        cleaned = ' '.join(str(address).split())
        
        # Remove common junk patterns
        cleaned = re.sub(r'\bNULL\b|\bNONE\b|\bN/A\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.strip()
        
        return cleaned if cleaned else None
    
    def _clean_text(self, text: str) -> Optional[str]:
        """Clean and standardize text fields."""
        if not text:
            return None
        
        # Basic cleaning
        cleaned = ' '.join(str(text).split())
        cleaned = re.sub(r'\bNULL\b|\bNONE\b|\bN/A\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.strip()
        
        return cleaned if cleaned else None
    
    def _clean_name(self, name: str) -> Optional[str]:
        """Clean person/company names."""
        if not name:
            return None
        
        # Basic cleaning
        cleaned = ' '.join(str(name).split())
        cleaned = re.sub(r'\bNULL\b|\bNONE\b|\bN/A\b', '', cleaned, flags=re.IGNORECASE)
        
        # Title case for names
        cleaned = cleaned.title().strip()
        
        return cleaned if cleaned else None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get normalization statistics."""
        return {
            **self.stats,
            'success_rate': self.stats['normalized'] / max(self.stats['processed'], 1),
            'error_rate': self.stats['errors'] / max(self.stats['processed'], 1)
        }