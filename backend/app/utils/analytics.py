#!/usr/bin/env python3
"""
Analytics utilities for tracking cancellation and reactivation events.

This module provides utility functions for sending analytics events to various
providers (PostHog, Segment, Mixpanel, GA4) and logging them to the database.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
from datetime import datetime, timezone
import uuid

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class AnalyticsConfig:
    """Configuration for analytics services."""
    provider: str = 'none'  # 'none'|'posthog'|'segment'|'mixpanel'|'ga4'
    api_key: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'AnalyticsConfig':
        """Create configuration from environment variables."""
        return cls(
            provider=os.getenv('ANALYTICS_PROVIDER', 'none').lower(),
            api_key=os.getenv('ANALYTICS_API_KEY')
        )
    
    def is_enabled(self) -> bool:
        """Check if analytics is enabled and properly configured."""
        return self.provider != 'none' and self.api_key is not None


class AnalyticsService:
    """Analytics service for tracking events across different providers."""
    
    def __init__(self, config: Optional[AnalyticsConfig] = None):
        """Initialize analytics service with configuration."""
        self.config = config or AnalyticsConfig.from_env()
        self._provider_client = None
        
        if self.config.is_enabled():
            self._initialize_provider()
    
    def _initialize_provider(self):
        """Initialize the analytics provider client."""
        try:
            if self.config.provider == 'posthog':
                self._initialize_posthog()
            elif self.config.provider == 'segment':
                self._initialize_segment()
            elif self.config.provider == 'mixpanel':
                self._initialize_mixpanel()
            elif self.config.provider == 'ga4':
                self._initialize_ga4()
        except Exception as e:
            logger.error(f"Failed to initialize {self.config.provider} analytics: {e}")
            self._provider_client = None
    
    def _initialize_posthog(self):
        """Initialize PostHog client."""
        try:
            import posthog
            posthog.api_key = self.config.api_key
            self._provider_client = posthog
            logger.info("PostHog analytics initialized")
        except ImportError:
            logger.warning("PostHog library not installed. Install with: pip install posthog")
    
    def _initialize_segment(self):
        """Initialize Segment client."""
        try:
            import analytics
            analytics.write_key = self.config.api_key
            self._provider_client = analytics
            logger.info("Segment analytics initialized")
        except ImportError:
            logger.warning("Segment library not installed. Install with: pip install analytics-python")
    
    def _initialize_mixpanel(self):
        """Initialize Mixpanel client."""
        try:
            from mixpanel import Mixpanel
            self._provider_client = Mixpanel(self.config.api_key)
            logger.info("Mixpanel analytics initialized")
        except ImportError:
            logger.warning("Mixpanel library not installed. Install with: pip install mixpanel")
    
    def _initialize_ga4(self):
        """Initialize Google Analytics 4 client."""
        try:
            from google.analytics.data_v1beta import BetaAnalyticsDataClient
            # GA4 requires more complex setup - this is a placeholder
            logger.info("GA4 analytics initialized (placeholder)")
        except ImportError:
            logger.warning("GA4 library not installed. Install with: pip install google-analytics-data")
    
    def track_event(
        self,
        event_name: str,
        event_type: str,
        account_id: Optional[str] = None,
        user_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Track an analytics event.
        
        Args:
            event_name: Name of the event (e.g., 'subscription_cancelled')
            event_type: Type of event ('user_intent' or 'system_driven')
            account_id: Account ID for the event
            user_id: User ID for the event
            properties: Additional properties for the event
            
        Returns:
            bool: True if event was successfully tracked, False otherwise
        """
        if not self.config.is_enabled():
            logger.debug(f"Analytics disabled, skipping event: {event_name}")
            return True
        
        properties = properties or {}
        properties.update({
            'event_type': event_type,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })
        
        # Track with provider
        provider_success = self._track_with_provider(event_name, account_id, user_id, properties)
        
        # Log to database
        db_success = self._log_to_database(event_name, event_type, account_id, user_id, properties)
        
        return provider_success and db_success
    
    def _track_with_provider(
        self,
        event_name: str,
        account_id: Optional[str],
        user_id: Optional[str],
        properties: Dict[str, Any]
    ) -> bool:
        """Send event to the configured analytics provider."""
        if not self._provider_client:
            return True  # Consider it successful if no provider is configured
        
        try:
            user_identifier = user_id or account_id or str(uuid.uuid4())
            
            if self.config.provider == 'posthog':
                self._provider_client.capture(user_identifier, event_name, properties)
            elif self.config.provider == 'segment':
                self._provider_client.track(user_identifier, event_name, properties)
            elif self.config.provider == 'mixpanel':
                self._provider_client.track(user_identifier, event_name, properties)
            elif self.config.provider == 'ga4':
                # GA4 tracking would go here
                logger.info(f"GA4 tracking: {event_name} for {user_identifier}")
            
            logger.info(f"Tracked event '{event_name}' with {self.config.provider}")
            return True
        except Exception as e:
            logger.error(f"Failed to track event with {self.config.provider}: {e}")
            return False
    
    def _log_to_database(
        self,
        event_name: str,
        event_type: str,
        account_id: Optional[str],
        user_id: Optional[str],
        properties: Dict[str, Any]
    ) -> bool:
        """Log event to database for server-side tracking."""
        try:
            # This would normally use a database connection
            # For now, we'll log the event details
            event_data = {
                'event_name': event_name,
                'event_type': event_type,
                'account_id': account_id,
                'user_id': user_id,
                'properties': properties,
                'provider': self.config.provider,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Database log: {json.dumps(event_data, indent=2)}")
            
            # TODO: Implement actual database logging
            # This would require a database connection and SQL execution
            
            return True
        except Exception as e:
            logger.error(f"Failed to log event to database: {e}")
            return False


# Global analytics service instance
_analytics_service: Optional[AnalyticsService] = None


def get_analytics_service() -> AnalyticsService:
    """Get the global analytics service instance."""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service


def track_cancellation_event(
    account_id: Optional[str] = None,
    user_id: Optional[str] = None,
    cancellation_reason: Optional[str] = None,
    subscription_type: Optional[str] = None,
    event_type: str = 'user_intent'
) -> bool:
    """
    Track a subscription cancellation event.
    
    Args:
        account_id: Account ID for the cancellation
        user_id: User ID for the cancellation
        cancellation_reason: Reason for cancellation
        subscription_type: Type of subscription being cancelled
        event_type: 'user_intent' or 'system_driven'
    
    Returns:
        bool: True if event was successfully tracked
    """
    properties = {}
    if cancellation_reason:
        properties['cancellation_reason'] = cancellation_reason
    if subscription_type:
        properties['subscription_type'] = subscription_type
    
    return get_analytics_service().track_event(
        event_name='subscription_cancelled',
        event_type=event_type,
        account_id=account_id,
        user_id=user_id,
        properties=properties
    )


def track_reactivation_event(
    account_id: Optional[str] = None,
    user_id: Optional[str] = None,
    reactivation_source: Optional[str] = None,
    subscription_type: Optional[str] = None,
    event_type: str = 'user_intent'
) -> bool:
    """
    Track a subscription reactivation event.
    
    Args:
        account_id: Account ID for the reactivation
        user_id: User ID for the reactivation
        reactivation_source: Source that triggered reactivation
        subscription_type: Type of subscription being reactivated
        event_type: 'user_intent' or 'system_driven'
    
    Returns:
        bool: True if event was successfully tracked
    """
    properties = {}
    if reactivation_source:
        properties['reactivation_source'] = reactivation_source
    if subscription_type:
        properties['subscription_type'] = subscription_type
    
    return get_analytics_service().track_event(
        event_name='subscription_reactivated',
        event_type=event_type,
        account_id=account_id,
        user_id=user_id,
        properties=properties
    )