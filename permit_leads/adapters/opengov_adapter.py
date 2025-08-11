"""OpenGov API adapter for permit data."""

import logging
from datetime import datetime
from typing import List, Optional

from ..models.permit import PermitRecord
from ..config_loader import Jurisdiction

logger = logging.getLogger(__name__)


class OpenGovAdapter:
    """Adapter for OpenGov API-based permit systems."""
    
    def __init__(self, jurisdiction: Jurisdiction):
        """Initialize OpenGov adapter."""
        self.jurisdiction = jurisdiction
        self.config = jurisdiction.source_config
    
    def scrape_permits(self, since: datetime, limit: Optional[int] = None) -> List[PermitRecord]:
        """Scrape permits from OpenGov API."""
        logger.warning(f"OpenGov adapter not yet implemented for {self.jurisdiction.name}")
        return []