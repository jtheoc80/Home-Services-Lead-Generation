
"""CSV HTTP connector for downloading and processing CSV data from web sources."""

import logging
import time

"""
CSV HTTP connector for ingesting permit data from CSV endpoints.

This module provides functionality to download and parse CSV files from HTTP endpoints,
handle various CSV formats, and normalize data for ingestion.
"""

import logging

import requests
import csv
import io
from datetime import datetime, timedelta

from typing import Dict, List, Optional, Any, Iterator, Tuple, Union
from urllib.parse import urlencode, urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from typing import Dict, List, Optional, Any, Iterator, Union
from urllib.parse import urljoin, urlencode
import time
import chardet


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

    """Connector for CSV files served over HTTP."""
    
    def __init__(self, url: str, timeout: int = 60, retry_count: int = 3, encoding: Optional[str] = None):
        """
        Initialize CSV HTTP connector.
        
        Args:
            url: URL of the CSV file
            timeout: Request timeout in seconds (longer for large files)
            retry_count: Number of retry attempts for failed requests
            encoding: Character encoding (auto-detected if None)
        """
        self.url = url
        self.timeout = timeout
        self.retry_count = retry_count
        self.encoding = encoding
        self.session = requests.Session()
        
        # Set common headers
        self.session.headers.update({
            'User-Agent': 'HomeServicesLeadGen/1.0 (Texas Permits Ingestion)',
            'Accept': 'text/csv, application/csv, text/plain'
        })
    
    def _download_csv(self) -> str:
        """
        Download CSV content with retry logic.
        
        Returns:
            CSV content as string
            
        Raises:
            Exception: If all retry attempts fail
        """
        for attempt in range(self.retry_count):
            try:
                logger.info(f"Downloading CSV from: {self.url}")
                response = self.session.get(self.url, timeout=self.timeout, stream=True)
                response.raise_for_status()
                
                # Download content in chunks for large files
                content_bytes = b''
                for chunk in response.iter_content(chunk_size=8192):
                    content_bytes += chunk
                
                # Detect encoding if not specified
                encoding = self.encoding
                if not encoding:
                    detected = chardet.detect(content_bytes[:10000])  # Check first 10KB
                    encoding = detected.get('encoding', 'utf-8')
                    confidence = detected.get('confidence', 0)
                    logger.info(f"Detected encoding: {encoding} (confidence: {confidence:.2f})")
                
                # Decode content
                try:
                    content = content_bytes.decode(encoding)
                except UnicodeDecodeError:
                    # Fallback to utf-8 with error handling
                    logger.warning(f"Failed to decode with {encoding}, falling back to utf-8")
                    content = content_bytes.decode('utf-8', errors='replace')
                
                logger.info(f"Downloaded {len(content)} characters")
                return content
                
            except Exception as e:
                logger.warning(f"Download attempt {attempt + 1} failed: {e}")
                if attempt == self.retry_count - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
    
    def parse_csv(
        self,
        content: str,
        delimiter: str = ',',
        quotechar: str = '"',
        skip_rows: int = 0,
        max_rows: Optional[int] = None
    ) -> Iterator[Dict[str, str]]:
        """
        Parse CSV content and yield rows as dictionaries.
        
        Args:
            content: CSV content as string
            delimiter: Field delimiter character
            quotechar: Quote character for field values
            skip_rows: Number of rows to skip at the beginning
            max_rows: Maximum number of data rows to process
            
        Yields:
            Dictionary for each row with column headers as keys
        """
        # Create CSV reader from string content
        csv_file = io.StringIO(content)
        
        # Skip initial rows if needed
        for _ in range(skip_rows):
            try:
                next(csv_file)
            except StopIteration:
                return
        
        try:
            # Detect dialect
            sample = content[:1024]
            sniffer = csv.Sniffer()
            
            try:
                dialect = sniffer.sniff(sample, delimiters=f'{delimiter}\t;|')
                logger.info(f"Detected CSV dialect: delimiter='{dialect.delimiter}', quotechar='{dialect.quotechar}'")
            except csv.Error:
                # Use manual settings if detection fails
                class CustomDialect(csv.excel):
                    delimiter = delimiter
                    quotechar = quotechar
                dialect = CustomDialect
                logger.info(f"Using manual CSV settings: delimiter='{delimiter}', quotechar='{quotechar}'")
            
            # Create DictReader
            reader = csv.DictReader(csv_file, dialect=dialect)
            
            row_count = 0
            for row in reader:
                if max_rows and row_count >= max_rows:
                    break
                
                # Clean up the row data
                cleaned_row = {}
                for key, value in row.items():
                    if key is None:
                        continue  # Skip columns without headers
                    
                    # Clean column name
                    clean_key = str(key).strip()
                    
                    # Clean value
                    clean_value = str(value).strip() if value is not None else ''
                    
                    cleaned_row[clean_key] = clean_value
                
                yield cleaned_row
                row_count += 1
            
            logger.info(f"Parsed {row_count} rows from CSV")
            
        except csv.Error as e:
            logger.error(f"CSV parsing error: {e}")
            raise
    
    def get_all_data(
        self,
        updated_since: Optional[datetime] = None,
        updated_field: Optional[str] = None,
        csv_params: Optional[Dict[str, Any]] = None,
        max_records: Optional[int] = None
    ) -> Iterator[Dict[str, Any]]:
        """
        Download and parse CSV data with optional date filtering.
        
        Args:
            updated_since: Filter records updated since this datetime
            updated_field: Field name for date filtering (applied post-download)
            csv_params: Additional CSV parsing parameters
            max_records: Maximum number of records to process
            
        Yields:
            Individual records with normalized structure
        """
        # Set default CSV parameters
        params = {
            'delimiter': ',',
            'quotechar': '"',
            'skip_rows': 0
        }
        if csv_params:
            params.update(csv_params)
        
        # Download CSV content
        content = self._download_csv()
        
        record_count = 0
        filtered_count = 0
        
        # Parse and yield records
        for row in self.parse_csv(content, **params):
            if max_records and record_count >= max_records:
                break
            
            # Apply date filtering if specified
            if updated_since and updated_field:
                if not self._is_record_updated_since(row, updated_field, updated_since):
                    filtered_count += 1
                    continue
            
            yield self._normalize_record(row)
            record_count += 1
        
        logger.info(f"Processed {record_count} records (filtered out {filtered_count})")
    
    def _is_record_updated_since(self, record: Dict[str, str], updated_field: str, updated_since: datetime) -> bool:
        """Check if a record was updated since the specified date."""
        if updated_field not in record:
            logger.warning(f"Updated field '{updated_field}' not found in record")
            return True  # Include record if field is missing
        
        field_value = record[updated_field]
        if not field_value:
            return True  # Include record if field is empty
        
        # Try to parse the date
        record_date = self._parse_date(field_value)
        if record_date is None:
            logger.warning(f"Could not parse date from field '{updated_field}': {field_value}")
            return True  # Include record if date parsing fails
        
        return record_date >= updated_since
    
    def _normalize_record(self, record: Dict[str, str]) -> Dict[str, Any]:
        """
        Normalize CSV record to standard format.
        
        Args:
            record: Raw CSV record as string dictionary
            
        Returns:
            Normalized record with proper data types
        """
        normalized = {
            'raw_data': record,
            'source_type': 'csv_http'
        }
        
        # Process each field
        for key, value in record.items():
            if not key or not value:
                continue
            
            normalized_key = key.lower().replace(' ', '_').replace('-', '_')
            
            # Handle different field types
            if 'date' in normalized_key or 'time' in normalized_key:
                normalized[normalized_key] = self._parse_date(value)
            elif normalized_key in ['latitude', 'lat', 'y']:
                normalized['latitude'] = self._parse_number(value)
            elif normalized_key in ['longitude', 'lon', 'lng', 'x']:
                normalized['longitude'] = self._parse_number(value)
            elif self._looks_like_number(value):
                normalized[normalized_key] = self._parse_number(value)
            elif self._looks_like_boolean(value):
                normalized[normalized_key] = self._parse_boolean(value)
            else:
                normalized[normalized_key] = value
        
        return normalized
    
    def _parse_date(self, value: str) -> Optional[datetime]:
        """Parse various date formats from CSV."""
        if not value or value.lower() in ['', 'null', 'na', 'n/a']:
            return None
        
        # Common CSV date formats
        date_formats = [
            '%Y-%m-%d %H:%M:%S',     # Standard datetime
            '%Y-%m-%d',              # Date only
            '%m/%d/%Y',              # US format
            '%m/%d/%Y %H:%M:%S',     # US format with time
            '%m/%d/%y',              # US format 2-digit year
            '%d/%m/%Y',              # European format
            '%Y-%m-%dT%H:%M:%S',     # ISO format
            '%Y-%m-%dT%H:%M:%S.%f',  # ISO with microseconds

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

                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {value}")
        return None
    
    def _parse_number(self, value: str) -> Optional[float]:
        """Parse numeric values from CSV."""
        if not value or value.lower() in ['', 'null', 'na', 'n/a']:
            return None
        
        # Remove common formatting
        clean_value = value.replace(',', '').replace('$', '').replace('%', '').strip()
        
        try:
            return float(clean_value)
        except ValueError:
            return None
    
    def _parse_boolean(self, value: str) -> Optional[bool]:
        """Parse boolean values from CSV."""
        if not value:
            return None
        
        value_lower = value.lower().strip()
        
        if value_lower in ['true', 't', 'yes', 'y', '1']:
            return True
        elif value_lower in ['false', 'f', 'no', 'n', '0']:
            return False
        else:
            return None
    
    def _looks_like_number(self, value: str) -> bool:
        """Check if a value looks like it should be a number."""
        if not value:
            return False
        
        # Remove common formatting and check if it's a number
        clean_value = value.replace(',', '').replace('$', '').replace('%', '').strip()
        
        try:
            float(clean_value)
            return True
        except ValueError:
            return False
    
    def _looks_like_boolean(self, value: str) -> bool:
        """Check if a value looks like a boolean."""
        if not value:
            return False
        
        value_lower = value.lower().strip()
        boolean_values = ['true', 'false', 't', 'f', 'yes', 'no', 'y', 'n', '1', '0']
        return value_lower in boolean_values
    
    def get_sample_data(self, num_rows: int = 5) -> List[Dict[str, str]]:
        """
        Get a small sample of data for testing and field discovery.
        
        Args:
            num_rows: Number of rows to sample
            
        Returns:
            List of sample records
        """
        content = self._download_csv()
        
        sample_records = []
        for i, record in enumerate(self.parse_csv(content)):
            if i >= num_rows:
                break
            sample_records.append(record)
        
        return sample_records
    
    def test_connection(self) -> bool:
        """
        Test if the CSV endpoint is accessible and parseable.
        
        Returns:
            True if connection and parsing successful, False otherwise
        """
        try:
            sample = self.get_sample_data(num_rows=1)
            return len(sample) > 0
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False


def create_csv_http_connector(source_config: Dict[str, Any]) -> CSVHTTPConnector:
    """
    Factory function to create CSV HTTP connector from source configuration.
    
    Args:
        source_config: Source configuration from sources_tx.yaml
        
    Returns:
        Configured CSV HTTP connector instance
    """
    endpoint = source_config.get('endpoint')
    if not endpoint:
        raise ValueError("CSV HTTP endpoint URL is required")
    
    timeout = source_config.get('timeout', 60)
    retry_count = source_config.get('retry_count', 3)
    encoding = source_config.get('encoding')
    
    return CSVHTTPConnector(
        url=endpoint,
        timeout=timeout,
        retry_count=retry_count,
        encoding=encoding
    )


# Example usage and testing
if __name__ == "__main__":
    # Example configuration for a CSV endpoint
    test_config = {
        'endpoint': 'https://example.com/permits.csv',
        'updated_field': 'issue_date'
    }
    
    # For testing, we'll use a publicly available CSV
    test_url = "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.csv"
    
    connector = CSVHTTPConnector(test_url)
    
    # Test connection
    if connector.test_connection():
        print("✓ Connection successful")
        
        # Get sample data
        sample = connector.get_sample_data(num_rows=3)
        print(f"Sample data ({len(sample)} rows):")
        for i, record in enumerate(sample):
            print(f"  Row {i+1}: {list(record.keys())}")
        
        # Test data processing
        count = 0
        for record in connector.get_all_data(max_records=5):
            count += 1
            print(f"Processed record {count}: {list(record.keys())}")
        
        print(f"✓ Successfully processed {count} test records")
    else:
        print("✗ Connection failed")

