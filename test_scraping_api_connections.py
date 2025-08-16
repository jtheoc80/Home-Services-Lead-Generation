#!/usr/bin/env python3
"""
Comprehensive Test Script for Scraping and API Connections to Supabase

This script tests:
1. Supabase database connectivity
2. Harris County permits scraper API connection
3. Data flow from scraping to Supabase
4. API endpoints that serve scraped data
5. End-to-end data verification

Usage:
    python3 test_scraping_api_connections.py [--mock] [--verbose]

Options:
    --mock      Use mock data instead of real API calls (safer for testing)
    --verbose   Enable detailed logging output
"""

import os
import sys
import json
import logging
import argparse
import asyncio
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not available, .env file will not be loaded")

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from supabase import create_client, Client
    from app.supabase_client import get_supabase_client
    from app.ingest import insert_lead
except ImportError as e:
    print(f"Warning: Could not import backend modules: {e}")
    print("Some tests may be skipped. Ensure you're in the project root and dependencies are installed.")

@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    duration: Optional[float] = None

class ScrapingAPITester:
    """Main test class for scraping and API connections"""
    
    def __init__(self, mock: bool = False, verbose: bool = False):
        self.mock = mock
        self.verbose = verbose
        self.setup_logging()
        self.results: List[TestResult] = []
        
        # Load environment variables
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_SERVICE_ROLE')
        self.harris_permits_url = os.getenv('HC_ISSUED_PERMITS_URL', 
            'https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0')
        
    def setup_logging(self):
        """Configure logging"""
        level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        self.logger = logging.getLogger(__name__)
        
    def add_result(self, test_name: str, success: bool, message: str, 
                   details: Optional[Dict[str, Any]] = None, duration: Optional[float] = None):
        """Add a test result"""
        result = TestResult(test_name, success, message, details, duration)
        self.results.append(result)
        
        # Log the result
        status = "✓ PASS" if success else "✗ FAIL"
        self.logger.info(f"{status} {test_name}: {message}")
        if details and self.verbose:
            self.logger.debug(f"Details: {json.dumps(details, indent=2)}")
            
    async def test_environment_setup(self) -> bool:
        """Test if required environment variables are set"""
        start_time = datetime.now()
        
        required_vars = ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var) and not os.getenv(var.replace('_KEY', '')):
        # Use unified fallback logic for required environment variables
        required_vars = [
            ('SUPABASE_URL', None),
            ('SUPABASE_SERVICE_ROLE_KEY', 'SUPABASE_SERVICE_ROLE')
        ]
        missing_vars = []
        
        for primary, fallback in required_vars:
            if get_env_with_fallback(primary, fallback) is None:
                if fallback:
                    missing_vars.append(f"{primary} (or fallback {fallback})")
                else:
                    missing_vars.append(primary)
                
        if missing_vars:
            self.add_result(
                "Environment Setup",
                False,
                f"Missing required environment variables: {', '.join(missing_vars)}",
                {"missing_vars": missing_vars, "note": "Create .env file with required variables"},
                (datetime.now() - start_time).total_seconds()
            )
            return False
            
        # Check if URLs are accessible
        env_details = {
            "supabase_url": self.supabase_url,
            "harris_permits_url": self.harris_permits_url,
            "service_key_present": bool(self.supabase_service_key)
        }
        
        self.add_result(
            "Environment Setup",
            True,
            "All required environment variables are present",
            env_details,
            (datetime.now() - start_time).total_seconds()
        )
        return True
        
    async def test_supabase_connectivity(self) -> bool:
        """Test Supabase database connectivity"""
        start_time = datetime.now()
        
        if not self.supabase_url or not self.supabase_service_key:
            self.add_result(
                "Supabase Connectivity",
                False,
                "Supabase credentials not configured",
                None,
                (datetime.now() - start_time).total_seconds()
            )
            return False
            
        try:
            # Test direct connection
            supabase: Client = create_client(self.supabase_url, self.supabase_service_key)
            
            # Test query to leads table
            result = supabase.table('leads').select('id', count='exact').limit(1).execute()
            
            details = {
                "table": "leads",
                "connection_method": "direct",
                "record_count": result.count if result.count is not None else 0
            }
            
            self.add_result(
                "Supabase Connectivity",
                True,
                f"Successfully connected to Supabase. Leads table has {result.count or 0} records.",
                details,
                (datetime.now() - start_time).total_seconds()
            )
            return True
            
        except Exception as e:
            self.add_result(
                "Supabase Connectivity", 
                False,
                f"Failed to connect to Supabase: {str(e)}",
                {"error": str(e), "error_type": type(e).__name__},
                (datetime.now() - start_time).total_seconds()
            )
            return False
            
    async def test_harris_county_api(self) -> bool:
        """Test Harris County permits API connectivity"""
        start_time = datetime.now()
        
        if self.mock:
            # Mock successful API test
            self.add_result(
                "Harris County API",
                True,
                "Mock API test passed",
                {"mock": True, "url": self.harris_permits_url},
                (datetime.now() - start_time).total_seconds()
            )
            return True
            
        try:
            # Test basic connectivity to Harris County API
            test_query = f"{self.harris_permits_url}/query"
            params = {
                'f': 'json',
                'where': '1=1',
                'outFields': 'OBJECTID',
                'resultRecordCount': 1
            }
            
            response = requests.get(test_query, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'features' in data:
                feature_count = len(data.get('features', []))
                details = {
                    "url": test_query,
                    "response_status": response.status_code,
                    "features_returned": feature_count,
                    "api_available": True
                }
                
                self.add_result(
                    "Harris County API",
                    True,
                    f"Successfully connected to Harris County API. Got {feature_count} test features.",
                    details,
                    (datetime.now() - start_time).total_seconds()
                )
                return True
            else:
                self.add_result(
                    "Harris County API",
                    False,
                    f"Unexpected API response format: {data}",
                    {"response_data": data},
                    (datetime.now() - start_time).total_seconds()
                )
                return False
                
        except requests.exceptions.Timeout:
            self.add_result(
                "Harris County API",
                False,
                "API request timed out (30 seconds)",
                {"error": "timeout", "url": self.harris_permits_url},
                (datetime.now() - start_time).total_seconds()
            )
            return False
        except requests.exceptions.RequestException as e:
            self.add_result(
                "Harris County API",
                False,
                f"Failed to connect to Harris County API: {str(e)}",
                {"error": str(e), "url": self.harris_permits_url},
                (datetime.now() - start_time).total_seconds()
            )
            return False
            
    async def test_data_ingestion(self) -> bool:
        """Test data ingestion from scraping to Supabase"""
        start_time = datetime.now()
        
        if not self.supabase_url or not self.supabase_service_key:
            self.add_result(
                "Data Ingestion",
                False,
                "Supabase not configured for ingestion test",
                None,
                (datetime.now() - start_time).total_seconds()
            )
            return False
            
        try:
            # Create a test lead data structure
            test_lead = {
                "jurisdiction": "harris_county_test",
                "permit_id": f"TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex}",
                "address": "123 Test Street, Houston, TX",
                "description": "Test permit for API connection verification",
                "value": 50000.0,
                "is_residential": True,
                "latitude": 29.7604,
                "longitude": -95.3698,
                "trade_tags": ["electrical", "plumbing"],
                "source": "api_connection_test"
            }
            
            # Test ingestion using the insert_lead function
            try:
                from app.ingest import insert_lead
                result = insert_lead(test_lead)
                
                details = {
                    "test_lead_id": result.get("id"),
                    "permit_id": test_lead["permit_id"],
                    "ingestion_method": "insert_lead_function",
                    "success": True
                }
                
                self.add_result(
                    "Data Ingestion",
                    True,
                    f"Successfully inserted test lead with ID: {result.get('id')}",
                    details,
                    (datetime.now() - start_time).total_seconds()
                )
                return True
                
            except ImportError:
                # Fall back to direct Supabase insertion
                supabase: Client = create_client(self.supabase_url, self.supabase_service_key)
                result = supabase.table('leads').insert(test_lead).execute()
                
                details = {
                    "test_lead_id": result.data[0].get("id") if result.data else None,
                    "permit_id": test_lead["permit_id"],
                    "ingestion_method": "direct_supabase",
                    "success": True
                }
                
                self.add_result(
                    "Data Ingestion", 
                    True,
                    f"Successfully inserted test lead via direct Supabase call",
                    details,
                    (datetime.now() - start_time).total_seconds()
                )
                return True
                
        except Exception as e:
            self.add_result(
                "Data Ingestion",
                False,
                f"Failed to ingest test data: {str(e)}",
                {"error": str(e), "test_lead": test_lead},
                (datetime.now() - start_time).total_seconds()
            )
            return False
            
    async def test_api_endpoints(self) -> bool:
        """Test API endpoints that serve scraped data"""
        start_time = datetime.now()
        
        # Test different API endpoints
        endpoints_to_test = [
            {"path": "/health/supabase", "description": "Supabase health check"},
            {"path": "/api/supa-env-check", "description": "Environment check"},
        ]
        
        base_url = os.getenv('BACKEND_URL', 'http://localhost:8000')
        successful_tests = 0
        
        for endpoint in endpoints_to_test:
            try:
                url = f"{base_url}{endpoint['path']}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    successful_tests += 1
                    self.logger.debug(f"✓ {endpoint['description']} - Status: {response.status_code}")
                else:
                    self.logger.debug(f"⚠ {endpoint['description']} - Status: {response.status_code}")
                    
            except requests.exceptions.ConnectionError:
                self.logger.debug(f"⚠ {endpoint['description']} - Connection refused (server not running)")
            except Exception as e:
                self.logger.debug(f"⚠ {endpoint['description']} - Error: {str(e)}")
                
        if successful_tests > 0:
            self.add_result(
                "API Endpoints",
                True,
                f"Successfully tested {successful_tests}/{len(endpoints_to_test)} API endpoints",
                {"base_url": base_url, "successful_tests": successful_tests, "total_tests": len(endpoints_to_test)},
                (datetime.now() - start_time).total_seconds()
            )
            return True
        else:
            self.add_result(
                "API Endpoints",
                False,
                f"No API endpoints were accessible. Backend server may not be running at {base_url}",
                {"base_url": base_url, "note": "Start backend with 'uvicorn main:app' from backend directory"},
                (datetime.now() - start_time).total_seconds()
            )
            return False
            
    async def test_permits_raw_table(self) -> bool:
        """Test permits_raw_harris table connectivity and data"""
        start_time = datetime.now()
        
        if not self.supabase_url or not self.supabase_service_key:
            self.add_result(
                "Permits Raw Table",
                False,
                "Supabase not configured",
                None,
                (datetime.now() - start_time).total_seconds()
            )
            return False
            
        try:
            supabase: Client = create_client(self.supabase_url, self.supabase_service_key)
            
            # Test permits_raw_harris table
            result = supabase.table('permits_raw_harris').select('event_id', count='exact').limit(1).execute()
            
            details = {
                "table": "permits_raw_harris",
                "record_count": result.count if result.count is not None else 0,
                "table_accessible": True
            }
            
            self.add_result(
                "Permits Raw Table",
                True,
                f"Successfully queried permits_raw_harris table. Found {result.count or 0} records.",
                details,
                (datetime.now() - start_time).total_seconds()
            )
            return True
            
        except Exception as e:
            self.add_result(
                "Permits Raw Table",
                False,
                f"Failed to access permits_raw_harris table: {str(e)}",
                {"error": str(e), "note": "Table may not exist. Run migrations first."},
                (datetime.now() - start_time).total_seconds()
            )
            return False
            
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return summary"""
        self.logger.info("🚀 Starting comprehensive scraping and API connection tests...")
        
        start_time = datetime.now()
        
        # Run all tests
        tests = [
            self.test_environment_setup(),
            self.test_supabase_connectivity(),
            self.test_harris_county_api(),
            self.test_permits_raw_table(),
            self.test_data_ingestion(),
            self.test_api_endpoints(),
        ]
        
        await asyncio.gather(*tests, return_exceptions=True)
        
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
            "mock_mode": self.mock
        }
        
        return summary
        
    def print_summary(self, summary: Dict[str, Any]):
        """Print test summary"""
        print("\n" + "="*60)
        print("🧪 SCRAPING AND API CONNECTION TEST SUMMARY")
        print("="*60)
        
        print(f"📊 Tests Run: {summary['total_tests']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"📈 Success Rate: {summary['success_rate']:.1f}%")
        print(f"⏱️  Total Duration: {summary['total_duration']:.2f}s")
        
        if summary['mock_mode']:
            print("🎭 Mock Mode: Enabled")
            
        print("\n📋 Test Details:")
        print("-" * 60)
        
        for result in self.results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            duration = f"({result.duration:.2f}s)" if result.duration else ""
            print(f"{status} {result.test_name} {duration}")
            print(f"   {result.message}")
            
            if not result.success and result.details:
                if 'note' in result.details:
                    print(f"   💡 Note: {result.details['note']}")
                    
        print("\n" + "="*60)
        
        # Provide actionable recommendations
        if summary['failed'] > 0:
            print("🔧 RECOMMENDED ACTIONS:")
            print("-" * 60)
            
            for result in self.results:
                if not result.success:
                    if "environment" in result.test_name.lower():
                        print("• Create .env file with required Supabase credentials")
                        print("• Copy .env.example to .env and fill in your values")
                    elif "supabase" in result.test_name.lower():
                        print("• Verify Supabase URL and service role key in .env")
                        print("• Check Supabase project status and permissions")
                    elif "harris" in result.test_name.lower():
                        print("• Check internet connectivity")
                        print("• Verify Harris County API is operational")
                    elif "api" in result.test_name.lower():
                        print("• Start the backend server: cd backend && uvicorn main:app")
                        print("• Check BACKEND_URL environment variable")
                    elif "permits_raw" in result.test_name.lower():
                        print("• Run database migrations to create permits_raw_harris table")
                        print("• Check database permissions and table existence")
                        
        else:
            print("🎉 ALL TESTS PASSED!")
            print("✅ Scraping and API connections are working correctly")
            print("✅ Data is being properly forwarded to Supabase")
            
        print("="*60)


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Test scraping and API connections to Supabase')
    parser.add_argument('--mock', action='store_true', help='Use mock data instead of real API calls')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Create and run tester
    tester = ScrapingAPITester(mock=args.mock, verbose=args.verbose)
    summary = await tester.run_all_tests()
    tester.print_summary(summary)
    
    # Exit with appropriate code
    sys.exit(0 if summary['failed'] == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())