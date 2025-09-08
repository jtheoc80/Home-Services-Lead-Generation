"""
Simple Socrata adapter that implements the SourceAdapter interface.
Used for Dallas and Austin permit data.
"""

import logging
import time
import json
import os
from typing import Optional, Dict, Any, Iterable
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .base import BaseAdapter

logger = logging.getLogger(__name__)


class SimpleSocrataAdapter(BaseAdapter):
    """Adapter for Socrata Open Data permit data sources."""
    
    # Rate limiting: maximum 5 requests per second
    MAX_REQUESTS_PER_SECOND = 5
    MIN_REQUEST_INTERVAL = 1.0 / MAX_REQUESTS_PER_SECOND  # 0.2 seconds
    
    def __init__(self, cfg: Dict[str, Any], session=None):
        super().__init__(cfg, session)
        
        # Socrata configuration  
        self.base_url = cfg.get('url')
        if not self.base_url:
            raise ValueError(f"No URL found in config for {self.name}")
        
        self.date_field = cfg.get('date_field', 'issued_date')
        self.field_map = cfg.get('field_map', {})
        self.max_retries = cfg.get('max_retries', 3)
        
        # Extract app token for X-App-Token header (required for Austin/San Antonio)
        self.app_token = cfg.get('app_token') or cfg.get('app_token_env')
        if self.app_token and self.app_token.startswith('${') and self.app_token.endswith('}'):
            # Handle environment variable format like ${AUSTIN_SODA_APP_TOKEN}
            env_var = self.app_token[2:-1]  # Remove ${ and }
            self.app_token = os.getenv(env_var)
        elif isinstance(self.app_token, str) and not self.app_token.startswith('$'):
            # Direct token value
            pass
        else:
            # Try common environment variable names
            import os
            env_vars = [
                'AUSTIN_SODA_APP_TOKEN', 'AUSTIN_SOCRATA_APP_TOKEN',
                'SA_SOCRATA_APP_TOKEN', 'DALLAS_SOCRATA_APP_TOKEN',
                'SOCRATA_APP_TOKEN', 'SODA_APP_TOKEN'
            ]
            for env_var in env_vars:
                token = os.getenv(env_var)
                if token:
                    self.app_token = token
                    logger.info(f"Using app token from {env_var}")
                    break
            else:
                self.app_token = None
                logger.warning(f"No Socrata app token found for {self.name}. Rate limits will be lower.")
        
        # Track last request time for rate limiting
        self._last_request_time = 0
        
        # Create session with retry strategy
        self.session = session or self._create_session()
    
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
        headers = {
            'User-Agent': 'PermitLeadBot/1.0 (Texas Building Permits)',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate'
        }
        
        # Add X-App-Token header if available (required for higher rate limits)
        if self.app_token:
            headers['X-App-Token'] = self.app_token
            logger.info(f"Using Socrata app token for {self.name}")
        
        session.headers.update(headers)
        
        return session
    
    def _rate_limit(self):
        """Enforce rate limiting for Socrata APIs."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.MIN_REQUEST_INTERVAL:
            sleep_time = self.MIN_REQUEST_INTERVAL - elapsed
            logger.debug(f"Rate limiting Socrata API: sleeping for {sleep_time:.3f} seconds")
            time.sleep(sleep_time)
        self._last_request_time = time.time()

    def fetch_since(self, since: datetime, limit: int = 5000) -> Iterable[Dict[str, Any]]:
        """Legacy method for backward compatibility."""
        logger.info(f"Fetching {self.name} permits since {since}")
        
        total_fetched = 0
        offset = 0
        batch_size = 1000  # Socrata recommended batch size
        
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
                
                for record in records:
                    yield record
                
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
        
        logger.info(f"Fetched {total_fetched} records from {self.name}")

    # SourceAdapter interface methods
    def fetch(self, since_days: int) -> Iterable[bytes | str]:
        """Fetch raw JSON data from Socrata API."""
        since = datetime.utcnow() - timedelta(days=since_days)
        logger.info(f"Fetching {self.name} permits since {since}")
        
        total_fetched = 0
        offset = 0
        batch_size = 1000  # Socrata recommended batch size
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
            
            # Add date filter
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
                
                # Yield raw JSON response as string
                yield json.dumps(records)
                
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
        
        logger.info(f"Fetched {total_fetched} records from {self.name}")

    def parse(self, raw: bytes | str) -> Iterable[Dict[str, Any]]:
        """Parse raw Socrata JSON response into individual records."""
        try:
            if isinstance(raw, bytes):
                raw = raw.decode('utf-8')
            
            records = json.loads(raw)
            
            for record in records:
                yield record
                
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to parse Socrata response: {e}")
            return

    def normalize(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Socrata record to standard format."""
        # Apply field mappings if configured
        normalized = {}
        for target_field, source_field in self.field_map.items():
            if source_field in row:
                normalized[target_field] = row[source_field]
        
        # Add standard fields with fallbacks
        normalized.update({
            "source": self.name,
            "permit_number": normalized.get("permit_number") or row.get("permit_number") or row.get("id") or "",
            "issued_date": normalized.get("issued_date") or row.get(self.date_field) or "",
            "address": normalized.get("address") or row.get("address") or row.get("original_address1") or "",
            "description": normalized.get("description") or row.get("work_description") or row.get("description") or "",
            "status": normalized.get("status") or row.get("status") or row.get("current_status") or "",
            "work_class": normalized.get("work_class") or row.get("permit_type") or row.get("work_type") or "",
            "category": normalized.get("category") or row.get("permit_type") or row.get("category") or "",
            "applicant": normalized.get("applicant") or row.get("contractor_name") or row.get("applicant_name") or "",
            "value": self._parse_value(normalized.get("value") or row.get("estimated_cost") or row.get("declared_valuation")),
            "raw_json": row,
        })
        
        return normalized

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