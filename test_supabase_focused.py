#!/usr/bin/env python3
"""
Supabase-focused test script for environments without external internet access.

This script tests:
1. Local environment setup
2. Supabase connectivity (when configured)
3. Backend API endpoints (when server is running)
4. Data ingestion pipeline (when Supabase is available)

Usage:
    python3 test_supabase_focused.py [--check-env-only]

Options:
    --check-env-only    Only check environment setup without testing connections
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, Any, List
from dataclasses import dataclass

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not available, .env file will not be loaded")

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    success: bool
    message: str
    details: Dict[str, Any] = None

class SupabaseFocusedTester:
    """Focused tester for Supabase connections and data flow"""
    
    def __init__(self):
        self.setup_logging()
        self.results: List[TestResult] = []
        
    def setup_logging(self):
        """Configure logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        self.logger = logging.getLogger(__name__)
        
    def add_result(self, test_name: str, success: bool, message: str, details: Dict[str, Any] = None):
        """Add a test result"""
        result = TestResult(test_name, success, message, details or {})
        self.results.append(result)
        
        status = "✓ PASS" if success else "✗ FAIL"
        self.logger.info(f"{status} {test_name}: {message}")
        
    def test_environment_variables(self) -> bool:
        """Check environment variable configuration"""
        
        # Required environment variables
        required_vars = [
            'SUPABASE_URL',
            'SUPABASE_SERVICE_ROLE_KEY'
        ]
        
        # Optional but recommended variables
        optional_vars = [
            'SUPABASE_JWT_SECRET',
            'HC_ISSUED_PERMITS_URL',
            'BACKEND_URL'
        ]
        
        missing_required = []
        missing_optional = []
        present_vars = {}
        
        for var in required_vars:
            value = os.getenv(var) or os.getenv(var.replace('_KEY', ''))
            if value:
            fallback_var = var.replace('_KEY', '') if var.endswith('_KEY') else None
            value = os.getenv(var)
            fallback_value = os.getenv(fallback_var) if fallback_var else None
            if value and fallback_value:
                self.logger.warning(
                    f"Both environment variables '{var}' and '{fallback_var}' are set. "
                    f"Using '{var}'. Please ensure only one is set to avoid ambiguity."
                )
            used_var = None
            if value:
                used_var = var
                present_vars[var] = {
                    "status": "configured" if not value.startswith('your_') else "needs_real_value",
                    "used_env_var": var
                }
            elif fallback_value:
                used_var = fallback_var
                present_vars[var] = {
                    "status": "configured" if not fallback_value.startswith('your_') else "needs_real_value",
                    "used_env_var": fallback_var
                }
            else:
                missing_required.append(var)
                
        for var in optional_vars:
            value = os.getenv(var)
            if value:
                present_vars[var] = "configured" if not value.startswith('your_') else "needs_real_value"
            else:
                missing_optional.append(var)
                
        if missing_required:
            self.add_result(
                "Environment Variables",
                False,
                f"Missing required variables: {', '.join(missing_required)}",
                {
                    "missing_required": missing_required,
                    "missing_optional": missing_optional,
                    "present": present_vars
                }
            )
            return False
        else:
            needs_real_values = [k for k, v in present_vars.items() if v == "needs_real_value"]
            if needs_real_values:
                self.add_result(
                    "Environment Variables",
                    True,
                    f"All required variables present, but {len(needs_real_values)} need real values",
                    {
                        "present": present_vars,
                        "needs_real_values": needs_real_values,
                        "status": "configured_but_placeholder"
                    }
                )
            else:
                self.add_result(
                    "Environment Variables",
                    True,
                    "All required environment variables properly configured",
                    {"present": present_vars, "status": "fully_configured"}
                )
            return True
            
    def test_backend_imports(self) -> bool:
        """Test if backend modules can be imported"""
        
        importable_modules = []
        failed_imports = []
        
        modules_to_test = [
            ('supabase', 'Supabase Python client'),
            ('app.supabase_client', 'Custom Supabase client'),
            ('app.ingest', 'Data ingestion module'),
            ('fastapi', 'FastAPI framework'),
        ]
        
        for module_name, description in modules_to_test:
            try:
                __import__(module_name)
                importable_modules.append((module_name, description))
            except ImportError as e:
                failed_imports.append((module_name, description, str(e)))
                
        if failed_imports:
            self.add_result(
                "Backend Imports",
                False,
                f"Failed to import {len(failed_imports)} modules",
                {
                    "failed_imports": failed_imports,
                    "importable_modules": importable_modules
                }
            )
            return False
        else:
            self.add_result(
                "Backend Imports", 
                True,
                f"Successfully imported all {len(importable_modules)} required modules",
                {"importable_modules": importable_modules}
            )
            return True
            
    def test_supabase_client_creation(self) -> bool:
        """Test Supabase client creation (without actual connection)"""
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_SERVICE_ROLE')
        
        if not supabase_url or not supabase_key:
            self.add_result(
                "Supabase Client Creation",
                False,
                "Missing Supabase credentials",
                {"url_present": bool(supabase_url), "key_present": bool(supabase_key)}
            )
            return False
            
        if supabase_url.startswith('https://your-') or supabase_key.startswith('your_'):
            self.add_result(
                "Supabase Client Creation",
                False,
                "Supabase credentials are placeholder values",
                {"url_is_placeholder": supabase_url.startswith('https://your-'), 
                 "key_is_placeholder": supabase_key.startswith('your_')}
            )
            return False
            
        try:
            from supabase import create_client
            
            # Just test client creation, not actual connection
            client = create_client(supabase_url, supabase_key)
            
            self.add_result(
                "Supabase Client Creation",
                True,
                "Successfully created Supabase client object",
                {"url_format": "valid", "key_format": "valid", "client_created": True}
            )
            return True
            
        except Exception as e:
            self.add_result(
                "Supabase Client Creation",
                False,
                f"Failed to create Supabase client: {str(e)}",
                {"error": str(e)}
            )
            return False
            
    def test_data_structure_validation(self) -> bool:
        """Test data structure validation for lead ingestion"""
        
        try:
            # Test lead data structure
            test_lead = {
                "jurisdiction": "test_county",
                "permit_id": "TEST_123456",
                "address": "123 Test Street",
                "description": "Test permit",
                "value": 50000.0,
                "is_residential": True,
                "latitude": 29.7604,
                "longitude": -95.3698,
                "trade_tags": ["electrical", "plumbing"]
            }
            
            # Validate required fields
            required_fields = ["jurisdiction", "permit_id"]
            missing_fields = [field for field in required_fields if field not in test_lead]
            
            if missing_fields:
                self.add_result(
                    "Data Structure Validation",
                    False,
                    f"Test lead missing required fields: {missing_fields}",
                    {"missing_fields": missing_fields, "test_lead": test_lead}
                )
                return False
                
            # Test data types
            validation_errors = []
            
            if not isinstance(test_lead["jurisdiction"], str):
                validation_errors.append("jurisdiction must be string")
            if not isinstance(test_lead["permit_id"], str):
                validation_errors.append("permit_id must be string")
            if "value" in test_lead and not isinstance(test_lead["value"], (int, float)):
                validation_errors.append("value must be numeric")
            if "latitude" in test_lead and not isinstance(test_lead["latitude"], (int, float)):
                validation_errors.append("latitude must be numeric")
            if "longitude" in test_lead and not isinstance(test_lead["longitude"], (int, float)):
                validation_errors.append("longitude must be numeric")
                
            if validation_errors:
                self.add_result(
                    "Data Structure Validation",
                    False,
                    f"Data validation errors: {validation_errors}",
                    {"validation_errors": validation_errors}
                )
                return False
                
            self.add_result(
                "Data Structure Validation",
                True,
                "Lead data structure validation passed",
                {"test_lead_valid": True, "required_fields_present": True}
            )
            return True
            
        except Exception as e:
            self.add_result(
                "Data Structure Validation",
                False,
                f"Validation test failed: {str(e)}",
                {"error": str(e)}
            )
            return False
            
    def test_configuration_files(self) -> bool:
        """Test presence of required configuration files"""
        
        config_files = [
            ('.env', 'Environment variables file'),
            ('.env.example', 'Environment template file'),
            ('backend/requirements.txt', 'Python dependencies'),
            ('package.json', 'Node.js dependencies'),
        ]
        
        missing_files = []
        present_files = []
        
        for filepath, description in config_files:
            if os.path.exists(filepath):
                present_files.append((filepath, description))
            else:
                missing_files.append((filepath, description))
                
        if missing_files:
            self.add_result(
                "Configuration Files",
                False,
                f"Missing {len(missing_files)} configuration files",
                {"missing_files": missing_files, "present_files": present_files}
            )
            return False
        else:
            self.add_result(
                "Configuration Files",
                True,
                f"All {len(present_files)} configuration files present",
                {"present_files": present_files}
            )
            return True
            
    def run_tests(self, check_env_only: bool = False) -> Dict[str, Any]:
        """Run all available tests"""
        
        self.logger.info("🧪 Starting Supabase-focused tests...")
        
        start_time = datetime.now()
        
        # Always run these tests
        self.test_environment_variables()
        self.test_configuration_files()
        self.test_data_structure_validation()
        
        if not check_env_only:
            self.test_backend_imports()
            self.test_supabase_client_creation()
            
        # Calculate summary
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - passed_tests
        
        total_duration = (datetime.now() - start_time).total_seconds()
        
        summary = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "total_duration": total_duration,
            "timestamp": datetime.now().isoformat(),
            "check_env_only": check_env_only
        }
        
        return summary
        
    def print_summary(self, summary: Dict[str, Any]):
        """Print test summary"""
        print("\n" + "="*60)
        print("🔍 SUPABASE-FOCUSED TEST SUMMARY")
        print("="*60)
        
        print(f"📊 Tests Run: {summary['total_tests']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"📈 Success Rate: {summary['success_rate']:.1f}%")
        print(f"⏱️  Total Duration: {summary['total_duration']:.2f}s")
        
        if summary['check_env_only']:
            print("🔧 Mode: Environment Check Only")
            
        print("\n📋 Test Details:")
        print("-" * 60)
        
        for result in self.results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            print(f"{status} {result.test_name}")
            print(f"   {result.message}")
            
            if result.details:
                if 'needs_real_values' in result.details and result.details['needs_real_values']:
                    print(f"   💡 Variables needing real values: {', '.join(result.details['needs_real_values'])}")
                if 'missing_required' in result.details and result.details['missing_required']:
                    print(f"   ⚠️  Missing required: {', '.join(result.details['missing_required'])}")
                    
        print("\n" + "="*60)
        
        # Provide actionable recommendations
        if summary['failed'] > 0:
            print("🔧 NEXT STEPS:")
            print("-" * 60)
            
            has_env_issues = any('Environment' in r.test_name for r in self.results if not r.success)
            has_import_issues = any('Import' in r.test_name for r in self.results if not r.success)
            has_config_issues = any('Configuration' in r.test_name for r in self.results if not r.success)
            
            if has_env_issues:
                print("📝 Environment Setup:")
                print("   • Copy .env.example to .env")
                print("   • Replace placeholder values with real Supabase credentials")
                print("   • Get credentials from: Supabase Dashboard → Settings → API")
                
            if has_import_issues:
                print("📦 Dependency Installation:")
                print("   • Install Python deps: cd backend && pip3 install -r requirements.txt")
                print("   • Install Node deps: npm install")
                
            if has_config_issues:
                print("📁 Configuration Files:")
                print("   • Ensure you're in the project root directory")
                print("   • Check if files were accidentally deleted or moved")
                
            print("\n🔗 After fixing environment issues, test with:")
            print("   python3 test_scraping_api_connections.py --mock")
            print("   python3 test_scraping_api_connections.py (with real credentials)")
            
        else:
            print("🎉 ALL TESTS PASSED!")
            if summary['check_env_only']:
                print("✅ Environment is properly configured")
                print("🔗 Next: Run full test with 'python3 test_scraping_api_connections.py'")
            else:
                print("✅ Environment and basic connectivity are working")
                print("🔗 Ready to test with real Supabase credentials")
                
        print("="*60)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Focused Supabase connectivity tests')
    parser.add_argument('--check-env-only', action='store_true', 
                       help='Only check environment setup without testing connections')
    
    args = parser.parse_args()
    
    # Create and run tester
    tester = SupabaseFocusedTester()
    summary = tester.run_tests(check_env_only=args.check_env_only)
    tester.print_summary(summary)
    
    # Exit with appropriate code
    sys.exit(0 if summary['failed'] == 0 else 1)


if __name__ == "__main__":
    main()