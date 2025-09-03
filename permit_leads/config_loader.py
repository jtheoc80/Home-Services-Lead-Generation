"""
Config loader for multi-region jurisdiction registry.

Loads registry.yaml and resolves runtime structures for regions,
jurisdictions, and plans configuration.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Region:
    """Region configuration model."""

    slug: str
    name: str
    level: str  # metro, state, national
    parent: Optional[str]
    timezone: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Region":
        return cls(
            slug=data["slug"],
            name=data["name"],
            level=data["level"],
            parent=data.get("parent"),
            timezone=data["timezone"],
        )


@dataclass
class Jurisdiction:
    """Jurisdiction configuration model."""

    slug: str
    name: str
    region_slug: str
    state: str
    fips: Optional[str]
    timezone: str
    provider: str  # arcgis, accela, opengov, html
    active: bool
    source_config: Dict[str, Any]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Jurisdiction":
        return cls(
            slug=data["slug"],
            name=data["name"],
            region_slug=data.get(
                "region_slug", data.get("region")
            ),  # Handle both region and region_slug
            state=data["state"],
            fips=data.get("fips"),
            timezone=data.get("timezone", "America/Chicago"),  # Default timezone
            provider=data["provider"],
            active=data.get("active", True),
            source_config=data["source_config"],
        )


@dataclass
class Plan:
    """Plan configuration model."""

    slug: str
    name: str
    monthly_price_cents: int
    credits: int
    scope: str  # metro, state, national
    regions: List[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Plan":
        return cls(
            slug=data["slug"],
            name=data["name"],
            monthly_price_cents=data["monthly_price_cents"],
            credits=data["credits"],
            scope=data["scope"],
            regions=data.get("regions", []),
        )


class ConfigLoader:
    """Loads and manages registry configuration."""

    def __init__(self, registry_path: Optional[str] = None):
        """Initialize config loader with registry path."""
        if registry_path is None:
            # Default to config/registry.yaml relative to permit_leads directory
            permit_leads_dir = Path(__file__).parent
            registry_path = permit_leads_dir / "config" / "registry.yaml"

        self.registry_path = Path(registry_path)
        self._regions: Dict[str, Region] = {}
        self._jurisdictions: Dict[str, Jurisdiction] = {}
        self._plans: Dict[str, Plan] = {}
        self._loaded = False

    def load(self) -> None:
        """Load configuration from registry file."""
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Registry file not found: {self.registry_path}")

        logger.info(f"Loading registry from {self.registry_path}")

        with open(self.registry_path, "r") as f:
            data = yaml.safe_load(f)

        # Load regions
        for region_data in data.get("regions", []):
            region = Region.from_dict(region_data)
            self._regions[region.slug] = region

        # Load jurisdictions
        for jurisdiction_data in data.get("jurisdictions", []):
            jurisdiction = Jurisdiction.from_dict(jurisdiction_data)
            self._jurisdictions[jurisdiction.slug] = jurisdiction

        # Load plans
        for plan_data in data.get("plans", []):
            plan = Plan.from_dict(plan_data)
            self._plans[plan.slug] = plan

        self._loaded = True
        logger.info(
            f"Loaded {len(self._regions)} regions, {len(self._jurisdictions)} jurisdictions, {len(self._plans)} plans"
        )

    def _ensure_loaded(self) -> None:
        """Ensure configuration is loaded."""
        if not self._loaded:
            self.load()

    @property
    def regions(self) -> Dict[str, Region]:
        """Get all regions."""
        self._ensure_loaded()
        return self._regions.copy()

    @property
    def jurisdictions(self) -> Dict[str, Jurisdiction]:
        """Get all jurisdictions."""
        self._ensure_loaded()
        return self._jurisdictions.copy()

    @property
    def plans(self) -> Dict[str, Plan]:
        """Get all plans."""
        self._ensure_loaded()
        return self._plans.copy()

    def get_region(self, slug: str) -> Optional[Region]:
        """Get region by slug."""
        self._ensure_loaded()
        return self._regions.get(slug)

    def get_jurisdiction(self, slug: str) -> Optional[Jurisdiction]:
        """Get jurisdiction by slug."""
        self._ensure_loaded()
        return self._jurisdictions.get(slug)

    def get_plan(self, slug: str) -> Optional[Plan]:
        """Get plan by slug."""
        self._ensure_loaded()
        return self._plans.get(slug)

    def get_active_jurisdictions(self) -> List[Jurisdiction]:
        """Get all active jurisdictions."""
        self._ensure_loaded()
        return [j for j in self._jurisdictions.values() if j.active]

    def get_jurisdictions_by_region(self, region_slug: str) -> List[Jurisdiction]:
        """Get all jurisdictions in a region."""
        self._ensure_loaded()
        return [j for j in self._jurisdictions.values() if j.region_slug == region_slug]

    def get_jurisdictions_by_state(self, state: str) -> List[Jurisdiction]:
        """Get all jurisdictions in a state."""
        self._ensure_loaded()
        return [j for j in self._jurisdictions.values() if j.state == state]

    def get_plans_by_scope(self, scope: str) -> List[Plan]:
        """Get plans by scope (metro, state, national)."""
        self._ensure_loaded()
        return [p for p in self._plans.values() if p.scope == scope]


# Global instance
_config_loader = None


def get_config_loader() -> ConfigLoader:
    """Get global config loader instance."""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader


def reload_config():
    """Reload configuration from registry file."""
    global _config_loader
    if _config_loader is not None:
        _config_loader._loaded = False
        _config_loader.load()
