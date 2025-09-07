"""
Test cases for ArcGIS adapter improvements.

Tests the enhanced ArcGIS adapter with:
- Retries with jitter for HTTP 429/5xx
- Respect for maxRecordCount from layer metadata
- Throttling to ≤ 5 req/s
- Logging of exact ArcGIS count via returnCountOnly=true
"""

import pytest
import time
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from permit_leads.adapters.arcgis_adapter import ArcGISAdapter
from permit_leads.config_loader import Jurisdiction


@pytest.fixture
def mock_jurisdiction():
    """Create a mock jurisdiction for testing."""
    return Jurisdiction(
        slug="test-county",
        name="Test County",
        region_slug="test-region",
        state="TX",
        fips=None,
        timezone="America/Chicago",
        provider="arcgis",
        active=True,
        source_config={
            "url": "https://test.arcgis.com/rest/services/TestService/FeatureServer/0",
            "date_field": "issue_date",
            "field_map": {
                "permit_number": "permit_no",
                "issued_date": "issue_date",
                "permit_type": "type",
                "value": "value",
                "contractor": "contractor_name",
                "address": "address",
            },
        },
    )


@pytest.fixture
def adapter(mock_jurisdiction):
    """Create ArcGIS adapter with mock jurisdiction."""
    return ArcGISAdapter(mock_jurisdiction)


def test_adapter_initialization(mock_jurisdiction):
    """Test adapter initializes correctly with URL handling."""
    # Test with 'url' key
    adapter = ArcGISAdapter(mock_jurisdiction)
    assert adapter.feature_server.endswith("/query")
    assert (
        adapter.base_url
        == "https://test.arcgis.com/rest/services/TestService/FeatureServer/0"
    )

    # Test with 'feature_server' key
    mock_jurisdiction.source_config = {
        "feature_server": "https://test.arcgis.com/rest/services/TestService/FeatureServer/0",
        "date_field": "issue_date",
        "field_map": {},
    }
    adapter = ArcGISAdapter(mock_jurisdiction)
    assert adapter.feature_server.endswith("/query")


def test_rate_limiting(adapter):
    """Test rate limiting enforces ≤ 5 req/s."""
    start_time = time.time()

    # Simulate multiple rate limit calls
    for _ in range(3):
        adapter._rate_limit()

    elapsed = time.time() - start_time
    # Should take at least 2 * MIN_REQUEST_INTERVAL (0.4 seconds for 3 calls)
    expected_min_time = 2 * adapter.MIN_REQUEST_INTERVAL
    assert (
        elapsed >= expected_min_time
    ), f"Rate limiting too fast: {elapsed} < {expected_min_time}"


@patch("permit_leads.adapters.arcgis_adapter.time.sleep")
def test_jitter_on_429(mock_sleep, adapter):
    """Test that 429 errors trigger jitter backoff."""
    mock_response = Mock()
    mock_response.status_code = 429

    with patch.object(adapter.session, "get", return_value=mock_response) as mock_get:
        result = adapter._make_request_with_jitter("http://test.com", {}, max_retries=2)

        # Should have made 3 attempts (initial + 2 retries)
        assert mock_get.call_count == 3

        # Should have called sleep 3 times: 2 retries + 1 for rate limiting
        assert mock_sleep.call_count == 3

        # Verify backoff times include jitter (should be > base exponential backoff)
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        # Skip the first rate limiting call, check the actual retry backoffs
        retry_sleeps = [
            s for s in sleep_calls if s > 0.5
        ]  # Filter out rate limiting sleeps
        assert len(retry_sleeps) >= 2  # Should have at least 2 retry backoffs
        assert retry_sleeps[0] > 1.0  # First retry: 2^0 + jitter > 1
        assert retry_sleeps[1] > 2.0  # Second retry: 2^1 + jitter > 2


@patch("permit_leads.adapters.arcgis_adapter.time.sleep")
def test_jitter_on_5xx(mock_sleep, adapter):
    """Test that 5xx errors trigger jitter backoff."""
    mock_response = Mock()
    mock_response.status_code = 500

    with patch.object(adapter.session, "get", return_value=mock_response) as mock_get:
        result = adapter._make_request_with_jitter("http://test.com", {}, max_retries=1)

        # Should have made 2 attempts (initial + 1 retry)
        assert mock_get.call_count == 2

        # Should have called sleep twice: 1 retry + 1 for rate limiting
        assert mock_sleep.call_count == 2


def test_get_layer_metadata(adapter):
    """Test layer metadata retrieval."""
    mock_metadata = {
        "maxRecordCount": 1000,
        "supportsPagination": True,
        "currentVersion": 10.91,
    }

    with patch.object(adapter, "_make_request_with_jitter", return_value=mock_metadata):
        metadata = adapter._get_layer_metadata()

        assert metadata == mock_metadata
        assert adapter._layer_metadata == mock_metadata  # Should be cached


def test_get_total_count(adapter):
    """Test total count retrieval with logging."""
    mock_count_response = {"count": 1234}

    with patch.object(
        adapter, "_make_request_with_jitter", return_value=mock_count_response
    ) as mock_request:
        count = adapter._get_total_count("issue_date >= DATE '2023-01-01'")

        assert count == 1234

        # Verify correct parameters were used
        args, kwargs = mock_request.call_args
        url, params = args
        assert params["returnCountOnly"] == "true"
        assert params["where"] == "issue_date >= DATE '2023-01-01'"


def test_get_total_count_logging(adapter, caplog):
    """Test that total count is logged correctly."""
    mock_count_response = {"count": 5678}

    with caplog.at_level("INFO"):
        with patch.object(
            adapter, "_make_request_with_jitter", return_value=mock_count_response
        ):
            adapter._get_total_count("test_query")

            # Check that the count was logged
            assert (
                "Total ArcGIS record count for query 'test_query': 5678" in caplog.text
            )


@patch("permit_leads.adapters.arcgis_adapter.logger")
def test_scrape_permits_respects_max_record_count(mock_logger, adapter):
    """Test that scraping respects maxRecordCount from metadata."""
    # Mock metadata with specific maxRecordCount
    mock_metadata = {"maxRecordCount": 500}
    mock_count_response = {"count": 1000}
    mock_features_response = {
        "features": [
            {
                "attributes": {"permit_no": "TEST001", "issue_date": "2023-01-01"},
                "geometry": {"x": -95.0, "y": 29.0},
            }
        ]
    }

    def mock_request_side_effect(url, params):
        if params.get("returnCountOnly") == "true":
            return mock_count_response
        elif url.endswith("/0"):  # Metadata request
            return mock_metadata
        else:  # Features request
            return mock_features_response

    with patch.object(
        adapter, "_make_request_with_jitter", side_effect=mock_request_side_effect
    ):
        since = datetime.now() - timedelta(days=1)
        permits = adapter.scrape_permits(since, limit=None)

        # Check that maxRecordCount was logged
        info_calls = [
            call
            for call in mock_logger.info.call_args_list
            if "maxRecordCount" in str(call)
        ]
        assert len(info_calls) > 0
        assert "500" in str(info_calls[0])


def test_scrape_permits_limits_page_size(adapter):
    """Test that page size is limited by maxRecordCount."""
    mock_metadata = {"maxRecordCount": 100}
    mock_count_response = {"count": 50}
    mock_features_response = {"features": []}

    def mock_request_side_effect(url, params):
        if params.get("returnCountOnly") == "true":
            return mock_count_response
        elif url.endswith("/0"):  # Metadata request
            return mock_metadata
        else:  # Features request
            # Verify that resultRecordCount doesn't exceed maxRecordCount
            assert params.get("resultRecordCount", 0) <= 100
            return mock_features_response

    with patch.object(
        adapter, "_make_request_with_jitter", side_effect=mock_request_side_effect
    ):
        since = datetime.now() - timedelta(days=1)
        adapter.scrape_permits(since, limit=None)


def test_scrape_permits_logging_flow(adapter, caplog):
    """Test that all required logging happens during scraping."""
    mock_metadata = {"maxRecordCount": 1000}
    mock_count_response = {"count": 123}
    mock_features_response = {"features": []}

    def mock_request_side_effect(url, params):
        if params.get("returnCountOnly") == "true":
            return mock_count_response
        elif url.endswith("/0"):  # Metadata request
            return mock_metadata
        else:
            return mock_features_response

    with caplog.at_level("INFO"):
        with patch.object(
            adapter, "_make_request_with_jitter", side_effect=mock_request_side_effect
        ):
            since = datetime.now() - timedelta(days=1)
            adapter.scrape_permits(since, limit=None)

            # Check for required log messages
            log_text = caplog.text
            assert "Total ArcGIS record count" in log_text
            assert "123" in log_text  # The count
            assert "maxRecordCount: 1000" in log_text


def test_request_throttling_actual_timing():
    """Test that actual request timing respects rate limits."""
    from permit_leads.config_loader import Jurisdiction
    from permit_leads.adapters.arcgis_adapter import ArcGISAdapter

    mock_jurisdiction = Jurisdiction(
        slug="test",
        name="Test",
        region_slug="test",
        state="TX",
        fips=None,
        timezone="America/Chicago",
        provider="arcgis",
        active=True,
        source_config={
            "url": "https://test.com/service/0",
            "date_field": "date",
            "field_map": {},
        },
    )
    adapter = ArcGISAdapter(mock_jurisdiction)

    # Test timing manually
    start_time = time.time()
    adapter._rate_limit()  # First call
    adapter._rate_limit()  # Second call should be delayed
    elapsed = time.time() - start_time

    # Should take at least MIN_REQUEST_INTERVAL
    assert elapsed >= adapter.MIN_REQUEST_INTERVAL * 0.9  # Allow some tolerance


def test_error_handling_in_scrape_permits(adapter):
    """Test error handling during scraping."""
    with patch.object(
        adapter, "_make_request_with_jitter", side_effect=Exception("Test error")
    ):
        since = datetime.now() - timedelta(days=1)
        permits = adapter.scrape_permits(since, limit=None)

        # Should return empty list on error
        assert permits == []


def test_config_key_compatibility(mock_jurisdiction):
    """Test backward compatibility with both 'url' and 'feature_server' keys."""
    # Test 'url' key (new format)
    mock_jurisdiction.source_config["url"] = "https://test.com/service/0"
    adapter1 = ArcGISAdapter(mock_jurisdiction)
    assert adapter1.feature_server.endswith("/query")

    # Test 'feature_server' key (old format)
    del mock_jurisdiction.source_config["url"]
    mock_jurisdiction.source_config["feature_server"] = "https://test.com/service/0"
    adapter2 = ArcGISAdapter(mock_jurisdiction)
    assert adapter2.feature_server.endswith("/query")

    # Test missing both keys raises error
    del mock_jurisdiction.source_config["feature_server"]
    with pytest.raises(ValueError, match="No feature_server or url found"):
        ArcGISAdapter(mock_jurisdiction)


def test_max_requests_per_second_constant():
    """Test that the rate limiting constant is set correctly."""
    assert ArcGISAdapter.MAX_REQUESTS_PER_SECOND == 5
    assert ArcGISAdapter.MIN_REQUEST_INTERVAL == 0.2  # 1/5 = 0.2 seconds
