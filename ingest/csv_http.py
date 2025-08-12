"""CSV HTTP connector for downloading and processing CSV data from web sources."""

import logging
import time
import requests
import csv
import io
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Iterator, Tuple, Union
from urllib.parse import urlencode, urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class CSVHTTPConnector:
    """CSV HTTP connector with rate limiting, pagination, and incremental updates."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize CSV HTTP connector with configuration."""
        self.config = config
        self.url = config["url"]
        self.updated_field = config.get("updated_field")
        self.primary_key = config.get("primary_key")
        self.rate_limit = config.get("rate_limit", 2)  # requests per second
        self.pagination_config = config.get("pagination", {})
        self.page_size = self.pagination_config.get("page_size", 1000)
        
        # CSV parsing options
        self.csv_options = config.get("csv_options", {
            "delimiter": ",",
            "quotechar": '"',
            "encoding": "utf-8"
        })
        
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
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set user agent
        session.headers.update({
            "User-Agent": "TexasDataIngest/1.0 (LeadLedgerPro)",
            "Accept": "text/csv, application/csv, text/plain"
        })
        
        return session
        
    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._request_interval:
            time.sleep(self._request_interval - elapsed)
        self._last_request_time = time.time()
        
    def _download_csv(self, url: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Download CSV content from URL."""
        self._rate_limit()
        
        try:
            response = self.session.get(url, params=params, timeout=60)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get("content-type", "").lower()
            if "csv" not in content_type and "text" not in content_type:
                logger.warning(f"Unexpected content type: {content_type}")
                
            return response.text
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download CSV: {e}")
            raise
            
    def _parse_csv_content(self, content: str) -> Iterator[Dict[str, Any]]:
        """Parse CSV content and yield records."""
        try:
            # Handle BOM if present
            if content.startswith('\ufeff'):
                content = content[1:]
                
            csv_reader = csv.DictReader(
                io.StringIO(content),
                delimiter=self.csv_options.get("delimiter", ","),
                quotechar=self.csv_options.get("quotechar", '"')
            )
            
            for row_num, row in enumerate(csv_reader, 1):
                try:
                    # Clean and normalize the row
                    cleaned_row = {k.strip(): v.strip() if v else None for k, v in row.items()}
                    yield self._normalize_record(cleaned_row)
                except Exception as e:
                    logger.warning(f"Error processing row {row_num}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to parse CSV content: {e}")
            raise
            
    def get_all_records(self) -> Iterator[Dict[str, Any]]:
        """Get all records from the CSV source."""
        logger.info(f"Downloading CSV from {self.url}")
        
        content = self._download_csv(self.url)
        
        if not content.strip():
            logger.warning("Empty CSV content received")
            return
            
        logger.info("Parsing CSV content")
        yield from self._parse_csv_content(content)
        
    def get_updated_since(self, since_date: datetime) -> Iterator[Dict[str, Any]]:
        """Get records updated since specified date."""
        if not self.updated_field:
            raise ValueError("updated_field not configured for incremental updates")
            
        logger.info(f"Fetching records updated since {since_date}")
        
        # For CSV sources, we typically need to download all data and filter
        for record in self.get_all_records():
            try:
                record_date = self._parse_date_field(record.get(self.updated_field))
                if record_date and record_date >= since_date:
                    yield record
            except Exception as e:
                logger.warning(f"Error parsing date for record: {e}")
                continue
                
    def get_paginated_records(
        self, 
        start_page: int = 0, 
        end_page: Optional[int] = None
    ) -> Iterator[Dict[str, Any]]:
        """Get records with pagination support (if URL supports it)."""
        pagination_method = self.pagination_config.get("method", "none")
        
        if pagination_method == "none":
            # No pagination, just return all records
            yield from self.get_all_records()
            return
            
        elif pagination_method == "offset":
            # Offset-based pagination
            offset = start_page * self.page_size
            while True:
                params = {
                    "offset": offset,
                    "limit": self.page_size
                }
                
                content = self._download_csv(self.url, params)
                records = list(self._parse_csv_content(content))
                
                if not records:
                    break
                    
                for record in records:
                    yield record
                    
                offset += len(records)
                
                if len(records) < self.page_size:
                    break
                    
                if end_page and (offset // self.page_size) >= end_page:
                    break
                    
        elif pagination_method == "date_range":
            # Date range pagination
            if not self.updated_field:
                raise ValueError("updated_field required for date_range pagination")
                
            # Split into daily chunks
            current_date = datetime.now() - timedelta(days=365)  # Default 1 year
            end_date = datetime.now()
            
            while current_date <= end_date:
                next_date = current_date + timedelta(days=1)
                
                params = {
                    "start_date": current_date.strftime("%Y-%m-%d"),
                    "end_date": next_date.strftime("%Y-%m-%d")
                }
                
                try:
                    content = self._download_csv(self.url, params)
                    yield from self._parse_csv_content(content)
                except Exception as e:
                    logger.warning(f"Failed to get data for {current_date}: {e}")
                    
                current_date = next_date
                
        elif pagination_method == "alphabetical":
            # Alphabetical pagination (for license data)
            letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            
            for letter in letters:
                params = {"search": letter, "limit": self.page_size}
                
                try:
                    content = self._download_csv(self.url, params)
                    yield from self._parse_csv_content(content)
                except Exception as e:
                    logger.warning(f"Failed to get data for letter {letter}: {e}")
                    
    def _parse_date_field(self, date_value: Any) -> Optional[datetime]:
        """Parse various date formats."""
        if not date_value:
            return None
            
        if isinstance(date_value, datetime):
            return date_value
            
        date_str = str(date_value).strip()
        if not date_str:
            return None
            
        # Common date formats
        date_formats = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%m/%d/%Y",
            "%m/%d/%Y %H:%M:%S",
            "%m-%d-%Y",
            "%d-%m-%Y",
            "%Y%m%d"
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
                
        logger.warning(f"Could not parse date: {date_value}")
        return None
        
    def _normalize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize CSV record to standard format."""
        # Apply field mappings if configured
        mappings = self.config.get("mappings", {})
        normalized = {}
        
        if mappings:
            for standard_field, source_field in mappings.items():
                normalized[standard_field] = record.get(source_field)
        else:
            normalized = record.copy()
            
        # Clean up common data issues
        for key, value in normalized.items():
            if isinstance(value, str):
                # Remove extra whitespace
                normalized[key] = value.strip()
                # Convert empty strings to None
                if not normalized[key]:
                    normalized[key] = None
                    
        # Add metadata
        normalized["_source"] = self.config.get("name", "csv_http")
        normalized["_category"] = self.config.get("category", "unknown")
        normalized["_jurisdiction"] = self.config.get("jurisdiction", "unknown")
        normalized["_ingested_at"] = datetime.utcnow().isoformat()
        
        return normalized
        
    def test_connection(self) -> Tuple[bool, str]:
        """Test connection to CSV source."""
        try:
            # Try to download first few bytes
            response = self.session.head(self.url, timeout=30)
            response.raise_for_status()
            
            content_length = response.headers.get("content-length")
            content_type = response.headers.get("content-type", "")
            
            message = f"Connection successful. Content-Type: {content_type}"
            if content_length:
                message += f", Size: {content_length} bytes"
                
            return True, message
            
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
            
    def get_sample_records(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get a sample of records for testing."""
        records = []
        try:
            for i, record in enumerate(self.get_all_records()):
                records.append(record)
                if i >= limit - 1:
                    break
        except Exception as e:
            logger.error(f"Failed to get sample records: {e}")
            
        return records


def create_csv_http_connector(config: Dict[str, Any]) -> CSVHTTPConnector:
    """Factory function to create CSV HTTP connector."""
    return CSVHTTPConnector(config)


# Example usage
if __name__ == "__main__":
    # Example configuration for TDLR contractor licenses
    config = {
        "name": "TDLR Contractor Licenses",
        "url": "https://www.tdlr.texas.gov/LicenseSearch/licfile.asp",
        "updated_field": "license_issue_date",
        "primary_key": "license_number",
        "category": "contractors",
        "jurisdiction": "texas-state",
        "rate_limit": 3,
        "pagination": {
            "method": "alphabetical",
            "page_size": 1000
        },
        "csv_options": {
            "delimiter": ",",
            "encoding": "utf-8"
        },
        "mappings": {
            "license_number": "license_number",
            "license_type": "license_type",
            "business_name": "business_name",
            "owner_name": "owner_name",
            "address": "business_address",
            "city": "business_city",
            "zip_code": "business_zip",
            "license_status": "license_status",
            "issue_date": "license_issue_date",
            "expiration_date": "license_expiration_date"
        }
    }
    
    connector = create_csv_http_connector(config)
    
    # Test connection
    success, message = connector.test_connection()
    print(f"Connection test: {message}")
    
    if success:
        # Get sample records
        sample_records = connector.get_sample_records(3)
        print(f"Retrieved {len(sample_records)} sample records")
        for i, record in enumerate(sample_records, 1):
            print(f"Record {i}: {record.get('license_number', 'N/A')} - {record.get('business_name', 'N/A')}")