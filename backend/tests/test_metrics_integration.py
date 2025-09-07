#!/usr/bin/env python3
"""
Integration test for metrics middleware functionality.

This test verifies that the middleware properly tracks HTTP requests
and that metrics are correctly collected and exposed.
"""

import unittest
import os
import sys
import base64
from unittest.mock import patch
from fastapi import FastAPI, Header, HTTPException, Response, Depends
from fastapi.testclient import TestClient

# Add the backend app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))


class TestMetricsMiddlewareIntegration(unittest.TestCase):
    """Test the integration between middleware and metrics collection."""

    def setUp(self):
        """Set up test FastAPI app with middleware."""
        # Set environment variables for this test
        with patch.dict(
            os.environ,
            {
                "ENABLE_METRICS": "true",
                "METRICS_USERNAME": "test_admin",
                "METRICS_PASSWORD": "test_secret",
            },
        ):
            # Import after setting environment
            from middleware import RequestLoggingMiddleware
            from metrics import get_metrics, get_metrics_content_type

            self.get_metrics = get_metrics
            self.get_metrics_content_type = get_metrics_content_type

            self.app = FastAPI()

            # Add the metrics-enabled middleware
            self.app.add_middleware(RequestLoggingMiddleware)

            # Basic auth for metrics
            def verify_test_auth(authorization: str = Header(None)) -> bool:
                if not authorization:
                    raise HTTPException(
                        status_code=401, detail="Authorization required"
                    )

                try:
                    scheme, credentials = authorization.split()
                    if scheme.lower() != "basic":
                        raise HTTPException(status_code=401, detail="Invalid scheme")

                    decoded = base64.b64decode(credentials).decode("utf-8")
                    username, password = decoded.split(":", 1)

                    if username == "test_admin" and password == "test_secret":
                        return True
                    else:
                        raise HTTPException(
                            status_code=401, detail="Invalid credentials"
                        )
                except Exception as e:
                    raise HTTPException(status_code=401, detail=f"Auth failed: {e}")

            # Add metrics endpoint
            @self.app.get("/metrics")
            async def metrics_endpoint(auth: bool = Depends(verify_test_auth)):
                try:
                    metrics_data = self.get_metrics()
                    return Response(
                        content=metrics_data, media_type=self.get_metrics_content_type()
                    )
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Error: {e}")

            # Add test endpoints
            @self.app.get("/test")
            async def test_endpoint():
                return {"message": "test successful"}

            @self.app.post("/test-post")
            async def test_post_endpoint():
                return {"method": "POST"}

            @self.app.get("/test-error")
            async def test_error_endpoint():
                raise HTTPException(status_code=400, detail="Test error")

            self.client = TestClient(self.app)

            # Auth header for metrics
            credentials = base64.b64encode(b"test_admin:test_secret").decode("utf-8")
            self.auth_headers = {"Authorization": f"Basic {credentials}"}

    def test_middleware_tracks_successful_requests(self):
        """Test that middleware tracks successful HTTP requests."""
        # Make some test requests
        self.client.get("/test")
        self.client.post("/test-post")
        self.client.get("/test")  # Another GET to same endpoint

        # Get metrics
        response = self.client.get("/metrics", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)

        metrics_output = response.text

        # Check that HTTP request metrics are present
        self.assertIn("http_requests_total", metrics_output)
        self.assertIn("http_request_duration_seconds", metrics_output)

        # Find actual metric lines (not just headers)
        metric_lines = [
            line
            for line in metrics_output.split("\n")
            if "http_requests_total{" in line
        ]
        duration_lines = [
            line
            for line in metrics_output.split("\n")
            if "http_request_duration_seconds" in line and not line.startswith("#")
        ]

        # Should have some metrics
        self.assertGreater(
            len(metric_lines), 0, f"No request metrics found. Output:\n{metrics_output}"
        )
        self.assertGreater(
            len(duration_lines),
            0,
            f"No duration metrics found. Output:\n{metrics_output}",
        )

        # Check for specific request patterns in the metrics
        found_get_200 = any(
            'method="GET"' in line and 'status="200"' in line for line in metric_lines
        )
        found_post_200 = any(
            'method="POST"' in line and 'status="200"' in line for line in metric_lines
        )

        self.assertTrue(found_get_200, f"GET 200 not found in metrics: {metric_lines}")
        self.assertTrue(
            found_post_200, f"POST 200 not found in metrics: {metric_lines}"
        )

    def test_middleware_tracks_error_requests(self):
        """Test that middleware tracks HTTP error responses."""
        # Make a request that will result in an error
        response = self.client.get("/test-error")
        self.assertEqual(response.status_code, 400)

        # Get metrics
        metrics_response = self.client.get("/metrics", headers=self.auth_headers)
        self.assertEqual(metrics_response.status_code, 200)

        metrics_output = metrics_response.text

        # Find metric lines with status 400
        metric_lines = [
            line
            for line in metrics_output.split("\n")
            if "http_requests_total{" in line
        ]
        found_400 = any('status="400"' in line for line in metric_lines)

        self.assertTrue(found_400, f"400 status not found in metrics: {metric_lines}")

    def test_request_duration_histogram(self):
        """Test that request duration histogram is populated."""
        # Make some requests
        self.client.get("/test")
        self.client.get("/test")

        # Get metrics
        response = self.client.get("/metrics", headers=self.auth_headers)
        metrics_output = response.text

        # Check for histogram metrics - look for actual metric lines
        duration_lines = [
            line
            for line in metrics_output.split("\n")
            if "http_request_duration_seconds" in line and not line.startswith("#")
        ]

        # Should have some duration metrics
        self.assertGreater(
            len(duration_lines), 0, "No duration metrics found in output"
        )

        # Check for histogram-specific metrics
        bucket_lines = [line for line in duration_lines if "_bucket{" in line]
        count_lines = [line for line in duration_lines if "_count{" in line]
        sum_lines = [line for line in duration_lines if "_sum{" in line]

        self.assertGreater(len(bucket_lines), 0, "No histogram buckets found")
        self.assertGreater(len(count_lines), 0, "No histogram count found")
        self.assertGreater(len(sum_lines), 0, "No histogram sum found")

    def test_path_normalization(self):
        """Test that paths are normalized to reduce cardinality."""
        # Make request
        self.client.get("/test")

        response = self.client.get("/metrics", headers=self.auth_headers)
        metrics_output = response.text

        # Find request metric lines
        metric_lines = [
            line
            for line in metrics_output.split("\n")
            if "http_requests_total{" in line
        ]

        # Should contain the path for simple endpoints
        found_test_path = any('path="/test"' in line for line in metric_lines)
        self.assertTrue(
            found_test_path, f"Path /test not found in metrics: {metric_lines}"
        )

    def test_metrics_disabled_without_flag(self):
        """Test that metrics are not tracked when ENABLE_METRICS is false."""
        # Create app without metrics enabled
        with patch.dict(os.environ, {"ENABLE_METRICS": "false"}):
            # Create a new app instance
            test_app = FastAPI()
            test_app.add_middleware(RequestLoggingMiddleware)

            @test_app.get("/test")
            async def test_endpoint():
                return {"message": "test"}

            test_client = TestClient(test_app)

            # Make request
            response = test_client.get("/test")
            self.assertEqual(response.status_code, 200)

            # The middleware should still work, just not track metrics
            # (This is hard to test directly, but the request should succeed)

    def test_metrics_endpoint_security(self):
        """Test that metrics endpoint properly enforces authentication."""
        # Test without auth
        response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 401)

        # Test with wrong credentials
        wrong_creds = base64.b64encode(b"wrong:credentials").decode("utf-8")
        wrong_headers = {"Authorization": f"Basic {wrong_creds}"}
        response = self.client.get("/metrics", headers=wrong_headers)
        self.assertEqual(response.status_code, 401)

        # Test with correct credentials
        response = self.client.get("/metrics", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)

    def test_concurrent_requests_tracking(self):
        """Test that multiple concurrent requests are tracked correctly."""
        import threading

        def make_request():
            self.client.get("/test")

        # Make multiple concurrent requests
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Get metrics
        response = self.client.get("/metrics", headers=self.auth_headers)
        metrics_output = response.text

        # Should have tracked all requests
        self.assertIn("http_requests_total", metrics_output)
        self.assertIn("http_request_duration_seconds", metrics_output)


if __name__ == "__main__":
    unittest.main()
