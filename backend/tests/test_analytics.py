#!/usr/bin/env python3
"""
Tests for the analytics service.
"""

import unittest
from unittest.mock import patch, MagicMock
from uuid import uuid4
import json
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from services.analytics import (
    AnalyticsService, 
    AnalyticsConfig, 
    DatabaseLogger,
    PostHogProvider,
    SegmentProvider,
    MixpanelProvider,
    get_analytics_service,
    track
)


class TestAnalyticsConfig(unittest.TestCase):
    """Test analytics configuration."""
    
    @patch.dict('os.environ', {
        'ANALYTICS_PROVIDER': 'posthog',
        'POSTHOG_API_KEY': 'test_key',
        'POSTHOG_HOST': 'https://test.posthog.com',
        'DATABASE_URL': 'postgresql://test'
    })
    def test_config_from_env(self):
        """Test configuration loading from environment variables."""
        config = AnalyticsConfig.from_env()
        
        self.assertEqual(config.provider, 'posthog')
        self.assertEqual(config.posthog_api_key, 'test_key')
        self.assertEqual(config.posthog_host, 'https://test.posthog.com')
        self.assertEqual(config.database_url, 'postgresql://test')


class TestDatabaseLogger(unittest.TestCase):
    """Test database logging functionality."""
    
    def setUp(self):
        self.account_id = uuid4()
        self.event = 'cancel.confirmed'
        self.properties = {'reason': 'too_expensive', 'plan': 'basic'}
    
    @patch('psycopg2.connect')
    def test_log_event_success(self, mock_connect):
        """Test successful event logging."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        logger = DatabaseLogger('postgresql://test')
        result = logger.log_event(self.event, self.account_id, self.properties)
        
        self.assertTrue(result)
        mock_cursor.execute.assert_called_once()
        
    def test_log_event_no_database_url(self):
        """Test logging when no database URL is provided."""
        logger = DatabaseLogger(None)
        result = logger.log_event(self.event, self.account_id, self.properties)
        
        self.assertFalse(result)
    
    @patch('psycopg2.connect')
    def test_log_event_database_error(self, mock_connect):
        """Test logging when database error occurs."""
        mock_connect.side_effect = Exception("Database connection failed")
        
        logger = DatabaseLogger('postgresql://test')
        result = logger.log_event(self.event, self.account_id, self.properties)
        
        self.assertFalse(result)


class TestPostHogProvider(unittest.TestCase):
    """Test PostHog provider."""
    
    def setUp(self):
        self.account_id = uuid4()
        self.event = 'cancel.confirmed'
        self.properties = {'reason': 'too_expensive', 'plan': 'basic'}
    
    def test_track_success(self):
        """Test successful PostHog tracking."""
        provider = PostHogProvider('test_key')
        
        # Mock the client directly
        mock_client = MagicMock()
        provider._client = mock_client
        
        result = provider.track(self.event, self.account_id, self.properties)
        
        self.assertTrue(result)
        mock_client.capture.assert_called_once_with(
            distinct_id=str(self.account_id),
            event=self.event,
            properties=self.properties
        )
    
    def test_track_no_client(self):
        """Test tracking when PostHog client is not available."""
        provider = PostHogProvider('test_key')
        
        with patch.object(provider, '_get_client', return_value=None):
            result = provider.track(self.event, self.account_id, self.properties)
            
        self.assertFalse(result)


class TestAnalyticsService(unittest.TestCase):
    """Test main analytics service."""
    
    def setUp(self):
        self.account_id = uuid4()
        self.event = 'cancel.confirmed'
        self.properties = {'reason': 'too_expensive', 'plan': 'basic'}
    
    @patch('services.analytics.DatabaseLogger')
    @patch('services.analytics.PostHogProvider')
    def test_track_with_provider(self, mock_posthog_provider, mock_db_logger):
        """Test tracking with external provider."""
        # Setup mocks
        mock_config = AnalyticsConfig(
            provider='posthog',
            posthog_api_key='test_key',
            database_url='postgresql://test'
        )
        mock_db_instance = mock_db_logger.return_value
        mock_db_instance.log_event.return_value = True
        
        mock_provider_instance = mock_posthog_provider.return_value
        mock_provider_instance.track.return_value = True
        
        # Test tracking
        service = AnalyticsService(mock_config)
        result = service.track(self.event, self.account_id, self.properties)
        
        # Verify both database and provider were called
        self.assertTrue(result['database'])
        self.assertTrue(result['provider'])
        mock_db_instance.log_event.assert_called_once()
        mock_provider_instance.track.assert_called_once()
    
    @patch('services.analytics.DatabaseLogger')
    def test_track_database_only(self, mock_db_logger):
        """Test tracking with database only (no external provider)."""
        mock_config = AnalyticsConfig(
            provider='none',
            database_url='postgresql://test'
        )
        mock_db_instance = mock_db_logger.return_value
        mock_db_instance.log_event.return_value = True
        
        service = AnalyticsService(mock_config)
        result = service.track(self.event, self.account_id, self.properties)
        
        self.assertTrue(result['database'])
        self.assertFalse(result['provider'])
        mock_db_instance.log_event.assert_called_once()
    
    @patch('services.analytics.DatabaseLogger')
    def test_track_cancellation(self, mock_db_logger):
        """Test cancellation tracking convenience method."""
        mock_config = AnalyticsConfig(database_url='postgresql://test')
        mock_db_instance = mock_db_logger.return_value
        mock_db_instance.log_event.return_value = True
        
        service = AnalyticsService(mock_config)
        result = service.track_cancellation(
            account_id=self.account_id,
            reason='too_expensive',
            notes_length=25,
            plan='basic',
            effective_at='end_of_period',
            trial_or_paid='paid'
        )
        
        self.assertTrue(result['database'])
        mock_db_instance.log_event.assert_called_once()
        
        # Verify the event properties
        call_args = mock_db_instance.log_event.call_args[0]
        self.assertEqual(call_args[0], 'cancel.confirmed')  # event name
        self.assertEqual(call_args[1], self.account_id)     # account_id
        
        properties = call_args[2]  # properties
        self.assertEqual(properties['reason'], 'too_expensive')
        self.assertEqual(properties['notes_length'], 25)
        self.assertEqual(properties['plan'], 'basic')
        self.assertEqual(properties['effective_at'], 'end_of_period')
        self.assertEqual(properties['trial_or_paid'], 'paid')
        self.assertEqual(properties['source'], 'user')
    
    @patch('services.analytics.DatabaseLogger')
    def test_track_reactivation(self, mock_db_logger):
        """Test reactivation tracking convenience method."""
        mock_config = AnalyticsConfig(database_url='postgresql://test')
        mock_db_instance = mock_db_logger.return_value
        mock_db_instance.log_event.return_value = True
        
        service = AnalyticsService(mock_config)
        result = service.track_reactivation(
            account_id=self.account_id,
            plan='basic',
            payment_provider='stripe'
        )
        
        self.assertTrue(result['database'])
        mock_db_instance.log_event.assert_called_once()
        
        # Verify the event properties
        call_args = mock_db_instance.log_event.call_args[0]
        self.assertEqual(call_args[0], 'reactivate.confirmed')  # event name
        self.assertEqual(call_args[1], self.account_id)         # account_id
        
        properties = call_args[2]  # properties
        self.assertEqual(properties['plan'], 'basic')
        self.assertEqual(properties['payment_provider'], 'stripe')
        self.assertEqual(properties['source'], 'user')


class TestGlobalFunctions(unittest.TestCase):
    """Test global analytics functions."""
    
    @patch('services.analytics.AnalyticsService')
    def test_get_analytics_service_singleton(self, mock_service_class):
        """Test that get_analytics_service returns a singleton."""
        # Reset the global service
        import services.analytics
        services.analytics._analytics_service = None
        
        service1 = get_analytics_service()
        service2 = get_analytics_service()
        
        self.assertIs(service1, service2)
        mock_service_class.assert_called_once()
    
    @patch('services.analytics.get_analytics_service')
    def test_track_convenience_function(self, mock_get_service):
        """Test the convenience track function."""
        mock_service = MagicMock()
        mock_service.track.return_value = {'database': True, 'provider': False}
        mock_get_service.return_value = mock_service
        
        account_id = uuid4()
        properties = {'test': 'value'}
        result = track('test.event', account_id, properties)
        
        self.assertEqual(result, {'database': True, 'provider': False})
        mock_service.track.assert_called_once_with('test.event', account_id, properties)


if __name__ == '__main__':
    unittest.main()