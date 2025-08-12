"""
Tests for notifications table functionality.
"""

import unittest
from pathlib import Path


class TestNotificationsTable(unittest.TestCase):
    """Test notifications table schema and basic functionality."""
    
    def test_notifications_migration_file_exists(self):
        """Test that the notifications migration file exists and has correct structure."""
        migration_file = Path(__file__).parent.parent / "app" / "migrations" / "002_notifications_table.sql"
        self.assertTrue(migration_file.exists(), "Notifications migration file should exist")
        
        content = migration_file.read_text()
        
        # Check for required table structure
        required_elements = [
            'CREATE TABLE IF NOT EXISTS notifications',
            'id BIGSERIAL PRIMARY KEY',
            'account_id UUID NOT NULL',
            'lead_id BIGINT NOT NULL', 
            'channel TEXT NOT NULL',
            'status TEXT NOT NULL DEFAULT',
            'created_at TIMESTAMPTZ DEFAULT now()',
            'sent_at TIMESTAMPTZ'
        ]
        
        for element in required_elements:
            self.assertIn(element, content, f"Missing required element: {element}")
    
    def test_notifications_indexes_defined(self):
        """Test that appropriate indexes are defined for performance."""
        migration_file = Path(__file__).parent.parent / "app" / "migrations" / "002_notifications_table.sql"
        content = migration_file.read_text()
        
        # Check for performance indexes
        required_indexes = [
            'idx_notifications_account_id',
            'idx_notifications_lead_id',
            'idx_notifications_channel',
            'idx_notifications_status',
            'idx_notifications_created_at',
            'idx_notifications_sent_at'
        ]
        
        for index in required_indexes:
            self.assertIn(index, content, f"Missing required index: {index}")
    
    def test_notifications_constraints(self):
        """Test that proper constraints are defined for data integrity."""
        migration_file = Path(__file__).parent.parent / "app" / "migrations" / "002_notifications_table.sql"
        content = migration_file.read_text()
        
        # Check for data integrity constraints
        self.assertIn("CHECK (channel IN ('inapp', 'email', 'sms'))", content, 
                      "Channel constraint should limit to valid values")
        self.assertIn("CHECK (status IN ('queued', 'sent', 'failed', 'read'))", content,
                      "Status constraint should limit to valid values")
    
    def test_models_sql_includes_notifications(self):
        """Test that the main models.sql file includes the notifications table."""
        models_file = Path(__file__).parent.parent / "app" / "models.sql"
        self.assertTrue(models_file.exists(), "Models.sql file should exist")
        
        content = models_file.read_text()
        self.assertIn('CREATE TABLE IF NOT EXISTS notifications', content,
                      "Main models file should include notifications table")
    
    def test_notification_channels_valid(self):
        """Test that notification channels are properly constrained."""
        valid_channels = ['inapp', 'email', 'sms']
        migration_file = Path(__file__).parent.parent / "app" / "migrations" / "002_notifications_table.sql"
        content = migration_file.read_text()
        
        for channel in valid_channels:
            self.assertIn(f"'{channel}'", content, f"Channel {channel} should be allowed")
    
    def test_notification_status_valid(self):
        """Test that notification statuses are properly constrained."""
        valid_statuses = ['queued', 'sent', 'failed', 'read']
        migration_file = Path(__file__).parent.parent / "app" / "migrations" / "002_notifications_table.sql"
        content = migration_file.read_text()
        
        for status in valid_statuses:
            self.assertIn(f"'{status}'", content, f"Status {status} should be allowed")
        
        # Check default status
        self.assertIn("DEFAULT 'queued'", content, "Default status should be 'queued'")


if __name__ == '__main__':
    unittest.main()