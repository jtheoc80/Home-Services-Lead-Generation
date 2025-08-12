"""
Abstract base scraper class with common utilities for permit data collection.
"""
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..models.permit import PermitRecord

# Try to import ingest logging (graceful fallback if not available)
try:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'app'))
    INGEST_LOGGING_AVAILABLE = True
except ImportError:
    INGEST_LOGGING_AVAILABLE = False

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    Abstract base class for permit scrapers.
    
    Provides common functionality:
    - HTTP session with retry logic and rate limiting
    - Polite delay between requests
    - User-agent management
    - Logging setup
    - Standard fetch -> parse -> normalize flow
    """
    
    def __init__(self, jurisdiction: str, base_url: str, 
                 user_agent: str = "PermitLeadBot/1.0 (+contact@example.com)",
                 delay_seconds: float = 1.0, max_retries: int = 3):
        """
        Initialize base scraper.
        
        Args:
            jurisdiction: Name of jurisdiction (e.g., "City of Houston")
            base_url: Base URL for the permit system
            user_agent: User-Agent string for requests
            delay_seconds: Polite delay between requests
            max_retries: Maximum number of retry attempts
        """
        self.jurisdiction = jurisdiction
        self.base_url = base_url
        self.user_agent = user_agent
        self.delay_seconds = delay_seconds
        self.max_retries = max_retries
        self.session = self._create_session()
        
        # Track last request time for rate limiting
        self._last_request_time = 0
    
    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry strategy and headers."""
        session = requests.Session()
        
        # Set up retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set headers
        session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        return session
    
    def _rate_limit(self):
        """Enforce polite delay between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.delay_seconds:
            sleep_time = self.delay_seconds - elapsed
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        self._last_request_time = time.time()
    
    def fetch_text(self, url: str, **kwargs) -> Optional[str]:
        """
        Fetch text content from URL with rate limiting and error handling.
        
        Args:
            url: URL to fetch
            **kwargs: Additional arguments for requests.get()
            
        Returns:
            Response text or None if failed
        """
        self._rate_limit()
        
        try:
            logger.debug(f"Fetching: {url}")
            response = self.session.get(url, timeout=30, **kwargs)
            response.raise_for_status()
            return response.text
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def fetch_json(self, url: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Fetch JSON content from URL.
        
        Args:
            url: URL to fetch
            **kwargs: Additional arguments for requests.get()
            
        Returns:
            Parsed JSON data or None if failed
        """
        self._rate_limit()
        
        try:
            logger.debug(f"Fetching JSON: {url}")
            response = self.session.get(url, timeout=30, **kwargs)
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch JSON from {url}: {e}")
            return None
        except ValueError as e:
            logger.error(f"Failed to parse JSON from {url}: {e}")
            return None
    
    @abstractmethod
    def fetch_permits(self, since: datetime, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch raw permit data from the source.
        
        Args:
            since: Only fetch permits issued/updated since this date
            limit: Maximum number of permits to fetch (None for no limit)
            
        Returns:
            List of raw permit data dictionaries
        """
        pass
    
    @abstractmethod
    def parse_permit(self, raw_data: Dict[str, Any]) -> Optional[PermitRecord]:
        """
        Parse raw permit data into normalized PermitRecord.
        
        Args:
            raw_data: Raw permit data from fetch_permits()
            
        Returns:
            Normalized PermitRecord or None if parsing failed
        """
        pass
    
    def scrape_permits(self, since: datetime, limit: Optional[int] = None, trace_id: Optional[str] = None) -> List[PermitRecord]:
        """
        Complete scraping workflow: fetch -> parse -> normalize.
        
        Args:
            since: Only fetch permits issued/updated since this date
            limit: Maximum number of permits to fetch (None for no limit)
            trace_id: Optional trace ID for logging ingest steps
            
        Returns:
            List of normalized PermitRecord objects
        """
        logger.info(f"Starting scrape for {self.jurisdiction} since {since}")
        
        # Use trace ID logging if available
        use_tracer = INGEST_LOGGING_AVAILABLE and trace_id
        
        if use_tracer:
            log_ingest_step(trace_id, "fetch_page", True, {
                "jurisdiction": self.jurisdiction,
                "since": since.isoformat(),
                "limit": limit
            })
        
        # Fetch raw data
        try:
            raw_permits = self.fetch_permits(since, limit)
            if not raw_permits:
                logger.warning(f"No raw permits fetched for {self.jurisdiction}")
                if use_tracer:
                    log_ingest_step(trace_id, "fetch_page", False, {
                        "error": "No raw permits fetched",
                        "jurisdiction": self.jurisdiction
                    })
                return []
            
            logger.info(f"Fetched {len(raw_permits)} raw permits from {self.jurisdiction}")
            if use_tracer:
                log_ingest_step(trace_id, "fetch_page", True, {
                    "permits_fetched": len(raw_permits),
                    "jurisdiction": self.jurisdiction
                })
        except Exception as e:
            logger.error(f"Error fetching permits: {e}")
            if use_tracer:
                log_ingest_step(trace_id, "fetch_page", False, {
                    "error": str(e),
                    "jurisdiction": self.jurisdiction
                })
            raise
        
        # Parse and normalize
        permits = []
        parse_errors = 0
        
        for raw_permit in raw_permits:
            try:
                permit = self.parse_permit(raw_permit)
                if permit:
                    permits.append(permit)
                else:
                    parse_errors += 1
                    
            except Exception as e:
                logger.error(f"Error parsing permit: {e}")
                parse_errors += 1
        
        logger.info(f"Parsed {len(permits)} permits from {self.jurisdiction} "
                   f"({parse_errors} parse errors)")
        
        # Log parse results
        if use_tracer:
            log_ingest_step(trace_id, "parse", parse_errors == 0, {
                "permits_parsed": len(permits),
                "parse_errors": parse_errors,
                "jurisdiction": self.jurisdiction
            })
        
        return permits
    
    def get_sample_data(self) -> List[Dict[str, Any]]:
        """
        Return sample/mock data for testing purposes.
        Override in subclasses to provide jurisdiction-specific test data.
        
        Returns:
            List of sample permit data dictionaries
        """
        return []