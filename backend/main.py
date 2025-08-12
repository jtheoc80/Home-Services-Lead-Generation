
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
import time
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request, Depends, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from dotenv import load_dotenv

# Import existing subscription API
from app.subscription_api import get_subscription_api
from app.auth import auth_user, admin_user, AuthUser

from app.middleware import RequestLoggingMiddleware, setup_json_logging

from app.supabase_client import get_supabase_client

# Import billing API
from app.billing_api import (
    create_customer, create_checkout_session_subscription, 
    create_checkout_session_credits, create_portal_session, 
    handle_webhook, get_user_credits, CheckoutSessionRequest
)

# Import lead claiming API
from app.lead_claims import claim_lead, get_user_claims, ClaimLeadRequest


# Import metrics if available
try:
    from app.metrics import get_metrics, get_metrics_content_type
    from app.settings import settings
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

# Import export control
from app.utils.export_control import get_export_controller, ExportType



# Import test Supabase router
from test_supabase import router as test_supabase_router
from app.supa_env_check import router as supa_env_check_router

# Import Redis client
from app.redis_client import ping_ms

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

# Add rate limiting middleware (avoid /healthz)
from app.middleware_rate_limit import RateLimitMiddleware

@app.middleware("http")
async def rate_limit_selected_routes(request, call_next):
    """Apply rate limiting to API routes but skip health checks"""
    if request.url.path.startswith("/api/") and not request.url.path == "/healthz":
        middleware = RateLimitMiddleware(app, limit=60, window=60)
        return await middleware.dispatch(request, call_next)
    return await call_next(request)

# Include test Supabase router
app.include_router(test_supabase_router, tags=["test", "supabase"])

# Include Supabase environment check router
app.include_router(supa_env_check_router, tags=["health", "supabase"])


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
        raise HTTPException(status_code=503, detail="Metrics not available")
    
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

class ExportDataRequest(BaseModel):
    export_type: str  # leads, permits, scored_leads, analytics, feedback
    format: Optional[str] = "csv"  # csv, json, xlsx
    filters: Optional[Dict[str, Any]] = None
    admin_override: Optional[bool] = False


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
    Health check endpoint with database and Redis connectivity check.
    
    Returns:
        Dict containing status, version, database and Redis connectivity status
    """
    # Get version from app metadata
    version = app.version
    
    # Check database connectivity with 300ms timeout
    db_status = "down"
    db_rtt = None
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
    
    # Check Redis connectivity
    redis_status, redis_rtt = await ping_ms()
    
    # Check Stripe connectivity
    stripe_status = "missing"
    stripe_rtt = None
    try:
        from app.stripe_client import get_stripe_client
        stripe_client = get_stripe_client()
        if stripe_client.is_configured:
            # Test with a safe 200ms API call and measure RTT
            start_time = time.time()
            if await asyncio.wait_for(
                asyncio.create_task(asyncio.to_thread(stripe_client.test_connection)), 
                timeout=0.2
            ):
                stripe_rtt = round((time.time() - start_time) * 1000, 2)
                stripe_status = "configured"
            else:
                stripe_status = "error"
        else:
            stripe_status = "missing"
    except asyncio.TimeoutError:
        stripe_status = "timeout"
    except Exception:
        stripe_status = "error"
    
    return {
        "status": "ok",
        "db": db_status,
        "db_rtt_ms": db_rtt,
        "redis": redis_status,
        "redis_rtt_ms": redis_rtt,
        "stripe": stripe_status,
        "stripe_rtt_ms": stripe_rtt,
        "ts": int(time.time())
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

@app.post("/api/export/data")
async def export_data(request: ExportDataRequest, user: AuthUser = Depends(auth_user)):
    """
    Export data with ALLOW_EXPORTS enforcement and admin override capability.
    
    This endpoint enforces ALLOW_EXPORTS=false server-side and only allows 
    exports when:
    1. ALLOW_EXPORTS=true in environment, OR
    2. User has admin role and explicitly requests admin_override=true
    
    All export attempts are logged for audit purposes.
    """
    try:
        export_controller = get_export_controller()
        
        # Validate export type
        try:
            export_type = ExportType(request.export_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid export_type: {request.export_type}"
            )
        
        # Check if this is an admin override request first
        is_admin_override = False
        if request.admin_override:
            # Verify user has admin privileges for override
            try:
                admin_user(user)  # This will raise HTTPException if not admin
                is_admin_override = True
                logger.info(f"Admin override requested by {user.email} for {export_type.value}")
            except HTTPException:
                # User is not admin but requested override
                logger.warning(f"Non-admin user {user.email} attempted admin override for export")
                raise HTTPException(
                    status_code=403,
                    detail="Admin privileges required for export override"
                )
        
        # Check if export is allowed (skip normal check if admin override)
        if is_admin_override:
            allowed = True
            reason = f"Admin override by {user.email}"
            logger.info(f"Export allowed via admin override: {user.email} exporting {export_type.value}")
        else:
            allowed, reason = export_controller.is_export_allowed(
                export_type, 
                user.email,
                request.filters
            )
        
        if not allowed:
            # Log blocked export attempt for audit
            logger.warning(f"Export blocked for {user.email}: {reason}")
            raise HTTPException(
                status_code=403,
                detail=f"Export not allowed: {reason}"
            )
        
        # Create and process export request
        export_request = export_controller.create_export_request(
            export_type=export_type,
            requester=user.email,
            parameters={
                "format": request.format,
                "filters": request.filters,
                "admin_override": request.admin_override,
                "user_id": user.account_id,
                "allowed_via_override": is_admin_override
            }
        )
        
        # Process the export (skip is_export_allowed check if admin override)
        if is_admin_override:
            # For admin override, manually create a successful result
            result = export_controller._create_admin_override_result(export_request)
        else:
            # Normal processing
            result = export_controller.process_export_request(export_request)
        
        if not result.success:
            raise HTTPException(
                status_code=500,
                detail=f"Export failed: {result.reason}"
            )
        
        return {
            "message": "Export completed successfully",
            "export_id": result.export_id,
            "export_type": export_type.value,
            "record_count": result.record_count,
            "allowed_via": "admin_override" if is_admin_override else "normal_permissions",
            "timestamp": result.timestamp.isoformat() if result.timestamp else None
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 403, 400) as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in export endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/export/status")
async def get_export_status(user: AuthUser = Depends(auth_user)):
    """
    Get export configuration status for the current user.
    
    Returns information about export permissions and available types.
    """
    try:
        export_controller = get_export_controller()
        status_info = export_controller.get_export_status()
        
        # Add user-specific information
        is_admin = False
        try:
            admin_user(user)
            is_admin = True
        except HTTPException:
            pass
        
        return {
            **status_info,
            "user_email": user.email,
            "user_is_admin": is_admin,
            "admin_override_available": is_admin,
            "message": "Admin override available" if is_admin else "Standard export permissions apply"
        }
        
    except Exception as e:
        logger.error(f"Error getting export status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ===== BILLING API ROUTES =====

@app.post("/api/billing/create-customer")
async def api_create_customer(user: AuthUser = Depends(auth_user)):
    """Create or retrieve Stripe customer for authenticated user."""
    return await create_customer(user)

@app.post("/api/billing/checkout/subscription")
async def api_checkout_subscription(
    request: CheckoutSessionRequest,
    user: AuthUser = Depends(auth_user),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """Create checkout session for subscription."""
    return await create_checkout_session_subscription(request, user, idempotency_key)

@app.post("/api/billing/checkout/credits")
async def api_checkout_credits(
    user: AuthUser = Depends(auth_user),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """Create checkout session for credit pack purchase."""
    return await create_checkout_session_credits(user, idempotency_key)

@app.post("/api/billing/portal")
async def api_billing_portal(user: AuthUser = Depends(auth_user)):
    """Create Customer Portal session for billing management."""
    return await create_portal_session(user)

@app.get("/api/billing/credits")
async def api_get_credits(user: AuthUser = Depends(auth_user)):
    """Get current credit balance for authenticated user."""
    return await get_user_credits(user)

@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events with signature verification."""
    return await handle_webhook(request)

# ===== LEAD CLAIMING API ROUTES =====

@app.post("/api/leads/claim")
async def api_claim_lead(
    request: ClaimLeadRequest,
    user: AuthUser = Depends(auth_user)
):
    """Claim a lead using credits."""
    return await claim_lead(request, user)

@app.get("/api/leads/claims")
async def api_get_user_claims(user: AuthUser = Depends(auth_user)):
    """Get all leads claimed by the authenticated user."""
    return await get_user_claims(user)

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

