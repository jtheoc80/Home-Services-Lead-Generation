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
from typing import Dict, List, Optional, Any, Iterator, Union
from urllib.parse import urljoin, urlencode
import time
import chardet

logger = logging.getLogger(__name__)


class CSVHTTPConnector:
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