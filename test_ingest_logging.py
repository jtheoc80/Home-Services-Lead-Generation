#!/usr/bin/env python3
"""
Test script for ingest logging functionality.

This script tests the ingest_logger module and trace API endpoint.
"""

import os
import sys
import uuid
import time
import requests
from typing import Dict, Any

# Add backend to path for testing
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

def test_ingest_logger_import():
    """Test that ingest_logger can be imported."""
    try:
        from app.ingest_logger import IngestTracer, log_ingest_step, get_trace_logs, generate_trace_id
        print("✓ Successfully imported ingest_logger module")
        return True
    except ImportError as e:
        print(f"✗ Failed to import ingest_logger: {e}")
        return False

def test_trace_id_generation():
    """Test trace ID generation."""
    try:
        from backend.app.ingest_logger import generate_trace_id
        trace_id = generate_trace_id()
        
        # Validate it's a proper UUID
        uuid_obj = uuid.UUID(trace_id)
        print(f"✓ Generated valid trace ID: {trace_id}")
        return trace_id
    except Exception as e:
        print(f"✗ Failed to generate trace ID: {e}")
        return None

def test_ingest_tracer_context():
    """Test IngestTracer context manager."""
    try:
        from backend.app.ingest_logger import IngestTracer
        
        with IngestTracer() as tracer:
            print(f"✓ Created IngestTracer with trace_id: {tracer.trace_id}")
            
            # Test logging various stages
            stages = ["fetch_page", "parse", "upsert", "db_insert"]
            for stage in stages:
                success = tracer.log(stage, True, {"test": f"Testing {stage}"})
                if success:
                    print(f"  ✓ Logged stage: {stage}")
                else:
                    print(f"  ✗ Failed to log stage: {stage}")
            
            return tracer.trace_id
            
    except Exception as e:
        print(f"✗ IngestTracer test failed: {e}")
        return None

def test_trace_api_endpoint(trace_id: str, debug_key: str = "test-debug-key"):
    """Test the trace API endpoint."""
    try:
        url = f"http://localhost:8000/api/leads/trace/{trace_id}"
        headers = {"X-Debug-Key": debug_key}
        
        print(f"Testing API endpoint: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ API returned {data.get('total_logs', 0)} logs for trace {trace_id}")
            return True
        elif response.status_code == 401:
            print(f"! API returned 401 - debug key might not be configured")
            return False
        else:
            print(f"✗ API returned status {response.status_code}: {response.text}")
            return False
            
    except requests.ConnectionError:
        print("! API server not running - skipping endpoint test")
        return False
    except Exception as e:
        print(f"✗ API test failed: {e}")
        return False

def test_direct_logging():
    """Test direct logging functions."""
    try:
        from backend.app.ingest_logger import log_ingest_step
        
        trace_id = str(uuid.uuid4())
        
        # Test successful step
        success = log_ingest_step(trace_id, "test_stage", True, {"test_data": "success"})
        if success:
            print(f"✓ Direct logging successful for trace: {trace_id}")
        else:
            print(f"✗ Direct logging failed for trace: {trace_id}")
            
        # Test failed step
        success = log_ingest_step(trace_id, "test_failure", False, {"error": "Test error"})
        if success:
            print(f"✓ Direct failure logging successful")
        else:
            print(f"✗ Direct failure logging failed")
            
        return trace_id
        
    except Exception as e:
        print(f"✗ Direct logging test failed: {e}")
        return None

def main():
    """Run all tests."""
    print("🧪 Testing ingest logging functionality\n")
    
    # Test 1: Import test
    if not test_ingest_logger_import():
        print("\n❌ Import test failed - cannot continue")
        return False
    
    print()
    
    # Test 2: Trace ID generation
    trace_id = test_trace_id_generation()
    if not trace_id:
        print("\n❌ Trace ID generation failed")
        return False
    
    print()
    
    # Test 3: Direct logging
    direct_trace_id = test_direct_logging()
    if not direct_trace_id:
        print("\n⚠️  Direct logging failed - database might not be available")
    
    print()
    
    # Test 4: IngestTracer context manager
    tracer_trace_id = test_ingest_tracer_context()
    if not tracer_trace_id:
        print("\n⚠️  IngestTracer test failed - database might not be available")
    
    print()
    
    # Test 5: API endpoint (if server is running)
    if tracer_trace_id:
        test_trace_api_endpoint(tracer_trace_id)
    
    print("\n🎉 Testing completed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)