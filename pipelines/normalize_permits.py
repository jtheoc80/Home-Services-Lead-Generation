"""
Permits normalization pipeline.

This module processes raw permit data from pipelines.load_raw and normalizes it
using the normalizers.permits module, upserting into gold.permits table.
"""

import logging
import os
import sys
import psycopg2
from pathlib import Path
from typing import Dict, List, Any, Optional
from psycopg2.extras import Json, RealDictCursor

# Add parent directory to path for imports  
sys.path.insert(0, str(Path(__file__).parent.parent))

from normalizers.permits import normalize, validate_normalized_record
# Use relative imports for sibling modules

from ..normalizers.permits import normalize, validate_normalized_record
from ..ingest.state import get_state_manager

logger = logging.getLogger(__name__)


class PermitsNormalizer:
    """Pipeline for normalizing raw permit data to gold.permits schema."""
    
    def __init__(self, db_url: Optional[str] = None):
        """Initialize normalizer with database connection."""
        self.db_url = db_url or os.environ.get('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL must be provided or set as environment variable")
        
        self.state_manager = get_state_manager()
    
    def _get_connection(self):
        """Get database connection."""
        return psycopg2.connect(self.db_url)
    
    def _ensure_gold_permits_exists(self):
        """Ensure gold.permits table exists (should be created by migration)."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Check if table exists
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'gold' 
                            AND table_name = 'permits'
                        )
                    """)
                    exists = cur.fetchone()[0]
                    
                    if not exists:
                        logger.error("gold.permits table does not exist. Run 'make db-migrate' first.")
                        raise Exception("gold.permits table not found")
                    
                    logger.info("gold.permits table exists")
        except Exception as e:
            logger.error(f"Failed to check gold.permits table: {e}")
            raise
    
    def normalize_raw_permits(self, source_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Normalize raw permit data and upsert to gold.permits.
        
        Args:
            source_data: Dictionary mapping source_id to list of raw records
            
        Returns:
            Dictionary with normalization results
        """
        self._ensure_gold_permits_exists()
        
        total_processed = 0
        total_errors = 0
        total_upserted = 0
        source_results = {}
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    for source_id, raw_records in source_data.items():
                        if not raw_records:
                            continue
                        
                        logger.info(f"Normalizing {len(raw_records)} records from {source_id}")
                        
                        # Get source metadata (for jurisdiction info)
                        source_meta = self._get_source_metadata(source_id)
                        
                        normalized_records = []
                        errors = []
                        
                        for raw_record in raw_records:
                            try:
                                # Normalize the record
                                normalized = normalize(source_meta, raw_record)
                                
                                # Validate the normalized record
                                validation_errors = validate_normalized_record(normalized)
                                if validation_errors:
                                    logger.warning(f"Validation errors for {normalized.get('permit_id')}: {validation_errors}")
                                    errors.extend(validation_errors)
                                    continue
                                
                                normalized_records.append(normalized)
                                total_processed += 1
                                
                            except Exception as e:
                                logger.error(f"Failed to normalize record: {e}")
                                errors.append(str(e))
                                total_errors += 1
                        
                        # Batch upsert normalized records
                        if normalized_records:
                            upserted = self._upsert_permits(cur, normalized_records)
                            total_upserted += upserted
                            
                            logger.info(f"Upserted {upserted} permits for {source_id}")
                        
                        source_results[source_id] = {
                            'processed': len(normalized_records),
                            'errors': len(errors),
                            'upserted': len(normalized_records)  # Assuming all go through
                        }
                    
                    # Commit all changes
                    conn.commit()
                    logger.info(f"Normalization complete: {total_processed} processed, {total_upserted} upserted, {total_errors} errors")
        
        except Exception as e:
            logger.error(f"Failed to normalize permits: {e}")
            raise
        
        return {
            'total_processed': total_processed,
            'total_upserted': total_upserted,
            'total_errors': total_errors,
            'source_results': source_results
        }
    
    def _get_source_metadata(self, source_id: str) -> Dict[str, Any]:
        """Get source metadata for normalization context."""
        # Default metadata based on source_id patterns
        source_metadata = {
            'id': source_id,
            'jurisdiction': 'unknown',
            'city': 'unknown',
            'county': 'unknown'
        }
        
        # Extract from source_id
        if 'dallas' in source_id.lower():
            source_metadata.update({
                'jurisdiction': 'Dallas',
                'city': 'Dallas', 
                'county': 'Dallas'
            })
        elif 'austin' in source_id.lower():
            source_metadata.update({
                'jurisdiction': 'Austin',
                'city': 'Austin',
                'county': 'Travis'
            })
        elif 'arlington' in source_id.lower():
            source_metadata.update({
                'jurisdiction': 'Arlington',
                'city': 'Arlington',
                'county': 'Tarrant'
            })
        elif 'harris' in source_id.lower():
            source_metadata.update({
                'jurisdiction': 'Harris County',
                'city': 'Houston',
                'county': 'Harris'
            })
        
        return source_metadata
    
    def _upsert_permits(self, cursor, normalized_records: List[Dict[str, Any]]) -> int:
        """
        Upsert normalized permits into gold.permits table.
        
        Args:
            cursor: Database cursor
            normalized_records: List of normalized permit records
            
        Returns:
            Number of records upserted
        """
        if not normalized_records:
            return 0
        
        # Build upsert SQL
        upsert_sql = """
            INSERT INTO gold.permits (
                source_id, permit_id, jurisdiction, city, county, state,
                status, permit_type, subtype, work_class, description,
                applied_at, issued_at, finaled_at,
                address_full, postal_code, parcel_id, valuation,
                contractor_name, contractor_license,
                latitude, longitude, geom, url, provenance, record_hash, updated_at
            ) VALUES (
                %(source_id)s, %(permit_id)s, %(jurisdiction)s, %(city)s, %(county)s, %(state)s,
                %(status)s, %(permit_type)s, %(subtype)s, %(work_class)s, %(description)s,
                %(applied_at)s, %(issued_at)s, %(finaled_at)s,
                %(address_full)s, %(postal_code)s, %(parcel_id)s, %(valuation)s,
                %(contractor_name)s, %(contractor_license)s,
                %(latitude)s, %(longitude)s, 
                CASE WHEN %(geom)s IS NOT NULL THEN ST_GeomFromText(%(geom)s, 4326) ELSE NULL END,
                %(url)s, %(provenance)s, %(record_hash)s, %(updated_at)s
            )
            ON CONFLICT (source_id, permit_id) DO UPDATE SET
                jurisdiction = EXCLUDED.jurisdiction,
                city = EXCLUDED.city,
                county = EXCLUDED.county,
                status = EXCLUDED.status,
                permit_type = EXCLUDED.permit_type,
                subtype = EXCLUDED.subtype,
                work_class = EXCLUDED.work_class,
                description = EXCLUDED.description,
                applied_at = EXCLUDED.applied_at,
                issued_at = EXCLUDED.issued_at,
                finaled_at = EXCLUDED.finaled_at,
                address_full = EXCLUDED.address_full,
                postal_code = EXCLUDED.postal_code,
                parcel_id = EXCLUDED.parcel_id,
                valuation = EXCLUDED.valuation,
                contractor_name = EXCLUDED.contractor_name,
                contractor_license = EXCLUDED.contractor_license,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                geom = EXCLUDED.geom,
                url = EXCLUDED.url,
                provenance = EXCLUDED.provenance,
                record_hash = EXCLUDED.record_hash,
                updated_at = EXCLUDED.updated_at
            WHERE gold.permits.record_hash != EXCLUDED.record_hash
        """
        
        # Prepare records for insert
        prepared_records = []
        for record in normalized_records:
            # Convert provenance to JSON
            prepared = record.copy()
            if 'provenance' in prepared:
                prepared['provenance'] = Json(prepared['provenance'])
            
            prepared_records.append(prepared)
        
        # Execute batch upsert
        cursor.executemany(upsert_sql, prepared_records)
        return cursor.rowcount


def normalize_from_raw_data(raw_data_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Normalize permit data from raw data loading results.
    
    Args:
        raw_data_results: Results from pipelines.load_raw
        
    Returns:
        Normalization results
    """
    # Extract source data from raw results
    source_data = {}
    
    for result in raw_data_results:
        if result.get('status') == 'success' and 'data' in result:
            source_id = result['source_id']
            source_data[source_id] = result['data']
    
    if not source_data:
        logger.warning("No data to normalize")
        return {'total_processed': 0, 'total_upserted': 0, 'total_errors': 0}
    
    # Normalize the data
    normalizer = PermitsNormalizer()
    return normalizer.normalize_raw_permits(source_data)


def main():
    """
    Main entry point for permits normalization.
    
    Can be run standalone or after load_raw pipeline.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Normalize permit data to gold.permits')
    parser.add_argument('--db-url', help='PostgreSQL connection URL (or set DATABASE_URL env var)')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Check database URL
    db_url = args.db_url or os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("DATABASE_URL required (--db-url or DATABASE_URL env var)")
        return 1
    
    try:
        # For standalone execution, we would need to read from somewhere
        # For now, just validate the setup
        normalizer = PermitsNormalizer(db_url)
        normalizer._ensure_gold_permits_exists()
        
        logger.info("Permits normalizer setup successful")
        logger.info("To use: import normalize_from_raw_data and pass raw data results")
        
        return 0
        
    except Exception as e:
        logger.error(f"Normalization setup failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())