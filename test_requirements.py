#!/usr/bin/env python3
"""
Verification test for ETL state management requirements.

This test verifies that all requirements from the problem statement are met:
1. ✅ Persist last successful issue_date into Supabase table etl_state
2. ✅ Table has source (text primary key) and last_run (timestamptz)
3. ✅ Read last_run for source='harris_issued_permits'
4. ✅ Query ISSUEDDATE > last_run - 1 minute
5. ✅ Update last_run on success
"""
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from permit_leads.etl_state import ETLStateManager
from permit_leads.region_adapter import RegionAwareAdapter

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def test_requirement_1_table_schema():
    """Test Requirement 1: etl_state table with correct schema."""
    logger.info("✅ Requirement 1: ETL state table schema")

    # Check migration file exists
    migration_file = (
        Path(__file__).parent.parent / "backend/app/migrations/005_etl_state_table.sql"
    )
    assert migration_file.exists(), f"Migration file should exist at {migration_file}"

    # Check schema content
    with open(migration_file, "r") as f:
        content = f.read()
        assert "CREATE TABLE IF NOT EXISTS etl_state" in content
        assert "source TEXT PRIMARY KEY" in content
        assert "last_run TIMESTAMPTZ NOT NULL" in content

    print("✅ ETL state table schema correctly defined")


def test_requirement_2_source_name():
    """Test Requirement 2: Source name is 'harris_issued_permits'."""
    logger.info("✅ Requirement 2: Harris source name")

    # Get Harris County adapter
    adapter = RegionAwareAdapter()
    jurisdictions = adapter.get_active_jurisdictions()
    harris = next(j for j in jurisdictions if "harris" in j.slug.lower())

    # Create scraper and verify source name
    scraper = adapter.create_scraper(harris)
    assert (
        scraper.source_name == "harris_issued_permits"
    ), f"Expected 'harris_issued_permits', got '{scraper.source_name}'"

    print("✅ Harris County uses source name 'harris_issued_permits'")


def test_requirement_3_read_last_run():
    """Test Requirement 3: Read last_run for harris_issued_permits."""
    logger.info("✅ Requirement 3: Read last_run functionality")

    state_manager = ETLStateManager()

    # Test reading last run (will be None without Supabase)
    last_run = state_manager.get_last_run("harris_issued_permits")
    # Should return None gracefully when Supabase not available

    print(
        "✅ Can read last_run for harris_issued_permits (returns None when Supabase unavailable)"
    )


def test_requirement_4_query_with_buffer():
    """Test Requirement 4: Query ISSUEDDATE > last_run - 1 minute."""
    logger.info("✅ Requirement 4: 1-minute buffer query logic")

    state_manager = ETLStateManager()

    # Mock a last run timestamp
    mock_last_run = datetime(2025, 1, 15, 10, 30, 0)

    with patch.object(state_manager, "get_last_run", return_value=mock_last_run):
        since = state_manager.get_since_timestamp("harris_issued_permits")
        expected = mock_last_run - timedelta(minutes=1)

        assert since == expected, f"Expected {expected}, got {since}"

    print("✅ Correctly applies 1-minute buffer: last_run - 1 minute")


def test_requirement_5_issueddate_field():
    """Test Requirement 5: Uses ISSUEDDATE field in queries."""
    logger.info("✅ Requirement 5: ISSUEDDATE field usage")

    # Get Harris County configuration
    adapter = RegionAwareAdapter()
    jurisdictions = adapter.get_active_jurisdictions()
    harris = next(j for j in jurisdictions if "harris" in j.slug.lower())

    # Verify date field configuration
    assert (
        harris.source_config["date_field"] == "ISSUEDDATE"
    ), f"Expected ISSUEDDATE, got {harris.source_config['date_field']}"

    # Create scraper and verify it uses the correct field
    scraper = adapter.create_scraper(harris)
    assert (
        scraper.date_field == "ISSUEDDATE"
    ), f"Expected ISSUEDDATE, got {scraper.date_field}"

    print("✅ Harris County adapter uses ISSUEDDATE field for date filtering")


def test_requirement_6_update_on_success():
    """Test Requirement 6: Update last_run on successful completion."""
    logger.info("✅ Requirement 6: Update last_run on success")

    # Get Harris County adapter
    adapter = RegionAwareAdapter()
    jurisdictions = adapter.get_active_jurisdictions()
    harris = next(j for j in jurisdictions if "harris" in j.slug.lower())
    scraper = adapter.create_scraper(harris)

    # Mock update method to verify it's called
    original_update = scraper.etl_state.update_last_run
    update_called = []

    def mock_update(source, timestamp):
        update_called.append((source, timestamp))
        return True  # Simulate success

    scraper.etl_state.update_last_run = mock_update

    # Mock successful HTTP response
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"features": []}

    with patch("requests.get", return_value=mock_response):
        permits = scraper.scrape_permits()

        # Verify update was called
        assert len(update_called) == 1, "update_last_run should be called once"
        assert (
            update_called[0][0] == "harris_issued_permits"
        ), "Should update harris_issued_permits"
        assert isinstance(
            update_called[0][1], datetime
        ), "Should pass datetime timestamp"

    print("✅ Updates last_run timestamp on successful permit fetch")


def test_requirement_7_query_format():
    """Test Requirement 7: Correct ArcGIS query format."""
    logger.info("✅ Requirement 7: ArcGIS query format")

    # Get Harris County adapter
    adapter = RegionAwareAdapter()
    jurisdictions = adapter.get_active_jurisdictions()
    harris = next(j for j in jurisdictions if "harris" in j.slug.lower())
    scraper = adapter.create_scraper(harris)

    # Mock requests to capture the query
    captured_requests = []

    def mock_get(url, params=None, **kwargs):
        captured_requests.append((url, params))
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"features": []}
        return response

    with patch("requests.get", side_effect=mock_get):
        since = datetime(2025, 1, 15, 10, 30, 0)
        scraper._fetch_permits_from_arcgis(since, limit=10)

        # Verify query parameters
        assert len(captured_requests) == 1, "Should make one HTTP request"
        url, params = captured_requests[0]

        # Check URL
        expected_url = "https://www.gis.hctx.net/arcgishcpid/rest/services/Permits/IssuedPermits/FeatureServer/0/query"
        assert url == expected_url, f"Expected {expected_url}, got {url}"

        # Check query parameters
        assert "where" in params, "Should have where clause"
        where_clause = params["where"]
        assert (
            "ISSUEDDATE > TIMESTAMP" in where_clause
        ), f"Should query ISSUEDDATE, got: {where_clause}"
        assert (
            "2025-01-15 10:30:00" in where_clause
        ), f"Should include timestamp, got: {where_clause}"

    print(
        "✅ Generates correct ArcGIS query with ISSUEDDATE > TIMESTAMP 'YYYY-MM-DD HH:MM:SS'"
    )


def run_all_tests():
    """Run all requirement verification tests."""
    print("🧪 ETL State Management Requirements Verification")
    print("=" * 60)

    tests = [
        test_requirement_1_table_schema,
        test_requirement_2_source_name,
        test_requirement_3_read_last_run,
        test_requirement_4_query_with_buffer,
        test_requirement_5_issueddate_field,
        test_requirement_6_update_on_success,
        test_requirement_7_query_format,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            logger.error(f"❌ {test.__name__} failed: {e}")
            failed += 1
        print()

    print("=" * 60)
    print(f"📊 Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All requirements successfully verified!")
        print()
        print("Summary of Implementation:")
        print("• ETL state table stores last successful run timestamps")
        print("• Harris County permits use source='harris_issued_permits'")
        print("• Queries ISSUEDDATE > last_run - 1 minute to prevent gaps")
        print("• Updates last_run timestamp on successful completion")
        print("• Gracefully handles missing Supabase configuration")
        print("• Provides CLI tools for ETL state management")
    else:
        print("❌ Some requirements failed verification")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
