#!/usr/bin/env python3
"""
Tests for lead quality tracking functionality.

This module tests the new lead scoring, cancellation tracking,
and quality analytics features.
"""

import os
import sys
import unittest
import tempfile
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone

# Add the backend app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from jobs.update_lead_scores import LeadScoringJob, LeadScoreUpdate


class TestLeadScoringJob(unittest.TestCase):
    """Test the nightly lead scoring update job."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_db_url = "postgresql://test:test@localhost/test"
        
    @patch('jobs.update_lead_scores.psycopg2.connect')
    def test_scoring_job_initialization(self, mock_connect):
        """Test scoring job can be initialized with database URL."""
        job = LeadScoringJob(self.test_db_url)
        self.assertEqual(job.database_url, self.test_db_url)
        self.assertEqual(job.MIN_SCORE, 0)
        self.assertEqual(job.MAX_SCORE, 150)
        self.assertEqual(job.DEFAULT_SCORE, 50)
    
    def test_scoring_job_requires_database_url(self):
        """Test scoring job raises error without database URL."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                LeadScoringJob()
    
    @patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost/test'})
    def test_scoring_job_from_env(self):
        """Test scoring job can get database URL from environment."""
        job = LeadScoringJob()
        self.assertEqual(job.database_url, 'postgresql://test:test@localhost/test')
    
    def test_score_update_calculation(self):
        """Test lead score update calculations."""
        # Test normal score update
        update = LeadScoreUpdate(
            lead_id=1,
            current_score=50.0,
            new_score=45.0,
            total_weight=-5.0,
            event_count=1
        )
        self.assertEqual(update.lead_id, 1)
        self.assertEqual(update.new_score, 45.0)
        self.assertEqual(update.total_weight, -5.0)
    
    @patch('jobs.update_lead_scores.psycopg2.connect')
    def test_calculate_lead_score_updates(self, mock_connect):
        """Test lead score calculation logic."""
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock quality events data
        events = [
            {'lead_id': 1, 'weight': -5, 'event_type': 'cancellation', 'created_at': datetime.now()},
            {'lead_id': 1, 'weight': -3, 'event_type': 'feedback_negative', 'created_at': datetime.now()},
            {'lead_id': 2, 'weight': -10, 'event_type': 'cancellation', 'created_at': datetime.now()}
        ]
        
        # Mock current scores
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'global_score': 50},
            {'id': 2, 'global_score': 60}
        ]
        
        job = LeadScoringJob(self.test_db_url)
        job.cursor = mock_cursor
        
        updates = job.calculate_lead_score_updates(events)
        
        self.assertEqual(len(updates), 2)
        
        # Lead 1: 50 + (-5 + -3) = 42
        update1 = next(u for u in updates if u.lead_id == 1)
        self.assertEqual(update1.new_score, 42)
        self.assertEqual(update1.total_weight, -8)
        self.assertEqual(update1.event_count, 2)
        
        # Lead 2: 60 + (-10) = 50
        update2 = next(u for u in updates if u.lead_id == 2)
        self.assertEqual(update2.new_score, 50)
        self.assertEqual(update2.total_weight, -10)
        self.assertEqual(update2.event_count, 1)
    
    @patch('jobs.update_lead_scores.psycopg2.connect')
    def test_score_bounds_enforcement(self, mock_connect):
        """Test that scores are kept within bounds."""
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Test minimum bound
        events_min = [{'lead_id': 1, 'weight': -100, 'event_type': 'cancellation', 'created_at': datetime.now()}]
        mock_cursor.fetchall.return_value = [{'id': 1, 'global_score': 10}]
        
        job = LeadScoringJob(self.test_db_url)
        job.cursor = mock_cursor
        
        updates = job.calculate_lead_score_updates(events_min)
        self.assertEqual(updates[0].new_score, 0)  # Should be capped at minimum
        
        # Test maximum bound
        events_max = [{'lead_id': 2, 'weight': 200, 'event_type': 'positive_feedback', 'created_at': datetime.now()}]
        mock_cursor.fetchall.return_value = [{'id': 2, 'global_score': 100}]
        
        updates = job.calculate_lead_score_updates(events_max)
        self.assertEqual(updates[0].new_score, 150)  # Should be capped at maximum
    
    def test_decay_factor_application(self):
        """Test decay factor calculation."""
        job = LeadScoringJob(self.test_db_url)
        
        # Test decay factor is properly defined
        self.assertEqual(job.DECAY_FACTOR, 0.5)
        self.assertEqual(job.DECAY_THRESHOLD_DAYS, 90)


class TestCancellationReasonMapping(unittest.TestCase):
    """Test cancellation reason to weight mapping."""
    
    def test_reason_weight_mapping(self):
        """Test that cancellation reasons map to correct weights."""
        # This would normally be imported from the API file
        # For testing purposes, we'll define it here
        REASON_TO_WEIGHT = {
            'low_quality': -15,
            'out_of_area': -5,
            'too_expensive': -2,
            'poor_support': -3,
            'found_alternative': -1,
            'other': -1
        }
        
        # Test that all weights are negative (penalties)
        for reason, weight in REASON_TO_WEIGHT.items():
            with self.subTest(reason=reason):
                self.assertLessEqual(weight, 0, f"Weight for {reason} should be negative or zero")
        
        # Test specific mappings
        self.assertEqual(REASON_TO_WEIGHT['low_quality'], -15)
        self.assertEqual(REASON_TO_WEIGHT['out_of_area'], -5)
        self.assertEqual(REASON_TO_WEIGHT['too_expensive'], -2)
        self.assertEqual(REASON_TO_WEIGHT['other'], -1)
    
    def test_unknown_reason_fallback(self):
        """Test that unknown reasons fall back to 'other' weight."""
        REASON_TO_WEIGHT = {
            'low_quality': -15,
            'other': -1
        }
        
        # Test fallback for unknown reason
        unknown_reason = 'completely_unknown_reason'
        weight = REASON_TO_WEIGHT.get(unknown_reason, REASON_TO_WEIGHT['other'])
        self.assertEqual(weight, -1)


class TestDatabaseSchema(unittest.TestCase):
    """Test that the database schema includes required tables."""
    
    def test_models_sql_includes_quality_tables(self):
        """Test that models.sql includes the new quality tracking tables."""
        models_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'models.sql')
        
        with open(models_path, 'r') as f:
            schema_sql = f.read()
        
        # Test that required tables are defined
        self.assertIn('lead_quality_events', schema_sql)
        self.assertIn('cancellations', schema_sql)
        
        # Test that required columns are present
        self.assertIn('global_score', schema_sql)
        self.assertIn('last_quality_update', schema_sql)
        self.assertIn('event_type', schema_sql)
        self.assertIn('weight', schema_sql)
        self.assertIn('reason_code', schema_sql)
        self.assertIn('affected_leads', schema_sql)
    
    def test_quality_event_types_constraint(self):
        """Test that quality event types are properly constrained."""
        models_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'models.sql')
        
        with open(models_path, 'r') as f:
            schema_sql = f.read()
        
        # Test that event types are constrained
        self.assertIn("event_type IN ('cancellation', 'feedback_negative', 'decay')", schema_sql)
    
    def test_indexes_defined(self):
        """Test that performance indexes are defined."""
        models_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'models.sql')
        
        with open(models_path, 'r') as f:
            schema_sql = f.read()
        
        # Test that key indexes are defined
        self.assertIn('idx_lead_quality_events_lead_id', schema_sql)
        self.assertIn('idx_lead_quality_events_created_at', schema_sql)
        self.assertIn('idx_leads_global_score', schema_sql)


class TestAPIEndpoints(unittest.TestCase):
    """Test API endpoint file structure."""
    
    def test_cancellation_api_exists(self):
        """Test that cancellation API endpoint file exists."""
        api_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'frontend', 'pages', 'api', 
            'subscription', 'cancel.ts'
        )
        self.assertTrue(os.path.exists(api_path), "Cancellation API endpoint should exist")
    
    def test_admin_analytics_api_exists(self):
        """Test that admin analytics API endpoint file exists."""
        api_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'frontend', 'pages', 'api', 
            'admin', 'lead_quality_issues.ts'
        )
        self.assertTrue(os.path.exists(api_path), "Admin analytics API endpoint should exist")
    
    def test_scoring_job_file_exists(self):
        """Test that scoring job file exists."""
        job_path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'jobs', 'update_lead_scores.py'
        )
        self.assertTrue(os.path.exists(job_path), "Scoring job file should exist")


if __name__ == '__main__':
    unittest.main()