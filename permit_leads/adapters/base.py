from typing import Protocol, Iterable, Dict, Any
import datetime as dt

class SourceAdapter(Protocol):
    """Formal interface for permit data source adapters.
    
    Unifies Houston/Dallas/Austin/SA/Harris into a single contract
    so runners don't need to special-case each source.
    """
    name: str
    
    def fetch(self, since_days: int) -> Iterable[bytes | str]:
        """Fetch raw data from the source.
        
        Args:
            since_days: Number of days back to fetch data from
            
        Returns:
            Iterable of raw data (bytes or strings)
        """
        pass
    
    def parse(self, raw: bytes | str) -> Iterable[Dict[str, Any]]:
        """Parse raw data into structured records.
        
        Args:
            raw: Raw data from fetch()
            
        Returns:
            Iterable of parsed dictionaries
        """
        pass
    
    def normalize(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a parsed record to standard format.
        
        Args:
            row: Parsed record from parse()
            
        Returns:
            Normalized record dictionary
        """
        pass


class BaseAdapter:
    """Base implementation of SourceAdapter interface."""
    
    def __init__(self, cfg: Dict[str, Any], session=None):
        self.cfg = cfg
        self.session = session
        self._name = cfg.get("name", "unknown")

    @property 
    def name(self) -> str:
        """Source name for identification."""
        return self._name

    def fetch_since(self, since: dt.datetime, limit: int = 5000) -> Iterable[Dict[str, Any]]:
        """Legacy method - implement fetch/parse/normalize instead."""
        raise NotImplementedError
        
    def fetch(self, since_days: int) -> Iterable[bytes | str]:
        """Fetch raw data from source."""
        raise NotImplementedError
        
    def parse(self, raw: bytes | str) -> Iterable[Dict[str, Any]]:
        """Parse raw data into records.""" 
        raise NotImplementedError
        
    def normalize(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize record to standard format."""
        raise NotImplementedError
