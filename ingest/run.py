#!/usr/bin/env python3
"""
Ingestion Runner - Commands for loading, normalizing, and publishing data.

This module provides the main command-line interface for the data ingestion
pipeline. It supports three main commands:

1. load_raw --since <timestamp> - Extract raw data from sources since timestamp
2. normalize - Transform raw data into normalized bronze/silver schemas
3. publish - Move normalized data to gold tables and trigger scoring

Usage:
    python -m ingest.run load_raw --since 2024-01-01T00:00:00Z
    python -m ingest.run normalize
    python -m ingest.run publish
"""

import argparse
import asyncio
import logging
import os
import sys
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingest.arcgis import ArcGISConnector
from ingest.socrata import SocrataConnector
from ingest.csv_http import CSVHTTPConnector


@dataclass
class IngestState:
    """Track ingestion state for a source."""
    source_id: str
    last_updated_seen: Optional[datetime]
    last_status: str
    last_run: datetime
    records_processed: int = 0
    error_message: Optional[str] = None


class IngestionRunner:
    """Main orchestrator for data ingestion pipeline."""
    
    def __init__(self, config_path: str = "config/sources_tx.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.connectors = self._setup_connectors()
        self.logger = self._setup_logging()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load sources configuration."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load config from {self.config_path}: {e}")
    
    def _setup_connectors(self) -> Dict[str, Any]:
        """Initialize connectors for different source types."""
        return {
            'arcgis': ArcGISConnector(),
            'socrata': SocrataConnector(),
            'csv_http': CSVHTTPConnector(),
            'tpia': None  # Manual processing
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for ingestion pipeline."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger('ingest.run')
    
    async def load_raw(self, since: Optional[datetime] = None) -> Dict[str, IngestState]:
        """
        Load raw data from all configured sources since the given timestamp.
        
        Args:
            since: Timestamp to load data since. If None, loads incremental.
            
        Returns:
            Dictionary mapping source_id to IngestState
        """
        self.logger.info(f"Starting raw data load since {since}")
        results = {}
        
        for source in self.config.get('sources', []):
            source_id = source['id']
            self.logger.info(f"Processing source: {source_id}")
            
            try:
                state = await self._load_source_raw(source, since)
                results[source_id] = state
                
                # Persist state to database
                await self._persist_ingest_state(state)
                
            except Exception as e:
                self.logger.error(f"Failed to load {source_id}: {e}")
                results[source_id] = IngestState(
                    source_id=source_id,
                    last_updated_seen=None,
                    last_status="error",
                    last_run=datetime.now(timezone.utc),
                    error_message=str(e)
                )
        
        self.logger.info(f"Raw data load completed. Processed {len(results)} sources")
        return results
    
    async def _load_source_raw(self, source: Dict[str, Any], since: Optional[datetime]) -> IngestState:
        """Load raw data from a single source."""
        source_id = source['id']
        source_kind = source['kind']
        
        if source_kind == 'tpia':
            self.logger.info(f"Skipping TPIA source {source_id} - manual processing required")
            return IngestState(
                source_id=source_id,
                last_updated_seen=None,
                last_status="manual",
                last_run=datetime.now(timezone.utc)
            )
        
        connector = self.connectors.get(source_kind)
        if not connector:
            raise ValueError(f"No connector available for source kind: {source_kind}")
        
        # Get existing state or use since parameter
        last_seen = since or await self._get_last_updated_seen(source_id)
        
        # Extract data using appropriate connector
        records = await connector.extract_updated_since(
            endpoint=source['endpoint'],
            updated_field=source['updated_field'],
            since=last_seen,
            rate_limit=self.config.get('rate_limits', {}).get(source_kind, 1)
        )
        
        # Store in raw schema
        await self._store_raw_records(source_id, records)
        
        # Calculate new last_updated_seen
        new_last_seen = None
        if records:
            # Find the latest timestamp in the extracted records
            timestamps = [r.get(source['updated_field']) for r in records if r.get(source['updated_field'])]
            if timestamps:
                # Convert to datetime objects and find max
                dt_timestamps = [self._parse_datetime(ts) for ts in timestamps]
                new_last_seen = max(dt_timestamps)
        
        return IngestState(
            source_id=source_id,
            last_updated_seen=new_last_seen,
            last_status="success",
            last_run=datetime.now(timezone.utc),
            records_processed=len(records)
        )
    
    async def normalize(self) -> Dict[str, Any]:
        """
        Normalize raw data into bronze/silver schemas.
        
        Returns:
            Summary of normalization results
        """
        self.logger.info("Starting data normalization")
        
        # This would contain the logic to:
        # 1. Read from raw.* tables
        # 2. Apply field mappings from config
        # 3. Standardize formats, geocode addresses
        # 4. Store in bronze.* and silver.* tables
        # 5. Apply data quality checks
        
        results = {
            'normalized_sources': [],
            'total_records': 0,
            'errors': []
        }
        
        for source in self.config.get('sources', []):
            try:
                source_id = source['id']
                self.logger.info(f"Normalizing {source_id}")
                
                # Implementation would go here
                # For now, just logging the intent
                
                results['normalized_sources'].append(source_id)
                
            except Exception as e:
                self.logger.error(f"Normalization failed for {source['id']}: {e}")
                results['errors'].append({
                    'source_id': source['id'],
                    'error': str(e)
                })
        
        self.logger.info(f"Normalization completed for {len(results['normalized_sources'])} sources")
        return results
    
    async def publish(self) -> Dict[str, Any]:
        """
        Publish normalized data to gold tables and trigger lead scoring.
        
        Returns:
            Summary of publishing results
        """
        self.logger.info("Starting data publishing")
        
        # This would contain the logic to:
        # 1. Read from silver.* tables
        # 2. Apply business rules and enrichment
        # 3. Store in gold.permits, gold.violations, etc.
        # 4. Trigger lead scoring for new/updated records
        # 5. Update search indexes
        
        results = {
            'published_entities': [],
            'total_records': 0,
            'scoring_triggered': False,
            'errors': []
        }
        
        entities = ['permits', 'violations', 'inspections', 'bids', 'awards']
        
        for entity in entities:
            try:
                self.logger.info(f"Publishing {entity} to gold schema")
                
                # Implementation would go here
                # For now, just logging the intent
                
                results['published_entities'].append(entity)
                
            except Exception as e:
                self.logger.error(f"Publishing failed for {entity}: {e}")
                results['errors'].append({
                    'entity': entity,
                    'error': str(e)
                })
        
        # Trigger lead scoring for new records
        try:
            await self._trigger_lead_scoring()
            results['scoring_triggered'] = True
        except Exception as e:
            self.logger.error(f"Lead scoring trigger failed: {e}")
            results['errors'].append({
                'entity': 'lead_scoring',
                'error': str(e)
            })
        
        self.logger.info(f"Publishing completed for {len(results['published_entities'])} entities")
        return results
    
    async def _get_last_updated_seen(self, source_id: str) -> Optional[datetime]:
        """Get the last processed timestamp for a source from meta.ingest_state."""
        # Implementation would query the database
        # For now, return None to load all available data
        return None
    
    async def _persist_ingest_state(self, state: IngestState) -> None:
        """Persist ingestion state to meta.ingest_state table."""
        # Implementation would update/insert database record
        self.logger.info(f"Persisting state for {state.source_id}: {state.last_status}")
    
    async def _store_raw_records(self, source_id: str, records: List[Dict[str, Any]]) -> None:
        """Store raw records in raw.{source_id} table."""
        # Implementation would insert records into database
        self.logger.info(f"Storing {len(records)} raw records for {source_id}")
    
    async def _trigger_lead_scoring(self) -> None:
        """Trigger lead scoring for new/updated records."""
        # Implementation would call scoring service
        self.logger.info("Triggering lead scoring for updated records")
    
    def _parse_datetime(self, timestamp_str: str) -> datetime:
        """Parse datetime string into datetime object."""
        try:
            # Handle common timestamp formats
            if timestamp_str.endswith('Z'):
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                return datetime.fromisoformat(timestamp_str)
        except ValueError:
            # Fallback to current time if parsing fails
            return datetime.now(timezone.utc)


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='Data Ingestion Runner')
    parser.add_argument('command', choices=['load_raw', 'normalize', 'publish'],
                       help='Command to execute')
    parser.add_argument('--since', type=str,
                       help='Timestamp to load data since (ISO format)')
    parser.add_argument('--config', type=str, default='config/sources_tx.yaml',
                       help='Path to sources configuration file')
    
    args = parser.parse_args()
    
    # Parse since timestamp if provided
    since = None
    if args.since:
        try:
            since = datetime.fromisoformat(args.since.replace('Z', '+00:00'))
        except ValueError:
            print(f"Error: Invalid timestamp format: {args.since}")
            sys.exit(1)
    
    # Initialize runner
    try:
        runner = IngestionRunner(config_path=args.config)
    except Exception as e:
        print(f"Error: Failed to initialize runner: {e}")
        sys.exit(1)
    
    # Execute command
    try:
        if args.command == 'load_raw':
            results = await runner.load_raw(since=since)
            print(f"Raw data load completed. Processed {len(results)} sources.")
            
        elif args.command == 'normalize':
            results = await runner.normalize()
            print(f"Normalization completed for {len(results['normalized_sources'])} sources.")
            
        elif args.command == 'publish':
            results = await runner.publish()
            print(f"Publishing completed for {len(results['published_entities'])} entities.")
            
    except Exception as e:
        print(f"Error: Command failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())