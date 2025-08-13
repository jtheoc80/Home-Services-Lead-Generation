
"""
Raw data loading pipeline for Texas permit sources.

This module reads config/sources_tx.yaml, pulls each source incrementally
using last_updated_seen state tracking, and writes raw data to the database.
"""

import logging
import yaml
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingest.socrata import fetch as socrata_fetch
from ingest.arcgis import query_layer
from ingest.state import get_last_updated_seen, update_last_updated_seen

logger = logging.getLogger(__name__)


def load_source_incremental(source_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load data incrementally from a single source.
    
    Args:
        source_config: Source configuration from sources_tx.yaml
        
    Returns:
        Load result dictionary with status and metrics
    """
    source_id = source_config['id']
    kind = source_config['kind']
    
    logger.info(f"Loading data from {source_id} ({kind})")
    
    try:
        # Get last update timestamp
        last_updated = get_last_updated_seen(source_id)
        
        # Default lookback for initial load
        if not last_updated:
            last_updated = datetime.now() - timedelta(days=30)
            logger.info(f"Initial load for {source_id}, looking back 30 days")
        else:
            logger.info(f"Incremental load for {source_id} since {last_updated}")
        
        records = []
        latest_timestamp = last_updated
        
        if kind == 'socrata':
            # Load from Socrata
            domain = source_config['domain']
            dataset = source_config['dataset']
            updated_fields = source_config['updated_field'].split('|')
            
            # Try each updated field until we find one that works
            for updated_field in updated_fields:
                try:
                    # Build WHERE clause for incremental load
                    timestamp_str = last_updated.strftime('%Y-%m-%dT%H:%M:%S')
                    where = f"{updated_field} >= '{timestamp_str}'"
                    
                    # Fetch data with pagination
                    offset = 0
                    limit = 1000
                    
                    while True:
                        batch = socrata_fetch(
                            domain=domain,
                            dataset=dataset,
                            where=where,
                            limit=limit,
                            offset=offset
                        )
                        
                        if not batch:
                            break
                        
                        records.extend(batch)
                        
                        # Track latest timestamp
                        for record in batch:
                            if updated_field in record:
                                record_time = datetime.fromisoformat(
                                    record[updated_field].replace('Z', '+00:00')
                                )
                                if record_time > latest_timestamp:
                                    latest_timestamp = record_time
                        
                        # Check if we got a full batch (more data available)
                        if len(batch) < limit:
                            break
                        
                        offset += limit
                        
                        # Safety limit
                        if offset >= 50000:
                            logger.warning(f"Hit 50k record limit for {source_id}")
                            break
                    
                    break  # Success with this field
                    
                except Exception as e:
                    logger.warning(f"Failed to load {source_id} with field {updated_field}: {e}")
                    continue
        
        elif kind == 'arcgis':
            # Load from ArcGIS
            base_url = source_config['base_url']
            layer = source_config['layer']
            updated_fields = source_config['updated_field'].split('|')
            
            # Try each updated field until we find one that works
            for updated_field in updated_fields:
                try:
                    # Build WHERE clause for ArcGIS (uses timestamp format)
                    timestamp_ms = int(last_updated.timestamp() * 1000)
                    where = f"{updated_field} >= timestamp '{timestamp_ms}'"
                    
                    # Fetch data with pagination
                    offset = 0
                    limit = 1000
                    
                    while True:
                        response = query_layer(
                            base_url=base_url,
                            layer=layer,
                            where=where,
                            result_offset=offset,
                            result_record_count=limit
                        )
                        
                        features = response.get('features', [])
                        if not features:
                            break
                        
                        # Convert ArcGIS features to flat records
                        for feature in features:
                            record = feature.get('attributes', {})
                            geometry = feature.get('geometry', {})
                            
                            # Add geometry coordinates if available
                            if 'x' in geometry and 'y' in geometry:
                                record['longitude'] = geometry['x']
                                record['latitude'] = geometry['y']
                            
                            records.append(record)
                            
                            # Track latest timestamp
                            if updated_field in record:
                                # ArcGIS timestamps are in milliseconds
                                record_time = datetime.fromtimestamp(record[updated_field] / 1000)
                                if record_time > latest_timestamp:
                                    latest_timestamp = record_time
                        
                        # Check if we got a full batch
                        if len(features) < limit:
                            break
                        
                        offset += limit
                        
                        # Safety limit
                        if offset >= 50000:
                            logger.warning(f"Hit 50k record limit for {source_id}")
                            break
                    
                    break  # Success with this field
                    
                except Exception as e:
                    logger.warning(f"Failed to load {source_id} with field {updated_field}: {e}")
                    continue
        
        else:
            logger.warning(f"Unsupported source kind: {kind} for {source_id}")
            return {'status': 'error', 'error': f'Unsupported kind: {kind}'}
        
        # Update state
        if records:
            success = update_last_updated_seen(source_id, latest_timestamp, 'success')
            if not success:
                logger.warning(f"Failed to update state for {source_id}")
        
        logger.info(f"Loaded {len(records)} records from {source_id}")
        
        return {
            'status': 'success',
            'records': len(records),
            'latest_timestamp': latest_timestamp.isoformat(),
            'data': records  # Include data for downstream processing
        }
        
    except Exception as e:
        logger.error(f"Failed to load {source_id}: {e}")
        update_last_updated_seen(source_id, None, 'error')
        return {'status': 'error', 'error': str(e)}


def main():
    """
    Main entry point for raw data loading.
    
    Supports command line arguments:
    --only: Comma-separated list of source IDs to load
    --since: ISO date to load since (overrides state)
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Load raw permit data from Texas sources')
    parser.add_argument('--only', help='Comma-separated list of source IDs to load')
    parser.add_argument('--since', help='ISO date to load since (e.g., 2024-01-01)')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load sources configuration
    config_path = Path(__file__).parent.parent / 'config' / 'sources_tx.yaml'
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load sources config: {e}")
        return 1
    
    sources = config.get('sources', [])
    
    # Filter sources if --only specified
    if args.only:
        only_sources = args.only.split(',')
        sources = [s for s in sources if s['id'] in only_sources]
        logger.info(f"Loading only sources: {only_sources}")
    
    # Override since date if specified
    if args.since:
        try:
            since_date = datetime.fromisoformat(args.since)
            # Reset state for all selected sources
            from ingest.state import reset_source_state
            for source in sources:
                reset_source_state(source['id'])
                # Set a manual state with the since date
                update_last_updated_seen(source['id'], since_date, 'manual_override')
            logger.info(f"Loading data since {args.since}")
        except ValueError as e:
            logger.error(f"Invalid since date format: {e}")
            return 1
    
    # Load data from each source
    results = []
    total_records = 0
    
    for source in sources:
        if source['kind'] == 'tpia':
            logger.info(f"Skipping TPIA source {source['id']} - requires manual processing")
            continue
        
        result = load_source_incremental(source)
        results.append({**result, 'source_id': source['id']})
        
        if result['status'] == 'success':
            total_records += result.get('records', 0)
    
    # Summary
    successful = sum(1 for r in results if r['status'] == 'success')
    failed = sum(1 for r in results if r['status'] == 'error')
    
    logger.info(f"Load complete: {successful} successful, {failed} failed, {total_records} total records")
    
    # Print results
    for result in results:
        status = result['status']
        source_id = result['source_id']
        if status == 'success':
            records = result.get('records', 0)
            print(f"✓ {source_id}: {records} records")
        else:
            error = result.get('error', 'Unknown error')
            print(f"✗ {source_id}: {error}")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())

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
    parser.add_argument('--only', help='Comma-separated list of source IDs to load')
    parser.add_argument('--since', help='ISO date to load since (e.g., 2024-01-01)')
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
        # Load sources configuration
        config_path = Path(__file__).parent.parent / 'config' / 'sources_tx.yaml'
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        sources = config.get('sources', [])
        
        # Filter sources if --only specified
        if args.only:
            only_sources = args.only.split(',')
            sources = [s for s in sources if s['id'] in only_sources]
            logger.info(f"Loading only sources: {only_sources}")
        
        # Override since date if specified
        if args.since:
            try:
                since_date = datetime.fromisoformat(args.since)
                # Reset state for all selected sources
                from ingest.state import IngestStateManager
                state_manager = IngestStateManager(db_url)
                for source in sources:
                    state_manager.reset_source_state(source['id'])
                    # Set a manual state with the since date
                    state_manager.update_last_updated_seen(source['id'], since_date, 'manual_override')
                logger.info(f"Loading data since {args.since}")
            except ValueError as e:
                logger.error(f"Invalid since date format: {e}")
                return 1
        
        # Load data from each source
        results = []
        total_records = 0
        
        for source in sources:
            if source['kind'] == 'tpia':
                logger.info(f"Skipping TPIA source {source['id']} - requires manual processing")
                continue
            
            result = load_source_incremental(source)
            results.append({**result, 'source_id': source['id']})
            
            if result['status'] == 'success':
                total_records += result.get('records', 0)
        
        # Summary
        successful = sum(1 for r in results if r['status'] == 'success')
        failed = sum(1 for r in results if r['status'] == 'error')
        
        logger.info(f"Load complete: {successful} successful, {failed} failed, {total_records} total records")
        
        # Print results
        for result in results:
            status = result['status']
            source_id = result['source_id']
            if status == 'success':
                records = result.get('records', 0)
                print(f"✓ {source_id}: {records} records")
            else:
                error = result.get('error', 'Unknown error')
                print(f"✗ {source_id}: {error}")
        
        return 0 if failed == 0 else 1
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())

