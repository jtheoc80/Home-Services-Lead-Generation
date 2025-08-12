#!/usr/bin/env python3
"""
Test FastAPI endpoint for trace logging.

This tests the /api/leads/trace/{id} endpoint with proper mocking.
"""

import os
import sys
import uuid
from unittest.mock import patch, MagicMock

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

# Set up minimal environment to avoid errors
os.environ.update({
    'SUPABASE_URL': 'https://example.supabase.co',
    'SUPABASE_ANON_KEY': 'test-anon-key',
    'SUPABASE_JWT_SECRET': 'test-jwt-secret',
    'X_DEBUG_KEY': 'test-debug-key-123'
})

from fastapi.testclient import TestClient

# Mock the Supabase client before importing main
with patch('app.supabase_client.get_supabase_client'):
    with patch('app.redis_client.ping_ms', return_value=('ok', 10)):
        from main import app

client = TestClient(app)

def test_trace_endpoint_auth():
    """Test authentication for trace endpoint."""
    trace_id = str(uuid.uuid4())
    
    # Test without debug key
    response = client.get(f"/api/leads/trace/{trace_id}")
    assert response.status_code == 401
    
    # Test with wrong debug key  
    response = client.get(
        f"/api/leads/trace/{trace_id}",
        headers={"X-Debug-Key": "wrong-key"}
    )
    assert response.status_code == 401
    
    print("✓ Authentication tests passed")

@patch('main.get_trace_logs')
def test_trace_endpoint_success(mock_get_logs):
    """Test successful trace retrieval."""
    trace_id = str(uuid.uuid4())
    
    # Mock successful log retrieval
    mock_logs = [
        {"id": 1, "trace_id": trace_id, "stage": "fetch_page", "ok": True, "details": {}},
        {"id": 2, "trace_id": trace_id, "stage": "parse", "ok": True, "details": {}}
    ]
    mock_get_logs.return_value = mock_logs
    
    response = client.get(
        f"/api/leads/trace/{trace_id}",
        headers={"X-Debug-Key": "test-debug-key-123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    print(f"Response data: {data}")  # Debug output
    assert data["trace_id"] == trace_id
    assert data["total_logs"] == 2
    assert len(data["logs"]) == 2
    
    print(f"✓ Successful retrieval test passed for trace: {trace_id}")

@patch('main.get_trace_logs')
def test_trace_endpoint_not_found(mock_get_logs):
    """Test trace not found scenario."""
    trace_id = str(uuid.uuid4())
    
    # Mock empty log retrieval
    mock_get_logs.return_value = []
    
    response = client.get(
        f"/api/leads/trace/{trace_id}",
        headers={"X-Debug-Key": "test-debug-key-123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["trace_id"] == trace_id
    assert data["total_logs"] == 0
    assert data["logs"] == []
    
    print(f"✓ Empty logs test passed for trace: {trace_id}")

@patch('main.get_trace_logs')
def test_trace_endpoint_error(mock_get_logs):
    """Test error handling in trace endpoint."""
    trace_id = str(uuid.uuid4())
    
    # Mock error in log retrieval
    mock_get_logs.return_value = None
    
    response = client.get(
        f"/api/leads/trace/{trace_id}",
        headers={"X-Debug-Key": "test-debug-key-123"}
    )
    
    assert response.status_code == 500
    
    print(f"✓ Error handling test passed for trace: {trace_id}")

def test_health_endpoint():
    """Test that health endpoint still works."""
    response = client.get("/health")
    assert response.status_code == 200
    
    print("✓ Health endpoint test passed")

def main():
    """Run all tests."""
    print("🧪 Testing FastAPI trace endpoint")
    print("=" * 40)
    
    try:
        test_trace_endpoint_auth()
        test_trace_endpoint_success()
        test_trace_endpoint_not_found()
        test_trace_endpoint_error()
        test_health_endpoint()
        
        print("\n✅ All FastAPI tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ FastAPI tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)