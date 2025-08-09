#!/usr/bin/env python3
"""
Analytics service for tracking events across multiple providers.

This module provides a unified interface for tracking analytics events
that can be sent to various analytics providers (PostHog, Segment, etc.)
and also logged to the database for reliable server-side tracking.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timezone
from dataclasses import dataclass
import psycopg2
from psycopg2.extras import Json

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class AnalyticsConfig:
    """Configuration for analytics services."""
    provider: str = 'none'
    posthog_api_key: Optional[str] = None
    posthog_host: Optional[str] = None
    segment_write_key: Optional[str] = None
    mixpanel_token: Optional[str] = None
    database_url: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'AnalyticsConfig':
        """Create configuration from environment variables."""
        return cls(
            provider=os.getenv('ANALYTICS_PROVIDER', 'none'),
            posthog_api_key=os.getenv('POSTHOG_API_KEY'),
            posthog_host=os.getenv('POSTHOG_HOST', 'https://app.posthog.com'),
            segment_write_key=os.getenv('SEGMENT_WRITE_KEY'),
            mixpanel_token=os.getenv('MIXPANEL_TOKEN'),
            database_url=os.getenv('DATABASE_URL')
        )


class DatabaseLogger:
    """Handles logging analytics events to the database."""
    
    def __init__(self, database_url: Optional[str]):
        self.database_url = database_url
        self._connection = None
    
    def _get_connection(self):
        """Get database connection."""
        if not self.database_url:
            return None
            
        if self._connection is None or self._connection.closed:
            try:
                self._connection = psycopg2.connect(self.database_url)
                self._connection.autocommit = True
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                return None
        
        return self._connection
    
    def log_event(self, event: str, account_id: UUID, properties: Dict[str, Any]) -> bool:
        """
        Log analytics event to database.
        
        Args:
            event: Event name
            account_id: User/account identifier
            properties: Event properties
            
        Returns:
            True if logged successfully, False otherwise
        """
        connection = self._get_connection()
        if not connection:
            logger.warning("Database connection not available. Skipping database logging.")
            return False
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO analytics_events (account_id, event, properties, created_at)
                    VALUES (%s, %s, %s, %s)
                """, (
                    str(account_id),
                    event,
                    Json(properties),
                    datetime.now(timezone.utc)
                ))
            
            logger.debug(f"Logged analytics event to database: {event}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log analytics event to database: {e}")
            return False
    
    def close(self):
        """Close database connection."""
        if self._connection and not self._connection.closed:
            self._connection.close()


class PostHogProvider:
    """PostHog analytics provider."""
    
    def __init__(self, api_key: str, host: str = 'https://app.posthog.com'):
        self.api_key = api_key
        self.host = host
        self._client = None
    
    def _get_client(self):
        """Lazy load PostHog client."""
        if self._client is None:
            try:
                import posthog
                posthog.api_key = self.api_key
                posthog.host = self.host
                self._client = posthog
            except ImportError:
                logger.warning("PostHog library not installed. PostHog tracking disabled.")
                return None
        return self._client
    
    def track(self, event: str, account_id: UUID, properties: Dict[str, Any]) -> bool:
        """Track event with PostHog."""
        client = self._get_client()
        if not client:
            return False
        
        try:
            client.capture(
                distinct_id=str(account_id),
                event=event,
                properties=properties
            )
            logger.debug(f"Tracked event with PostHog: {event}")
            return True
        except Exception as e:
            logger.error(f"PostHog tracking failed: {e}")
            return False


class SegmentProvider:
    """Segment analytics provider."""
    
    def __init__(self, write_key: str):
        self.write_key = write_key
        self._client = None
    
    def _get_client(self):
        """Lazy load Segment client."""
        if self._client is None:
            try:
                import analytics
                analytics.write_key = self.write_key
                self._client = analytics
            except ImportError:
                logger.warning("Segment analytics library not installed. Segment tracking disabled.")
                return None
        return self._client
    
    def track(self, event: str, account_id: UUID, properties: Dict[str, Any]) -> bool:
        """Track event with Segment."""
        client = self._get_client()
        if not client:
            return False
        
        try:
            client.track(
                user_id=str(account_id),
                event=event,
                properties=properties
            )
            logger.debug(f"Tracked event with Segment: {event}")
            return True
        except Exception as e:
            logger.error(f"Segment tracking failed: {e}")
            return False


class MixpanelProvider:
    """Mixpanel analytics provider."""
    
    def __init__(self, token: str):
        self.token = token
        self._client = None
    
    def _get_client(self):
        """Lazy load Mixpanel client."""
        if self._client is None:
            try:
                from mixpanel import Mixpanel
                self._client = Mixpanel(self.token)
            except ImportError:
                logger.warning("Mixpanel library not installed. Mixpanel tracking disabled.")
                return None
        return self._client
    
    def track(self, event: str, account_id: UUID, properties: Dict[str, Any]) -> bool:
        """Track event with Mixpanel."""
        client = self._get_client()
        if not client:
            return False
        
        try:
            client.track(str(account_id), event, properties)
            logger.debug(f"Tracked event with Mixpanel: {event}")
            return True
        except Exception as e:
            logger.error(f"Mixpanel tracking failed: {e}")
            return False


class AnalyticsService:
    """Main analytics service that coordinates tracking across providers."""
    
    def __init__(self, config: Optional[AnalyticsConfig] = None):
        self.config = config or AnalyticsConfig.from_env()
        self.database_logger = DatabaseLogger(self.config.database_url)
        self.provider = self._initialize_provider()
    
    def _initialize_provider(self):
        """Initialize the configured analytics provider."""
        provider_name = self.config.provider.lower()
        
        if provider_name == 'posthog' and self.config.posthog_api_key:
            return PostHogProvider(self.config.posthog_api_key, self.config.posthog_host or 'https://app.posthog.com')
        elif provider_name == 'segment' and self.config.segment_write_key:
            return SegmentProvider(self.config.segment_write_key)
        elif provider_name == 'mixpanel' and self.config.mixpanel_token:
            return MixpanelProvider(self.config.mixpanel_token)
        else:
            logger.info(f"Analytics provider '{provider_name}' not configured or not supported")
            return None
    
    def track(self, event: str, account_id: UUID, properties: Dict[str, Any]) -> Dict[str, bool]:
        """
        Track an analytics event.
        
        Args:
            event: Event name
            account_id: User/account identifier
            properties: Event properties
            
        Returns:
            Dictionary with tracking results for each target
        """
        results = {
            'database': False,
            'provider': False
        }
        
        # Always try to log to database for reliable server-side tracking
        results['database'] = self.database_logger.log_event(event, account_id, properties)
        
        # Track with external provider if configured
        if self.provider:
            results['provider'] = self.provider.track(event, account_id, properties)
        
        logger.info(f"Analytics event tracked: {event} (database: {results['database']}, provider: {results['provider']})")
        return results
    
    def track_cancellation(
        self,
        account_id: UUID,
        reason: str,
        notes_length: int,
        plan: str,
        effective_at: str,
        trial_or_paid: str,
        source: str = 'user'
    ) -> Dict[str, bool]:
        """Track subscription cancellation event."""
        return self.track('cancel.confirmed', account_id, {
            'reason': reason,
            'notes_length': notes_length,
            'plan': plan,
            'effective_at': effective_at,
            'trial_or_paid': trial_or_paid,
            'source': source,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    def track_reactivation(
        self,
        account_id: UUID,
        plan: str,
        payment_provider: str,
        source: str = 'user'
    ) -> Dict[str, bool]:
        """Track subscription reactivation event."""
        return self.track('reactivate.confirmed', account_id, {
            'plan': plan,
            'payment_provider': payment_provider,
            'source': source,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    def close(self):
        """Clean up resources."""
        self.database_logger.close()


# Global analytics service instance
_analytics_service = None

def get_analytics_service() -> AnalyticsService:
    """Get the global analytics service instance."""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service


def track(event: str, account_id: UUID, properties: Dict[str, Any]) -> Dict[str, bool]:
    """
    Convenience function to track an analytics event.
    
    Args:
        event: Event name
        account_id: User/account identifier  
        properties: Event properties
        
    Returns:
        Dictionary with tracking results
    """
    service = get_analytics_service()
    return service.track(event, account_id, properties)