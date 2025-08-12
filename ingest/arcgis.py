
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

"""
ArcGIS REST API connector for ingesting permit data.

This module provides functionality to connect to ArcGIS FeatureServer endpoints,
query data with pagination and date filtering, and normalize responses for ingestion.
"""

import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Iterator
from urllib.parse import urlencode
import time


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

    """Connector for ArcGIS REST API FeatureServer endpoints."""
    
    def __init__(self, base_url: str, timeout: int = 30, retry_count: int = 3):
        """
        Initialize ArcGIS connector.
        
        Args:
            base_url: Base URL of the ArcGIS FeatureServer
            timeout: Request timeout in seconds
            retry_count: Number of retry attempts for failed requests
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.retry_count = retry_count
        self.session = requests.Session()
        
        # Set common headers
        self.session.headers.update({
            'User-Agent': 'HomeServicesLeadGen/1.0 (Texas Permits Ingestion)',
            'Accept': 'application/json'
        })
    
    def _make_request(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.
        
        Args:
            url: Request URL
            params: Query parameters
            
        Returns:
            JSON response data
            
        Raises:
            Exception: If all retry attempts fail
        """
        for attempt in range(self.retry_count):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                
                data = response.json()
                if 'error' in data:
                    raise Exception(f"ArcGIS API error: {data['error']}")
                
                return data
                
            except Exception as e:
                logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                if attempt == self.retry_count - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
    
    def query_features(
        self,
        updated_since: Optional[datetime] = None,
        updated_field: str = "LAST_EDITED_DATE",
        page_size: int = 1000,
        result_offset: int = 0,
        where_clause: Optional[str] = None,
        out_fields: str = "*"
    ) -> Dict[str, Any]:
        """
        Query features from ArcGIS FeatureServer.
        
        Args:
            updated_since: Filter records updated since this datetime
            updated_field: Field name for date filtering
            page_size: Number of records per page
            result_offset: Starting offset for pagination
            where_clause: Custom WHERE clause for filtering
            out_fields: Comma-separated list of fields to return
            
        Returns:
            ArcGIS query response with features and metadata
        """
        query_url = f"{self.base_url}/query"
        
        # Build WHERE clause
        where_parts = []
        if updated_since:
            # ArcGIS expects date in Unix timestamp milliseconds
            timestamp_ms = int(updated_since.timestamp() * 1000)
            where_parts.append(f"{updated_field} >= timestamp '{timestamp_ms}'")
        
        if where_clause:
            where_parts.append(where_clause)
        
        where_sql = " AND ".join(where_parts) if where_parts else "1=1"
        
        params = {
            'where': where_sql,
            'outFields': out_fields,
            'returnGeometry': 'true',
            'spatialRel': 'esriSpatialRelIntersects',
            'f': 'json',
            'resultOffset': result_offset,
            'resultRecordCount': page_size,
            'orderByFields': f"{updated_field} ASC"
        }
        
        logger.info(f"Querying ArcGIS: {query_url} with WHERE: {where_sql}")
        return self._make_request(query_url, params)
    
    def get_all_features(
        self,
        updated_since: Optional[datetime] = None,
        updated_field: str = "LAST_EDITED_DATE",
        page_size: int = 1000,
        max_records: Optional[int] = None
    ) -> Iterator[Dict[str, Any]]:
        """
        Generator that yields all features with automatic pagination.
        
        Args:
            updated_since: Filter records updated since this datetime
            updated_field: Field name for date filtering
            page_size: Number of records per page
            max_records: Maximum total records to fetch (None for unlimited)
            
        Yields:
            Individual feature records with normalized structure
        """
        offset = 0
        total_fetched = 0
        
        while True:
            try:
                response = self.query_features(
                    updated_since=updated_since,
                    updated_field=updated_field,
                    page_size=page_size,
                    result_offset=offset
                )
                
                features = response.get('features', [])
                if not features:
                    break
                
                for feature in features:
                    if max_records and total_fetched >= max_records:
                        return
                    
                    yield self._normalize_feature(feature)
                    total_fetched += 1
                
                # Check if we've reached the end
                if len(features) < page_size:
                    break
                
                offset += page_size
                
                # Check if server indicates more records exist
                if 'exceededTransferLimit' in response and not response['exceededTransferLimit']:
                    break
                
                logger.info(f"Fetched {total_fetched} records so far...")
                
            except Exception as e:
                logger.error(f"Error fetching features at offset {offset}: {e}")
                break
        
        logger.info(f"Total features fetched: {total_fetched}")
    
    def _normalize_feature(self, feature: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize ArcGIS feature to standard format.
        
        Args:
            feature: Raw ArcGIS feature object
            
        Returns:
            Normalized feature with standard field names
        """
        attributes = feature.get('attributes', {})
        geometry = feature.get('geometry', {})
        
        normalized = {
            'raw_attributes': attributes,
            'geometry': geometry,
            'source_type': 'arcgis'
        }
        
        # Extract geometry coordinates if available
        if geometry:
            if 'x' in geometry and 'y' in geometry:
                normalized['longitude'] = geometry['x']
                normalized['latitude'] = geometry['y']
            elif 'coordinates' in geometry:
                coords = geometry['coordinates']
                if isinstance(coords, list) and len(coords) >= 2:
                    normalized['longitude'] = coords[0]
                    normalized['latitude'] = coords[1]
        
        # Convert timestamp fields to datetime objects
        for key, value in attributes.items():
            if key.upper().endswith('DATE') and value:
                try:
                    # ArcGIS timestamps are in milliseconds
                    if isinstance(value, (int, float)) and value > 0:
                        normalized[key.lower()] = datetime.fromtimestamp(value / 1000)
                except (ValueError, TypeError, OSError):
                    # Keep original value if conversion fails
                    normalized[key.lower()] = value
            else:
                normalized[key.lower()] = value
        
        return normalized
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        Get metadata about the ArcGIS service.
        
        Returns:
            Service metadata including fields, capabilities, etc.
        """
        info_url = self.base_url
        params = {'f': 'json'}
        
        logger.info(f"Getting service info: {info_url}")
        return self._make_request(info_url, params)
    
    def get_field_info(self) -> List[Dict[str, Any]]:
        """
        Get information about available fields in the service.
        
        Returns:
            List of field definitions with names, types, etc.
        """
        service_info = self.get_service_info()
        return service_info.get('fields', [])
    
    def test_connection(self) -> bool:
        """
        Test if the ArcGIS service is accessible.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            info = self.get_service_info()
            return 'name' in info or 'mapName' in info
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False


def create_arcgis_connector(source_config: Dict[str, Any]) -> ArcGISConnector:
    """
    Factory function to create ArcGIS connector from source configuration.
    
    Args:
        source_config: Source configuration from sources_tx.yaml
        
    Returns:
        Configured ArcGIS connector instance
    """
    endpoint = source_config.get('endpoint')
    if not endpoint:
        raise ValueError("ArcGIS endpoint URL is required")
    
    timeout = source_config.get('timeout', 30)
    retry_count = source_config.get('retry_count', 3)
    
    return ArcGISConnector(
        base_url=endpoint,
        timeout=timeout,
        retry_count=retry_count
    )


# Example usage and testing
if __name__ == "__main__":
    # Example configuration for Harris County
    test_config = {
        'endpoint': 'https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0',
        'updated_field': 'ISSUEDDATE'
    }
    
    connector = create_arcgis_connector(test_config)
    
    # Test connection
    if connector.test_connection():
        print("✓ Connection successful")
        
        # Get service info
        info = connector.get_service_info()
        print(f"Service: {info.get('name', 'Unknown')}")
        
        # Get field info
        fields = connector.get_field_info()
        print(f"Available fields: {len(fields)}")
        for field in fields[:5]:  # Show first 5 fields
            print(f"  - {field.get('name')}: {field.get('type')}")
        
        # Test querying recent data (last 7 days)
        since_date = datetime.now() - timedelta(days=7)
        print(f"\nTesting query for records since {since_date}")
        
        count = 0
        for feature in connector.get_all_features(
            updated_since=since_date,
            updated_field=test_config['updated_field'],
            max_records=5
        ):
            count += 1
            print(f"Record {count}: {list(feature.keys())}")
        
        print(f"✓ Successfully fetched {count} test records")
    else:
        print("✗ Connection failed")

