#!/usr/bin/env python3
"""
Demonstration of existing scraping and API testing infrastructure

This script demonstrates how to use the existing test scripts and shows
what works with the current setup in the repository.
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description, cwd=None):
    """Run a command and capture its output"""
    print(f"\n🔧 {description}")
    print(f"Running: {cmd}")
    print("-" * 60)
    
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=cwd,
            timeout=30
        )
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
            
        print(f"Exit code: {result.returncode}")
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Command timed out after 30 seconds")
        return False
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False

def main():
    print("🧪 SCRAPING AND API CONNECTION TESTING DEMONSTRATION")
    print("="*70)
    print()
    print("This demonstration shows the testing infrastructure available")
    print("for verifying scraping and API connections to Supabase.")
    print()
    
    # Check if we're in the right directory
    if not os.path.exists('backend') or not os.path.exists('.env.example'):
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
        
    print("📁 Project Structure Check:")
    key_files = [
        'backend/requirements.txt',
        '.env.example', 
        'scripts/e2e_supabase_delta.ts',
        'scripts/harrisCounty/issuedPermits.ts',
        'backend/test_supabase.py',
        'test_scraping_api_connections.py',
        'test_supabase_focused.py'
    ]
    
    for file in key_files:
        exists = "✅" if os.path.exists(file) else "❌"
        print(f"  {exists} {file}")
        
    print()
    
    # 1. Show environment setup
    print("1️⃣  ENVIRONMENT SETUP TESTING")
    run_command(
        "python3 test_supabase_focused.py --check-env-only",
        "Testing environment variable configuration"
    )
    
    # 2. Show backend dependency check
    print("\n2️⃣  BACKEND IMPORTS AND DEPENDENCY TESTING") 
    run_command(
        "python3 test_supabase_focused.py",
        "Testing backend imports and basic setup"
    )
    
    # 3. Show comprehensive test in mock mode
    print("\n3️⃣  COMPREHENSIVE TESTING (MOCK MODE)")
    run_command(
        "python3 test_scraping_api_connections.py --mock",
        "Running comprehensive test suite in mock mode"
    )
    
    # 4. Show existing TypeScript E2E test structure
    print("\n4️⃣  EXISTING E2E TEST FRAMEWORK")
    if os.path.exists('scripts/e2e_supabase_delta.ts'):
        print("📋 TypeScript E2E Test Available:")
        print("   tsx scripts/e2e_supabase_delta.ts --dry-run")
        print("   (requires tsx: npm install -g tsx)")
        
        # Try to show the test help
        run_command(
            "npx tsx scripts/e2e_supabase_delta.ts --help || head -20 scripts/e2e_supabase_delta.ts",
            "Checking TypeScript E2E test"
        )
    
    # 5. Show Harris County scraper 
    print("\n5️⃣  HARRIS COUNTY SCRAPER TESTING")
    if os.path.exists('scripts/harrisCounty/issuedPermits.ts'):
        print("📋 Harris County Scraper Available:")
        print("   tsx scripts/harrisCounty/issuedPermits.ts --since 1d")
        
        run_command(
            "head -30 scripts/harrisCounty/issuedPermits.ts",
            "Showing Harris County scraper structure"
        )
    
    # 6. Show Supabase smoke test documentation
    print("\n6️⃣  SUPABASE REST API SMOKE TESTS")
    if os.path.exists('docs/supabase/SMOKE_TEST.md'):
        run_command(
            "head -50 docs/supabase/SMOKE_TEST.md",
            "Showing Supabase REST API smoke test documentation"
        )
    
    # 7. Show existing backend test endpoints
    print("\n7️⃣  BACKEND API TEST ENDPOINTS")
    if os.path.exists('backend/test_supabase.py'):
        run_command(
            "grep -A 5 '@router\\.' backend/test_supabase.py || head -20 backend/test_supabase.py",
            "Showing available backend test endpoints"
        )
    
    print("\n" + "="*70)
    print("🎯 SUMMARY: AVAILABLE TESTING TOOLS")
    print("="*70)
    
    print("""
📋 IMMEDIATE TESTING (No external dependencies):
   • python3 test_supabase_focused.py --check-env-only
   • python3 test_supabase_focused.py
   • python3 test_scraping_api_connections.py --mock

🔧 WITH SUPABASE CREDENTIALS:
   • python3 test_scraping_api_connections.py
   • tsx scripts/e2e_supabase_delta.ts --dry-run
   
🌐 WITH BACKEND SERVER RUNNING:
   • curl http://localhost:8000/health/supabase
   • curl http://localhost:8000/api/supa-env-check
   
📡 WITH INTERNET ACCESS:
   • tsx scripts/harrisCounty/issuedPermits.ts --since 1d
   • Use curl commands from docs/supabase/SMOKE_TEST.md

🎯 COMPLETE E2E TEST:
   1. Set up real Supabase credentials in .env
   2. Start backend: cd backend && uvicorn main:app  
   3. Run: python3 test_scraping_api_connections.py
   4. Run: tsx scripts/e2e_supabase_delta.ts
""")
    
    print("="*70)
    print("✅ Testing infrastructure is ready for use!")
    print("💡 Next: Configure real Supabase credentials to test live connections")

if __name__ == "__main__":
    main()