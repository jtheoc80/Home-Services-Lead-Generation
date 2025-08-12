"""Enhanced ArcGIS adapter with ETL state management for Harris County permits."""

import logging
import requests
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlencode

from ..models.permit import PermitRecord
from ..config_loader import Jurisdiction
from ..etl_state import ETLStateManager

logger = logging.getLogger(__name__)


class ETLAwareArcGISAdapter:
    """
    Enhanced ArcGIS adapter with ETL state management.
    
    This adapter tracks the last successful run timestamp to enable
    incremental data loading and prevent gaps in permit data.
    """
    
    def __init__(self, jurisdiction: Jurisdiction):
        """Initialize enhanced ArcGIS adapter."""
        self.jurisdiction = jurisdiction
        self.config = jurisdiction.source_config
        logger.debug(f"Config for {jurisdiction.name}: {self.config}")
        self.feature_server = self.config['url']
        self.date_field = self.config['date_field']
        self.field_map = self.config.get('field_map', {})
        
        # Initialize ETL state manager
        self.etl_state = ETLStateManager()
        
        # Determine source name for state tracking
        self.source_name = self._get_source_name()
    
    def _get_source_name(self) -> str:
        """Get the source name for ETL state tracking."""
        # For Harris County, use 'harris_issued_permits' as specified in requirements
        if 'harris' in self.jurisdiction.slug.lower():
            return 'harris_issued_permits'
        else:
            # For other jurisdictions, use jurisdiction slug
            return f"{self.jurisdiction.slug}_permits"
    
    def scrape_permits(self, since: Optional[datetime] = None, limit: Optional[int] = None) -> List[PermitRecord]:
        """
        Scrape permits from ArcGIS Feature Server with ETL state management.
        
        Args:
            since: Optional override for since timestamp (for backward compatibility)
            limit: Maximum number of records to fetch
            
        Returns:
            List of PermitRecord objects
        """
        try:
            # Determine the since timestamp using ETL state management
            if since is None:
                since = self.etl_state.get_since_timestamp(self.source_name, fallback_days=7)
            
            logger.info(f"Scraping {self.jurisdiction.name} permits since {since}")
            
            # Fetch permits from ArcGIS
            permits = self._fetch_permits_from_arcgis(since, limit)
            
            # Update ETL state with current timestamp on successful fetch (regardless of result count)
            current_time = datetime.utcnow()
            success = self.etl_state.update_last_run(self.source_name, current_time)
            
            if success:
                logger.info(f"Updated ETL state for {self.source_name}: {current_time}")
            else:
                logger.warning(f"Failed to update ETL state for {self.source_name}")
            
            return permits
            
        except Exception as e:
            logger.error(f"Error scraping permits from {self.jurisdiction.name}: {e}")
            return []
    
    def _fetch_permits_from_arcgis(self, since: datetime, limit: Optional[int] = None) -> List[PermitRecord]:
        """Fetch permits from ArcGIS Feature Server."""
        try:
            # Build query parameters with proper date format for ArcGIS
            # ArcGIS expects timestamps in epoch milliseconds or specific date formats
            since_str = since.strftime('%Y-%m-%d %H:%M:%S')
            # ArcGIS expects timestamps in epoch milliseconds or specific date formats.
            # Use epoch milliseconds for better compatibility
            epoch_ms = int(since.timestamp() * 1000)
            where_clause = f"{self.date_field} > {epoch_ms}"
            
            params = {
                'where': where_clause,
                'outFields': '*',
                'f': 'json',
                'returnGeometry': 'true',
                'orderByFields': f"{self.date_field} ASC"  # Order by date for consistent processing
            }
            
            if limit:
                params['resultRecordCount'] = limit
            
            url = f"{self.feature_server}/query"
            logger.debug(f"Querying ArcGIS: {url}?{urlencode(params)}")
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'features' not in data:
                logger.warning(f"No features found in ArcGIS response for {self.jurisdiction.name}")
                return []
            
            permits = []
            for feature in data['features']:
                try:
                    permit = self._parse_feature(feature)
                    if permit:
                        permits.append(permit)
                except Exception as e:
                    logger.warning(f"Error parsing feature: {e}")
                    continue
            
            logger.info(f"Successfully fetched {len(permits)} permits from {self.jurisdiction.name}")
            return permits
            
        except Exception as e:
            logger.error(f"Error fetching from ArcGIS for {self.jurisdiction.name}: {e}")
            raise
    
    def _parse_feature(self, feature: dict) -> Optional[PermitRecord]:
        """Parse ArcGIS feature into PermitRecord."""
        attributes = feature.get('attributes', {})
        geometry = feature.get('geometry', {})
        
        # Map fields using configuration
        mapped_data = {}
        for permit_field, source_field in self.field_map.items():
            if source_field in attributes:
                value = attributes[source_field]
                
                # Handle datetime fields
                if permit_field in ['issue_date', 'application_date', 'expiration_date'] and value:
                    # ArcGIS often returns epoch milliseconds
                    if isinstance(value, (int, float)) and value > 0:
                        try:
                            # Convert from epoch milliseconds
                            mapped_data[permit_field] = datetime.fromtimestamp(value / 1000)
                        except (ValueError, OSError):
                            # If conversion fails, keep original value
                            mapped_data[permit_field] = value
                    else:
                        mapped_data[permit_field] = value
                else:
                    mapped_data[permit_field] = value
        
        # Extract coordinates if available
        if geometry and 'x' in geometry and 'y' in geometry:
            mapped_data['longitude'] = geometry['x']
            mapped_data['latitude'] = geometry['y']
        
        # Set jurisdiction
        mapped_data['jurisdiction'] = self.jurisdiction.name
        
        # Add scraped timestamp
        mapped_data['scraped_at'] = datetime.utcnow()
        
        try:
            return PermitRecord(**mapped_data)
        except Exception as e:
            logger.warning(f"Error creating PermitRecord: {e}")
            logger.debug(f"Mapped data: {mapped_data}")
            return None
    
    def get_last_run(self) -> Optional[datetime]:
        """Get the last successful run timestamp for this source."""
        return self.etl_state.get_last_run(self.source_name)
    
    def update_last_run(self, timestamp: datetime) -> bool:
        """Update the last successful run timestamp for this source."""
        return self.etl_state.update_last_run(self.source_name, timestamp)