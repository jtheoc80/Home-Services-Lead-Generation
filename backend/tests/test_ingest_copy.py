#!/usr/bin/env python3
"""
Test for the enhanced ingest functionality with PostgreSQL COPY support.
"""

import pytest
import os
import tempfile
import csv
from unittest.mock import patch, MagicMock

# Set required environment variables for testing
os.environ['SUPABASE_JWT_SECRET'] = 'test_secret'
os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'test_service_role'


def test_lead_ingestor_initialization():
    """Test LeadIngestor initialization with copy option."""
    from app.ingest import LeadIngestor
    
    # Test default initialization (use_copy=True)
    ingestor = LeadIngestor("postgresql://test")
    assert ingestor.use_copy is True
    
    # Test initialization with copy disabled
    ingestor_no_copy = LeadIngestor("postgresql://test", use_copy=False)
    assert ingestor_no_copy.use_copy is False


def test_csv_parsing_comprehensive():
    """Test comprehensive CSV row parsing."""
    from app.ingest import LeadIngestor
    
    ingestor = LeadIngestor("postgresql://test")
    
    # Test row with all fields populated
    test_row = {
        'jurisdiction': 'City of Houston',
        'permit_id': 'BP2025000123',
        'address': '1234 Main St, Houston, TX 77001',
        'description': 'New Construction',
        'work_class': 'Residential Building',
        'category': 'residential',
        'status': 'Issued',
        'issue_date': '2025-01-15',
        'applicant': 'ABC Construction LLC',
        'owner': 'John Smith',
        'value': '450000.0',
        'is_residential': 'true',
        'scraped_at': '2025-08-09T02:49:06.035319+00:00',
        'latitude': '29.7604',
        'longitude': '-95.3698',
        'apn': '123-456-789',
        'year_built': '2020',
        'heated_sqft': '2500.0',
        'lot_size': '8000.0',
        'land_use': 'Residential',
        'owner_kind': 'Individual',
        'trade_tags': '["construction", "residential"]',
        'budget_band': '400k+',
        'start_by_estimate': '2025-02-01',
        'lead_score': '75.5',
        'score_recency': '15.0',
        'score_trade_match': '25.0',
        'score_value': '20.0',
        'score_parcel_age': '10.0',
        'score_inspection': '5.5',
        'scoring_version': '2.0.0'
    }
    
    parsed = ingestor.parse_csv_row(test_row)
    
    # Verify parsed values
    assert parsed['jurisdiction'] == 'City of Houston'
    assert parsed['permit_id'] == 'BP2025000123'
    assert parsed['value'] == 450000.0
    assert parsed['is_residential'] is True
    assert parsed['latitude'] == 29.7604
    assert parsed['longitude'] == -95.3698
    assert parsed['year_built'] == 2020
    assert parsed['heated_sqft'] == 2500.0
    assert parsed['trade_tags'] == ['construction', 'residential']
    assert parsed['lead_score'] == 75.5


def test_csv_parsing_with_empty_values():
    """Test CSV parsing with empty/None values."""
    from app.ingest import LeadIngestor
    
    ingestor = LeadIngestor("postgresql://test")
    
    # Test row with minimal required fields
    test_row = {
        'jurisdiction': 'Test City',
        'permit_id': 'TEST123',
        'address': '',
        'value': '',
        'is_residential': '',
        'trade_tags': '',
        'year_built': 'None'
    }
    
    parsed = ingestor.parse_csv_row(test_row)
    
    assert parsed['jurisdiction'] == 'Test City'
    assert parsed['permit_id'] == 'TEST123'
    assert parsed['address'] is None
    assert parsed['value'] is None
    assert parsed['is_residential'] is None
    assert parsed['trade_tags'] is None
    assert parsed['year_built'] is None


@patch('app.ingest.psycopg2.connect')
def test_copy_method_with_mock_database(mock_connect):
    """Test the COPY-based ingestion method with mocked database."""
    from app.ingest import LeadIngestor
    
    # Create a temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
        writer = csv.writer(tmp_file)
        writer.writerow([
            'jurisdiction', 'permit_id', 'address', 'description', 'work_class',
            'category', 'status', 'issue_date', 'applicant', 'owner', 'value',
            'is_residential', 'scraped_at', 'latitude', 'longitude', 'apn',
            'year_built', 'heated_sqft', 'lot_size', 'land_use', 'owner_kind',
            'trade_tags', 'budget_band', 'start_by_estimate', 'lead_score',
            'score_recency', 'score_trade_match', 'score_value', 'score_parcel_age',
            'score_inspection', 'scoring_version'
        ])
        writer.writerow([
            'Test City', 'TEST123', '123 Test St', 'Test Description', 'Test Class',
            'test', 'Issued', '2025-01-15', 'Test Applicant', 'Test Owner', '50000.0',
            'true', '2025-08-09T02:49:06.035319+00:00', '29.7604', '-95.3698', '123-456-789',
            '2020', '2000.0', '7000.0', 'Residential', 'Individual',
            '["test"]', '50k+', '2025-02-01', '70.0',
            '10.0', '20.0', '15.0', '12.0', '3.0', '2.0.0'
        ])
        tmp_csv_path = tmp_file.name
    
    try:
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1
        mock_cursor.fetchone.return_value = [1]
        
        # Test the ingestor
        ingestor = LeadIngestor("postgresql://test", use_copy=True)
        result = ingestor.ingest_csv_with_copy(tmp_csv_path)
        
        # Verify results
        assert result == 1
        
        # Verify database operations were called
        mock_connect.assert_called_once()
        mock_conn.cursor.assert_called()
        mock_cursor.execute.assert_called()
        mock_cursor.copy_from.assert_called_once()
        mock_conn.commit.assert_called_once()
        
    finally:
        # Clean up temporary file
        os.unlink(tmp_csv_path)


@patch('app.ingest.psycopg2.connect')
def test_ingest_csv_fallback_to_insert(mock_connect):
    """Test that COPY method falls back to INSERT when it fails."""
    from app.ingest import LeadIngestor
    
    # Create a temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
        writer = csv.writer(tmp_file)
        writer.writerow(['jurisdiction', 'permit_id', 'address'])
        writer.writerow(['Test City', 'TEST123', '123 Test St'])
        tmp_csv_path = tmp_file.name
    
    try:
        # Mock database connection to fail on COPY but succeed on INSERT
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Make COPY fail the first time, succeed on INSERT
        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:  # First call (COPY)
                raise Exception("COPY failed")
            # Subsequent calls succeed
        
        mock_cursor.copy_from.side_effect = side_effect
        mock_cursor.fetchone.return_value = [1]
        
        # Test the ingestor
        ingestor = LeadIngestor("postgresql://test", use_copy=True)
        
        # This should attempt COPY, fail, then fall back to INSERT
        with patch.object(ingestor, 'ingest_csv_with_insert', return_value=1) as mock_insert:
            result = ingestor.ingest_csv(tmp_csv_path)
            
        # Verify fallback occurred
        assert result == 1
        assert ingestor.use_copy is False  # Should be disabled after failure
        mock_insert.assert_called_once_with(tmp_csv_path)
        
    finally:
        # Clean up temporary file
        os.unlink(tmp_csv_path)


def test_file_not_found_error():
    """Test handling of missing CSV files."""
    from app.ingest import LeadIngestor
    
    ingestor = LeadIngestor("postgresql://test")
    
    with pytest.raises(FileNotFoundError, match="CSV file not found"):
        ingestor.ingest_csv("/nonexistent/file.csv")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])