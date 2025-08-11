"""
Regional configuration management for multi-region support.

This module provides utilities for loading and managing regional configurations,
including metro areas, jurisdictions, and region-specific settings.
"""

import yaml
import os
from typing import Dict, List, Optional, Any
from pathlib import Path


class RegionConfig:
    """Manages regional configuration and provides region-aware functionality."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize region configuration.
        
        Args:
            config_path: Path to regions.yaml file. If None, uses default location.
        """
        if config_path is None:
            # Default to config/regions.yaml relative to project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "regions.yaml"
        
        self.config_path = Path(config_path)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load regions configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Regions config file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def get_active_regions(self) -> List[str]:
        """Get list of active region IDs."""
        return [
            region_id 
            for region_id, region_data in self._config['regions'].items()
            if region_data.get('active', False)
        ]
    
    def get_active_metros(self, region_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of active metro areas.
        
        Args:
            region_id: Filter by specific region. If None, returns all active metros.
            
        Returns:
            List of metro dictionaries with id, region_id, and metro data.
        """
        metros = []
        regions_to_check = [region_id] if region_id else self.get_active_regions()
        
        for rid in regions_to_check:
            region_data = self._config['regions'].get(rid, {})
            if not region_data.get('active', False):
                continue
                
            for metro_id, metro_data in region_data.get('metros', {}).items():
                if metro_data.get('active', False):
                    metros.append({
                        'id': metro_id,
                        'region_id': rid,
                        'display_name': metro_data.get('display_name', metro_id.title()),
                        'short_name': metro_data.get('short_name', metro_id.title()),
                        'center_lat': metro_data.get('center_lat'),
                        'center_lng': metro_data.get('center_lng'),
                        'radius_miles': metro_data.get('radius_miles', 30),
                        'description': metro_data.get('description', ''),
                        'jurisdictions': metro_data.get('jurisdictions', [])
                    })
        
        return metros
    
    def get_metro_by_id(self, region_id: str, metro_id: str) -> Optional[Dict[str, Any]]:
        """Get metro data by region and metro ID."""
        region_data = self._config['regions'].get(region_id, {})
        metro_data = region_data.get('metros', {}).get(metro_id)
        
        if not metro_data:
            return None
        
        return {
            'id': metro_id,
            'region_id': region_id,
            'display_name': metro_data.get('display_name', metro_id.title()),
            'short_name': metro_data.get('short_name', metro_id.title()),
            'center_lat': metro_data.get('center_lat'),
            'center_lng': metro_data.get('center_lng'),
            'radius_miles': metro_data.get('radius_miles', 30),
            'description': metro_data.get('description', ''),
            'jurisdictions': metro_data.get('jurisdictions', []),
            'seo_keywords': metro_data.get('seo_keywords', [])
        }
    
    def get_jurisdictions_for_metro(self, region_id: str, metro_id: str) -> List[str]:
        """Get list of jurisdictions for a metro area."""
        metro = self.get_metro_by_id(region_id, metro_id)
        return metro['jurisdictions'] if metro else []
    
    def get_default_region_metro(self) -> Tuple[str, str]:
        """Get default region and metro IDs."""
        default_region = self._config.get('default_region', 'texas')
        default_metro = self._config.get('default_metro', 'houston')
        return default_region, default_metro
    
    def get_region_config(self, region_id: str) -> Dict[str, Any]:
        """Get region-specific configuration (trade priorities, value bands, etc)."""
        return self._config.get('region_configs', {}).get(region_id, {})
    
    def get_trade_priorities(self, region_id: str) -> Dict[str, int]:
        """Get trade priorities for a region."""
        region_config = self.get_region_config(region_id)
        return region_config.get('trade_priorities', {})
    
    def get_inspection_days(self, region_id: str, jurisdiction: str) -> int:
        """Get estimated inspection days for a jurisdiction."""
        region_config = self.get_region_config(region_id)
        inspection_days = region_config.get('inspection_days', {})
        return inspection_days.get(jurisdiction, inspection_days.get('default', 7))
    
    def get_value_bands(self, region_id: str) -> Dict[str, int]:
        """Get value band thresholds for a region."""
        region_config = self.get_region_config(region_id)
        return region_config.get('value_bands', {
            'low': 5000, 'medium': 15000, 'high': 50000, 'premium': 100000
        })
    
    def find_metro_by_jurisdiction(self, jurisdiction: str) -> Optional[tuple[str, str]]:
        """
        Find region and metro IDs by jurisdiction name.
        
        Returns:
            Tuple of (region_id, metro_id) or None if not found.
        """
        for region_id, region_data in self._config['regions'].items():
            if not region_data.get('active', False):
                continue
                
            for metro_id, metro_data in region_data.get('metros', {}).items():
                if not metro_data.get('active', False):
                    continue
                    
                if jurisdiction in metro_data.get('jurisdictions', []):
                    return region_id, metro_id
        
        return None
    
    def get_seo_config(self) -> Dict[str, Any]:
        """Get SEO configuration templates."""
        return self._config.get('seo_config', {})
    
    def generate_seo_data(self, region_id: str, metro_id: str, trades: List[str] = None) -> Dict[str, str]:
        """
        Generate SEO data for a region/metro.
        
        Args:
            region_id: Region identifier
            metro_id: Metro identifier  
            trades: List of trade types for keyword generation
            
        Returns:
            Dictionary with title, description, and keywords
        """
        metro = self.get_metro_by_id(region_id, metro_id)
        if not metro:
            return {}
        
        seo_config = self.get_seo_config()
        metro_name = metro['display_name']
        
        # Generate title
        title_template = seo_config.get('title_template', '{metro} Home Services Leads | LeadLedgerPro')
        title = title_template.format(metro=metro_name)
        
        # Generate description
        desc_template = seo_config.get('description_template', 
            'Quality home service contractor leads from building permits in {metro}.')
        trades_str = ', '.join(trades) if trades else 'home services'
        description = desc_template.format(metro=metro_name, trades=trades_str)
        
        # Generate keywords
        keywords = metro.get('seo_keywords', []).copy()
        if trades:
            keyword_template = seo_config.get('keywords_template', ['{trades} {metro}'])
            for template in keyword_template:
                for trade in trades:
                    keywords.append(template.format(metro=metro_name, trades=trade))
        
        return {
            'title': title,
            'description': description,
            'keywords': keywords
        }


# Global instance for easy access
_region_config = None

def get_region_config() -> RegionConfig:
    """Get the global region configuration instance."""
    global _region_config
    if _region_config is None:
        _region_config = RegionConfig()
    return _region_config