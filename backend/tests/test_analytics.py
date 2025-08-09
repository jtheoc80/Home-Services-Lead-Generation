#!/usr/bin/env python3
"""
Tests for the analytics tracking functionality.

This module tests the analytics service, event tracking, and provider integrations.
"""

import os
import unittest
from unittest.mock import patch, MagicMock
import sys
import json

# Add the backend app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from utils.analytics import (
    AnalyticsConfig, 
    AnalyticsService, 
    get_analytics_service,
    track_cancellation_event,
    track_reactivation_event
)


class TestAnalyticsConfig(unittest.TestCase):
    """Test analytics configuration functionality."""
    
    def setUp(self):
        # Clear environment variables
        for var in ['ANALYTICS_PROVIDER', 'ANALYTICS_API_KEY']:
            if var in os.environ:
                del os.environ[var]
    
    def test_config_from_env_disabled_by_default(self):
        """Test that analytics is disabled by default."""
        config = AnalyticsConfig.from_env()
        
        self.assertEqual(config.provider, 'none')
        self.assertIsNone(config.api_key)
        self.assertFalse(config.is_enabled())
    
    def test_config_from_env_with_posthog(self):
        """Test analytics configuration with PostHog."""
        os.environ['ANALYTICS_PROVIDER'] = 'posthog'
        os.environ['ANALYTICS_API_KEY'] = 'test_posthog_key'
        
        config = AnalyticsConfig.from_env()
        
        self.assertEqual(config.provider, 'posthog')
        self.assertEqual(config.api_key, 'test_posthog_key')
        self.assertTrue(config.is_enabled())
    
    def test_config_from_env_with_segment(self):
        """Test analytics configuration with Segment."""
        os.environ['ANALYTICS_PROVIDER'] = 'segment'
        os.environ['ANALYTICS_API_KEY'] = 'test_segment_key'
        
        config = AnalyticsConfig.from_env()
        
        self.assertEqual(config.provider, 'segment')
        self.assertEqual(config.api_key, 'test_segment_key')
        self.assertTrue(config.is_enabled())
    
    def test_config_case_insensitive(self):
        """Test that provider names are case insensitive."""
        os.environ['ANALYTICS_PROVIDER'] = 'POSTHOG'
        os.environ['ANALYTICS_API_KEY'] = 'test_key'
        
        config = AnalyticsConfig.from_env()
        
        self.assertEqual(config.provider, 'posthog')
        self.assertTrue(config.is_enabled())
    
    def test_config_missing_api_key(self):
        """Test that service is disabled without API key."""
        os.environ['ANALYTICS_PROVIDER'] = 'posthog'
        # No API key set
        
        config = AnalyticsConfig.from_env()
        
        self.assertEqual(config.provider, 'posthog')
        self.assertIsNone(config.api_key)
        self.assertFalse(config.is_enabled())


class TestAnalyticsService(unittest.TestCase):
    """Test analytics service functionality."""
    
    def setUp(self):
        # Clear environment variables
        for var in ['ANALYTICS_PROVIDER', 'ANALYTICS_API_KEY']:
            if var in os.environ:
                del os.environ[var]
    
    def test_service_disabled_by_default(self):
        """Test that service is disabled when no provider is configured."""
        service = AnalyticsService()
        
        self.assertFalse(service.config.is_enabled())
        self.assertIsNone(service._provider_client)
    
    def test_service_with_invalid_provider(self):
        """Test service behavior with invalid provider."""
        config = AnalyticsConfig(provider='invalid', api_key='test_key')
        service = AnalyticsService(config)
        
        # Should not crash, but provider client should remain None
        self.assertIsNone(service._provider_client)
    
    @patch('utils.analytics.logger')
    def test_track_event_disabled_service(self, mock_logger):
        """Test tracking events when service is disabled."""
        service = AnalyticsService()
        
        result = service.track_event(
            event_name='test_event',
            event_type='user_intent',
            account_id='test_account'
        )
        
        self.assertTrue(result)  # Should succeed even when disabled
        mock_logger.debug.assert_called_once()
    
    @patch('utils.analytics.logger')
    def test_track_event_with_properties(self, mock_logger):
        """Test tracking events with custom properties."""
        service = AnalyticsService()
        
        properties = {
            'test_property': 'test_value',
            'numeric_property': 123
        }
        
        result = service.track_event(
            event_name='test_event',
            event_type='system_driven',
            account_id='test_account',
            user_id='test_user',
            properties=properties
        )
        
        self.assertTrue(result)
        # Verify that the event was logged to database (mock implementation)
        # Since the service is disabled, only debug log should be called
        mock_logger.debug.assert_called_once()
    
    @patch('utils.analytics.logger')
    def test_track_event_with_enabled_service(self, mock_logger):
        """Test tracking events with enabled analytics service."""
        config = AnalyticsConfig(provider='posthog', api_key='test_key')
        service = AnalyticsService(config)
        
        # Mock the provider client to avoid import errors
        service._provider_client = MagicMock()
        
        properties = {
            'test_property': 'test_value',
            'numeric_property': 123
        }
        
        result = service.track_event(
            event_name='test_event',
            event_type='system_driven',
            account_id='test_account',
            user_id='test_user',
            properties=properties
        )
        
        self.assertTrue(result)
        # Verify that database logging was called
        self.assertTrue(any('Database log:' in str(call) for call in mock_logger.info.call_args_list))
    
    @patch('utils.analytics.logger')
    def test_track_event_with_posthog(self, mock_logger):
        """Test tracking events with PostHog provider."""
        config = AnalyticsConfig(provider='posthog', api_key='test_key')
        service = AnalyticsService(config)
        
        # Mock the PostHog client directly
        mock_posthog = MagicMock()
        service._provider_client = mock_posthog
        
        result = service.track_event(
            event_name='test_event',
            event_type='user_intent',
            user_id='test_user'
        )
        
        self.assertTrue(result)
        mock_posthog.capture.assert_called_once()
    
    def test_log_to_database_format(self):
        """Test that database logging includes all required fields."""
        service = AnalyticsService()
        
        with patch('utils.analytics.logger') as mock_logger:
            service._log_to_database(
                event_name='test_event',
                event_type='user_intent',
                account_id='test_account',
                user_id='test_user',
                properties={'key': 'value'}
            )
            
            # Verify the log call
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            
            # Extract JSON from log message
            json_str = log_message.replace('Database log: ', '')
            event_data = json.loads(json_str)
            
            # Verify all required fields are present
            self.assertEqual(event_data['event_name'], 'test_event')
            self.assertEqual(event_data['event_type'], 'user_intent')
            self.assertEqual(event_data['account_id'], 'test_account')
            self.assertEqual(event_data['user_id'], 'test_user')
            self.assertEqual(event_data['properties']['key'], 'value')
            self.assertEqual(event_data['provider'], 'none')
            self.assertIn('created_at', event_data)


class TestAnalyticsHelperFunctions(unittest.TestCase):
    """Test analytics helper functions for cancellation and reactivation."""
    
    def setUp(self):
        # Clear environment variables
        for var in ['ANALYTICS_PROVIDER', 'ANALYTICS_API_KEY']:
            if var in os.environ:
                del os.environ[var]
    
    @patch('utils.analytics.get_analytics_service')
    def test_track_cancellation_event(self, mock_get_service):
        """Test cancellation event tracking."""
        mock_service = MagicMock()
        mock_service.track_event.return_value = True
        mock_get_service.return_value = mock_service
        
        result = track_cancellation_event(
            account_id='test_account',
            user_id='test_user',
            cancellation_reason='too_expensive',
            subscription_type='premium'
        )
        
        self.assertTrue(result)
        mock_service.track_event.assert_called_once_with(
            event_name='subscription_cancelled',
            event_type='user_intent',
            account_id='test_account',
            user_id='test_user',
            properties={
                'cancellation_reason': 'too_expensive',
                'subscription_type': 'premium'
            }
        )
    
    @patch('utils.analytics.get_analytics_service')
    def test_track_cancellation_event_minimal(self, mock_get_service):
        """Test cancellation event tracking with minimal parameters."""
        mock_service = MagicMock()
        mock_service.track_event.return_value = True
        mock_get_service.return_value = mock_service
        
        result = track_cancellation_event()
        
        self.assertTrue(result)
        mock_service.track_event.assert_called_once_with(
            event_name='subscription_cancelled',
            event_type='user_intent',
            account_id=None,
            user_id=None,
            properties={}
        )
    
    @patch('utils.analytics.get_analytics_service')
    def test_track_reactivation_event(self, mock_get_service):
        """Test reactivation event tracking."""
        mock_service = MagicMock()
        mock_service.track_event.return_value = True
        mock_get_service.return_value = mock_service
        
        result = track_reactivation_event(
            account_id='test_account',
            user_id='test_user',
            reactivation_source='email_campaign',
            subscription_type='premium',
            event_type='system_driven'
        )
        
        self.assertTrue(result)
        mock_service.track_event.assert_called_once_with(
            event_name='subscription_reactivated',
            event_type='system_driven',
            account_id='test_account',
            user_id='test_user',
            properties={
                'reactivation_source': 'email_campaign',
                'subscription_type': 'premium'
            }
        )
    
    @patch('utils.analytics.get_analytics_service')
    def test_track_reactivation_event_minimal(self, mock_get_service):
        """Test reactivation event tracking with minimal parameters."""
        mock_service = MagicMock()
        mock_service.track_event.return_value = True
        mock_get_service.return_value = mock_service
        
        result = track_reactivation_event()
        
        self.assertTrue(result)
        mock_service.track_event.assert_called_once_with(
            event_name='subscription_reactivated',
            event_type='user_intent',
            account_id=None,
            user_id=None,
            properties={}
        )
    
    def test_get_analytics_service_singleton(self):
        """Test that get_analytics_service returns the same instance."""
        service1 = get_analytics_service()
        service2 = get_analytics_service()
        
        self.assertIs(service1, service2)


if __name__ == '__main__':
    unittest.main()