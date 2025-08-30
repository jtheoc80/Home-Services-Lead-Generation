"""
Socrata adapter for jurisdiction-based permit scraping.
"""

import logging
import time
from typing import List, Optional, Dict, Any
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..config_loader import Jurisdiction
from ..models.permit import PermitRecord

logger = logging.getLogger(__name__)


class SocrataAdapter:
    """Adapter for Socrata Open Data permit data sources."""
    
    # Rate limiting: maximum 5 requests per second
    MAX_REQUESTS_PER_SECOND = 5
    MIN_REQUEST_INTERVAL = 1.0 / MAX_REQUESTS_PER_SECOND  # 0.2 seconds
    
    def __init__(self, jurisdiction: Jurisdiction, max_retries: int = 3):
        """Initialize Socrata adapter."""
        self.jurisdiction = jurisdiction
        self.config = jurisdiction.source_config
        self.max_retries = max_retries
        
        # Extract Socrata configuration
        self.base_url = self.config.get('url')
        if not self.base_url:
            raise ValueError(f"No URL found in config for {jurisdiction.name}")
        
        self.date_field = self.config['date_field']
        self.field_map = self.config.get('field_map', {})
        
        # Track last request time for rate limiting
        self._last_request_time = 0
        
        # Create session with retry strategy
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry strategy for Socrata APIs."""
        session = requests.Session()
        
        # Retry strategy for Socrata APIs
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set headers for Socrata APIs
        session.headers.update({
            'User-Agent': 'PermitLeadBot/1.0 (Texas Building Permits)',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate'
        })
        
        return session
    
    def _rate_limit(self):
        """Enforce rate limiting for Socrata APIs."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.MIN_REQUEST_INTERVAL:
            sleep_time = self.MIN_REQUEST_INTERVAL - elapsed
            logger.debug(f"Rate limiting Socrata API: sleeping for {sleep_time:.3f} seconds")
            time.sleep(sleep_time)
        self._last_request_time = time.time()
    
    def scrape_permits(self, since: datetime, limit: Optional[int] = None) -> List[PermitRecord]:
        """
        Scrape permits from Socrata API.
        
        Args:
            since: Only return records updated since this timestamp
            limit: Maximum number of records to return
            
        Returns:
            List of PermitRecord objects
        """
        logger.info(f"Scraping {self.jurisdiction.name} permits since {since}")
        
        permits = []
        total_fetched = 0
        offset = 0
        batch_size = 1000  # Socrata recommended batch size
        
        if limit is None:
            limit = 10000  # Default limit
        
        while total_fetched < limit:
            # Apply rate limiting
            self._rate_limit()
            
            # Build SoQL parameters
            params = {
                "$select": "*",
                "$limit": min(batch_size, limit - total_fetched),
                "$offset": offset,
                "$order": f"{self.date_field} DESC"
            }
            
            # Add date filter if provided
            if since:
                since_iso = since.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
                params["$where"] = f"{self.date_field} >= '{since_iso}'"
            
            logger.debug(f"Fetching batch with params: {params}")
            
            try:
                response = self.session.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                
                records = response.json()
                if not records:
                    logger.info("No more records to fetch")
                    break
                
                logger.debug(f"Fetched {len(records)} records in this batch")
                
                # Parse records into PermitRecord objects
                batch_permits = []
                for record in records:
                    permit = self._parse_record(record)
                    if permit:
                        batch_permits.append(permit)
                
                permits.extend(batch_permits)
                total_fetched += len(records)
                offset += len(records)
                
                # If we got fewer records than requested, we're done
                if len(records) < batch_size:
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching data from Socrata API: {e}")
                if self.max_retries > 0:
                    logger.info("Retrying after error...")
                    time.sleep(2)
                    continue
                else:
                    raise
        
        logger.info(f"Scraped {len(permits)} permits from {self.jurisdiction.name}")
        return permits
    
    def _parse_record(self, record: Dict[str, Any]) -> Optional[PermitRecord]:
        """Parse a Socrata record into a PermitRecord."""
        try:
            # Map fields according to configuration
            mapped_data = {}
            
            for target_field, source_field in self.field_map.items():
                if source_field in record:
                    mapped_data[target_field] = record[source_field]
            
            # Ensure we have required fields with fallbacks
            permit_data = {
                'permit_id': mapped_data.get('permit_id') or record.get('permit_number') or record.get('id'),
                'address': mapped_data.get('address') or record.get('address') or '',
                'description': mapped_data.get('description') or record.get('work_description') or '',
                'applicant': mapped_data.get('applicant') or record.get('contractor_name') or '',
                'value': self._parse_value(mapped_data.get('value') or record.get('estimated_cost')),
                'work_class': mapped_data.get('work_class') or record.get('permit_type') or '',
                'issue_date': self._parse_date(mapped_data.get('issue_date') or record.get(self.date_field)),
                'source': f"socrata_{self.jurisdiction.slug}",
                'source_url': self.base_url,
                'raw_data': record
            }
            
            # Remove None values
            permit_data = {k: v for k, v in permit_data.items() if v is not None}
            
            return PermitRecord(**permit_data)
            
        except Exception as e:
            logger.warning(f"Failed to parse record: {e}")
            logger.debug(f"Problematic record: {record}")
            return None
    
    def _parse_value(self, value_str: Any) -> Optional[float]:
        """Parse permit value from string."""
        if value_str is None:
            return None
        
        try:
            # Handle various value formats
            if isinstance(value_str, (int, float)):
                return float(value_str)
            
            value_str = str(value_str).strip()
            if not value_str:
                return None
            
            # Remove common prefixes and characters
            value_str = value_str.replace('$', '').replace(',', '').replace(' ', '')
            
            if value_str.lower() in ['n/a', 'na', 'none', 'null', '']:
                return None
            
            return float(value_str)
        except (ValueError, TypeError):
            return None
    
    def _parse_date(self, date_str: Any) -> Optional[datetime]:
        """Parse date from various formats."""
        if date_str is None:
            return None
        
        try:
            if isinstance(date_str, datetime):
                return date_str
            
            date_str = str(date_str).strip()
            if not date_str:
                return None
            
            # Try common date formats
            for fmt in [
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
                "%m/%d/%Y %H:%M:%S",
                "%m/%d/%Y"
            ]:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            logger.warning(f"Could not parse date: {date_str}")
            return None
            
        except Exception as e:
            logger.warning(f"Error parsing date {date_str}: {e}")
            return None