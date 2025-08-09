"""Accela HTML adapter for permit data."""

import logging
from datetime import datetime
from typing import List, Optional
from bs4 import BeautifulSoup
import requests

from ..models.permit import PermitRecord
from ..config_loader import Jurisdiction

logger = logging.getLogger(__name__)


class AccelaAdapter:
    """Adapter for Accela HTML-based permit systems."""
    
    def __init__(self, jurisdiction: Jurisdiction):
        """Initialize Accela adapter."""
        self.jurisdiction = jurisdiction
        self.config = jurisdiction.source_config
        self.base_url = self.config['base_url']
        self.field_map = self.config.get('field_map', {})
    
    def scrape_permits(self, since: datetime, limit: Optional[int] = None) -> List[PermitRecord]:
        """Scrape permits from Accela HTML interface."""
        try:
            # For now, use existing Houston City scraper logic as fallback
            from ..scrapers.houston_city import HoustonCityScraper
            
            logger.info(f"Using Houston City scraper for {self.jurisdiction.name} (Accela)")
            scraper = HoustonCityScraper()
            permits = scraper.scrape_permits(since, limit=limit)
            
            # Update jurisdiction name
            for permit in permits:
            permits = [replace(permit, jurisdiction=self.jurisdiction.name) for permit in permits]
            
            return permits
            
        except Exception as e:
            logger.error(f"Error scraping Accela for {self.jurisdiction.name}: {e}")
            return []