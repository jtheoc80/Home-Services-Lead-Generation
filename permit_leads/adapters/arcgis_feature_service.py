from typing import Dict, Any, Iterable, Optional
import datetime as dt
from urllib.parse import urlencode
import time
import random
import logging
import requests
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .base import BaseAdapter

logger = logging.getLogger(__name__)


class ArcGISFeatureServiceAdapter(BaseAdapter):
    """
    Query an ArcGIS FeatureServer/MapServer layer for permits.
    Works with endpoints like:
      https://<host>/arcgis/rest/services/<path>/<FeatureServer|MapServer>/<layer>/query

    Required config:
      - name: Display name
      - type: arcgis_feature_service
      - url:  full /query endpoint OR layer endpoint (we'll append /query)
      - date_field: Field to filter by date (e.g., 'GAL_REC_DATE', 'ISSUEDDATE')
      - mappings: dict for field mapping into normalized record (optional)

    Notes:
      - We page using resultOffset/resultRecordCount up to 'limit' rows.
      - Returns raw ArcGIS attributes; normalization handled upstream.
      - Includes retries with jitter for HTTP 429/5xx errors
      - Respects maxRecordCount from layer metadata
      - Throttles to ≤ 5 req/s
      - Logs exact ArcGIS count before paging
    """
    
    # Rate limiting: maximum 5 requests per second
    MAX_REQUESTS_PER_SECOND = 5
    MIN_REQUEST_INTERVAL = 1.0 / MAX_REQUESTS_PER_SECOND  # 0.2 seconds
    
    def __init__(self, cfg: Dict[str, Any], session=None):
        super().__init__(cfg, session)
        self.session = session or self._create_session()
        
        # Track last request time for rate limiting
        self._last_request_time = 0
        
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

    def _query_url(self) -> str:
        url = self.cfg["url"]
        return url if url.rstrip('/').endswith('/query') else url.rstrip('/') + '/query'
    
    def _base_url(self) -> str:
        """Get base URL without /query for metadata requests."""
        query_url = self._query_url()
        return query_url.rstrip('/query')
    
    def _get_layer_metadata(self) -> Dict[str, Any]:
        """Get layer metadata including maxRecordCount."""
        if self._layer_metadata is not None:
            return self._layer_metadata
        
        try:
            params = {'f': 'json'}
            metadata = self._make_request_with_jitter(self._base_url(), params)
            
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
            
            result = self._make_request_with_jitter(self._query_url(), params)
            
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

    # New SourceAdapter interface methods
    def fetch(self, since_days: int) -> Iterable[bytes | str]:
        """Fetch raw JSON data from ArcGIS FeatureServer."""
        since = dt.datetime.utcnow() - dt.timedelta(days=since_days)
        date_field = self.cfg["date_field"]
        url = self._query_url()
        where = f"{date_field} >= TIMESTAMP '{since.strftime('%Y-%m-%d %H:%M:%S')}'"

        # Get total count first and log it
        total_count = self._get_total_count(where)
        logger.info(f"ArcGIS total count for query since {since}: {total_count}")
        
        if total_count == 0:
            logger.info("No records found matching criteria")
            return

        # Get layer metadata to respect maxRecordCount
        metadata = self._get_layer_metadata()
        max_record_count = metadata.get('maxRecordCount', 2000)
        
        # Use the smaller of maxRecordCount or default page size
        page_size = min(max_record_count, 2000)
        out_fields = self.cfg.get("out_fields", "*")

        fetched = 0
        offset = 0
        limit = 10000  # Default limit
        
        while fetched < limit and fetched < total_count:
            # Calculate how many records to request in this batch
            records_to_fetch = min(page_size, limit - fetched, total_count - fetched)
            
            params = {
                "where": where,
                "outFields": out_fields,
                "f": "json",
                "returnGeometry": "false",
                "resultOffset": offset,
                "resultRecordCount": records_to_fetch,
                "orderByFields": f"{date_field} DESC"
            }
            
            logger.debug(f"Fetching batch: offset={offset}, count={records_to_fetch}")
            
            data = self._make_request_with_jitter(url, params)
            
            if not data:
                logger.warning("No data returned from request")
                break
                
            # Yield raw JSON response as string
            yield json.dumps(data)
            
            feats = data.get("features", [])
            fetched += len(feats)
            
            # If we got fewer features than requested, we've reached the end
            if len(feats) < records_to_fetch:
                logger.info("Reached end of available results")
                break
                
            offset += len(feats)

    def parse(self, raw: bytes | str) -> Iterable[Dict[str, Any]]:
        """Parse raw ArcGIS JSON response into individual feature records."""
        try:
            if isinstance(raw, bytes):
                raw = raw.decode('utf-8')
            
            data = json.loads(raw)
            features = data.get("features", [])
            
            for feat in features:
                attrs = feat.get("attributes", {})
                yield attrs
                
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse ArcGIS response: {e}")
            return

    def normalize(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize ArcGIS feature attributes to standard format."""
        mappings = self.cfg.get("mappings", {})
        
        # Apply field mappings if configured
        normalized = {}
        for target_field, source_field in mappings.items():
            if source_field in row:
                normalized[target_field] = row[source_field]
        
        # Add standard fields with fallbacks
        normalized.update({
            "source": self.name,
            "permit_number": normalized.get("permit_number") or row.get("PERMITNUMBER") or row.get("permit_id") or "",
            "issued_date": normalized.get("issued_date") or row.get("ISSUEDDATE") or row.get("issue_date") or "",
            "address": normalized.get("address") or row.get("FULLADDRESS") or row.get("full_address") or "",
            "description": normalized.get("description") or row.get("PERMITNAME") or row.get("description") or "",
            "status": normalized.get("status") or row.get("STATUS") or "",
            "work_class": normalized.get("work_class") or row.get("APPTYPE") or "",
            "category": normalized.get("category") or row.get("APPTYPE") or "",
            "applicant": normalized.get("applicant") or row.get("APPLICANTNAME") or "",
            "value": self._parse_value(normalized.get("value") or row.get("PERMITVALUATION")),
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
