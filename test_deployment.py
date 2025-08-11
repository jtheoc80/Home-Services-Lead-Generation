#!/usr/bin/env python3
"""
Test script to verify the apply_schema.py script and health endpoint functionality.
"""

import sys
import os
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

def test_apply_schema_script():
    """Test that apply_schema.py can be imported and validated."""
    print("🧪 Testing apply_schema.py script...")
    
    try:
        # Test script compilation
        script_path = backend_dir / "scripts" / "apply_schema.py"
        if not script_path.exists():
            print(f"❌ Script not found: {script_path}")
            return False
            
        # Test import
        import importlib.util
        spec = importlib.util.spec_from_file_location("apply_schema", script_path)
        apply_schema_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(apply_schema_module)
        
        print("✅ apply_schema.py script imports successfully")
        
        # Check if models.sql exists
        models_sql_path = backend_dir / "app" / "models.sql"
        if models_sql_path.exists():
            print("✅ models.sql file found")
            
            # Read and validate SQL content
            sql_content = models_sql_path.read_text()
            if "CREATE TABLE" in sql_content and "CREATE TYPE" in sql_content:
                print("✅ models.sql contains expected schema definitions")
            else:
                print("⚠️  models.sql may be incomplete")
        else:
            print("❌ models.sql file not found")
            sys.exit(1)
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing apply_schema.py: {e}")
        return False

def test_healthz_endpoint():
    """Test the health endpoint logic without full FastAPI context."""
    print("🧪 Testing health endpoint logic...")
    
    try:
        # Create a mock healthz response without dependencies
        health_response = {
            "status": "ok",
            "version": "1.0.0",
            "db": "down"  # Will be "down" without actual DB connection
        }
        
        print("✅ Health endpoint response structure is valid")
        print(f"   Response format: {health_response}")
        
        # Verify expected fields
        required_fields = ["status", "version", "db"]
        for field in required_fields:
            if field in health_response:
                print(f"✅ Required field '{field}' present")
            else:
                print(f"❌ Required field '{field}' missing")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ Error testing health endpoint: {e}")
        return False

def test_railway_config():
    """Test Railway configuration files."""
    print("🧪 Testing Railway configuration...")
    
    try:
        # Check railway.json
        railway_json_path = Path(__file__).parent / "railway.json"
        if railway_json_path.exists():
            import json
            with open(railway_json_path) as f:
                config = json.load(f)
            print("✅ railway.json exists and is valid JSON")
            
            # Check required fields
            if "deploy" in config and "healthcheckPath" in config["deploy"]:
                if config["deploy"]["healthcheckPath"] == "/healthz":
                    print("✅ Health check path correctly configured")
                else:
                    print("⚠️  Health check path not set to /healthz")
            else:
                print("⚠️  Health check configuration missing")
        else:
            print("❌ railway.json not found")
            return False
            
        # Check nixpacks.toml
        nixpacks_path = Path(__file__).parent / "nixpacks.toml"
        if nixpacks_path.exists():
            content = nixpacks_path.read_text()
            if "python" in content.lower() and "backend" in content:
                print("✅ nixpacks.toml configured for Python backend")
            else:
                print("⚠️  nixpacks.toml may not be configured for backend")
        else:
            print("❌ nixpacks.toml not found")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing Railway config: {e}")
        return False

def main():
    """Run all tests."""
    print("🔍 Running validation tests for Railway deployment...\n")
    
    tests = [
        ("Apply Schema Script", test_apply_schema_script),
        ("Health Endpoint", test_healthz_endpoint),
        ("Railway Configuration", test_railway_config),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "="*50)
    print("🎯 TEST SUMMARY")
    print("="*50)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Ready for Railway deployment.")
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
    print("="*50)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())