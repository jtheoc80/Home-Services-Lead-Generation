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
                    logger.warning(f"Coordinates outside Texas bounds: {lat}, {lon}")
                    
            except (ValueError, TypeError):
                logger.warning(f"Invalid coordinates: {lat}, {lon}")
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