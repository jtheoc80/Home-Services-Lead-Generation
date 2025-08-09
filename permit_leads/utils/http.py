"""
HTTP utilities for permit scraping with retry logic and session management.
"""
import time
import logging
from typing import Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


def get_session(user_agent: str = "PermitLeadBot/1.0 (+contact@example.com)", 
               max_retries: int = 3) -> requests.Session:
    """
    Create a configured HTTP session with retry strategy.
    
    Args:
        user_agent: User-Agent string for requests
        max_retries: Maximum number of retry attempts
        
    Returns:
        Configured requests.Session object
    """
    session = requests.Session()
    
    # Set up retry strategy
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Set common headers
    session.headers.update({
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    
    return session


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((requests.RequestException, requests.Timeout))
)
def fetch_text(url: str, session: Optional[requests.Session] = None, 
               delay: float = 1.0, **kwargs) -> Optional[str]:
    """
    Fetch text content from URL with retry and rate limiting.
    
    Args:
        url: URL to fetch
        session: Optional requests.Session to use
        delay: Delay in seconds before request (for rate limiting)
        **kwargs: Additional arguments for requests.get()
        
    Returns:
        Response text or None if failed
    """
    if delay > 0:
        time.sleep(delay)
    
    if session is None:
        session = get_session()
    
    try:
        logger.debug(f"Fetching text from: {url}")
        response = session.get(url, timeout=30, **kwargs)
        response.raise_for_status()
        return response.text
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch text from {url}: {e}")
        raise


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((requests.RequestException, requests.Timeout))
)
def fetch_json(url: str, session: Optional[requests.Session] = None,
               delay: float = 1.0, **kwargs) -> Optional[Dict[str, Any]]:
    """
    Fetch JSON content from URL with retry and rate limiting.
    
    Args:
        url: URL to fetch
        session: Optional requests.Session to use
        delay: Delay in seconds before request (for rate limiting)
        **kwargs: Additional arguments for requests.get()
        
    Returns:
        Parsed JSON data or None if failed
    """
    if delay > 0:
        time.sleep(delay)
    
    if session is None:
        session = get_session()
    
    try:
        logger.debug(f"Fetching JSON from: {url}")
        response = session.get(url, timeout=30, **kwargs)
        response.raise_for_status()
        return response.json()
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch JSON from {url}: {e}")
        raise
    except ValueError as e:
        logger.error(f"Failed to parse JSON from {url}: {e}")
        raise


class PoliteSession:
    """
    HTTP session wrapper that enforces polite delays between requests.
    
    This is compatible with the existing codebase's PoliteSession usage.
    """
    
    def __init__(self, user_agent: str = "PermitLeadBot/1.0 (+contact@example.com)",
                 delay_seconds: float = 1.0, max_retries: int = 3):
        """
        Initialize polite session.
        
        Args:
            user_agent: User-Agent string for requests
            delay_seconds: Minimum delay between requests in seconds
            max_retries: Maximum number of retry attempts
        """
        self.session = get_session(user_agent, max_retries)
        self.delay_seconds = delay_seconds
        self._last_request_time = 0
    
    def _rate_limit(self):
        """Enforce polite delay between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.delay_seconds:
            sleep_time = self.delay_seconds - elapsed
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        self._last_request_time = time.time()
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """
        Perform GET request with rate limiting.
        
        Args:
            url: URL to request
            **kwargs: Additional arguments for requests.get()
            
        Returns:
            requests.Response object
        """
        self._rate_limit()
        return self.session.get(url, **kwargs)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        """
        Perform POST request with rate limiting.
        
        Args:
            url: URL to request
            **kwargs: Additional arguments for requests.post()
            
        Returns:
            requests.Response object
        """
        self._rate_limit()
        return self.session.post(url, **kwargs)


def backoff_wrapper(func):
    """
    Decorator to add exponential backoff retry logic to functions.
    
    Usage:
        @backoff_wrapper
        def my_fetch_function():
            # function that might fail
            pass
    """
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.RequestException, requests.Timeout))
    )(func)