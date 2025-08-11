#!/usr/bin/env python3
"""
Test script for the ETL-aware ArcGIS adapter.

This script tests the adapter functionality without making actual HTTP requests.
"""
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add permit_leads to path
sys.path.append(str(Path(__file__).parent.parent))

from permit_leads.config_loader import Jurisdiction
from permit_leads.adapters.etl_aware_arcgis_adapter import ETLAwareArcGISAdapter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockJurisdiction:
    """Mock jurisdiction for testing."""
    def __init__(self):
        self.slug = 'tx-harris'
        self.name = 'Harris County'
        self.source_config = {
            'feature_server': 'https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0',
            'date_field': 'ISSUEDDATE',
            'field_map': {
                'permit_id': 'PERMITNUMBER',
                'issue_date': 'ISSUEDDATE',
                'address': 'FULLADDRESS',
                'description': 'PROJECTNAME',
                'status': 'STATUS',
                'work_class': 'APPTYPE',
                'category': 'APPTYPE',
                'value': 'PERMITVALUATION',
                'applicant': 'APPLICANTNAME',
                'owner': 'OWNERNAME'
            }
        }


def test_adapter_initialization():
    """Test adapter initialization."""
    logger.info("Testing ETL-aware ArcGIS adapter initialization...")
    
    # Create mock jurisdiction
    jurisdiction = MockJurisdiction()
    
    # Initialize adapter
    adapter = ETLAwareArcGISAdapter(jurisdiction)
    
    logger.info(f"✅ Adapter created for {adapter.jurisdiction.name}")
    logger.info(f"✅ Source name: {adapter.source_name}")
    logger.info(f"✅ Date field: {adapter.date_field}")
    logger.info(f"✅ Feature server: {adapter.feature_server}")
    
    # Test ETL state methods
    last_run = adapter.get_last_run()
    logger.info(f"✅ Last run: {last_run}")
    
    # Test since timestamp generation
    since = adapter.etl_state.get_since_timestamp(adapter.source_name)
    logger.info(f"✅ Since timestamp: {since}")


if __name__ == "__main__":
    test_adapter_initialization()