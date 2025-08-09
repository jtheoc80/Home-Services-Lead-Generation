#!/usr/bin/env python3
"""
Flask application for LeadLedgerPro backend API.
Provides health endpoint and request logging middleware.
"""
import time
import logging
from datetime import datetime
from flask import Flask, jsonify, request, g

from app.settings import settings
from app.health_api import health_api, request_logger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = settings.secret_key


@app.before_request
def before_request():
    """Set up request tracking."""
    g.request_id = request_logger.generate_request_id()
    g.start_time = time.time()
    
    # Extract account ID from headers if available
    g.account_id = request.headers.get('X-Account-ID')
    
    # Log request start
    request_logger.log_request(
        request_id=g.request_id,
        method=request.method,
        path=request.path,
        account_id=g.account_id
    )


@app.after_request
def after_request(response):
    """Log completed request."""
    if hasattr(g, 'request_id') and hasattr(g, 'start_time'):
        response_time_ms = (time.time() - g.start_time) * 1000
        
        request_logger.log_request(
            request_id=g.request_id,
            method=request.method,
            path=request.path,
            account_id=getattr(g, 'account_id', None),
            status_code=response.status_code,
            response_time_ms=response_time_ms
        )
        
        # Add request ID to response headers
        response.headers['X-Request-ID'] = g.request_id
    
    return response


@app.route('/health')
def health_check():
    """
    Health check endpoint.
    
    Returns:
        JSON response with service health status
    """
    status = health_api.handle_health_check()
    
    # Return 503 if not healthy
    status_code = 200 if status.get('ok', False) else 503
    
    return jsonify(status), status_code


@app.route('/health/ready')
def readiness_check():
    """
    Readiness check endpoint for Kubernetes/container orchestration.
    
    Returns:
        JSON response indicating if service is ready to accept traffic
    """
    try:
        # Check if core dependencies are available
        from app.settings import settings as app_settings
        
        return jsonify({
            "ready": True,
        
        
        return jsonify({
            "ready": True,
            "env": settings.app_env,
            "timestamp": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return jsonify({
            "ready": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 503


@app.route('/health/live')
def liveness_check():
    """
    Liveness check endpoint for Kubernetes/container orchestration.
    
    Returns:
        JSON response indicating if service is alive
    """
    return jsonify({
        "alive": True,
        "timestamp": datetime.utcnow().isoformat()
    }), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "error": "Not Found",
        "message": "The requested resource was not found.",
        "timestamp": datetime.utcnow().isoformat()
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        "error": "Internal Server Error",
        "message": "An unexpected error occurred.",
        "timestamp": datetime.utcnow().isoformat()
    }), 500


if __name__ == '__main__':
    logger.info(f"Starting LeadLedgerPro backend in {settings.app_env} mode")
    logger.info(f"Debug mode: {settings.debug}")
    
    app.run(
        host=settings.api_host,
        port=settings.api_port,
        debug=settings.debug
    )