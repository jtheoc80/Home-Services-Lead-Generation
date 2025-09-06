#!/usr/bin/env python3
"""
Simple test to verify metrics middleware functionality works as expected.
"""

import unittest
import os
import sys
import base64
from unittest.mock import patch

# Add the backend app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))


class TestMetricsMiddleware(unittest.TestCase):
    """Test metrics middleware with proper environment setup."""

    @patch.dict(os.environ, {"ENABLE_METRICS": "true"})
    def test_middleware_integration_working(self):
        """Test that middleware properly integrates with metrics when enabled."""
        # Import after setting environment
        from fastapi import FastAPI, Header, HTTPException, Response, Depends
        from fastapi.testclient import TestClient
        from middleware import RequestLoggingMiddleware
        from metrics import get_metrics, get_metrics_content_type

        # Create app with middleware
        app = FastAPI()
        app.add_middleware(RequestLoggingMiddleware)

        # Simple auth function
        def verify_auth(authorization: str = Header(None)) -> bool:
            if not authorization:
                raise HTTPException(status_code=401, detail="Auth required")

            scheme, credentials = authorization.split()
            decoded = base64.b64decode(credentials).decode("utf-8")
            username, password = decoded.split(":", 1)

            if username == "admin" and password == "secret":
                return True
            raise HTTPException(status_code=401, detail="Invalid")

        # Add endpoints
        @app.get("/metrics")
        async def metrics(auth: bool = Depends(verify_auth)):
            return Response(
                content=get_metrics(), media_type=get_metrics_content_type()
            )

        @app.get("/test")
        async def test():
            return {"test": "ok"}

        @app.get("/error")
        async def error():
            raise HTTPException(status_code=400, detail="Test error")

        client = TestClient(app)

        # Make test requests
        client.get("/test")
        client.get("/error")
        client.get("/test")  # Another successful request

        # Get metrics
        creds = base64.b64encode(b"admin:secret").decode("utf-8")
        headers = {"Authorization": f"Basic {creds}"}
        response = client.get("/metrics", headers=headers)

        self.assertEqual(response.status_code, 200)
        metrics_output = response.text

        # Verify metrics contain expected data
        self.assertIn("http_requests_total", metrics_output)
        self.assertIn("http_request_duration_seconds", metrics_output)

        # Find metric lines
        lines = metrics_output.split("\n")
        request_metrics = [line for line in lines if "http_requests_total{" in line]
        duration_metrics = [
            line
            for line in lines
            if "http_request_duration_seconds" in line and not line.startswith("#")
        ]

        # Should have some metrics
        self.assertGreater(len(request_metrics), 0, "No request metrics found")
        self.assertGreater(len(duration_metrics), 0, "No duration metrics found")

        # Check for specific status codes
        found_200 = any('status="200"' in line for line in request_metrics)
        found_400 = any('status="400"' in line for line in request_metrics)

        self.assertTrue(found_200, "200 status not tracked")
        self.assertTrue(found_400, "400 status not tracked")

        print("✓ Middleware integration test passed")
        print(f"  Found {len(request_metrics)} request metrics")
        print(f"  Found {len(duration_metrics)} duration metrics")

    @patch.dict(os.environ, {"ENABLE_METRICS": "false"})
    def test_middleware_disabled_when_metrics_off(self):
        """Test that middleware works but doesn't track metrics when disabled."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from middleware import RequestLoggingMiddleware

        app = FastAPI()
        app.add_middleware(RequestLoggingMiddleware)

        @app.get("/test")
        async def test():
            return {"test": "ok"}

        client = TestClient(app)

        # Make request - should work even if metrics disabled
        response = client.get("/test")
        self.assertEqual(response.status_code, 200)

        # Should have request ID header
        self.assertIn("x-request-id", response.headers)

        print("✓ Middleware works correctly when metrics disabled")


if __name__ == "__main__":
    unittest.main()
