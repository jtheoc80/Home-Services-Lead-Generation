"""ArcGIS Feature Server adapter for permit data."""

import logging
import requests
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlencode

from ..models.permit import PermitRecord
from ..config_loader import Jurisdiction

logger = logging.getLogger(__name__)


class ArcGISAdapter:
    """Adapter for ArcGIS Feature Server permit data sources."""
    
    def __init__(self, jurisdiction: Jurisdiction):
        """Initialize ArcGIS adapter."""
        self.jurisdiction = jurisdiction
        self.config = jurisdiction.source_config
        self.feature_server = self.config['feature_server']
        self.date_field = self.config['date_field']
        self.field_map = self.config.get('field_map', {})
    
    def scrape_permits(self, since: datetime, limit: Optional[int] = None) -> List[PermitRecord]:
        """Scrape permits from ArcGIS Feature Server."""
        try:
            # Build query parameters
            since_str = since.strftime('%Y-%m-%d')
            where_clause = f"{self.date_field} >= DATE '{since_str}'"
            
            params = {
                'where': where_clause,
                'outFields': '*',
                'f': 'json',
                'returnGeometry': 'true'
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
            
            return permits
            
        except Exception as e:
            logger.error(f"Error scraping ArcGIS for {self.jurisdiction.name}: {e}")
            return []
    
    def _parse_feature(self, feature: dict) -> Optional[PermitRecord]:
        """Parse ArcGIS feature into PermitRecord."""
        attributes = feature.get('attributes', {})
        geometry = feature.get('geometry', {})
        
        # Map fields using configuration
        mapped_data = {}
        for permit_field, source_field in self.field_map.items():
            if source_field in attributes:
                mapped_data[permit_field] = attributes[source_field]
        
        # Extract coordinates if available
        if geometry and 'x' in geometry and 'y' in geometry:
            mapped_data['longitude'] = geometry['x']
            mapped_data['latitude'] = geometry['y']
        
        # Set jurisdiction
        mapped_data['jurisdiction'] = self.jurisdiction.name
        
        try:
            return PermitRecord(**mapped_data)
        except Exception as e:
            logger.warning(f"Error creating PermitRecord: {e}")
            return None