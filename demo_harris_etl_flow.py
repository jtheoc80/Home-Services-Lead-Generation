#!/usr/bin/env python3
"""
Demo script showing proper ETL state management flow for Harris County permits.

This script demonstrates:
1. How to query ArcGIS with ISSUEDDATE > last_run - interval '1 minute'
2. How to update last_run only after successful upsert
3. How the ETL state manager handles the source="harris_issued_permits"
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

# Add permit_leads to path
sys.path.append(str(Path(__file__).parent))

from permit_leads.adapters.etl_aware_arcgis_adapter import ETLAwareArcGISAdapter
from permit_leads.models.permit import PermitRecord

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MockJurisdiction:
    """Mock jurisdiction for Harris County testing."""

    def __init__(self):
        self.slug = "tx-harris"
        self.name = "Harris County"
        self.source_config = {
            "feature_server": "https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0",
            "date_field": "ISSUEDDATE",
            "date_format": "string",  # Use string format for timestamp queries
            "field_map": {
                "permit_id": "PERMITNUMBER",
                "issue_date": "ISSUEDDATE",
                "address": "FULLADDRESS",
                "description": "PROJECTNAME",
                "status": "STATUS",
                "work_class": "APPTYPE",
                "category": "APPTYPE",
                "value": "PERMITVALUATION",
                "applicant": "APPLICANTNAME",
                "owner": "OWNERNAME",
            },
        }


def simulate_upsert_operation(permits: List[PermitRecord]) -> bool:
    """
    Simulate an upsert operation to a database.

    In a real implementation, this would save the permits to Supabase
    or another database. For this demo, we just simulate success.

    Args:
        permits: List of permits to upsert

    Returns:
        True if upsert was successful
    """
    if not permits:
        logger.info("No permits to upsert")
        return True

    logger.info(f"Simulating upsert of {len(permits)} permits...")

    # Simulate some processing time and potential failure
    try:
        # In a real implementation, you would:
        # 1. Connect to the database
        # 2. Upsert each permit (insert or update if exists)
        # 3. Handle any errors
        # 4. Return success/failure status

        # For demo purposes, we'll just log the permits
        for i, permit in enumerate(permits[:3]):  # Show first 3 permits
            logger.info(f"  Permit {i+1}: {permit.permit_id} - {permit.address}")

        if len(permits) > 3:
            logger.info(f"  ... and {len(permits) - 3} more permits")

        logger.info("✅ Upsert operation successful")
        return True

    except Exception as e:
        logger.error(f"❌ Upsert operation failed: {e}")
        return False


def demonstrate_etl_flow():
    """Demonstrate the complete ETL flow with proper state management."""
    logger.info("🏠 Starting Harris County ETL Flow Demonstration")
    logger.info("=" * 60)

    # 1. Initialize the ETL-aware ArcGIS adapter
    logger.info("1. Initializing ETL-aware ArcGIS adapter...")
    jurisdiction = MockJurisdiction()
    adapter = ETLAwareArcGISAdapter(jurisdiction)

    logger.info(f"   ✅ Adapter created for {adapter.jurisdiction.name}")
    logger.info(f"   ✅ Source name: {adapter.source_name}")
    logger.info(f"   ✅ Date field: {adapter.date_field}")

    # 2. Check current ETL state
    logger.info("\n2. Checking current ETL state...")
    last_run = adapter.get_last_run()
    if last_run:
        logger.info(f"   ✅ Last successful run: {last_run}")
    else:
        logger.info("   ℹ️  No previous run recorded")

    # 3. Get the 'since' timestamp (includes 1-minute buffer)
    logger.info("\n3. Determining query timestamp...")
    since_timestamp = adapter.etl_state.get_since_timestamp(
        adapter.source_name, fallback_days=7
    )
    logger.info(f"   ✅ Will query permits with ISSUEDDATE > {since_timestamp}")
    logger.info("   ℹ️  Note: This includes a 1-minute buffer to prevent gaps")

    # 4. Simulate scraping permits (would normally query ArcGIS)
    logger.info("\n4. Scraping permits from ArcGIS...")
    logger.info("   ⚠️  Note: This is a demo - not making actual HTTP requests")

    # For demo purposes, create some mock permits
    mock_permits = [
        PermitRecord(
            permit_id="HP2025-001",
            jurisdiction="Harris County",
            address="123 Main St, Houston, TX",
            description="Single family residence",
            issue_date=datetime.now() - timedelta(hours=2),
            scraped_at=datetime.now(),
        ),
        PermitRecord(
            permit_id="HP2025-002",
            jurisdiction="Harris County",
            address="456 Oak Ave, Katy, TX",
            description="Commercial renovation",
            issue_date=datetime.now() - timedelta(hours=1),
            scraped_at=datetime.now(),
        ),
    ]

    logger.info(f"   ✅ Retrieved {len(mock_permits)} permits from ArcGIS")

    # 5. Simulate upsert operation
    logger.info("\n5. Upserting permits to database...")
    upsert_success = simulate_upsert_operation(mock_permits)

    # 6. Update ETL state ONLY after successful upsert
    logger.info("\n6. Updating ETL state...")
    if upsert_success:
        # This is the key requirement: only update after successful upsert
        success = adapter.update_etl_state_after_upsert(len(mock_permits))
        if success:
            logger.info(
                f"   ✅ ETL state updated successfully for {adapter.source_name}"
            )
        else:
            logger.info("   ⚠️  ETL state update failed (but upsert succeeded)")
    else:
        logger.info("   ⚠️  Skipping ETL state update due to upsert failure")

    # 7. Verify the updated state
    logger.info("\n7. Verifying ETL state update...")
    if upsert_success:
        new_last_run = adapter.get_last_run()
        if new_last_run:
            logger.info(f"   ✅ New last run timestamp: {new_last_run}")
            if last_run and new_last_run > last_run:
                logger.info("   ✅ Timestamp successfully advanced")
            elif not last_run:
                logger.info("   ✅ First run timestamp recorded")
        else:
            logger.info(
                "   ⚠️  Could not retrieve updated timestamp (database not available)"
            )

    logger.info("\n" + "=" * 60)
    logger.info("🎉 ETL Flow Demonstration Complete!")
    logger.info("\nKey Points Demonstrated:")
    logger.info("✅ Source name is exactly 'harris_issued_permits'")
    logger.info("✅ Query uses ISSUEDDATE > last_run - interval '1 minute'")
    logger.info("✅ ETL state is updated ONLY after successful upsert")
    logger.info("✅ Proper error handling and logging throughout")


if __name__ == "__main__":
    demonstrate_etl_flow()
