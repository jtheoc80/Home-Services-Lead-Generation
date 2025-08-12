
"""Raw data loading pipeline for Texas data sources."""

import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Iterator
from dataclasses import dataclass
from pathlib import Path
import yaml

# Import our connectors
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingest.arcgis import create_arcgis_connector
from ingest.socrata import create_socrata_connector  
from ingest.csv_http import create_csv_http_connector

logger = logging.getLogger(__name__)


@dataclass
class LoadResult:
    """Result of a data load operation."""
    source_name: str
    records_loaded: int
    start_time: datetime
    end_time: datetime
    status: str  # success, partial, failed
    errors: List[str]
    metadata: Dict[str, Any]


class RawDataLoader:
    """Pipeline for loading raw data from Texas sources into staging tables."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the raw data loader."""
        self.config_path = config_path or "config/sources_tx.yaml"
        self.config = self._load_config()
        self.connectors = {}
        self._setup_connectors()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration file: {e}")
            raise
            
    def _setup_connectors(self):
        """Initialize connectors for each data source."""
        sources = self.config.get("sources", [])
        
        for source in sources:
            source_type = source.get("type")
            source_name = source.get("name")
            
            if source_type == "foia_placeholder":
                # Skip FOIA placeholders for now
                logger.info(f"Skipping FOIA placeholder: {source_name}")
                continue
                
            try:
                if source_type == "arcgis_feature_service":
                    connector = create_arcgis_connector(source)
                elif source_type == "socrata":
                    connector = create_socrata_connector(source)
                elif source_type == "csv_http":
                    connector = create_csv_http_connector(source)
                else:
                    logger.warning(f"Unknown source type: {source_type} for {source_name}")
                    continue
                    
                self.connectors[source_name] = {
                    "connector": connector,
                    "config": source
                }
                logger.info(f"Initialized connector for: {source_name}")
                
            except Exception as e:
                logger.error(f"Failed to initialize connector for {source_name}: {e}")
                
    def load_source(
        self, 
        source_name: str, 
        incremental: bool = True,
        since_date: Optional[datetime] = None
    ) -> LoadResult:
        """Load data from a specific source."""
        start_time = datetime.utcnow()
        
        if source_name not in self.connectors:
            return LoadResult(
                source_name=source_name,
                records_loaded=0,
                start_time=start_time,
                end_time=datetime.utcnow(),
                status="failed",
                errors=[f"Source not found: {source_name}"],
                metadata={}
            )
            
        connector_info = self.connectors[source_name]
        connector = connector_info["connector"]
        config = connector_info["config"]
        
        errors = []
        records = []
        
        try:
            # Test connection first
            success, message = connector.test_connection()
            if not success:
                return LoadResult(
                    source_name=source_name,
                    records_loaded=0,
                    start_time=start_time,
                    end_time=datetime.utcnow(),
                    status="failed",
                    errors=[f"Connection test failed: {message}"],
                    metadata={}
                )
                
            logger.info(f"Loading data from {source_name}")
            
            # Determine data extraction method
            if incremental and hasattr(connector, 'get_updated_since'):
                # Use incremental loading
                if not since_date:
                    # Default to last 7 days for initial incremental load
                    since_date = datetime.utcnow() - timedelta(days=7)
                    
                record_iterator = connector.get_updated_since(since_date)
            else:
                # Full load
                if hasattr(connector, 'get_all_records'):
                    record_iterator = connector.get_all_records()
                elif hasattr(connector, 'get_paginated_records'):
                    record_iterator = connector.get_paginated_records()
                else:
                    # Fallback to feature/records method
                    record_iterator = connector.get_paginated_features() if hasattr(connector, 'get_paginated_features') else []
                    
            # Collect records
            for record in record_iterator:
                try:
                    # Validate and clean record
                    cleaned_record = self._clean_record(record, config)
                    records.append(cleaned_record)
                    
                    # Log progress every 1000 records
                    if len(records) % 1000 == 0:
                        logger.info(f"Loaded {len(records)} records from {source_name}")
                        
                except Exception as e:
                    errors.append(f"Error processing record: {str(e)}")
                    if len(errors) > 100:  # Limit error collection
                        break
                        
        except Exception as e:
            logger.error(f"Error loading from {source_name}: {e}")
            return LoadResult(
                source_name=source_name,
                records_loaded=0,
                start_time=start_time,
                end_time=datetime.utcnow(),
                status="failed",
                errors=[str(e)],
                metadata={}
            )
            
        end_time = datetime.utcnow()
        
        # Save raw data to JSON files (in production, this would go to database)
        if records:
            self._save_raw_data(source_name, records, start_time)
            
        # Determine status
        if not records and not errors:
            status = "success"  # No new data
        elif errors and len(errors) > len(records) * 0.1:  # More than 10% errors
            status = "partial"
        elif errors:
            status = "partial"
        else:
            status = "success"
            
        return LoadResult(
            source_name=source_name,
            records_loaded=len(records),
            start_time=start_time,
            end_time=end_time,
            status=status,
            errors=errors[:10],  # Keep only first 10 errors
            metadata={
                "config": config.get("name", source_name),
                "category": config.get("category", "unknown"),
                "jurisdiction": config.get("jurisdiction", "unknown"),
                "incremental": incremental,
                "since_date": since_date.isoformat() if since_date else None
            }
        )
        
    def _clean_record(self, record: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate a record."""
        cleaned = record.copy()
        
        # Ensure required metadata fields
        cleaned["_source"] = config.get("name", "unknown")
        cleaned["_category"] = config.get("category", "unknown")
        cleaned["_jurisdiction"] = config.get("jurisdiction", "unknown")
        cleaned["_loaded_at"] = datetime.utcnow().isoformat()
        
        # Add primary key if available
        primary_key = config.get("primary_key")
        if primary_key and primary_key in record:
            cleaned["_primary_key"] = record[primary_key]
            
        # Validate geography fields
        lat = cleaned.get("latitude")
        lon = cleaned.get("longitude")
        if lat and lon:
            try:
                cleaned["latitude"] = float(lat)
                cleaned["longitude"] = float(lon)
                
                # Basic sanity check for Texas coordinates
                if not (25.0 <= cleaned["latitude"] <= 37.0 and -107.0 <= cleaned["longitude"] <= -93.0):
                    logger.warning("Coordinates outside Texas bounds for a record.")
                    
            except (ValueError, TypeError):
                logger.warning("Invalid coordinates for a record.")
                cleaned["latitude"] = None
                cleaned["longitude"] = None
                
        return cleaned
        
    def _save_raw_data(self, source_name: str, records: List[Dict[str, Any]], timestamp: datetime):
        """Save raw data to file system (temporary implementation)."""
        # Create data directory
        data_dir = Path("data/raw")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename with timestamp
        safe_name = source_name.replace(" ", "_").replace("/", "_").lower()
        filename = f"{safe_name}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = data_dir / filename
        
        try:
            with open(filepath, 'w') as f:
                json.dump(records, f, indent=2, default=str)
            logger.info(f"Saved {len(records)} records to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save raw data: {e}")
            
    def load_all_sources(
        self, 
        incremental: bool = True,
        since_date: Optional[datetime] = None,
        categories: Optional[List[str]] = None
    ) -> List[LoadResult]:
        """Load data from all configured sources."""
        results = []
        
        for source_name, connector_info in self.connectors.items():
            config = connector_info["config"]
            
            # Filter by category if specified
            if categories and config.get("category") not in categories:
                logger.info(f"Skipping {source_name} (category filter)")
                continue
                
            logger.info(f"Loading data from {source_name}")
            result = self.load_source(source_name, incremental, since_date)
            results.append(result)
            
            # Log result
            if result.status == "success":
                logger.info(f"Successfully loaded {result.records_loaded} records from {source_name}")
            else:
                logger.warning(f"Load completed with status {result.status} for {source_name}: {result.errors}")
                
        return results
        
    def get_available_sources(self) -> List[Dict[str, Any]]:
        """Get list of available sources with metadata."""
        sources = []
        
        for source_name, connector_info in self.connectors.items():
            config = connector_info["config"]
            sources.append({
                "name": source_name,
                "type": config.get("type"),
                "category": config.get("category"),
                "jurisdiction": config.get("jurisdiction"),
                "has_incremental": bool(config.get("updated_field"))
            })
            
        return sources


def main():
    """Example usage of the raw data loader."""
    # Set up logging

"""
Raw data loading pipeline.

This module reads source configurations, fetches data using appropriate connectors,
and persists raw data with ingest state tracking.
"""

import logging
import yaml
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import psycopg2
from psycopg2.extras import Json

logger = logging.getLogger(__name__)

# Import connectors
import sys
import os

# Add the parent directory to the path to import ingest modules
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from ingest import create_connector
except ImportError as e:
    logger.error(f"Failed to import ingest connectors: {e}")
    # For now, create a placeholder function
    def create_connector(source_config):
        logger.warning(f"Connector creation not available for {source_config.get('id')}")
        return None


class RawDataLoader:
    """Pipeline for loading raw permit data from various sources."""
    
    def __init__(self, db_url: str, sources_config_path: str):
        """
        Initialize the raw data loader.
        
        Args:
            db_url: PostgreSQL connection URL
            sources_config_path: Path to sources_tx.yaml configuration
        """
        self.db_url = db_url
        self.sources_config_path = sources_config_path
        self.sources_config = self._load_sources_config()
    
    def _load_sources_config(self) -> Dict[str, Any]:
        """Load sources configuration from YAML file."""
        try:
            with open(self.sources_config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded sources config with {len(config.get('tier_1_sources', []))} Tier-1 sources")
            return config
        except Exception as e:
            logger.error(f"Failed to load sources config: {e}")
            raise
    
    def _get_db_connection(self):
        """Create database connection."""
        return psycopg2.connect(self.db_url)
    
    def _ensure_raw_tables_exist(self):
        """Ensure raw data tables exist in database."""
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()
            
            # Create raw_permits table for storing raw permit data
            cur.execute("""
                CREATE TABLE IF NOT EXISTS raw_permits (
                    id SERIAL PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    raw_data JSONB NOT NULL,
                    extracted_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(source_id, raw_data->>'permit_id', raw_data->>'issue_date')
                )
            """)
            
            # Create ingest_state table for tracking last successful ingests
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ingest_state (
                    source_id TEXT PRIMARY KEY,
                    last_successful_run TIMESTAMPTZ,
                    last_record_date TIMESTAMPTZ,
                    records_processed INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    error_message TEXT,
                    metadata JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            
            # Create indexes for performance
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_raw_permits_source_id 
                ON raw_permits(source_id)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_raw_permits_extracted_at 
                ON raw_permits(extracted_at)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_raw_permits_permit_id 
                ON raw_permits((raw_data->>'permit_id'))
            """)
            
            conn.commit()
            logger.info("Raw data tables initialized")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to create raw tables: {e}")
            raise
        finally:
            conn.close()
    
    def _get_last_ingest_date(self, source_id: str) -> Optional[datetime]:
        """Get the last successful ingest date for a source."""
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT last_record_date FROM ingest_state WHERE source_id = %s",
                (source_id,)
            )
            result = cur.fetchone()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Failed to get last ingest date for {source_id}: {e}")
            return None
        finally:
            conn.close()
    
    def _update_ingest_state(
        self, 
        source_id: str, 
        status: str, 
        records_processed: int = 0,
        last_record_date: Optional[datetime] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Update ingest state for a source."""
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()
            
            update_values = {
                'status': status,
                'records_processed': records_processed,
                'updated_at': datetime.now(),
                'error_message': error_message,
                'metadata': Json(metadata) if metadata else None
            }
            
            if status == 'success':
                update_values['last_successful_run'] = datetime.now()
            
            if last_record_date:
                update_values['last_record_date'] = last_record_date
            
            # Use UPSERT (ON CONFLICT)
            cur.execute("""
                INSERT INTO ingest_state (source_id, status, records_processed, last_record_date,
                                        last_successful_run, error_message, metadata, updated_at)
                VALUES (%(source_id)s, %(status)s, %(records_processed)s, %(last_record_date)s,
                        %(last_successful_run)s, %(error_message)s, %(metadata)s, %(updated_at)s)
                ON CONFLICT (source_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    records_processed = EXCLUDED.records_processed,
                    last_record_date = COALESCE(EXCLUDED.last_record_date, ingest_state.last_record_date),
                    last_successful_run = COALESCE(EXCLUDED.last_successful_run, ingest_state.last_successful_run),
                    error_message = EXCLUDED.error_message,
                    metadata = EXCLUDED.metadata,
                    updated_at = EXCLUDED.updated_at
            """, {
                'source_id': source_id,
                **update_values
            })
            
            conn.commit()
            logger.info(f"Updated ingest state for {source_id}: {status}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to update ingest state for {source_id}: {e}")
            raise
        finally:
            conn.close()
    
    def _store_raw_records(self, source_id: str, source_type: str, records: List[Dict[str, Any]]) -> int:
        """Store raw records in database."""
        if not records:
            return 0
        
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()
            
            # Batch insert raw records
            insert_sql = """
                INSERT INTO raw_permits (source_id, source_type, raw_data)
                VALUES (%s, %s, %s)
                ON CONFLICT (source_id, (raw_data->>'permit_id'), (raw_data->>'issue_date'))
                DO UPDATE SET
                    raw_data = EXCLUDED.raw_data,
                    updated_at = NOW()
            """
            
            batch_data = []
            for record in records:
                batch_data.append((source_id, source_type, Json(record)))
            
            cur.executemany(insert_sql, batch_data)
            conn.commit()
            
            rows_affected = cur.rowcount
            logger.info(f"Stored {rows_affected} records for {source_id}")
            return rows_affected
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to store raw records for {source_id}: {e}")
            raise
        finally:
            conn.close()
    
    def ingest_source(self, source_config: Dict[str, Any], full_refresh: bool = False) -> Dict[str, Any]:
        """
        Ingest data from a single source.
        
        Args:
            source_config: Source configuration dictionary
            full_refresh: If True, ignore last ingest date and fetch all available data
            
        Returns:
            Dictionary with ingest results
        """
        source_id = source_config['id']
        source_kind = source_config['kind']
        
        logger.info(f"Starting ingest for {source_id} ({source_kind})")
        
        try:
            # Create connector
            connector = create_connector(source_config)
            if not connector:
                if source_kind == 'tpia':
                    logger.info(f"Skipping TPIA source {source_id} - requires manual processing")
                    return {'status': 'skipped', 'reason': 'TPIA requires manual processing'}
                else:
                    raise ValueError(f"Could not create connector for {source_id}")
            
            # Test connection
            if not connector.test_connection():
                raise Exception("Connection test failed")
            
            # Determine date filter
            updated_since = None
            if not full_refresh:
                last_ingest = self._get_last_ingest_date(source_id)
                if last_ingest:
                    # Add small buffer to avoid missing records
                    updated_since = last_ingest - timedelta(hours=1)
                    logger.info(f"Fetching records updated since {updated_since}")
                else:
                    # First time ingesting - get last 30 days
                    updated_since = datetime.now() - timedelta(days=30)
                    logger.info(f"First ingest - fetching last 30 days since {updated_since}")
            
            # Update status to running
            self._update_ingest_state(source_id, 'running')
            
            # Fetch data
            records = []
            latest_date = None
            updated_field = source_config.get('updated_field')
            
            if hasattr(connector, 'get_all_data'):
                # CSV HTTP connector
                for record in connector.get_all_data(
                    updated_since=updated_since,
                    updated_field=updated_field,
                    max_records=50000  # Reasonable limit for single run
                ):
                    records.append(record)
                    
                    # Track latest date for state tracking
                    if updated_field and updated_field.lower() in record:
                        record_date = record.get(updated_field.lower())
                        if isinstance(record_date, datetime):
                            if not latest_date or record_date > latest_date:
                                latest_date = record_date
            
            elif hasattr(connector, 'get_all_features'):
                # ArcGIS connector
                for feature in connector.get_all_features(
                    updated_since=updated_since,
                    updated_field=updated_field,
                    max_records=50000
                ):
                    records.append(feature)
                    
                    # Track latest date
                    if updated_field and updated_field.lower() in feature:
                        feature_date = feature.get(updated_field.lower())
                        if isinstance(feature_date, datetime):
                            if not latest_date or feature_date > latest_date:
                                latest_date = feature_date
            
            else:
                # Socrata or other connector with get_all_data method
                for record in connector.get_all_data(
                    updated_since=updated_since,
                    updated_field=updated_field,
                    max_records=50000
                ):
                    records.append(record)
                    
                    # Track latest date
                    if updated_field and updated_field.lower() in record:
                        record_date = record.get(updated_field.lower())
                        if isinstance(record_date, datetime):
                            if not latest_date or record_date > latest_date:
                                latest_date = record_date
            
            # Store raw records
            records_stored = self._store_raw_records(source_id, source_kind, records)
            
            # Update ingest state
            metadata = {
                'records_fetched': len(records),
                'records_stored': records_stored,
                'updated_since': updated_since.isoformat() if updated_since else None,
                'latest_record_date': latest_date.isoformat() if latest_date else None
            }
            
            self._update_ingest_state(
                source_id=source_id,
                status='success',
                records_processed=records_stored,
                last_record_date=latest_date,
                metadata=metadata
            )
            
            result = {
                'status': 'success',
                'records_fetched': len(records),
                'records_stored': records_stored,
                'latest_date': latest_date
            }
            
            logger.info(f"Completed ingest for {source_id}: {result}")
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to ingest {source_id}: {error_msg}")
            
            # Update state with error
            self._update_ingest_state(
                source_id=source_id,
                status='error',
                error_message=error_msg,
                metadata={'error_type': type(e).__name__}
            )
            
            return {
                'status': 'error',
                'error': error_msg
            }
    
    def run_tier1_ingests(self, full_refresh: bool = False) -> Dict[str, Any]:
        """Run ingests for all Tier-1 sources."""
        self._ensure_raw_tables_exist()
        
        tier1_sources = self.sources_config.get('tier_1_sources', [])
        results = {}
        
        logger.info(f"Starting Tier-1 ingests for {len(tier1_sources)} sources")
        
        for source in tier1_sources:
            source_id = source['id']
            try:
                result = self.ingest_source(source, full_refresh=full_refresh)
                results[source_id] = result
            except Exception as e:
                logger.error(f"Critical error ingesting {source_id}: {e}")
                results[source_id] = {'status': 'critical_error', 'error': str(e)}
        
        # Summary
        successful = sum(1 for r in results.values() if r.get('status') == 'success')
        failed = sum(1 for r in results.values() if r.get('status') in ['error', 'critical_error'])
        skipped = sum(1 for r in results.values() if r.get('status') == 'skipped')
        
        logger.info(f"Tier-1 ingests complete: {successful} successful, {failed} failed, {skipped} skipped")
        
        return {
            'summary': {
                'total': len(tier1_sources),
                'successful': successful,
                'failed': failed,
                'skipped': skipped
            },
            'results': results
        }
    
    def run_tier2_ingests(self, full_refresh: bool = False) -> Dict[str, Any]:
        """Run ingests for all Tier-2 sources."""
        self._ensure_raw_tables_exist()
        
        tier2_sources = self.sources_config.get('tier_2_sources', [])
        results = {}
        
        logger.info(f"Starting Tier-2 ingests for {len(tier2_sources)} sources")
        
        for source in tier2_sources:
            source_id = source['id']
            try:
                result = self.ingest_source(source, full_refresh=full_refresh)
                results[source_id] = result
            except Exception as e:
                logger.error(f"Critical error ingesting {source_id}: {e}")
                results[source_id] = {'status': 'critical_error', 'error': str(e)}
        
        # Summary
        successful = sum(1 for r in results.values() if r.get('status') == 'success')
        failed = sum(1 for r in results.values() if r.get('status') in ['error', 'critical_error'])
        skipped = sum(1 for r in results.values() if r.get('status') == 'skipped')
        
        logger.info(f"Tier-2 ingests complete: {successful} successful, {failed} failed, {skipped} skipped")
        
        return {
            'summary': {
                'total': len(tier2_sources),
                'successful': successful,
                'failed': failed,
                'skipped': skipped
            },
            'results': results
        }


def main():
    """CLI entry point for raw data loading."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Load raw permit data from Texas sources')
    parser.add_argument('--tier', choices=['1', '2', 'all'], default='1',
                       help='Which tier to process (default: 1)')
    parser.add_argument('--full-refresh', action='store_true',
                       help='Ignore last ingest dates and fetch all available data')
    parser.add_argument('--sources-config', default='config/sources_tx.yaml',
                       help='Path to sources configuration file')
    parser.add_argument('--db-url', help='PostgreSQL connection URL (or set DATABASE_URL env var)')
    
    args = parser.parse_args()
    
    # Setup logging

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    

    # Initialize loader
    loader = RawDataLoader()
    
    # Show available sources
    sources = loader.get_available_sources()
    print(f"Available sources: {len(sources)}")
    for source in sources:
        print(f"  - {source['name']} ({source['type']}) - {source['category']}")
    
    # Load data from permits category only
    print("\nLoading permit data...")
    results = loader.load_all_sources(
        incremental=True,
        since_date=datetime.utcnow() - timedelta(days=1),
        categories=["permits"]
    )
    
    # Print results
    print(f"\nLoad Results:")
    total_records = 0
    for result in results:
        print(f"  {result.source_name}: {result.records_loaded} records ({result.status})")
        if result.errors:
            print(f"    Errors: {len(result.errors)}")
        total_records += result.records_loaded
        
    print(f"\nTotal records loaded: {total_records}")


if __name__ == "__main__":
    main()

    # Get database URL
    db_url = args.db_url or os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("Database URL required (--db-url or DATABASE_URL env var)")
        return 1
    
    try:
        loader = RawDataLoader(db_url, args.sources_config)
        
        if args.tier == '1':
            result = loader.run_tier1_ingests(full_refresh=args.full_refresh)
        elif args.tier == '2':
            result = loader.run_tier2_ingests(full_refresh=args.full_refresh)
        else:  # all
            result1 = loader.run_tier1_ingests(full_refresh=args.full_refresh)
            result2 = loader.run_tier2_ingests(full_refresh=args.full_refresh)
            result = {
                'tier_1': result1,
                'tier_2': result2
            }
        
        print(json.dumps(result, indent=2, default=str))
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())

