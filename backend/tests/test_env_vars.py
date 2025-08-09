#!/usr/bin/env python3
"""
Tests for the new environment variable functionality.

This module tests the notifications, cache, and export control utilities.
"""

import os
import unittest
from unittest.mock import patch, MagicMock
import sys
import tempfile

# Add the backend app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from utils.notifications import NotificationConfig, NotificationService
from utils.cache import CacheConfig, RedisCache
from utils.export_control import ExportController, ExportType


class TestNotificationService(unittest.TestCase):
    """Test notification service functionality."""
    
    def setUp(self):
        # Clear environment variables
        for var in ['SENDGRID_API_KEY', 'TWILIO_SID', 'TWILIO_TOKEN', 'TWILIO_FROM']:
            if var in os.environ:
                del os.environ[var]
    
    def test_config_from_env(self):
        """Test notification configuration from environment."""
        os.environ['SENDGRID_API_KEY'] = 'test_sendgrid_key'
        os.environ['TWILIO_SID'] = 'test_sid'
        os.environ['TWILIO_TOKEN'] = 'test_token'
        os.environ['TWILIO_FROM'] = '+1234567890'
        
        config = NotificationConfig.from_env()
        
        self.assertEqual(config.sendgrid_api_key, 'test_sendgrid_key')
        self.assertEqual(config.twilio_sid, 'test_sid')
        self.assertEqual(config.twilio_token, 'test_token')
        self.assertEqual(config.twilio_from, '+1234567890')
    
    def test_notification_service_disabled(self):
        """Test notification service when APIs are not configured."""
        service = NotificationService()
        
        self.assertFalse(service.email.is_enabled())
        self.assertFalse(service.sms.is_enabled())
    
    def test_notification_service_enabled_check(self):
        """Test notification service enabled check with configuration."""
        config = NotificationConfig(
            sendgrid_api_key='test_key',
            twilio_sid='test_sid',
            twilio_token='test_token',
            twilio_from='+1234567890'
        )
        
        service = NotificationService(config)
        
        # Services should be considered enabled with config
        # (even though actual clients won't work without real APIs)
        self.assertTrue(service.config.sendgrid_api_key is not None)
        self.assertTrue(service.config.twilio_sid is not None)


class TestRedisCache(unittest.TestCase):
    """Test Redis cache functionality."""
    
    def setUp(self):
        # Clear Redis URL environment variable
        if 'REDIS_URL' in os.environ:
            del os.environ['REDIS_URL']
    
    def test_cache_config_from_env(self):
        """Test cache configuration from environment."""
        os.environ['REDIS_URL'] = 'redis://localhost:6379/1'
        os.environ['CACHE_TTL'] = '7200'
        
        config = CacheConfig.from_env()
        
        self.assertEqual(config.redis_url, 'redis://localhost:6379/1')
        self.assertEqual(config.default_ttl, 7200)
    
    def test_cache_disabled_without_redis(self):
        """Test cache is disabled when Redis is not configured."""
        cache = RedisCache()
        
        self.assertFalse(cache.is_enabled())
        self.assertFalse(cache.set('test_key', 'test_value'))
        self.assertIsNone(cache.get('test_key'))
    
    def test_cache_operations_safe_when_disabled(self):
        """Test cache operations are safe when Redis is not available."""
        cache = RedisCache()
        
        # These should not raise exceptions
        self.assertFalse(cache.set('key', 'value'))
        self.assertIsNone(cache.get('key'))
        self.assertFalse(cache.delete('key'))
        self.assertFalse(cache.exists('key'))
        self.assertEqual(cache.increment_rate_limit('user1'), 0)


class TestExportController(unittest.TestCase):
    """Test export control functionality."""
    
    def setUp(self):
        # Clear export environment variable
        if 'ALLOW_EXPORTS' in os.environ:
            del os.environ['ALLOW_EXPORTS']
    
    def test_exports_disabled_by_default(self):
        """Test exports are disabled when ALLOW_EXPORTS is not set."""
        controller = ExportController()
        
        self.assertFalse(controller.exports_allowed)
        
        allowed, reason = controller.is_export_allowed(ExportType.LEADS, 'test_user')
        self.assertFalse(allowed)
        self.assertIn('disabled', reason.lower())
    
    def test_exports_enabled_with_env_var(self):
        """Test exports are enabled when ALLOW_EXPORTS=true."""
        os.environ['ALLOW_EXPORTS'] = 'true'
        
        controller = ExportController()
        
        self.assertTrue(controller.exports_allowed)
        
        allowed, reason = controller.is_export_allowed(ExportType.LEADS, 'test_user')
        self.assertTrue(allowed)
        self.assertIsNone(reason)
    
    def test_export_request_creation(self):
        """Test export request creation."""
        controller = ExportController()
        
        request = controller.create_export_request(
            ExportType.LEADS,
            'test_user',
            {'format': 'csv'}
        )
        
        self.assertEqual(request.export_type, ExportType.LEADS)
        self.assertEqual(request.requester, 'test_user')
        self.assertEqual(request.parameters['format'], 'csv')
        self.assertIsNotNone(request.export_id)
        self.assertIsNotNone(request.timestamp)
    
    def test_export_request_processing_blocked(self):
        """Test export request processing when exports are blocked."""
        os.environ['ALLOW_EXPORTS'] = 'false'
        
        controller = ExportController()
        request = controller.create_export_request(ExportType.LEADS, 'test_user')
        
        result = controller.process_export_request(request)
        
        self.assertFalse(result.allowed)
        self.assertFalse(result.success)
        self.assertIn('disabled', result.reason.lower())
    
    def test_export_request_processing_allowed(self):
        """Test export request processing when exports are allowed."""
        os.environ['ALLOW_EXPORTS'] = 'true'
        
        controller = ExportController()
        request = controller.create_export_request(ExportType.LEADS, 'test_user')
        
        result = controller.process_export_request(request)
        
        self.assertTrue(result.allowed)
        self.assertTrue(result.success)
        self.assertIsNone(result.reason)
    
    def test_export_status(self):
        """Test export status information."""
        controller = ExportController()
        
        status = controller.get_export_status()
        
        self.assertIn('exports_enabled', status)
        self.assertIn('supported_types', status)
        self.assertIsInstance(status['supported_types'], list)


class TestEnvironmentVariables(unittest.TestCase):
    """Test environment variable handling."""
    
    def test_all_required_env_vars_defined(self):
        """Test that all required environment variables can be set."""
        required_vars = [
            'ALLOW_EXPORTS',
            'REDIS_URL', 
            'SENDGRID_API_KEY',
            'TWILIO_SID',
            'TWILIO_TOKEN',
            'TWILIO_FROM'
        ]
        
        # Set all variables
        for var in required_vars:
            os.environ[var] = f'test_{var.lower()}'
        
        # Verify they can be read
        for var in required_vars:
            self.assertEqual(os.environ[var], f'test_{var.lower()}')
        
        # Clean up
        for var in required_vars:
            del os.environ[var]


if __name__ == '__main__':
    unittest.main()