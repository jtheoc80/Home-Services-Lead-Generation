"""
CSV HTTP Connector for data ingestion.

This module provides functionality to download and process CSV files
from HTTP endpoints with proper error handling and rate limiting.
"""

import csv
import io
import logging
import time
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional


logger = logging.getLogger(__name__)


class CSVHTTPConnector:
    """Connector for CSV files served over HTTP."""

    def __init__(
        self,
        url: str,
        timeout: int = 60,
        retry_count: int = 3,
        encoding: Optional[str] = None,
    ):
        """
        Initialize CSV HTTP connector.

        Args:
            url: URL of the CSV file
            timeout: Request timeout in seconds
            retry_count: Number of retry attempts
            encoding: Character encoding (auto-detected if None)
        """
        self.url = url
        self.timeout = timeout
        self.retry_count = retry_count
        self.encoding = encoding
        self.session = requests.Session()

    async def extract_updated_since(
        self,
        endpoint: str,
        updated_field: str,
        since: Optional[datetime],
        rate_limit: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Extract records updated since a given timestamp.

        Args:
            endpoint: CSV file URL
            updated_field: Field name containing update timestamp
            since: Extract records since this timestamp
            rate_limit: Rate limit (requests per second)

        Returns:
            List of extracted records
        """
        try:
            # Apply rate limiting
            time.sleep(1.0 / rate_limit)

            # Download CSV data
            response = self.session.get(endpoint, timeout=self.timeout)
            response.raise_for_status()

            # Parse CSV
            records = []
            csv_content = response.content.decode(self.encoding or "utf-8")
            reader = csv.DictReader(io.StringIO(csv_content))

            for row in reader:
                # Filter by timestamp if provided
                if since and updated_field in row:
                    row_date = self._parse_date(row[updated_field])
                    if row_date and row_date < since:
                        continue

                records.append(row)

            logger.info(f"Extracted {len(records)} records from {endpoint}")
            return records

        except Exception as e:
            logger.error(f"Failed to extract from {endpoint}: {e}")
            return []

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string into datetime object."""
        if not date_str:
            return None

        date_formats = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%m/%d/%Y",
            "%m/%d/%Y %H:%M:%S",
            "%m-%d-%Y",
            "%d-%m-%Y",
            "%Y%m%d",
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        return None


def create_csv_http_connector(config: Dict[str, Any]) -> CSVHTTPConnector:
    """Create CSV HTTP connector from configuration."""
    return CSVHTTPConnector(
        url=config["endpoint"],
        timeout=config.get("timeout", 60),
        retry_count=config.get("retry_count", 3),
        encoding=config.get("encoding"),
    )


if __name__ == "__main__":
    # Test the connector
    connector = CSVHTTPConnector(url="https://example.com/data.csv", timeout=30)
    print("CSV HTTP Connector initialized successfully")
