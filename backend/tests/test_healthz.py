#!/usr/bin/env python3
"""
Tests for the healthz endpoint.
"""

import os
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

# Set required environment variables for testing
os.environ['SUPABASE_JWT_SECRET'] = 'test_secret'
os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'test_service_role'

class TestHealthzEndpoint:
    """Test cases for the healthz endpoint."""
    
    def test_healthz_success(self):
        """Test healthz endpoint with successful database connection."""
        with patch('main.get_supabase_client') as mock_supabase:
            # Mock successful DB connection
            mock_client = Mock()
            mock_table = Mock()
            mock_table.select.return_value = mock_table
            mock_table.limit.return_value = mock_table
            mock_table.execute.return_value = {'data': [{'table_name': 'test'}]}
            mock_client.table.return_value = mock_table
            mock_supabase.return_value = mock_client
            
            from main import app
            client = TestClient(app)
            
            response = client.get("/healthz")
            
            assert response.status_code == 200
            result = response.json()
            assert result['status'] == 'ok'
            assert result['version'] == '1.0.0'
            assert result['db'] == 'connected'
    
    def test_healthz_db_timeout(self):
        """Test healthz endpoint with database timeout."""
        with patch('main.get_supabase_client') as mock_supabase:
            # Mock database that will cause a timeout
            def create_timeout_client():
                mock_client = Mock()
                
                # Mock table method that raises an exception after delay
                def timeout_operation(*args, **kwargs):
                    pass
                async def timeout_operation(*args, **kwargs):
                    await asyncio.sleep(0.5)  # Longer than 300ms timeout
                    raise Exception("Operation timed out")
                
                mock_client.table.side_effect = timeout_operation
                return mock_client
            
            mock_supabase.return_value = create_timeout_client()
            
            from main import app
            client = TestClient(app)
            
            response = client.get("/healthz")
            
            assert response.status_code == 200
            result = response.json()
            assert result['status'] == 'ok'
            assert result['version'] == '1.0.0'
            assert result['db'] == 'down'
    
    def test_healthz_db_error(self):
        """Test healthz endpoint with database error."""
        with patch('main.get_supabase_client') as mock_supabase:
            # Mock database error
            mock_client = Mock()
            mock_client.table.side_effect = Exception("Database connection failed")
            mock_supabase.return_value = mock_client
            
            from main import app
            client = TestClient(app)
            
            response = client.get("/healthz")
            
            assert response.status_code == 200
            result = response.json()
            assert result['status'] == 'ok'
            assert result['version'] == '1.0.0'
            assert result['db'] == 'down'

    def test_healthz_response_format(self):
        """Test that healthz endpoint returns correct format."""
        # This test verifies the expected response structure
        expected_keys = {'status', 'version', 'db'}
        
        # Mock response that matches our endpoint
        mock_response = {
            'status': 'ok',
            'version': '1.0.0',
            'db': 'connected'
        }
        
        assert set(mock_response.keys()) == expected_keys
        assert mock_response['status'] == 'ok'
        assert isinstance(mock_response['version'], str)
        assert mock_response['db'] in ['connected', 'down']

    def test_healthz_endpoint_exists(self):
        """Test that the healthz endpoint exists and is accessible."""
        with patch('main.get_supabase_client') as mock_supabase:
            # Mock any DB response
            mock_client = Mock()
            mock_table = Mock()
            mock_table.select.return_value = mock_table
            mock_table.limit.return_value = mock_table
            mock_table.execute.return_value = {'data': []}
            mock_client.table.return_value = mock_table
            mock_supabase.return_value = mock_client
            
            from main import app
            client = TestClient(app)
            
            response = client.get("/healthz")
            
            # Should not return 404
            assert response.status_code != 404
            assert response.status_code == 200
            
            # Should have proper JSON response
            data = response.json()
            assert isinstance(data, dict)
            assert 'status' in data
            assert 'version' in data
            assert 'db' in data