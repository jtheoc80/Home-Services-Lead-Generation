"""Enhanced Socrata Open Data connector with rate limiting, pagination, and incremental updates."""

import logging
import time
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Iterator, Tuple
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class SocrataConnector:
    """Enhanced Socrata Open Data connector with advanced capabilities."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Socrata connector with configuration."""
        self.config = config
        self.domain = config["domain"]
        self.dataset_id = config["dataset_id"]
        self.updated_field = config.get("updated_field")
        self.primary_key = config.get("primary_key")
        self.rate_limit = config.get("rate_limit", 5)  # requests per second
        self.pagination_config = config.get("pagination", {})
        self.page_size = self.pagination_config.get("page_size", 1000)
        
        # Build base URL
        self.base_url = f"https://{self.domain}/resource/{self.dataset_id}.json"
        
        # Rate limiting
        self._last_request_time = 0
        self._request_interval = 1.0 / self.rate_limit
        
        # HTTP session with retry strategy
        self.session = self._create_session()
        
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
        
        # Set user agent
        session.headers.update({
            "User-Agent": "TexasDataIngest/1.0 (LeadLedgerPro)",
            "Accept": "application/json"
        })
        
        return session
        
    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._request_interval:
            time.sleep(self._request_interval - elapsed)
        self._last_request_time = time.time()
        
    def _make_request(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Make rate-limited request to Socrata API."""
        self._rate_limit()
        
        try:
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Handle Socrata error responses
            if isinstance(data, dict) and data.get("error"):
                raise ValueError(f"Socrata API error: {data.get('message', str(data))}")
                
            return data if isinstance(data, list) else []
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise
            
    def get_record_count(self, where_clause: Optional[str] = None) -> int:
        """Get total count of records matching criteria."""
        count_url = f"https://{self.domain}/resource/{self.dataset_id}.json"
        params = {"$select": "count(*)"}
        
        if where_clause:
            params["$where"] = where_clause
            
        try:
            data = self._make_request(params)
            if data and len(data) > 0:
                return int(data[0].get("count", 0))
            return 0
        except Exception as e:
            logger.warning(f"Could not get record count: {e}")
            return -1  # Unknown count
            
    def get_updated_since(self, since_date: datetime) -> Iterator[Dict[str, Any]]:
        """Get records updated since specified date."""
        if not self.updated_field:
            raise ValueError("updated_field not configured for incremental updates")
            
        # Format date for SoQL query (ISO 8601)
        date_str = since_date.strftime("%Y-%m-%dT%H:%M:%S.000")
        where_clause = f"{self.updated_field} >= '{date_str}'"
        
        logger.info(f"Fetching records updated since {date_str}")
        
        yield from self.get_paginated_records(where_clause)
        
    def get_paginated_records(self, where_clause: Optional[str] = None) -> Iterator[Dict[str, Any]]:
        """Get records with pagination support."""
        offset = 0
        total_count = self.get_record_count(where_clause)
        
        if total_count > 0:
            logger.info(f"Total records to fetch: {total_count}")
        else:
            logger.info("Fetching records (count unknown)")
        
        while True:
            params = {
                "$limit": self.page_size,
                "$offset": offset,
                "$order": self.primary_key if self.primary_key else ":id"
            }
            
            if where_clause:
                params["$where"] = where_clause
                
            logger.info(f"Fetching batch {offset // self.page_size + 1}, "
                       f"offset {offset}")
            
            records = self._make_request(params)
            
            if not records:
                logger.info("No more records to fetch")
                break
                
            for record in records:
                yield self._normalize_record(record)
                
            offset += len(records)
            
            # Break if we got fewer records than requested (end of data)
            if len(records) < self.page_size:
                break
                
    def get_records_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime,
        date_field: Optional[str] = None
    ) -> Iterator[Dict[str, Any]]:
        """Get records within a specific date range."""
        field = date_field or self.updated_field
        if not field:
            raise ValueError("No date field specified for date range query")
            
        start_str = start_date.strftime("%Y-%m-%dT%H:%M:%S.000")
        end_str = end_date.strftime("%Y-%m-%dT%H:%M:%S.000")
        
        where_clause = f"{field} >= '{start_str}' AND {field} <= '{end_str}'"
        
        logger.info(f"Fetching records from {start_str} to {end_str}")
        
        yield from self.get_paginated_records(where_clause)
        
    def _normalize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Socrata record to standard format."""
        # Apply field mappings if configured
        mappings = self.config.get("mappings", {})
        normalized = {}
        
        if mappings:
            for standard_field, source_field in mappings.items():
                # Handle composite fields (comma-separated)
                if "," in source_field:
                    # Concatenate multiple source fields
                    parts = [
                        str(record.get(field.strip(), "")).strip() 
                        for field in source_field.split(",")
                    ]
                    normalized[standard_field] = " ".join(filter(None, parts))
                else:
                    normalized[standard_field] = record.get(source_field)
        else:
            normalized = record.copy()
            
        # Handle common Socrata location fields
        if "location" in record and isinstance(record["location"], dict):
            location = record["location"]
            if "latitude" in location:
                normalized["latitude"] = float(location["latitude"])
            if "longitude" in location:
                normalized["longitude"] = float(location["longitude"])
                
        # Handle geocoded location
        if ":@computed_region" in record:
            # Socrata often includes computed geographic regions
            pass
            
        # Add metadata
        normalized["_source"] = self.config.get("name", "socrata")
        normalized["_category"] = self.config.get("category", "unknown")
        normalized["_jurisdiction"] = self.config.get("jurisdiction", "unknown")
        normalized["_ingested_at"] = datetime.utcnow().isoformat()
        
        return normalized
        
    def test_connection(self) -> Tuple[bool, str]:
        """Test connection to Socrata dataset."""
        try:
            params = {"$limit": 1}
            records = self._make_request(params)
            
            if isinstance(records, list):
                count = self.get_record_count()
                return True, f"Connection successful. Dataset has {count} records"
            else:
                return False, "Unexpected response format"
                
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
            
    def get_dataset_metadata(self) -> Dict[str, Any]:
        """Get dataset metadata from Socrata."""
        try:
            metadata_url = f"https://{self.domain}/api/views/{self.dataset_id}.json"
            
            response = self.session.get(metadata_url, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get dataset metadata: {e}")
            return {}
            
    def get_field_info(self) -> List[Dict[str, Any]]:
        """Get field information from the dataset."""
        metadata = self.get_dataset_metadata()
        return metadata.get("columns", [])
        
    def search_records(self, query: str) -> Iterator[Dict[str, Any]]:
        """Search records using Socrata's full-text search."""
        params = {
            "$q": query,
            "$limit": self.page_size,
            "$offset": 0
        }
        
        offset = 0
        while True:
            params["$offset"] = offset
            records = self._make_request(params)
            
            if not records:
                break
                
            for record in records:
                yield self._normalize_record(record)
                
            offset += len(records)
            
            if len(records) < self.page_size:
                break


def create_socrata_connector(config: Dict[str, Any]) -> SocrataConnector:
    """Factory function to create Socrata connector."""
    return SocrataConnector(config)


# Example usage
if __name__ == "__main__":
    # Example configuration for Dallas permits
    config = {
        "name": "Dallas Building Permits",
        "domain": "www.dallasopendata.com",
        "dataset_id": "e7gq-4sah",
        "updated_field": "issued_date",
        "primary_key": "permit_number",
        "category": "permits",
        "jurisdiction": "dallas",
        "rate_limit": 5,
        "pagination": {"page_size": 1000},
        "mappings": {
            "permit_number": "permit_number",
            "issued_date": "issued_date",
            "address": "address",
            "description": "work_description",
            "status": "permit_status",
            "work_class": "permit_type_desc",
            "category": "permit_class",
            "value": "estimated_cost",
            "applicant": "contractor_name"
        }
    }
    
    connector = create_socrata_connector(config)
    
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