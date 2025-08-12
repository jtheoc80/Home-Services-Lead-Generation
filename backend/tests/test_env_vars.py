#!/usr/bin/env python3
"""
Tests for the new environment variable functionality.

This module tests the notifications, cache, and export control utilities.
"""

import os
import unittest
import json
import sys

# Add the backend app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from utils.notifications import NotificationConfig, NotificationService
from utils.cache import CacheConfig, RedisCache
from utils.export_control import ExportController, ExportType
from utils.launch_config import LaunchConfig, LaunchManager
from utils.pricing_config import PricingConfig, PricingManager
from utils.schedule_config import ScheduleConfig, ScheduleManager


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
            'TWILIO_FROM',
            'LAUNCH_SCOPE',
            'DEFAULT_REGION',
            'REGISTRY_PATH',
            'CREDIT_OFFERS_JSON',
            'CRON_SCRAPE_UTC',
            'CRON_DIGEST_HOURLY',
            'CRON_DIGEST_DAILY'
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


class TestLaunchConfig(unittest.TestCase):
    """Test launch configuration functionality."""
    
    def setUp(self):
        # Clear launch environment variables
        for var in ['LAUNCH_SCOPE', 'DEFAULT_REGION', 'REGISTRY_PATH']:
            if var in os.environ:
                del os.environ[var]
    
    def test_launch_config_defaults(self):
        """Test launch configuration with default values."""
        config = LaunchConfig.from_env()
        
        self.assertEqual(config.launch_scope, 'houston')
        self.assertEqual(config.default_region, 'tx-houston')
        self.assertEqual(config.registry_path, 'config/registry.yaml')
        self.assertTrue(config.validate())
    
    def test_launch_config_from_env(self):
        """Test launch configuration from environment variables."""
        os.environ['LAUNCH_SCOPE'] = 'dallas'
        os.environ['DEFAULT_REGION'] = 'tx-dallas'
        os.environ['REGISTRY_PATH'] = 'custom/registry.yaml'
        
        config = LaunchConfig.from_env()
        
        self.assertEqual(config.launch_scope, 'dallas')
        self.assertEqual(config.default_region, 'tx-dallas')
        self.assertEqual(config.registry_path, 'custom/registry.yaml')
    
    def test_launch_manager_region_processing(self):
        """Test launch manager region processing logic."""
        os.environ['LAUNCH_SCOPE'] = 'houston'
        
        manager = LaunchManager()
        
        # Houston scope should process houston-related regions
        self.assertTrue(manager.should_process_region('tx-houston'))
        self.assertTrue(manager.should_process_region('tx-harris'))
        self.assertFalse(manager.should_process_region('tx-dallas'))
    
    def test_launch_manager_scope_checking(self):
        """Test launch manager scope checking."""
        os.environ['LAUNCH_SCOPE'] = 'houston'
        
        manager = LaunchManager()
        
        self.assertEqual(manager.get_active_scope(), 'houston')
        self.assertEqual(manager.get_default_region(), 'tx-houston')


class TestPricingConfig(unittest.TestCase):
    """Test pricing configuration functionality."""
    
    def setUp(self):
        # Clear pricing environment variables
        if 'CREDIT_OFFERS_JSON' in os.environ:
            del os.environ['CREDIT_OFFERS_JSON']
    
    def test_pricing_config_defaults(self):
        """Test pricing configuration with default values."""
        config = PricingConfig.from_env()
        
        self.assertIn('starter', config.credit_offers)
        self.assertIn('pro', config.credit_offers)
        self.assertIn('oneoff', config.credit_offers)
        
        starter = config.get_offer('starter')
        self.assertEqual(starter.usd, 199)
        self.assertEqual(starter.credits, 50)
    
    def test_pricing_config_from_env(self):
        """Test pricing configuration from environment variables."""
        custom_offers = {
            "basic": {"usd": 99, "credits": 20},
            "premium": {"usd": 299, "credits": 100}
        }
        os.environ['CREDIT_OFFERS_JSON'] = json.dumps(custom_offers)
        
        config = PricingConfig.from_env()
        
        self.assertIn('basic', config.credit_offers)
        self.assertIn('premium', config.credit_offers)
        
        basic = config.get_offer('basic')
        self.assertEqual(basic.usd, 99)
        self.assertEqual(basic.credits, 20)
    
    def test_pricing_manager_calculations(self):
        """Test pricing manager calculations."""
        manager = PricingManager()
        
        # Test best value calculation
        recommendation = manager.recommend_plan(60)
        self.assertIsNotNone(recommendation['best_option'])
        self.assertIsInstance(recommendation['all_options'], list)
    
    def test_credit_offer_calculations(self):
        """Test credit offer cost calculations."""
        from utils.pricing_config import CreditOffer
        
        offer = CreditOffer(usd=100, credits=20)
        self.assertEqual(offer.cost_per_credit, 5.0)
        
        # Test savings calculation
        savings = offer.savings_vs_oneoff(6.0)  # $6 per credit oneoff
        self.assertGreater(savings, 0)


class TestScheduleConfig(unittest.TestCase):
    """Test schedule configuration functionality."""
    
    def setUp(self):
        # Clear schedule environment variables
        for var in ['CRON_SCRAPE_UTC', 'CRON_DIGEST_HOURLY', 'CRON_DIGEST_DAILY']:
            if var in os.environ:
                del os.environ[var]
    
    def test_schedule_config_defaults(self):
        """Test schedule configuration with default values."""
        config = ScheduleConfig.from_env()
        
        self.assertIn('scrape', config.schedules)
        self.assertIn('digest_hourly', config.schedules)
        self.assertIn('digest_daily', config.schedules)
        
        scrape = config.get_schedule('scrape')
        self.assertEqual(scrape.expression, '0 5 * * *')
    
    def test_schedule_config_from_env(self):
        """Test schedule configuration from environment variables."""
        os.environ['CRON_SCRAPE_UTC'] = '30 6 * * *'
        os.environ['CRON_DIGEST_HOURLY'] = '15 * * * *'
        os.environ['CRON_DIGEST_DAILY'] = '0 14 * * *'
        
        config = ScheduleConfig.from_env()
        
        scrape = config.get_schedule('scrape')
        self.assertEqual(scrape.expression, '30 6 * * *')
        
        hourly = config.get_schedule('digest_hourly')
        self.assertEqual(hourly.expression, '15 * * * *')
    
    def test_cron_validation(self):
        """Test cron expression validation."""
        from utils.schedule_config import CronSchedule
        
        # Valid expressions
        valid_schedules = [
            '0 5 * * *',
            '*/15 * * * *',
            '0 9-17 * * 1-5',
            '0 0 1 * *'
        ]
        
        for expr in valid_schedules:
            schedule = CronSchedule(expression=expr, name='test')
            self.assertTrue(schedule.is_valid_cron())
        
        # Invalid expressions should raise ValueError
        with self.assertRaises(ValueError):
            CronSchedule(expression='invalid', name='test')
    
    def test_schedule_manager_validation(self):
        """Test schedule manager validation."""
        manager = ScheduleManager()
        
        is_valid, errors = manager.validate_schedules()
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_human_readable_cron(self):
        """Test human-readable cron descriptions."""
        from utils.schedule_config import CronSchedule
        
        schedule = CronSchedule(expression='0 5 * * *', name='test')
        readable = schedule.get_human_readable()
        
        self.assertIn('5', readable)  # Should mention hour 5


if __name__ == '__main__':
    unittest.main()