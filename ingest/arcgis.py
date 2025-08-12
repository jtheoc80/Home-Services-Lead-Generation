"""Enhanced ArcGIS Feature Service connector with rate limiting, pagination, and incremental updates."""

import logging
import time
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Iterator, Tuple
from urllib.parse import urlencode
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class ArcGISConnector:
    """Enhanced ArcGIS Feature Service connector with advanced capabilities."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize ArcGIS connector with configuration."""
        self.config = config
        self.url = config["url"]
        self.updated_field = config.get("updated_field")
        self.primary_key = config.get("primary_key")
        self.rate_limit = config.get("rate_limit", 5)  # requests per second
        self.pagination_config = config.get("pagination", {})
        self.page_size = self.pagination_config.get("page_size", 1000)
        
        # Rate limiting
        self._last_request_time = 0
        self._request_interval = 1.0 / self.rate_limit
        
        # HTTP session with retry strategy
        self.session = self._create_session()
        
        # Base query parameters
        self.base_params = {
            "f": "json",
            "outFields": "*",
            "where": "1=1",
            "orderByFields": self.primary_key if self.primary_key else "",
            "resultRecordCount": self.page_size
        }
        
    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry strategy."""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
        
    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._request_interval:
            time.sleep(self._request_interval - elapsed)
        self._last_request_time = time.time()
        
    def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make rate-limited request to ArcGIS service."""
        self._rate_limit()
        
        try:
            response = self.session.get(self.url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if data.get("error"):
                raise ValueError(f"ArcGIS API error: {data['error']}")
                
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise
            
    def get_feature_count(self, where_clause: str = "1=1") -> int:
        """Get total count of features matching criteria."""
        params = {
            "f": "json",
            "where": where_clause,
            "returnCountOnly": "true"
        }
        
        data = self._make_request(params)
        return data.get("count", 0)
        
    def get_updated_since(self, since_date: datetime) -> Iterator[Dict[str, Any]]:
        """Get records updated since specified date."""
        if not self.updated_field:
            raise ValueError("updated_field not configured for incremental updates")
            
        # Format date for ArcGIS query
        date_str = since_date.strftime("%Y-%m-%d %H:%M:%S")
        where_clause = f"{self.updated_field} >= TIMESTAMP '{date_str}'"
        
        logger.info(f"Fetching records updated since {date_str}")
        
        yield from self.get_paginated_features(where_clause)
        
    def get_paginated_features(self, where_clause: str = "1=1") -> Iterator[Dict[str, Any]]:
        """Get features with pagination support."""
        offset = 0
        total_count = self.get_feature_count(where_clause)
        
        logger.info(f"Total features to fetch: {total_count}")
        
        while offset < total_count:
            params = self.base_params.copy()
            params.update({
                "where": where_clause,
                "resultOffset": offset
            })
            
            logger.info(f"Fetching batch {offset // self.page_size + 1}, "
                       f"records {offset}-{min(offset + self.page_size, total_count)}")
            
            data = self._make_request(params)
            features = data.get("features", [])
            
            if not features:
                logger.warning(f"No features returned at offset {offset}")
                break
                
            for feature in features:
                yield self._normalize_feature(feature)
                
            offset += len(features)
            
            # Break if we got fewer records than requested (end of data)
            if len(features) < self.page_size:
                break
                
    def _normalize_feature(self, feature: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize ArcGIS feature to standard format."""
        attributes = feature.get("attributes", {})
        geometry = feature.get("geometry", {})
        
        # Apply field mappings if configured
        mappings = self.config.get("mappings", {})
        normalized = {}
        
        if mappings:
            for standard_field, source_field in mappings.items():
                normalized[standard_field] = attributes.get(source_field)
        else:
            normalized = attributes.copy()
            
        # Add geometry if present
        if geometry:
            if "x" in geometry and "y" in geometry:
                normalized["longitude"] = geometry["x"]
                normalized["latitude"] = geometry["y"]
            elif "rings" in geometry or "paths" in geometry:
                # For polygon/polyline geometries, store as WKT or GeoJSON
                normalized["geometry"] = geometry
                
        # Add metadata
        normalized["_source"] = self.config.get("name", "arcgis")
        normalized["_category"] = self.config.get("category", "unknown")
        normalized["_jurisdiction"] = self.config.get("jurisdiction", "unknown")
        normalized["_ingested_at"] = datetime.utcnow().isoformat()
        
        return normalized
        
    def test_connection(self) -> Tuple[bool, str]:
        """Test connection to ArcGIS service."""
        try:
            params = {"f": "json", "where": "1=1", "returnCountOnly": "true"}
            data = self._make_request(params)
            
            if "count" in data:
                return True, f"Connection successful. Total records: {data['count']}"
            else:
                return False, "Unexpected response format"
                
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
            
    def get_field_info(self) -> List[Dict[str, Any]]:
        """Get field information from the service."""
        try:
            # Get service metadata
            metadata_url = self.url.replace("/query", "")
            params = {"f": "json"}
            
            response = self.session.get(metadata_url, params=params, timeout=30)
            response.raise_for_status()
            
            metadata = response.json()
            return metadata.get("fields", [])
            
        except Exception as e:
            logger.error(f"Failed to get field info: {e}")
            return []


def create_arcgis_connector(config: Dict[str, Any]) -> ArcGISConnector:
    """Factory function to create ArcGIS connector."""
    return ArcGISConnector(config)


# Example usage
if __name__ == "__main__":
    # Example configuration
    config = {
        "name": "Harris County Permits",
        "url": "https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0/query",
        "updated_field": "ISSUEDDATE",
        "primary_key": "PERMITNUMBER",
        "category": "permits",
        "jurisdiction": "harris-county",
        "rate_limit": 5,
        "pagination": {"page_size": 1000},
        "mappings": {
            "permit_number": "PERMITNUMBER",
            "issued_date": "ISSUEDDATE",
            "address": "FULLADDRESS",
            "description": "PROJECTNAME",
            "status": "STATUS",
            "work_class": "APPTYPE"
        }
    }
    
    connector = create_arcgis_connector(config)
    
    # Test connection
    success, message = connector.test_connection()
    print(f"Connection test: {message}")
    
    if success:
        # Get recent records
        since_date = datetime.now() - timedelta(days=7)
        count = 0
        for record in connector.get_updated_since(since_date):
            print(f"Record {count + 1}: {record.get('permit_number', 'N/A')}")
            count += 1
            if count >= 5:  # Limit to 5 for demo
                break
        print(f"Fetched {count} records")