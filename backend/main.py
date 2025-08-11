
#!/usr/bin/env python3
"""
FastAPI application entry point for Home Services Lead Generation backend.

This module creates and configures the FastAPI application with all necessary
endpoints for subscription management and lead generation services.
"""

import logging
import os
import asyncio
import secrets
import base64
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request, Depends, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from dotenv import load_dotenv

# Import existing subscription API
from app.subscription_api import get_subscription_api
from app.auth import auth_user, AuthUser

from app.middleware import RequestLoggingMiddleware, setup_json_logging

from app.supabase_client import get_supabase_client

# Import metrics if available
try:
    from app.metrics import get_metrics, get_metrics_content_type
    from app.settings import settings
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False


# Import test Supabase router
from test_supabase import router as test_supabase_router

# Load environment variables
load_dotenv()

# Configure JSON logging
setup_json_logging()
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="LeadLedgerPro API",
    description="Home Services Lead Generation API with Supabase Authentication",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS origins from environment variable
# Default to localhost for development, but allow override for production
allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],  # Frontend origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Include test Supabase router
app.include_router(test_supabase_router, tags=["test", "supabase"])


# Pydantic models for request/response validation
class CancellationRequest(BaseModel):
    user_id: str
    reason_category: Optional[str] = None
    reason_notes: Optional[str] = None
    processed_by: Optional[str] = None

class ReactivationRequest(BaseModel):
    user_id: str


def verify_metrics_auth(authorization: str = Header(None)) -> bool:
    """
    Verify basic authentication for metrics endpoint.
    
    Args:
        authorization: Authorization header containing basic auth credentials
        
    Returns:
        True if authentication successful
        
    Raises:
        HTTPException: If authentication fails
    """
    if not METRICS_AVAILABLE or not getattr(settings, 'enable_metrics', False):
        raise HTTPException(status_code=404, detail="Metrics not available")
    
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Basic"}
        )
    
    try:
        # Parse basic auth header
        scheme, credentials = authorization.split()
        if scheme.lower() != 'basic':
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
        
        # Decode credentials
        decoded = base64.b64decode(credentials).decode('utf-8')
        username, password = decoded.split(':', 1)
        
        # Verify credentials using constant-time comparison
        expected_username = getattr(settings, 'metrics_username', 'admin')
        expected_password = getattr(settings, 'metrics_password', 'changeme')
        
        if not (secrets.compare_digest(username, expected_username) and 
                secrets.compare_digest(password, expected_password)):
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Basic"}
            )
        
        return True
        
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication failed")

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "LeadLedgerPro API is running",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "healthy"
    }

@app.get("/api/me")
async def get_current_user(user: AuthUser = Depends(auth_user)):
    """
    Get current authenticated user information.
    
    This endpoint returns the account_id and email of the authenticated user
    based on the JWT token provided in the Authorization header.
    
    Args:
        user: The authenticated user (injected by auth dependency)
        
    Returns:
        Dict containing account_id and email of the authenticated user
    """
    return {
        "account_id": user.account_id,
        "email": user.email
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "leadledderpro-api"}

@app.get("/healthz")
async def healthz():
    """
    Health check endpoint with database connectivity check.
    
    Returns:
        Dict containing status, version, and database connectivity status
    """
    # Get version from app metadata
    version = app.version
    
    # Check database connectivity with 300ms timeout
    db_status = "down"
    try:
        # Create a timeout task for DB check
        async def check_db():
            try:
                supabase = get_supabase_client()
                # Simple query to test connectivity - try to query any table with minimal data
                # This is a lightweight operation that tests database connection
                # Query a valid user table to test connectivity (replace 'users' with a table that exists in your schema)
                result = supabase.table('users').select('id').limit(1).execute()
                return result is not None
            except Exception:
                return False
        
        # Wait for DB check with 300ms timeout
        db_connected = await asyncio.wait_for(check_db(), timeout=0.3)
        if db_connected:
            db_status = "connected"
    except asyncio.TimeoutError:
        logger.warning("Database health check timed out after 300ms")
        db_status = "down"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "down"
    
    return {
        "status": "ok",
        "version": version,
        "db": db_status
    }

@app.get("/metrics")
async def metrics_endpoint(auth: bool = Depends(verify_metrics_auth)):
    """
    Prometheus metrics endpoint with basic authentication.
    
    This endpoint exposes Prometheus-style metrics for monitoring.
    Access is protected by basic authentication and can be disabled
    in production unless ENABLE_METRICS=true is set.
    
    Returns:
        Prometheus formatted metrics
    """
    try:
        metrics_data = get_metrics()
        return Response(
            content=metrics_data,
            media_type=get_metrics_content_type()
        )
    except Exception as e:
        logger.error(f"Error generating metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating metrics")

# Subscription management endpoints
@app.post("/api/subscription/cancel")
async def cancel_subscription(request: CancellationRequest):
    """Cancel a user's subscription."""
    try:
        subscription_api = get_subscription_api()
        result = subscription_api.cancel_subscription(request.dict())
        
        if result['success']:
            return JSONResponse(
                status_code=result['status_code'],
                content=result
            )
        else:
            raise HTTPException(
                status_code=result['status_code'],
                detail=result['error']
            )
    except Exception as e:
        logger.error(f"Error cancelling subscription: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/subscription/reactivate")
async def reactivate_subscription(request: ReactivationRequest):
    """Reactivate a user's subscription."""
    try:
        subscription_api = get_subscription_api()
        result = subscription_api.reactivate_subscription(request.dict())
        
        if result['success']:
            return JSONResponse(
                status_code=result['status_code'],
                content=result
            )
        else:
            raise HTTPException(
                status_code=result['status_code'],
                detail=result['error']
            )
    except Exception as e:
        logger.error(f"Error reactivating subscription: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/subscription/status/{user_id}")
async def get_subscription_status(user_id: str):
    """Get subscription status for a user."""
    try:
        subscription_api = get_subscription_api()
        result = subscription_api.get_subscription_status(user_id)
        
        if result['success']:
            return JSONResponse(
                status_code=result['status_code'],
                content=result
            )
        else:
            raise HTTPException(
                status_code=result['status_code'],
                detail=result['error']
            )
    except Exception as e:
        logger.error(f"Error getting subscription status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/admin/cancellations")
async def get_cancellation_records(request: Request, admin_user_id: str = Query(...)):
    """Get cancellation records for admin review."""
    try:
        subscription_api = get_subscription_api()
        result = subscription_api.get_cancellation_records(admin_user_id)
        
        if result['success']:
            return JSONResponse(
                status_code=result['status_code'],
                content=result
            )
        else:
            raise HTTPException(
                status_code=result['status_code'],
                detail=result['error']
            )
    except Exception as e:
        logger.error(f"Error getting cancellation records: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable with default fallback
    port = int(os.getenv("PORT", 8000))
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=False
    )

