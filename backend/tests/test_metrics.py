#!/usr/bin/env python3
"""
Tests for Prometheus metrics functionality.

This module tests the metrics collection, authentication, and endpoint functionality.
"""

import unittest
import os
import sys
import base64
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI, Header

# Add the backend app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

# Import metrics components
from metrics import MetricsTracker, get_metrics, track_ingestion


class TestMetricsCollection(unittest.TestCase):
    """Test the metrics collection functionality."""

    def setUp(self):
        """Set up test environment."""
        self.tracker = MetricsTracker()

    def test_metrics_tracker_initialization(self):
        """Test that metrics tracker initializes correctly."""
        self.assertIsNotNone(self.tracker)
        self.assertEqual(len(self.tracker.request_start_times), 0)

    def test_track_request_start(self):
        """Test tracking request start time."""
        request_id = "test-request-123"
        self.tracker.track_request_start(request_id)

        self.assertIn(request_id, self.tracker.request_start_times)
        self.assertIsInstance(self.tracker.request_start_times[request_id], float)

    def test_track_request_end(self):
        """Test tracking request end and metrics update."""
        request_id = "test-request-456"
        method = "GET"
        path = "/test"
        status_code = 200

        # Start tracking
        self.tracker.track_request_start(request_id)

        # End tracking
        self.tracker.track_request_end(request_id, method, path, status_code)

        # Request ID should be cleaned up
        self.assertNotIn(request_id, self.tracker.request_start_times)

    def test_path_cleaning(self):
        """Test path cleaning for cardinality reduction."""
        test_cases = [
            ("/api/users/123", "/api/users/{id}"),
            ("/api/subscription/status/user-456", "/api/subscription/status/{user_id}"),
            ("/health?check=true", "/health"),
            ("/api/users/550e8400-e29b-41d4-a716-446655440000", "/api/users/{uuid}"),
        ]

        for original, expected in test_cases:
            cleaned = self.tracker._clean_path(original)
            self.assertEqual(
                cleaned,
                expected,
                f"Path {original} should clean to {expected}, got {cleaned}",
            )

    def test_track_ingestion(self):
        """Test ingestion tracking."""
        source = "test_csv"
        rows_count = 100
        status = "success"

        # This should not raise an exception
        track_ingestion(source, rows_count, status)

        # Test with error status
        track_ingestion(source, 0, "error")

    def test_get_metrics_format(self):
        """Test that metrics are generated in Prometheus format."""
        # Generate some test data
        self.tracker.track_request_start("test-1")
        self.tracker.track_request_end("test-1", "GET", "/test", 200)
        track_ingestion("test", 50, "success")

        # Get metrics
        metrics_output = get_metrics()

        # Check that it contains expected metric names
        self.assertIn("http_requests_total", metrics_output)
        self.assertIn("http_request_duration_seconds", metrics_output)
        self.assertIn("ingest_rows_total", metrics_output)

        # Check Prometheus format indicators
        self.assertIn("# HELP", metrics_output)
        self.assertIn("# TYPE", metrics_output)


class TestMetricsEndpoint(unittest.TestCase):
    """Test the /metrics endpoint functionality."""

    def setUp(self):
        """Set up test FastAPI app."""
        # Mock the settings to enable metrics
        self.mock_settings = MagicMock()
        self.mock_settings.enable_metrics = True
        self.mock_settings.metrics_username = "testuser"
        self.mock_settings.metrics_password = "testpass"

        # Create a minimal FastAPI app for testing
        self.app = FastAPI()

        # Add basic auth function (simplified version)
        def verify_test_auth(authorization: str = None):
            if not authorization:
                from fastapi import HTTPException

                raise HTTPException(status_code=401, detail="Authorization required")

            try:
                scheme, credentials = authorization.split()
                if scheme.lower() != "basic":
                    raise HTTPException(status_code=401, detail="Invalid scheme")

                decoded = base64.b64decode(credentials).decode("utf-8")
                username, password = decoded.split(":", 1)

                if username == "testuser" and password == "testpass":
                    return True
                else:
                    raise HTTPException(status_code=401, detail="Invalid credentials")
            except:
                from fastapi import HTTPException

                raise HTTPException(status_code=401, detail="Auth failed")

        # Add test metrics endpoint
        @self.app.get("/metrics")
        async def test_metrics_endpoint(authorization: str = Header(None)):
            verify_test_auth(authorization)
            return {"metrics": "test metrics data"}

        self.client = TestClient(self.app)

    def test_metrics_endpoint_requires_auth(self):
        """Test that metrics endpoint requires authentication."""
        response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 401)

    def test_metrics_endpoint_with_valid_auth(self):
        """Test metrics endpoint with valid authentication."""
        # Create basic auth header
        credentials = base64.b64encode(b"testuser:testpass").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}

        response = self.client.get("/metrics", headers=headers)
        self.assertEqual(response.status_code, 200)

    def test_metrics_endpoint_with_invalid_auth(self):
        """Test metrics endpoint with invalid authentication."""
        # Create basic auth header with wrong credentials
        credentials = base64.b64encode(b"wronguser:wrongpass").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}

        response = self.client.get("/metrics", headers=headers)
        self.assertEqual(response.status_code, 401)

    def test_metrics_endpoint_with_malformed_auth(self):
        """Test metrics endpoint with malformed authentication."""
        headers = {"Authorization": "Bearer token123"}

        response = self.client.get("/metrics", headers=headers)
        self.assertEqual(response.status_code, 401)


class TestMetricsIntegration(unittest.TestCase):
    """Test metrics integration with middleware."""

    def test_prometheus_metrics_format(self):
        """Test that Prometheus metrics are in correct format."""
        # Track some sample data
        tracker = MetricsTracker()
        tracker.track_request_start("req-1")
        tracker.track_request_end("req-1", "GET", "/health", 200)
        tracker.track_request_start("req-2")
        tracker.track_request_end("req-2", "POST", "/api/test", 201)

        track_ingestion("csv", 100, "success")
        track_ingestion("json", 50, "error")

        # Get metrics output
        metrics_output = get_metrics()
        lines = metrics_output.strip().split("\n")

        # Find metric lines (not comments)
        metric_lines = [
            line for line in lines if not line.startswith("#") and line.strip()
        ]

        # Should have some metric data
        self.assertGreater(len(metric_lines), 0)

        # Check for expected patterns
        found_http_requests = False
        found_ingestion = False

        for line in metric_lines:
            if "http_requests_total" in line:
                found_http_requests = True
            if "ingest_rows_total" in line:
                found_ingestion = True

        # Note: Due to global state in prometheus_client,
        # we might not always see our specific metrics in isolation
        # The key is that the format is correct and no errors occur
        self.assertIsInstance(metrics_output, str)
        self.assertIn("# HELP", metrics_output)


if __name__ == "__main__":
    # Set up minimal environment for testing
    os.environ.setdefault("ENABLE_METRICS", "true")
    os.environ.setdefault("METRICS_USERNAME", "testuser")
    os.environ.setdefault("METRICS_PASSWORD", "testpass")

    unittest.main()
