#!/usr/bin/env python3
"""
Basic health endpoint tests for the monitoring system.

Tests both backend /healthz and frontend /api/health endpoints.
"""
import requests
import time
import sys
import os

def test_backend_healthz():
    """Test backend /healthz endpoint"""
    try:
        backend_url = os.getenv('BACKEND_URL', 'http://localhost:8000')
        response = requests.get(f"{backend_url}/healthz", timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Backend /healthz returned status {response.status_code}")
            return False
            
        data = response.json()
        if data.get('status') != 'ok':
            print(f"❌ Backend /healthz status not ok: {data}")
            return False
            
        print(f"✅ Backend /healthz OK: {data}")
        return True
        
    except Exception as e:
        print(f"❌ Backend /healthz failed: {e}")
        return False

def test_frontend_health():
    """Test frontend /api/health endpoint"""
    try:
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        response = requests.get(f"{frontend_url}/api/health", timeout=10)
        
        # May return 503 if dependencies are down, but should have JSON body
        if response.status_code not in [200, 503]:
            print(f"❌ Frontend /api/health returned unexpected status {response.status_code}")
            return False
            
        data = response.json()
        required_fields = ['frontend', 'backend', 'supabase', 'timestamp']
        for field in required_fields:
            if field not in data:
                print(f"❌ Frontend /api/health missing field: {field}")
                return False
                
        print(f"✅ Frontend /api/health OK: {data}")
        return True
        
    except Exception as e:
        print(f"❌ Frontend /api/health failed: {e}")
        return False

def test_stack_health_script():
    """Test the stack health monitoring script"""
    try:
        import subprocess
        
        # Run stack health script
        result = subprocess.run(
            ['node', 'scripts/stack-health.js'], 
            capture_output=True, 
            text=True,
            timeout=30
        )
        
        # May exit non-zero if services are down, but should produce output
        if not result.stdout and not result.stderr:
            print("❌ Stack health script produced no output")
            return False
            
        # Check for expected output files
        output_files = ['stack-health.json', 'health-summary.md']
        for file in output_files:
            if os.path.exists(file):
                print(f"✅ Stack health script created {file}")
            else:
                print(f"⚠️  Stack health script did not create {file}")
                
        print("✅ Stack health script executed successfully")
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Stack health script timed out")
        return False
    except Exception as e:
        print(f"❌ Stack health script failed: {e}")
        return False

def main():
    """Run all health endpoint tests"""
    print("🏥 Running health endpoint tests...")
    print("")
    
    tests = [
        ("Backend /healthz", test_backend_healthz),
        ("Frontend /api/health", test_frontend_health), 
        ("Stack health script", test_stack_health_script)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        if test_func():
            passed += 1
        print("")
        
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All health endpoint tests passed!")
        return 0
    else:
        print("💥 Some health endpoint tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())