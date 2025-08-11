"""
Region-aware adapter factory for permit data sources.

Creates appropriate adapters based on jurisdiction configuration
from the registry system.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .config_loader import get_config_loader, Jurisdiction, Region
from .models.permit import PermitRecord

logger = logging.getLogger(__name__)


class RegionAwareAdapter:
    """Adapter factory for creating jurisdiction-specific scrapers."""
    
    def __init__(self):
        """Initialize adapter factory."""
        self.config_loader = get_config_loader()
    
    def get_active_jurisdictions(self) -> List[Jurisdiction]:
        """Get all active jurisdictions from config."""
        return self.config_loader.get_active_jurisdictions()
    
    def create_scraper(self, jurisdiction: Jurisdiction):
        """Create appropriate scraper for jurisdiction based on provider type."""
        
        if jurisdiction.provider == 'arcgis':
            return self._create_arcgis_scraper(jurisdiction)
        elif jurisdiction.provider == 'accela':
            return self._create_accela_scraper(jurisdiction)
        elif jurisdiction.provider == 'opengov':
            return self._create_opengov_scraper(jurisdiction)
        elif jurisdiction.provider == 'html':
            return self._create_html_scraper(jurisdiction)
        else:
            raise ValueError(f"Unknown provider type: {jurisdiction.provider}")
    
    def _create_arcgis_scraper(self, jurisdiction: Jurisdiction):
        """Create ArcGIS Feature Server scraper."""
        # Use ETL-aware adapter for Harris County to enable state tracking
        if 'harris' in jurisdiction.slug.lower():
            from .adapters.etl_aware_arcgis_adapter import ETLAwareArcGISAdapter
            return ETLAwareArcGISAdapter(jurisdiction)
        else:
            from .adapters.arcgis_adapter import ArcGISAdapter
            return ArcGISAdapter(jurisdiction)
    
    def _create_accela_scraper(self, jurisdiction: Jurisdiction):
        """Create Accela HTML scraper."""
        from .adapters.accela_adapter import AccelaAdapter
        return AccelaAdapter(jurisdiction)
    
    def _create_opengov_scraper(self, jurisdiction: Jurisdiction):
        """Create OpenGov API scraper."""
        from .adapters.opengov_adapter import OpenGovAdapter
        return OpenGovAdapter(jurisdiction)
    
    def _create_html_scraper(self, jurisdiction: Jurisdiction):
        """Create generic HTML scraper."""
        from .adapters.html_adapter import HTMLAdapter
        return HTMLAdapter(jurisdiction)
    
    def annotate_with_region_info(self, permit: PermitRecord, jurisdiction: Jurisdiction, region: Region) -> PermitRecord:
        """Annotate permit record with region/jurisdiction information."""
        # Create a copy with additional fields
        permit_dict = permit.dict()
        
        # Add region/jurisdiction metadata
        permit_dict.update({
            'jurisdiction_slug': jurisdiction.slug,
            'jurisdiction_id': jurisdiction.slug,  # Use slug as ID for now
            'region_slug': region.slug,
            'region_id': region.slug,  # Use slug as ID for now
            'state': jurisdiction.state,
            'jurisdiction_name': jurisdiction.name,
            'region_name': region.name
        })
        
        # Set lat/lon from latitude/longitude if available for PostGIS compatibility
        if hasattr(permit, 'latitude') and hasattr(permit, 'longitude'):
            if permit.latitude and permit.longitude:
                permit_dict['lat'] = permit.latitude
                permit_dict['lon'] = permit.longitude
        
        return PermitRecord(**permit_dict)
    
    def scrape_jurisdiction(self, jurisdiction_slug: str, since: datetime, limit: Optional[int] = None) -> List[PermitRecord]:
        """Scrape permits for a specific jurisdiction."""
        jurisdiction = self.config_loader.get_jurisdiction(jurisdiction_slug)
        if not jurisdiction:
            raise ValueError(f"Jurisdiction not found: {jurisdiction_slug}")
        
        if not jurisdiction.active:
            logger.info(f"Skipping inactive jurisdiction: {jurisdiction_slug}")
            return []
        
        region = self.config_loader.get_region(jurisdiction.region_slug)
        if not region:
            raise ValueError(f"Region not found for jurisdiction: {jurisdiction.region_slug}")
        
        logger.info(f"Scraping {jurisdiction.name} ({jurisdiction.provider}) since {since}")
        
        try:
            scraper = self.create_scraper(jurisdiction)
            permits = scraper.scrape_permits(since, limit=limit)
            
            # Annotate permits with region information
            annotated_permits = []
            for permit in permits:
                annotated_permit = self.annotate_with_region_info(permit, jurisdiction, region)
                annotated_permits.append(annotated_permit)
            
            logger.info(f"Scraped {len(annotated_permits)} permits from {jurisdiction.name}")
            return annotated_permits
            
        except Exception as e:
            logger.error(f"Error scraping {jurisdiction.name}: {e}")
            return []
    
    def scrape_all_jurisdictions(self, since: datetime, limit: Optional[int] = None) -> Dict[str, List[PermitRecord]]:
        """Scrape permits from all active jurisdictions."""
        jurisdictions = self.get_active_jurisdictions()
        results = {}
        
        for jurisdiction in jurisdictions:
            permits = self.scrape_jurisdiction(jurisdiction.slug, since, limit)
            results[jurisdiction.slug] = permits
        
        return results