#!/usr/bin/env python3
"""
Request logging middleware for FastAPI application.

This module provides middleware for JSON structured logging with request tracking,
including request_id generation and timing measurement.
"""

import json
import time
import uuid
import logging
from typing import Callable, Dict, Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record):
        # Create the basic log entry
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }
        
        # Add extra fields if present
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        
        return json.dumps(log_entry)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests in JSON format.
    
    This middleware:
    - Generates unique request IDs for each request
    - Measures request duration
    - Logs request details in JSON format
    - Adds request_id to response headers
    """

    def __init__(self, app, logger_name: str = __name__):
        super().__init__(app)
        self.logger = logging.getLogger(logger_name)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and response with logging.
        
        Args:
            request: The incoming HTTP request
            call_next: The next middleware or endpoint handler
            
        Returns:
            Response with added request_id header and timing logged
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Add request_id to request state for access in endpoints if needed
        request.state.request_id = request_id
        
        # Record start time
        start_time = time.time()
        
        # Process the request
        try:
            response = await call_next(request)
        except Exception as exc:
            # Log error and create error response
            duration_ms = round((time.time() - start_time) * 1000, 2)
            
            log_data = {
                "request_id": request_id,
                "path": str(request.url.path),
                "method": request.method,
                "status": 500,
                "duration_ms": duration_ms,
                "error": str(exc)
            }
            
            self.logger.error(json.dumps(log_data))
            
            # Return error response with request_id header
            response = JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "request_id": request_id}
            )
            response.headers["X-Request-ID"] = request_id
            return response
        
        # Calculate duration
        duration_ms = round((time.time() - start_time) * 1000, 2)
        
        # Add request_id to response headers
        response.headers["X-Request-ID"] = request_id
        
        # Prepare log data
        log_data = {
            "request_id": request_id,
            "path": str(request.url.path),
            "method": request.method,
            "status": response.status_code,
            "duration_ms": duration_ms
        }
        
        # Log the request
        self.logger.info(json.dumps(log_data))
        
        return response


def setup_json_logging(logger_name: str = None) -> None:
    """
    Configure JSON logging for the application.
    
    This sets up structured logging that outputs JSON formatted log messages
    suitable for log aggregation systems.
    
    Args:
        logger_name: Name of the logger to configure. If None, configures root logger.
    """
    # Get the logger
    if logger_name:
        logger = logging.getLogger(logger_name)
    else:
        logger = logging.getLogger()
    
    # Remove existing handlers to avoid duplication
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler with JSON formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    
    # Add handler to logger
    logger.addHandler(console_handler)
    logger.setLevel(logging.INFO)