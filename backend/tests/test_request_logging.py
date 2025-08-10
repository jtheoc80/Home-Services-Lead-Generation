#!/usr/bin/env python3
"""
Tests for the request logging middleware.

This module tests the JSON logging functionality and request ID generation.
"""

import json
import unittest
import logging
from unittest.mock import patch, MagicMock
from fastapi import FastAPI, Response
from fastapi.testclient import TestClient
from io import StringIO
import sys
import os

# Add the backend app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from middleware import RequestLoggingMiddleware, setup_json_logging


class TestRequestLoggingMiddleware(unittest.TestCase):
    """Test the request logging middleware functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a test FastAPI app
        self.app = FastAPI()
        
        # Add the middleware
        self.app.add_middleware(RequestLoggingMiddleware)
        
        # Add a simple test endpoint
        @self.app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        @self.app.get("/error")
        async def error_endpoint():
            raise Exception("Test error")
        
        # Create test client
        self.client = TestClient(self.app)
    
    def test_request_id_header_added(self):
        """Test that X-Request-ID header is added to responses."""
        response = self.client.get("/test")
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("x-request-id", response.headers)
        
        # Check that request ID is a valid UUID format
        request_id = response.headers["x-request-id"]
        self.assertTrue(len(request_id) > 20)  # UUIDs are longer than 20 chars
        self.assertIn("-", request_id)  # UUIDs contain hyphens
    
    def test_unique_request_ids(self):
        """Test that each request gets a unique request ID."""
        response1 = self.client.get("/test")
        response2 = self.client.get("/test")
        
        request_id1 = response1.headers["x-request-id"]
        request_id2 = response2.headers["x-request-id"]
        
        self.assertNotEqual(request_id1, request_id2)
    
    def test_logging_output_format(self):
        """Test that logging output is in correct JSON format."""
        # Capture logging output
        log_capture = StringIO()
        
        # Set up test logger
        test_logger = logging.getLogger("test.middleware")
        handler = logging.StreamHandler(log_capture)
        test_logger.addHandler(handler)
        test_logger.setLevel(logging.INFO)
        
        # Create app with custom logger
        app = FastAPI()
        app.add_middleware(RequestLoggingMiddleware, logger_name="test.middleware")
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        client = TestClient(app)
        
        # Make request
        response = client.get("/test")
        
        # Get log output
        log_output = log_capture.getvalue()
        
        # Should contain JSON log entry
        self.assertIn("request_id", log_output)
        self.assertIn("path", log_output)
        self.assertIn("method", log_output)
        self.assertIn("status", log_output)
        self.assertIn("duration_ms", log_output)
        
        # Extract the JSON part and validate it's valid JSON
        lines = log_output.strip().split('\n')
        found_valid_json = False
        for line in lines:
            if "request_id" in line:
                # The middleware logs JSON directly as the message
                # Look for the JSON part in the log output
                try:
                    # The JSON is the actual log message in our middleware
                    if line.strip().startswith('{"request_id"'):
                        log_data = json.loads(line.strip())
                        found_valid_json = True
                    else:
                        # Find JSON within the log line
                        start = line.find('{"request_id"')
                        if start != -1:
                            # Find the end of the JSON
                            end = start
                            brace_count = 0
                            for i, char in enumerate(line[start:]):
                                if char == '{':
                                    brace_count += 1
                                elif char == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        end = start + i + 1
                                        break
                            
                            if end > start:
                                json_part = line[start:end]
                                log_data = json.loads(json_part)
                                found_valid_json = True
                    
                    if found_valid_json:
                        # Verify required fields
                        self.assertIn("request_id", log_data)
                        self.assertIn("path", log_data)
                        self.assertIn("method", log_data)
                        self.assertIn("status", log_data)
                        self.assertIn("duration_ms", log_data)
                        
                        # Verify values
                        self.assertEqual(log_data["path"], "/test")
                        self.assertEqual(log_data["method"], "GET")
                        self.assertEqual(log_data["status"], 200)
                        self.assertIsInstance(log_data["duration_ms"], (int, float))
                        self.assertGreaterEqual(log_data["duration_ms"], 0)
                        break
                except json.JSONDecodeError:
                    continue
        
        if not found_valid_json:
            self.fail(f"Log output does not contain valid JSON: {log_output}")
    
    def test_error_handling(self):
        """Test that errors are properly logged and handled."""
        # Capture logging output
        log_capture = StringIO()
        
        # Set up test logger
        test_logger = logging.getLogger("test.error.middleware")
        handler = logging.StreamHandler(log_capture)
        test_logger.addHandler(handler)
        test_logger.setLevel(logging.ERROR)
        
        # Create app with custom logger
        app = FastAPI()
        app.add_middleware(RequestLoggingMiddleware, logger_name="test.error.middleware")
        
        @app.get("/error")
        async def error_endpoint():
            raise Exception("Test error")
        
        client = TestClient(app)
        
        # Make request to error endpoint
        response = client.get("/error")
        
        # Should get 500 status
        self.assertEqual(response.status_code, 500)
        
        # Should have request ID header
        self.assertIn("x-request-id", response.headers)
        
        # Should have error in response
        response_data = response.json()
        self.assertIn("error", response_data)
        self.assertIn("request_id", response_data)
        
        # Check error logging
        log_output = log_capture.getvalue()
        self.assertIn("error", log_output.lower())
        self.assertIn("Test error", log_output)
    
    def test_different_http_methods(self):
        """Test logging works for different HTTP methods."""
        # Add endpoints for different methods
        @self.app.post("/test-post")
        async def post_endpoint():
            return {"method": "POST"}
        
        @self.app.put("/test-put")
        async def put_endpoint():
            return {"method": "PUT"}
        
        # Test different methods
        methods_to_test = [
            ("GET", "/test"),
            ("POST", "/test-post"),
            ("PUT", "/test-put")
        ]
        
        for method, path in methods_to_test:
            with self.subTest(method=method, path=path):
                if method == "GET":
                    response = self.client.get(path)
                elif method == "POST":
                    response = self.client.post(path)
                elif method == "PUT":
                    response = self.client.put(path)
                
                # All should have request ID headers
                self.assertIn("x-request-id", response.headers)
                self.assertEqual(response.status_code, 200)


class TestJSONLoggingSetup(unittest.TestCase):
    """Test the JSON logging setup functionality."""
    
    def test_setup_json_logging(self):
        """Test that JSON logging setup works correctly."""
        # Create a test logger
        test_logger_name = "test.json.logger"
        
        # Set up JSON logging
        setup_json_logging(test_logger_name)
        
        # Get the logger
        logger = logging.getLogger(test_logger_name)
        
        # Should have handlers
        self.assertGreater(len(logger.handlers), 0)
        
        # Should be at INFO level
        self.assertEqual(logger.level, logging.INFO)
    
    def test_json_formatter_output(self):
        """Test that JSON formatter produces valid JSON."""
        # Capture output
        log_capture = StringIO()
        
        # Create a logger and manually add JSON formatter to avoid conflicts
        test_logger = logging.getLogger("test.json.formatter.manual")
        
        # Clear any existing handlers
        test_logger.handlers.clear()
        
        # Create custom JSON formatter
        from middleware import JSONFormatter
        
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(JSONFormatter())
        test_logger.addHandler(handler)
        test_logger.setLevel(logging.INFO)
        
        # Log a message
        test_logger.info("Test message")
        
        # Get output
        log_output = log_capture.getvalue().strip()
        
        # Should be valid JSON
        try:
            log_data = json.loads(log_output)
            self.assertIn("timestamp", log_data)
            self.assertIn("level", log_data)
            self.assertIn("logger", log_data)
            self.assertIn("message", log_data)
            self.assertEqual(log_data["level"], "INFO")
            self.assertEqual(log_data["message"], "Test message")
        except json.JSONDecodeError:
            self.fail(f"Log output is not valid JSON: {log_output}")


if __name__ == '__main__':
    unittest.main()