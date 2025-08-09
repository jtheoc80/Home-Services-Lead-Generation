"""Generic HTML adapter for permit data."""

import logging
from datetime import datetime
from typing import List, Optional

from ..models.permit import PermitRecord
from ..config_loader import Jurisdiction

logger = logging.getLogger(__name__)


class HTMLAdapter:
    """Adapter for generic HTML-based permit systems."""
    
    def __init__(self, jurisdiction: Jurisdiction):
        """Initialize HTML adapter."""
        self.jurisdiction = jurisdiction
        self.config = jurisdiction.source_config
    
    def scrape_permits(self, since: datetime, limit: Optional[int] = None) -> List[PermitRecord]:
        """Scrape permits from HTML interface."""
        logger.warning(f"HTML adapter not yet implemented for {self.jurisdiction.name}")
        return []