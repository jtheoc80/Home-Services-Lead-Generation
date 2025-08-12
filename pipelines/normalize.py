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
from typing import Dict, List, Optional, Any, Union
import psycopg2
from psycopg2.extras import Json, RealDictCursor
import re

logger = logging.getLogger(__name__)


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