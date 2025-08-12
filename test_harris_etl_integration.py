#!/usr/bin/env python3
"""
Integration test for Harris County ETL state management.

This test validates the complete flow without making actual HTTP requests.
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add permit_leads to path
sys.path.append(str(Path(__file__).parent))

from permit_leads.adapters.etl_aware_arcgis_adapter import ETLAwareArcGISAdapter
from permit_leads.etl_state import ETLStateManager
from permit_leads.models.permit import PermitRecord


class MockJurisdiction:
    """Mock jurisdiction for Harris County testing."""
    def __init__(self):
        self.slug = 'tx-harris'
        self.name = 'Harris County'
        self.source_config = {
            'feature_server': 'https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0',
            'date_field': 'ISSUEDDATE',
            'date_format': 'string',
            'field_map': {
                'permit_id': 'PERMITNUMBER',
                'issue_date': 'ISSUEDDATE',
                'address': 'FULLADDRESS'
            }
        }


class TestHarrisCountyETLIntegration(unittest.TestCase):
    """Test Harris County ETL state management integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.jurisdiction = MockJurisdiction()
        self.adapter = ETLAwareArcGISAdapter(self.jurisdiction)
    
    def test_source_name_is_harris_issued_permits(self):
        """Test that source name is exactly 'harris_issued_permits'."""
        self.assertEqual(self.adapter.source_name, 'harris_issued_permits')
    
    def test_etl_state_manager_initialization(self):
        """Test ETL state manager initializes properly."""
        manager = ETLStateManager()
        self.assertIsNotNone(manager)
        # Should work even without Supabase
        self.assertIsNone(manager.supabase)  # No credentials in test env
    
    def test_get_since_timestamp_with_fallback(self):
        """Test getting since timestamp with fallback."""
        since = self.adapter.etl_state.get_since_timestamp('harris_issued_permits', fallback_days=7)
        self.assertIsInstance(since, datetime)
        # Should be approximately 7 days ago
        expected = datetime.utcnow() - timedelta(days=7)
        delta = abs((since - expected).total_seconds())
        self.assertLess(delta, 60)  # Within 1 minute
    
    def test_get_since_timestamp_with_existing_run(self):
        """Test getting since timestamp with mock existing run."""
        # Mock the ETL state manager to return a last run
        with patch.object(self.adapter.etl_state, 'get_last_run') as mock_get:
            last_run = datetime.utcnow() - timedelta(hours=2)
            mock_get.return_value = last_run
            
            since = self.adapter.etl_state.get_since_timestamp('harris_issued_permits')
            
            # Should be last_run - 1 minute
            expected = last_run - timedelta(minutes=1)
            self.assertEqual(since, expected)
    
    @patch('permit_leads.adapters.etl_aware_arcgis_adapter.requests.get')
    def test_arcgis_query_format(self, mock_get):
        """Test that ArcGIS query uses correct format."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {'features': []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test with string date format
        since = datetime(2025, 8, 10, 12, 0, 0)
        self.adapter._fetch_permits_from_arcgis(since)
        
        # Verify the call was made with correct parameters
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        params = call_args[1]['params']
        
        # Check that where clause uses TIMESTAMP format for string dates
        where_clause = params['where']
        self.assertIn('ISSUEDDATE >', where_clause)
        self.assertIn('TIMESTAMP', where_clause)
        self.assertIn('2025-08-10 12:00:00', where_clause)
    
    @patch('permit_leads.adapters.etl_aware_arcgis_adapter.requests.get')
    def test_arcgis_query_epoch_format(self, mock_get):
        """Test that ArcGIS query uses epoch format when configured."""
        # Configure for epoch format
        self.adapter.config['date_format'] = 'epoch'
        
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {'features': []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test with epoch date format
        since = datetime(2025, 8, 10, 12, 0, 0)
        self.adapter._fetch_permits_from_arcgis(since)
        
        # Verify the call was made with correct parameters
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        params = call_args[1]['params']
        
        # Check that where clause uses epoch milliseconds
        where_clause = params['where']
        self.assertIn('ISSUEDDATE >', where_clause)
        self.assertNotIn('TIMESTAMP', where_clause)
        # Should contain epoch milliseconds (large number)
        epoch_ms = int(since.timestamp() * 1000)
        self.assertIn(str(epoch_ms), where_clause)
    
    def test_scrape_permits_does_not_update_state(self):
        """Test that scrape_permits does not update ETL state."""
        with patch.object(self.adapter, '_fetch_permits_from_arcgis') as mock_fetch:
            with patch.object(self.adapter.etl_state, 'update_last_run') as mock_update:
                # Mock return empty list
                mock_fetch.return_value = []
                
                # Scrape permits
                permits = self.adapter.scrape_permits()
                
                # Verify fetch was called but update was NOT called
                mock_fetch.assert_called_once()
                mock_update.assert_not_called()
                
                self.assertEqual(permits, [])
    
    def test_update_etl_state_after_upsert(self):
        """Test updating ETL state after successful upsert."""
        with patch.object(self.adapter.etl_state, 'update_last_run') as mock_update:
            mock_update.return_value = True
            
            # Call the update method
            success = self.adapter.update_etl_state_after_upsert(5)
            
            # Verify it was called with source name and a timestamp
            mock_update.assert_called_once()
            call_args = mock_update.call_args
            source_arg = call_args[0][0]
            timestamp_arg = call_args[0][1]
            
            self.assertEqual(source_arg, 'harris_issued_permits')
            self.assertIsInstance(timestamp_arg, datetime)
            self.assertTrue(success)
    
    def test_parse_feature_handles_epoch_timestamps(self):
        """Test parsing ArcGIS features with epoch timestamp dates."""
        # Mock feature with epoch millisecond timestamp
        epoch_ms = int(datetime(2025, 8, 10, 12, 0, 0).timestamp() * 1000)
        feature = {
            'attributes': {
                'PERMITNUMBER': 'HP2025-001',
                'ISSUEDDATE': epoch_ms,
                'FULLADDRESS': '123 Main St'
            },
            'geometry': {'x': -95.369, 'y': 29.760}
        }
        
        permit = self.adapter._parse_feature(feature)
        
        self.assertIsNotNone(permit)
        self.assertEqual(permit.permit_id, 'HP2025-001')
        self.assertEqual(permit.address, '123 Main St')
        self.assertIsInstance(permit.issue_date, datetime)
        self.assertEqual(permit.longitude, -95.369)
        self.assertEqual(permit.latitude, 29.760)
        self.assertEqual(permit.jurisdiction, 'Harris County')


if __name__ == '__main__':
    unittest.main()