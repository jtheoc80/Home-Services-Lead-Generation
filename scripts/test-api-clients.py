#!/usr/bin/env python3
"""
Test script to verify the generated Python API client works correctly.
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

def test_python_client():
    """Test that the Python client can be imported and instantiated."""
    try:
        from clients import LeadLedgerProClient
        
        # Test basic instantiation
        client = LeadLedgerProClient(base_url='http://localhost:8000')
        
        print("✅ Python client imported successfully")
        print(f"✅ Client has health API: {hasattr(client, 'health')}")
        print(f"✅ Client has subscription API: {hasattr(client, 'subscription')}")
        print(f"✅ Client has export API: {hasattr(client, 'export')}")
        print(f"✅ Client has auth API: {hasattr(client, 'auth')}")
        print(f"✅ Client has admin API: {hasattr(client, 'admin')}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import Python client: {e}")
        print("💡 This is expected if the OpenAPI generation hasn't run yet")
        return False
    except Exception as e:
        print(f"❌ Error testing Python client: {e}")
        return False

def test_generated_files():
    """Test that generated files exist in the expected locations."""
    backend_dir = Path(__file__).parent.parent / "backend"
    frontend_dir = Path(__file__).parent.parent / "frontend"
    
    # Check Python client files
    python_client_dir = backend_dir / "clients" / "leadledderpro_client"
    if python_client_dir.exists():
        print("✅ Python client directory exists")
        
        # Check for key files
        key_files = ["__init__.py", "api_client.py", "configuration.py"]
        for file in key_files:
            if (python_client_dir / file).exists():
                print(f"✅ Python client has {file}")
            else:
                print(f"❌ Python client missing {file}")
    else:
        print("❌ Python client directory not found")
    
    # Check TypeScript client files
    ts_client_file = frontend_dir / "src" / "lib" / "api-client.ts"
    if ts_client_file.exists():
        print("✅ TypeScript client file exists")
    else:
        print("❌ TypeScript client file not found")
    
    # Check OpenAPI spec
    spec_file = Path(__file__).parent.parent / "openapi.yaml"
    if spec_file.exists():
        print("✅ OpenAPI specification exists")
    else:
        print("❌ OpenAPI specification not found")

if __name__ == "__main__":
    print("🧪 Testing OpenAPI generated clients...")
    print()
    
    test_generated_files()
    print()
    test_python_client()
    
    print()
    print("🎯 Test completed!")
    print("💡 To regenerate clients, run: python scripts/extract-openapi.py")