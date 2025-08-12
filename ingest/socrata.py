"""
Socrata Open Data API connector for ingesting permit data.

This module provides functionality to connect to Socrata SODA API endpoints,
query data with pagination and date filtering, and normalize responses for ingestion.
"""

import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Iterator
from urllib.parse import urljoin, urlencode
import time

logger = logging.getLogger(__name__)


class SocrataConnector:
    """Connector for Socrata Open Data API (SODA) endpoints."""
    
    def __init__(self, base_url: str, app_token: Optional[str] = None, timeout: int = 30, retry_count: int = 3):
        """
        Initialize Socrata connector.
        
        Args:
            base_url: Base URL of the Socrata dataset (ending in .json)
            app_token: Optional Socrata app token for higher rate limits
            timeout: Request timeout in seconds
            retry_count: Number of retry attempts for failed requests
        """
        self.base_url = base_url.rstrip('/')
        self.app_token = app_token
        self.timeout = timeout
        self.retry_count = retry_count
        self.session = requests.Session()
        
        # Set common headers
        headers = {
            'User-Agent': 'HomeServicesLeadGen/1.0 (Texas Permits Ingestion)',
            'Accept': 'application/json'
        }
        
        if app_token:
            headers['X-App-Token'] = app_token
        
        self.session.headers.update(headers)
    
    def _make_request(self, url: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Make HTTP request with retry logic.
        
        Args:
            url: Request URL
            params: Query parameters
            
        Returns:
            JSON response data as list of records
            
        Raises:
            Exception: If all retry attempts fail
        """
        for attempt in range(self.retry_count):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                
                data = response.json()
                
                # Handle Socrata error responses
                if isinstance(data, dict) and 'error' in data:
                    raise Exception(f"Socrata API error: {data['error']}")
                
                # Ensure we have a list
                if not isinstance(data, list):
                    data = [data] if data else []
                
                return data
                
            except Exception as e:
                logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                if attempt == self.retry_count - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
    
    def query_data(
        self,
        updated_since: Optional[datetime] = None,
        updated_field: str = "updated_at",
        limit: int = 1000,
        offset: int = 0,
        where_clause: Optional[str] = None,
        select_fields: Optional[str] = None,
        order_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query data from Socrata dataset.
        
        Args:
            updated_since: Filter records updated since this datetime
            updated_field: Field name for date filtering
            limit: Number of records per page (max 50000)
            offset: Starting offset for pagination
            where_clause: Custom WHERE clause for filtering (SoQL syntax)
            select_fields: Comma-separated list of fields to return
            order_by: ORDER BY clause for sorting
            
        Returns:
            List of records
        """
        params = {
            '$limit': min(limit, 50000),  # Socrata max limit
            '$offset': offset
        }
        
        # Build WHERE clause using SoQL syntax
        where_parts = []
        if updated_since:
            # Socrata expects ISO 8601 format
            iso_date = updated_since.strftime('%Y-%m-%dT%H:%M:%S')
            where_parts.append(f"{updated_field} >= '{iso_date}'")
        
        if where_clause:
            where_parts.append(where_clause)
        
        if where_parts:
            params['$where'] = " AND ".join(where_parts)
        
        if select_fields:
            params['$select'] = select_fields
        
        if order_by:
            params['$order'] = order_by
        elif updated_field:
            params['$order'] = f"{updated_field} ASC"
        
        logger.info(f"Querying Socrata: {self.base_url} with params: {params}")
        return self._make_request(self.base_url, params)
    
    def get_all_data(
        self,
        updated_since: Optional[datetime] = None,
        updated_field: str = "updated_at",
        page_size: int = 1000,
        max_records: Optional[int] = None
    ) -> Iterator[Dict[str, Any]]:
        """
        Generator that yields all records with automatic pagination.
        
        Args:
            updated_since: Filter records updated since this datetime
            updated_field: Field name for date filtering
            page_size: Number of records per page
            max_records: Maximum total records to fetch (None for unlimited)
            
        Yields:
            Individual records with normalized structure
        """
        offset = 0
        total_fetched = 0
        
        while True:
            try:
                records = self.query_data(
                    updated_since=updated_since,
                    updated_field=updated_field,
                    limit=page_size,
                    offset=offset,
                    order_by=f"{updated_field} ASC"
                )
                
                if not records:
                    break
                
                for record in records:
                    if max_records and total_fetched >= max_records:
                        return
                    
                    yield self._normalize_record(record)
                    total_fetched += 1
                
                # Check if we've reached the end
                if len(records) < page_size:
                    break
                
                offset += page_size
                logger.info(f"Fetched {total_fetched} records so far...")
                
            except Exception as e:
                logger.error(f"Error fetching records at offset {offset}: {e}")
                break
        
        logger.info(f"Total records fetched: {total_fetched}")
    
    def _normalize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Socrata record to standard format.
        
        Args:
            record: Raw Socrata record
            
        Returns:
            Normalized record with standard field names
        """
        normalized = {
            'raw_data': record,
            'source_type': 'socrata'
        }
        
        # Copy all fields to normalized record
        for key, value in record.items():
            normalized_key = key.lower().replace(' ', '_')
            
            # Handle date/datetime fields
            if 'date' in normalized_key or 'time' in normalized_key:
                normalized[normalized_key] = self._parse_date(value)
            # Handle coordinate fields
            elif normalized_key in ['latitude', 'lat', 'y']:
                normalized['latitude'] = self._parse_number(value)
            elif normalized_key in ['longitude', 'lon', 'lng', 'x']:
                normalized['longitude'] = self._parse_number(value)
            # Handle location fields (Socrata often has combined location)
            elif normalized_key == 'location':
                if isinstance(value, dict):
                    if 'latitude' in value:
                        normalized['latitude'] = self._parse_number(value['latitude'])
                    if 'longitude' in value:
                        normalized['longitude'] = self._parse_number(value['longitude'])
                normalized[normalized_key] = value
            # Handle numeric fields
            elif self._looks_like_number(value):
                normalized[normalized_key] = self._parse_number(value)
            else:
                normalized[normalized_key] = value
        
        return normalized
    
    def _parse_date(self, value: Any) -> Optional[datetime]:
        """Parse various date formats from Socrata."""
        if not value or value in ['', 'null', 'NULL']:
            return None
        
        if isinstance(value, datetime):
            return value
        
        if not isinstance(value, str):
            return None
        
        # Common Socrata date formats
        date_formats = [
            '%Y-%m-%dT%H:%M:%S.%f',  # ISO 8601 with microseconds
            '%Y-%m-%dT%H:%M:%S',     # ISO 8601
            '%Y-%m-%d %H:%M:%S',     # Standard datetime
            '%Y-%m-%d',              # Date only
            '%m/%d/%Y',              # US format
            '%m/%d/%Y %H:%M:%S',     # US format with time
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {value}")
        return None
    
    def _parse_number(self, value: Any) -> Optional[float]:
        """Parse numeric values from Socrata."""
        if value is None or value in ['', 'null', 'NULL']:
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Remove common formatting
            clean_value = value.replace(',', '').replace('$', '').strip()
            try:
                return float(clean_value)
            except ValueError:
                return None
        
        return None
    
    def _looks_like_number(self, value: Any) -> bool:
        """Check if a value looks like it should be a number."""
        if isinstance(value, (int, float)):
            return True
        
        if isinstance(value, str):
            # Remove common formatting and check if it's a number
            clean_value = value.replace(',', '').replace('$', '').strip()
            try:
                float(clean_value)
                return True
            except ValueError:
                return False
        
        return False
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the Socrata dataset.
        
        Returns:
            Dataset metadata
        """
        # Socrata metadata is available by replacing .json with .json?$limit=0
        metadata_url = self.base_url.replace('.json', '.json')
        params = {'$limit': 0}
        
        try:
            response = self.session.get(metadata_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            # Get headers which contain metadata
            metadata = {
                'last_modified': response.headers.get('Last-Modified'),
                'content_type': response.headers.get('Content-Type'),
                'rate_limit_remaining': response.headers.get('X-RateLimit-Remaining'),
                'rate_limit_limit': response.headers.get('X-RateLimit-Limit'),
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to get metadata: {e}")
            return {}
    
    def test_connection(self) -> bool:
        """
        Test if the Socrata endpoint is accessible.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to fetch just one record
            records = self.query_data(limit=1)
            return isinstance(records, list)
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False


def create_socrata_connector(source_config: Dict[str, Any]) -> SocrataConnector:
    """
    Factory function to create Socrata connector from source configuration.
    
    Args:
        source_config: Source configuration from sources_tx.yaml
        
    Returns:
        Configured Socrata connector instance
    """
    endpoint = source_config.get('endpoint')
    if not endpoint:
        raise ValueError("Socrata endpoint URL is required")
    
    app_token = source_config.get('app_token')
    timeout = source_config.get('timeout', 30)
    retry_count = source_config.get('retry_count', 3)
    
    return SocrataConnector(
        base_url=endpoint,
        app_token=app_token,
        timeout=timeout,
        retry_count=retry_count
    )


# Example usage and testing
if __name__ == "__main__":
    # Example configuration for Dallas open data
    test_config = {
        'endpoint': 'https://www.dallasopendata.com/resource/building-permits.json',
        'updated_field': 'issue_date'
    }
    
    connector = create_socrata_connector(test_config)
    
    # Test connection
    if connector.test_connection():
        print("✓ Connection successful")
        
        # Get metadata
        metadata = connector.get_metadata()
        print(f"Metadata: {metadata}")
        
        # Test querying recent data (last 30 days)
        since_date = datetime.now() - timedelta(days=30)
        print(f"\nTesting query for records since {since_date}")
        
        count = 0
        for record in connector.get_all_data(
            updated_since=since_date,
            updated_field=test_config['updated_field'],
            max_records=5
        ):
            count += 1
            print(f"Record {count}: {list(record.keys())}")
        
        print(f"✓ Successfully fetched {count} test records")
    else:
        print("✗ Connection failed")