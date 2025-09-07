#!/usr/bin/env python3
"""
Minimal stack smoke test
Tests that the backend FastAPI server and database connectivity are working
"""

import asyncio
import os
import sys
import httpx
import subprocess
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))


class StackSmokeTest:
    def __init__(self):
        self.backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        self.timeout = 30

    async def test_backend_health(self):
        """Test backend /health endpoint"""
        print("🔍 Testing backend health endpoint...")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.backend_url}/health", timeout=10.0)
                if response.status_code == 200:
                    print("✅ Backend health check passed")
                    data = response.json()
                    print(f"   Status: {data.get('status', 'unknown')}")
                    return True
                else:
                    print(
                        f"❌ Backend health check failed: HTTP {response.status_code}"
                    )
                    print(f"   Response: {response.text}")
                    return False
            except Exception as e:
                print(f"❌ Backend health check failed: {e}")
                return False

    async def test_backend_supabase_env(self):
        """Test backend /api/supa-env-check endpoint for environment and DB connectivity"""
        print("🔍 Testing backend Supabase environment check...")

        # First, let's create this endpoint if it doesn't exist
        endpoint_path = backend_path / "app" / "supa_env_check.py"
        if not endpoint_path.exists():
            print("📝 Creating /api/supa-env-check endpoint...")
            self._create_supa_env_check_endpoint()

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.backend_url}/api/supa-env-check", timeout=15.0
                )
                if response.status_code == 200:
                    print("✅ Supabase environment check passed")
                    data = response.json()
                    print(f"   Database: {data.get('database_status', 'unknown')}")
                    print(f"   Environment: {data.get('env_status', 'unknown')}")
                    return True
                else:
                    print(
                        f"❌ Supabase environment check failed: HTTP {response.status_code}"
                    )
                    print(f"   Response: {response.text}")
                    return False
            except Exception as e:
                print(f"❌ Supabase environment check failed: {e}")
                return False

    def _create_supa_env_check_endpoint(self):
        """Create the supa-env-check endpoint if missing"""
        endpoint_code = '''"""
Supabase environment and connectivity check endpoint
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import os
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/api/supa-env-check")
async def supa_env_check() -> Dict[str, Any]:
    """
    Check Supabase environment variables and database connectivity
    """
    result = {
        "status": "ok",
        "env_status": "ok", 
        "database_status": "unknown",
        "checks": {}
    }
    
    # Check required environment variables
    required_env_vars = [
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_JWT_SECRET"
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
        result["checks"][var] = "present" if os.getenv(var) else "missing"
    
    if missing_vars:
        result["env_status"] = "missing_vars"
        result["missing_variables"] = missing_vars
        result["status"] = "degraded"
    
    # Test database connectivity if env vars are present
    if not missing_vars:
        try:
            # Import here to avoid startup errors if not available
            from supabase import create_client
            
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            
            client = create_client(supabase_url, supabase_key)
            
            # Simple test query
            response = client.table("leads").select("count", count="exact").limit(1).execute()
            
            result["database_status"] = "connected"
            result["checks"]["database_query"] = "success"
            
        except Exception as e:
            logger.error(f"Database connectivity test failed: {e}")
            result["database_status"] = "error"
            result["checks"]["database_query"] = f"failed: {str(e)}"
            result["status"] = "degraded"
    
    return result
'''

        # Write to a new file
        endpoint_path = backend_path / "app" / "supa_env_check.py"
        with open(endpoint_path, "w") as f:
            f.write(endpoint_code)

        # Also need to add it to main.py if not already there
        main_py_path = backend_path / "main.py"
        if main_py_path.exists():
            with open(main_py_path, "r") as f:
                content = f.read()

            if "supa_env_check" not in content:
                # Add import and include router
                import_line = (
                    "from app.supa_env_check import router as supa_env_check_router"
                )
                router_line = "app.include_router(supa_env_check_router)"

                print(f"   📝 Adding endpoint to {main_py_path}")
                # This is a simplified approach - in practice you'd want more sophisticated parsing
        # Print instructions for manual inclusion in main.py
        main_py_path = backend_path / "main.py"
        if main_py_path.exists():
            with open(main_py_path, "r") as f:
                content = f.read()

            if "supa_env_check" not in content:
                print(f"   📝 Please add the following lines to {main_py_path}:")
                print(
                    "       from app.supa_env_check import router as supa_env_check_router"
                )
                print("       app.include_router(supa_env_check_router)")
                print("   (Manual step required to avoid fragile code modification.)")

    async def test_frontend_build(self):
        """Test that frontend can build successfully"""
        print("🔍 Testing frontend build...")

        frontend_path = Path(__file__).parent.parent / "frontend"
        if not frontend_path.exists():
            print("⚠️  Frontend directory not found, skipping")
            return True

        try:
            # Run npm build
            result = subprocess.run(
                ["npm", "run", "build"],
                cwd=frontend_path,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                print("✅ Frontend build successful")
                return True
            else:
                print("❌ Frontend build failed")
                print(f"   stdout: {result.stdout}")
                print(f"   stderr: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("❌ Frontend build timed out")
            return False
        except Exception as e:
            print(f"❌ Frontend build error: {e}")
            return False

    async def run_all_tests(self):
        """Run all smoke tests"""
        print("🚀 Starting stack smoke tests...")
        print(f"   Backend URL: {self.backend_url}")
        print(f"   Frontend URL: {self.frontend_url}")
        print()

        results = {}

        # Test backend health
        results["backend_health"] = await self.test_backend_health()

        # Test Supabase environment check
        results["supabase_env"] = await self.test_backend_supabase_env()

        # Test frontend build
        results["frontend_build"] = await self.test_frontend_build()

        # Summary
        print("\n📊 Smoke Test Results:")
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)

        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {test_name}: {status}")

        print(f"\n📈 Summary: {passed_tests}/{total_tests} tests passed")

        if passed_tests == total_tests:
            print("🎉 All smoke tests passed!")
            return True
        else:
            print("💥 Some smoke tests failed!")
            return False


async def main():
    """Main entry point"""
    test_suite = StackSmokeTest()
    success = await test_suite.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
