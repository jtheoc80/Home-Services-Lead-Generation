#!/usr/bin/env python3
"""
Launch configuration utility for managing scope and region settings.

This module provides configuration for launch scope, default region,
and registry path settings from environment variables.
"""

import os
import logging
from typing import Optional
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class LaunchConfig:
    """Configuration for launch scope and region settings."""

    launch_scope: str = "houston"
    default_region: str = "tx-houston"
    registry_path: str = "config/registry.yaml"

    @classmethod
    def from_env(cls) -> "LaunchConfig":
        """Create configuration from environment variables."""
        return cls(
            launch_scope=os.getenv("LAUNCH_SCOPE", "houston"),
            default_region=os.getenv("DEFAULT_REGION", "tx-houston"),
            registry_path=os.getenv("REGISTRY_PATH", "config/registry.yaml"),
        )

    def validate(self) -> bool:
        """Validate configuration settings."""
        if not self.launch_scope:
            logger.error("Launch scope cannot be empty")
            return False

        if not self.default_region:
            logger.error("Default region cannot be empty")
            return False

        if not self.registry_path:
            logger.error("Registry path cannot be empty")
            return False

        return True

    def get_registry_full_path(self, base_path: Optional[str] = None) -> str:
        """Get the full path to the registry file."""
        if base_path:
            return os.path.join(base_path, self.registry_path)
        return self.registry_path

    def is_scope_enabled(self, scope: str) -> bool:
        """Check if a specific scope is enabled."""
        return scope.lower() == self.launch_scope.lower()

    def is_region_enabled(self, region: str) -> bool:
        """Check if a specific region is enabled."""
        return region.lower() == self.default_region.lower()


class LaunchManager:
    """Manager for launch configuration and scope checking."""

    def __init__(self, config: Optional[LaunchConfig] = None):
        self.config = config or LaunchConfig.from_env()

        if not self.config.validate():
            raise ValueError("Invalid launch configuration")

    def get_active_scope(self) -> str:
        """Get the currently active launch scope."""
        return self.config.launch_scope

    def get_default_region(self) -> str:
        """Get the default region."""
        return self.config.default_region

    def get_registry_path(self, base_path: Optional[str] = None) -> str:
        """Get the registry file path."""
        return self.config.get_registry_full_path(base_path)

    def should_process_region(self, region: str) -> bool:
        """Determine if a region should be processed based on launch scope."""
        # For houston scope, process tx-houston and related regions
        if self.config.launch_scope == "houston":
            houston_regions = [
                "tx-houston",
                "tx-harris",
                "tx-fort-bend",
                "tx-brazoria",
                "tx-galveston",
            ]
            return region in houston_regions

        # For other scopes, check if region matches default
        return self.config.is_region_enabled(region)

    def get_launch_info(self) -> dict:
        """Get comprehensive launch information."""
        return {
            "launch_scope": self.config.launch_scope,
            "default_region": self.config.default_region,
            "registry_path": self.config.registry_path,
            "is_valid": self.config.validate(),
        }


# Global instance for easy access
_launch_manager: Optional[LaunchManager] = None


def get_launch_manager() -> LaunchManager:
    """Get global launch manager instance."""
    global _launch_manager
    if _launch_manager is None:
        _launch_manager = LaunchManager()
    return _launch_manager


def get_launch_config() -> LaunchConfig:
    """Get launch configuration."""
    return get_launch_manager().config
