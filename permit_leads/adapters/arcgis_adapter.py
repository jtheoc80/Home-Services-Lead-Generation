"""ArcGIS Feature Server adapter for permit data."""

import logging
import requests
import time
import random
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urlencode
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..models.permit import PermitRecord
from ..config_loader import Jurisdiction

logger = logging.getLogger(__name__)


class ArcGISAdapter:
    """Adapter for ArcGIS Feature Server permit data sources."""
    
    # Rate limiting: maximum 5 requests per second
    MAX_REQUESTS_PER_SECOND = 5
    MIN_REQUEST_INTERVAL = 1.0 / MAX_REQUESTS_PER_SECOND  # 0.2 seconds
    
    def __init__(self, jurisdiction: Jurisdiction):
        """Initialize ArcGIS adapter."""
        self.jurisdiction = jurisdiction
        self.config = jurisdiction.source_config
        # Handle both 'feature_server' and 'url' keys for backward compatibility
        self.feature_server = self.config.get('feature_server') or self.config.get('url')
        if not self.feature_server:
            raise ValueError(f"No feature_server or url found in config for {jurisdiction.name}")
        
        # Ensure URL ends with /query
        if not self.feature_server.endswith('/query'):
            if self.feature_server.endswith('/'):
                self.feature_server = self.feature_server + 'query'
            else:
                self.feature_server = self.feature_server + '/query'
        
        # Get the base URL without /query for metadata requests
        self.base_url = self.feature_server.rstrip('/query')
        
        self.date_field = self.config['date_field']
        self.field_map = self.config.get('field_map', {})
        
        # Track last request time for rate limiting
        self._last_request_time = 0
        
        # Create session with enhanced retry strategy
        self.session = self._create_session()
        
        # Cache for layer metadata
        self._layer_metadata = None
    
    def _create_session(self) -> requests.Session:
        """Create HTTP session with enhanced retry strategy including jitter."""
        session = requests.Session()
        
        # Enhanced retry strategy with jitter for 429 and 5xx errors
        retry_strategy = Retry(
            total=5,  # Maximum number of retries
            backoff_factor=1,  # Base backoff factor
            status_forcelist=[429, 500, 502, 503, 504],  # Retry on these HTTP status codes
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            raise_on_redirect=False,
            raise_on_status=False
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set headers
        session.headers.update({
            'User-Agent': 'PermitLeadBot/1.0 (+contact@example.com)',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
        return session
    
    def _rate_limit(self):
        """Enforce rate limiting to stay under 5 req/s."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.MIN_REQUEST_INTERVAL:
            sleep_time = self.MIN_REQUEST_INTERVAL - elapsed
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.3f} seconds")
            time.sleep(sleep_time)
        self._last_request_time = time.time()
    
    def _make_request_with_jitter(self, url: str, params: Dict[str, Any], max_retries: int = 5) -> Optional[Dict[str, Any]]:
        """Make HTTP request with jitter on retries."""
        self._rate_limit()
        
        for attempt in range(max_retries + 1):
            try:
                logger.debug(f"Making request (attempt {attempt + 1}): {url}?{urlencode(params)}")
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 429:
                    # Rate limited, apply exponential backoff with jitter
                    backoff = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Rate limited (429), backing off for {backoff:.2f} seconds")
                    time.sleep(backoff)
                    continue
                elif response.status_code >= 500:
                    # Server error, apply exponential backoff with jitter
                    backoff = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Server error ({response.status_code}), backing off for {backoff:.2f} seconds")
                    time.sleep(backoff)
                    continue
                
                response.raise_for_status()
                return response.json()
                
            except requests.RequestException as e:
                if attempt < max_retries:
                    backoff = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Request failed: {e}, retrying in {backoff:.2f} seconds")
                    time.sleep(backoff)
                else:
                    logger.error(f"Request failed after {max_retries + 1} attempts: {e}")
                    raise
        
        return None
    
    def _get_layer_metadata(self) -> Dict[str, Any]:
        """Get layer metadata including maxRecordCount."""
        if self._layer_metadata is not None:
            return self._layer_metadata
        
        try:
            params = {'f': 'json'}
            metadata = self._make_request_with_jitter(self.base_url, params)
            
            if metadata:
                self._layer_metadata = metadata
                max_records = metadata.get('maxRecordCount', 2000)
                logger.info(f"Layer metadata retrieved: maxRecordCount={max_records}")
                return metadata
            else:
                logger.warning("Failed to retrieve layer metadata, using defaults")
                return {'maxRecordCount': 2000}
                
        except Exception as e:
            logger.error(f"Error retrieving layer metadata: {e}")
            return {'maxRecordCount': 2000}
    
    def _get_total_count(self, where_clause: str) -> int:
        """Get total count of records matching the where clause."""
        try:
            params = {
                'where': where_clause,
                'returnCountOnly': 'true',
                'f': 'json'
            }
            
            result = self._make_request_with_jitter(self.feature_server, params)
            
            if result and 'count' in result:
                count = result['count']
                logger.info(f"Total ArcGIS record count for query '{where_clause}': {count}")
                return count
            else:
                logger.warning(f"Could not retrieve count, response: {result}")
                return 0
                
        except Exception as e:
            logger.error(f"Error getting total count: {e}")
            return 0
    
    def scrape_permits(self, since: datetime, limit: Optional[int] = None) -> List[PermitRecord]:
        """Scrape permits from ArcGIS Feature Server with proper paging and rate limiting."""
        try:
            # Build query parameters
            since_str = since.strftime('%Y-%m-%d')
            where_clause = f"{self.date_field} >= DATE '{since_str}'"
            
            # Get total count first and log it
            total_count = self._get_total_count(where_clause)
            logger.info(f"ArcGIS total count for {self.jurisdiction.name} since {since_str}: {total_count}")
            
            if total_count == 0:
                logger.info(f"No records found for {self.jurisdiction.name}")
                return []
            
            # Get layer metadata to respect maxRecordCount
            metadata = self._get_layer_metadata()
            max_record_count = metadata.get('maxRecordCount', 2000)
            logger.info(f"Using maxRecordCount: {max_record_count} for {self.jurisdiction.name}")
            
            # Use the smaller of maxRecordCount or requested limit
            page_size = max_record_count
            if limit and limit < page_size:
                page_size = limit
            
            permits = []
            offset = 0
            records_fetched = 0
            
            while records_fetched < total_count and (not limit or records_fetched < limit):
                # Calculate how many records to request in this batch
                records_to_fetch = page_size
                if limit and (records_fetched + records_to_fetch) > limit:
                    records_to_fetch = limit - records_fetched
                
                params = {
                    'where': where_clause,
                    'outFields': '*',
                    'f': 'json',
                    'returnGeometry': 'true',
                    'resultOffset': offset,
                    'resultRecordCount': records_to_fetch,
                    'orderByFields': f"{self.date_field} DESC"
                }
                
                logger.debug(f"Fetching batch: offset={offset}, count={records_to_fetch}")
                
                data = self._make_request_with_jitter(self.feature_server, params)
                
                if not data or 'features' not in data:
                    logger.warning(f"No features found in response for {self.jurisdiction.name}, offset {offset}")
                    break
                
                features = data['features']
                if not features:
                    logger.info(f"No more features available for {self.jurisdiction.name}")
                    break
                
                # Parse features in this batch
                batch_permits = []
                for feature in features:
                    try:
                        permit = self._parse_feature(feature)
                        if permit:
                            batch_permits.append(permit)
                    except Exception as e:
                        logger.warning(f"Error parsing feature: {e}")
                        continue
                
                permits.extend(batch_permits)
                records_fetched += len(features)
                offset += len(features)
                
                logger.info(f"Fetched {len(batch_permits)} permits from batch, total so far: {len(permits)}")
                
                # If we got fewer features than requested, we've reached the end
                if len(features) < records_to_fetch:
                    logger.info(f"Reached end of results for {self.jurisdiction.name}")
                    break
            
            logger.info(f"Completed scraping {self.jurisdiction.name}: {len(permits)} permits collected")
            return permits
            
        except Exception as e:
            logger.error(f"Error scraping ArcGIS for {self.jurisdiction.name}: {e}")
            return []
    
    def _parse_feature(self, feature: dict) -> Optional[PermitRecord]:
        """Parse ArcGIS feature into PermitRecord."""
        attributes = feature.get('attributes', {})
        geometry = feature.get('geometry', {})
        
        # Map fields using configuration
        mapped_data = {}
        for permit_field, source_field in self.field_map.items():
            if source_field in attributes:
                mapped_data[permit_field] = attributes[source_field]
        
        # Extract coordinates if available
        if geometry and 'x' in geometry and 'y' in geometry:
            mapped_data['longitude'] = geometry['x']
            mapped_data['latitude'] = geometry['y']
        
        # Set jurisdiction
        mapped_data['jurisdiction'] = self.jurisdiction.name
        
        try:
            return PermitRecord(**mapped_data)
        except Exception as e:
            logger.warning(f"Error creating PermitRecord: {e}")
            return None