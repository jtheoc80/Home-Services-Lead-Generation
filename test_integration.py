#!/usr/bin/env python3
"""
Integration test for ETL state management with Harris County permits.

This demonstrates the complete ETL state workflow without requiring
actual HTTP requests or Supabase connectivity.
"""
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

# Add permit_leads to path
sys.path.append(str(Path(__file__).parent.parent))

from permit_leads.region_adapter import RegionAwareAdapter
from permit_leads.models.permit import PermitRecord

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def mock_arcgis_response():
    """Create a mock ArcGIS response."""
    return {
        'features': [
            {
                'attributes': {
                    'PERMITNUMBER': 'BP2025000001',
                    'ISSUEDDATE': int(datetime.now().timestamp() * 1000),  # epoch milliseconds
                    'FULLADDRESS': '123 Main St, Houston, TX 77001',
                    'PROJECTNAME': 'Single Family Residence',
                    'STATUS': 'Issued',
                    'APPTYPE': 'Residential Building',
                    'PERMITVALUATION': 350000,
                    'APPLICANTNAME': 'ABC Construction LLC',
                    'OWNERNAME': 'John Doe'
                },
                'geometry': {
                    'x': -95.3698,
                    'y': 29.7604
                }
            },
            {
                'attributes': {
                    'PERMITNUMBER': 'BP2025000002',
                    'ISSUEDDATE': int((datetime.now() - timedelta(hours=2)).timestamp() * 1000),
                    'FULLADDRESS': '456 Oak Ave, Houston, TX 77002',
                    'PROJECTNAME': 'Kitchen Renovation',
                    'STATUS': 'Issued',
                    'APPTYPE': 'Residential Alteration',
                    'PERMITVALUATION': 85000,
                    'APPLICANTNAME': 'XYZ Contractors Inc',
                    'OWNERNAME': 'Jane Smith'
                },
                'geometry': {
                    'x': -95.3799,
                    'y': 29.7505
                }
            }
        ]
    }


def test_harris_county_etl_integration():
    """Test the complete ETL integration for Harris County."""
    logger.info("🏗️  Testing Harris County ETL Integration")
    
    # Initialize region adapter
    adapter = RegionAwareAdapter()
    
    # Get Harris County configuration
    jurisdictions = adapter.get_active_jurisdictions()
    harris = None
    for j in jurisdictions:
        if 'harris' in j.slug.lower():
            harris = j
            break
    
    if not harris:
        logger.error("❌ Harris County not found in configuration")
        return
    
    logger.info(f"✅ Found Harris County: {harris.name}")
    
    # Create ETL-aware scraper
    scraper = adapter.create_scraper(harris)
    logger.info(f"✅ Created {type(scraper).__name__}")
    
    # Check ETL state management
    logger.info(f"🔍 ETL Source: {scraper.source_name}")
    
    # Test getting last run (should be None initially)
    last_run = scraper.get_last_run()
    logger.info(f"📅 Last run: {last_run}")
    
    # Test since timestamp generation
    since = scraper.etl_state.get_since_timestamp(scraper.source_name)
    logger.info(f"📅 Since timestamp (with buffer): {since}")
    
    # Mock the HTTP request to test parsing
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = mock_arcgis_response()
    
    with patch('requests.get', return_value=mock_response):
        logger.info("🌐 Testing permit fetching with mocked response...")
        
        # Test scraping without actual HTTP request
        permits = scraper._fetch_permits_from_arcgis(since, limit=10)
        
        logger.info(f"📋 Fetched {len(permits)} permits")
        
        for i, permit in enumerate(permits):
            logger.info(f"  {i+1}. {permit.permit_id} - {permit.address}")
            logger.info(f"     Type: {permit.work_class}, Value: ${permit.value:,.2f}")
            logger.info(f"     Issue Date: {permit.issue_date}")
    
    # Test successful completion workflow
    logger.info("✅ ETL Integration Test Complete")
    
    # Show what would happen on successful run
    current_time = datetime.utcnow()
    logger.info(f"💾 Would update last_run to: {current_time}")
    
    # Calculate next run's since timestamp
    next_since = current_time - timedelta(minutes=1)
    logger.info(f"➡️  Next run would start from: {next_since} (1-minute buffer)")


if __name__ == "__main__":
    test_harris_county_etl_integration()