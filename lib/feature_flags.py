"""Feature flag configuration and utilities for Texas data ingestion."""

import os
from typing import Dict, Any, Optional


class FeatureFlags:
    """Feature flag management for the Texas data ingestion system."""
    
    def __init__(self):
        """Initialize feature flags from environment variables."""
        self._flags = {
            # Weather integration feature flag
            "USE_WEATHER": self._get_bool_env("USE_WEATHER", False),
            
            # Additional feature flags for future use
            "USE_GEOCODING": self._get_bool_env("USE_GEOCODING", True),
            "USE_ENTITY_RESOLUTION": self._get_bool_env("USE_ENTITY_RESOLUTION", True),
            "USE_DATA_VALIDATION": self._get_bool_env("USE_DATA_VALIDATION", True),
            "USE_INCREMENTAL_LOADS": self._get_bool_env("USE_INCREMENTAL_LOADS", True),
            
            # Debug and development flags
            "DEBUG_MODE": self._get_bool_env("DEBUG_MODE", False),
            "MOCK_DATA_SOURCES": self._get_bool_env("MOCK_DATA_SOURCES", False),
        }
        
    def _get_bool_env(self, key: str, default: bool) -> bool:
        """Get boolean value from environment variable."""
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")
        
    def is_enabled(self, flag_name: str) -> bool:
        """Check if a feature flag is enabled."""
        return self._flags.get(flag_name, False)
        
    def get_flag(self, flag_name: str, default: Any = None) -> Any:
        """Get feature flag value with optional default."""
        return self._flags.get(flag_name, default)
        
    def set_flag(self, flag_name: str, value: Any):
        """Set feature flag value (for testing)."""
        self._flags[flag_name] = value
        
    def get_all_flags(self) -> Dict[str, Any]:
        """Get all feature flags."""
        return self._flags.copy()
        
    @property
    def use_weather(self) -> bool:
        """Check if weather integration is enabled."""
        return self.is_enabled("USE_WEATHER")
        
    @property
    def use_geocoding(self) -> bool:
        """Check if geocoding is enabled."""
        return self.is_enabled("USE_GEOCODING")
        
    @property
    def use_entity_resolution(self) -> bool:
        """Check if entity resolution is enabled."""
        return self.is_enabled("USE_ENTITY_RESOLUTION")
        
    @property
    def use_data_validation(self) -> bool:
        """Check if data validation is enabled."""
        return self.is_enabled("USE_DATA_VALIDATION")
        
    @property
    def debug_mode(self) -> bool:
        """Check if debug mode is enabled."""
        return self.is_enabled("DEBUG_MODE")


# Global feature flags instance
feature_flags = FeatureFlags()


def weather_enabled() -> bool:
    """Convenience function to check if weather features are enabled."""
    return feature_flags.use_weather


def with_weather_guard(func):
    """Decorator to guard functions that require weather features."""
    def wrapper(*args, **kwargs):
        if not weather_enabled():
            raise RuntimeError(
                "Weather features are disabled. Set USE_WEATHER=true to enable."
            )
        return func(*args, **kwargs)
    return wrapper


class WeatherIntegration:
    """Weather integration module (placeholder implementation)."""
    
    def __init__(self):
        """Initialize weather integration."""
        if not weather_enabled():
            raise RuntimeError("Weather integration is disabled")
            
    @with_weather_guard
    def get_weather_data(self, location: str, date: str) -> Optional[Dict[str, Any]]:
        """Get weather data for a location and date."""
        # This would integrate with weather APIs when enabled
        return {
            "location": location,
            "date": date,
            "temperature": None,
            "precipitation": None,
            "conditions": None,
            "note": "Weather integration is not implemented yet"
        }
        
    @with_weather_guard
    def enrich_permit_with_weather(self, permit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich permit data with weather information."""
        # This would add weather context to permit records
        enriched = permit_data.copy()
        
        address = permit_data.get("address")
        issued_date = permit_data.get("issued_date")
        
        if address and issued_date:
            weather_data = self.get_weather_data(address, issued_date)
            enriched["weather_context"] = weather_data
            
        return enriched


def create_weather_integration() -> Optional[WeatherIntegration]:
    """Create weather integration instance if enabled."""
    if weather_enabled():
        return WeatherIntegration()
    return None


# Example of guarded weather functionality
def process_permits_with_weather(permits: list) -> list:
    """Process permits with optional weather enrichment."""
    if not weather_enabled():
        # Just return permits without weather data
        return permits
        
    try:
        weather_integration = WeatherIntegration()
        enriched_permits = []
        
        for permit in permits:
            try:
                enriched = weather_integration.enrich_permit_with_weather(permit)
                enriched_permits.append(enriched)
            except Exception as e:
                # Log error and continue without weather data
                print(f"Warning: Could not enrich permit with weather data: {e}")
                enriched_permits.append(permit)
                
        return enriched_permits
        
    except Exception as e:
        print(f"Weather integration failed: {e}")
        return permits


if __name__ == "__main__":
    # Example usage and testing
    print("Feature Flags Status:")
    flags = feature_flags.get_all_flags()
    for flag_name, value in flags.items():
        status = "✓" if value else "✗"
        print(f"  {status} {flag_name}: {value}")
        
    print(f"\nWeather integration enabled: {weather_enabled()}")
    
    # Test weather integration
    if weather_enabled():
        try:
            weather = WeatherIntegration()
            print("Weather integration initialized successfully")
        except Exception as e:
            print(f"Weather integration failed: {e}")
    else:
        print("Weather integration is disabled (USE_WEATHER=false)")
        
    # Test guarded functionality
    sample_permits = [
        {
            "permit_number": "P123",
            "address": "123 Main St, Houston, TX",
            "issued_date": "2024-01-15"
        }
    ]
    
    processed = process_permits_with_weather(sample_permits)
    print(f"\nProcessed {len(processed)} permits")
    
    if weather_enabled() and "weather_context" in processed[0]:
        print("Weather data was added to permits")
    else:
        print("No weather data added (feature disabled or unavailable)")