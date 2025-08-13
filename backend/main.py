
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
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, Depends, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from dotenv import load_dotenv

# Import scoring module
from scoring.v0 import score_v0

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

# Import ingest logging
from app.ingest_logger import get_trace_logs


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
try:
    from app.supa_env_check import router as supa_env_check_router
    SUPA_ENV_CHECK_AVAILABLE = True
except ImportError:
    supa_env_check_router = None
    SUPA_ENV_CHECK_AVAILABLE = False

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

# Include demand index API router
try:
    from app.demand_index_api import router as demand_index_router
    app.include_router(demand_index_router, tags=["forecast", "demand-index"])
    DEMAND_INDEX_AVAILABLE = True
except ImportError:
    demand_index_router = None
    DEMAND_INDEX_AVAILABLE = False


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

# Lead scoring models
class LeadScoreInput(BaseModel):
    lead_id: Optional[str] = None
    created_at: Optional[str] = None  
    trade_tags: Optional[List[str]] = None
    value: Optional[float] = None
    year_built: Optional[int] = None
    owner_kind: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    jurisdiction: Optional[str] = None

class LeadScoreRequest(BaseModel):
    lead: LeadScoreInput
    version: Optional[str] = "v0"

class LeadScoreResponse(BaseModel):
    lead_id: Optional[str]
    version: str
    score: int
    reasons: List[str]
    scored_at: str


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
    Health check endpoint with comprehensive monitoring information.
    
    Returns:
        Dict containing status, version, database, Redis, ingestion status,
        and sources connectivity
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
                # Test with meta.sources table (should always exist after migration)
                result = supabase.table('meta.sources').select('id').limit(1).execute()
                return result is not None
            except Exception:
                return False
        
        # Wait for DB check with 300ms timeout
        db_connected = await asyncio.wait_for(check_db(), timeout=0.3)
        if db_connected:
            db_status = "up"
    except asyncio.TimeoutError:
        logger.warning("Database health check timed out after 300ms")
        db_status = "down"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "down"
    
    # Check ingestion status
    ingest_last_run = None
    ingest_ok = True
    try:
        supabase = get_supabase_client()
        # Get the most recent ingestion run
        result = supabase.table('meta.ingest_state').select('last_run, last_status').order('last_run', desc=True).limit(1).execute()
        
        if result.data:
            ingest_last_run = result.data[0]['last_run']
            # Check if last run was successful and within last 25 hours (daily + buffer)
            from datetime import datetime, timezone, timedelta
            last_run = datetime.fromisoformat(ingest_last_run.replace('Z', '+00:00'))
            age_hours = (datetime.now(timezone.utc) - last_run).total_seconds() / 3600
            
            if age_hours > 25:  # Allow 1 hour buffer on daily schedule
                ingest_ok = False
            elif result.data[0]['last_status'] != 'success':
                ingest_ok = False
        else:
            ingest_ok = False  # No ingestion runs found
    except Exception as e:
        logger.error(f"Ingestion status check failed: {str(e)}")
        ingest_ok = False
    
    # Check sources status
    sources_ok = True
    try:
        # Load sources config and check if all active sources are reachable
        import yaml
        with open('config/sources_tx.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Quick connectivity test for a sample of sources
        # In production, this might be cached or run periodically
        active_sources = [s for s in config.get('sources', []) if s.get('kind') != 'tpia']
        if len(active_sources) == 0:
            sources_ok = False
    except Exception as e:
        logger.error(f"Sources status check failed: {str(e)}")
        sources_ok = False
    
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
        "ingest_last_run": ingest_last_run,
        "ingest_ok": ingest_ok,
        "sources_ok": sources_ok,
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


# ===== TX PERMITS DEMO API ROUTES =====

class PermitRecord(BaseModel):
    """Permit record model for API responses."""
    permit_id: str
    city: str
    permit_type: Optional[str]
    issued_at: Optional[str]
    valuation: Optional[float]
    address_full: Optional[str]
    contractor_name: Optional[str]
    status: Optional[str]

class LeadScoreRecord(BaseModel):
    """Lead score record model for API responses."""
    permit_id: str
    city: str
    issued_at: Optional[str]
    score: int
    reasons: List[str]

@app.get("/api/demo/permits")
async def get_demo_permits(city: Optional[str] = Query(None, description="Filter by city")):
    """
    Get latest 50 permits from gold.permits for demo purposes.
    
    This endpoint returns recent permits for the TX permits demo page,
    optionally filtered by city (Dallas, Austin, Arlington).
    
    Args:
        city: Optional city filter
        
    Returns:
        List of recent permit records
    """
    try:
        supabase = get_supabase_client()
        
        # Build query
        query = supabase.table("gold.permits").select(
            "permit_id, city, permit_type, issued_at, valuation, "
            "address_full, contractor_name, status"
        ).order("issued_at", desc=True).limit(50)
        
        # Apply city filter if provided
        if city:
            query = query.eq("city", city)
        
        # Execute query
        response = query.execute()
        
        if response.data is None:
            logger.warning("No permits data returned from database")
            return []
        
        # Convert to response format
        permits = []
        for record in response.data:
            permits.append(PermitRecord(
                permit_id=record.get("permit_id", ""),
                city=record.get("city", ""),
                permit_type=record.get("permit_type"),
                issued_at=record.get("issued_at"),
                valuation=record.get("valuation"),
                address_full=record.get("address_full"),
                contractor_name=record.get("contractor_name"),
                status=record.get("status")
            ))
        
        logger.info(f"Returned {len(permits)} permits for demo (city filter: {city or 'none'})")
        return permits
        
    except Exception as e:
        logger.error(f"Error fetching demo permits: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch permits data"
        )

@app.get("/api/leads/scores")
async def get_lead_scores(
    city: Optional[str] = Query(None, description="Filter by city"),
    limit: int = Query(50, ge=1, le=100, description="Number of results (1-100)")
):
    """
    Get last 50 scored permits with scores and reasons.
    
    This endpoint returns recent permits along with their lead scores
    from the gold.lead_scores table, joined with permit data.
    
    Args:
        city: Optional city filter
        limit: Number of results to return (default 50, max 100)
        
    Returns:
        List of permits with their lead scores
    """
    try:
        supabase = get_supabase_client()
        
        # Query to join permits with lead scores
        # Note: Supabase doesn't support complex joins easily, so we'll do it in two queries
        
        # First, get recent lead scores
        scores_query = supabase.table("gold.lead_scores").select(
            "lead_id, score, reasons, created_at"
        ).eq("version", "v0").order("created_at", desc=True).limit(limit)
        
        scores_response = scores_query.execute()
        
        if not scores_response.data:
            logger.info("No lead scores found")
            return []
        
        # Extract lead IDs to get corresponding permits
        # lead_id is SHA1 hash of source_id||permit_id, so we need to match differently
        # For now, let's get recent permits and match them up
        
        permits_query = supabase.table("gold.permits").select(
            "source_id, permit_id, city, issued_at, address_full"
        ).order("updated_at", desc=True).limit(limit * 2)  # Get more to increase match chances
        
        if city:
            permits_query = permits_query.eq("city", city)
        
        permits_response = permits_query.execute()
        
        if not permits_response.data:
            logger.info("No permits found")
            return []
        
        # Build a map of permit records for matching
        permit_map = {}
        for permit in permits_response.data:
            # Compute the same lead_id hash used in publishing
            import hashlib
            lead_id = hashlib.sha1(f"{permit['source_id']}||{permit['permit_id']}".encode()).hexdigest()
            permit_map[lead_id] = permit
        
        # Match scores with permits
        results = []
        for score_record in scores_response.data:
            lead_id = score_record["lead_id"]
            
            if lead_id in permit_map:
                permit = permit_map[lead_id]
                
                # Apply city filter if specified
                if city and permit.get("city") != city:
                    continue
                
                results.append(LeadScoreRecord(
                    permit_id=permit["permit_id"],
                    city=permit.get("city", ""),
                    issued_at=permit.get("issued_at"),
                    score=score_record["score"],
                    reasons=score_record["reasons"]
                ))
        
        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        
        # Limit results
        results = results[:limit]
        
        logger.info(f"Returned {len(results)} scored permits (city filter: {city or 'none'})")
        return results
        
    except Exception as e:
        logger.error(f"Error fetching lead scores: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch lead scores"
        )


# ===== LEAD SCORING API ROUTES =====

@app.post("/v1/lead-score", response_model=LeadScoreResponse)
async def score_lead_v1(request: LeadScoreRequest):
    """
    Score a lead using the specified scoring algorithm version.
    
    This endpoint accepts a normalized lead payload and returns a score (0-100)
    with detailed reasons. Supports versioned scoring algorithms for A/B testing
    and algorithm evolution.
    
    Args:
        request: Lead scoring request containing lead data and optional version
        
    Returns:
        Lead score response with score, reasons, and metadata
        
    Raises:
        HTTPException: For invalid input data or scoring errors
    """
    try:
        # Validate scoring version
        if request.version not in ["v0"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported scoring version: {request.version}"
            )
        
        # Convert Pydantic model to dict for scoring function
        lead_data = request.lead.dict(exclude_none=True)
        
        # Generate lead_id if not provided
        if not lead_data.get('lead_id'):
            lead_data['lead_id'] = str(uuid.uuid4())
        
        # Score the lead using v0 algorithm
        if request.version == "v0":
            result = score_v0(lead_data)
        else:
            raise HTTPException(
                status_code=500,
                detail="Scoring algorithm not implemented"
            )
        
        # Persist score to database
        try:
            await persist_lead_score(
                lead_id=lead_data['lead_id'],
                version=request.version,
                score=result['score'],
                reasons=result['reasons']
            )
        except Exception as e:
            logger.warning(f"Failed to persist lead score: {str(e)}")
            # Continue processing even if persistence fails
        
        # Build response
        response = LeadScoreResponse(
            lead_id=lead_data['lead_id'],
            version=request.version,
            score=result['score'],
            reasons=result['reasons'],
            scored_at=datetime.now().isoformat()
        )
        
        logger.info(f"Lead scored: {lead_data['lead_id']} -> {result['score']}/100")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scoring lead: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during lead scoring"
        )


async def persist_lead_score(lead_id: str, version: str, score: int, reasons: List[str]):
    """
    Persist lead score to gold.lead_scores table.
    
    Args:
        lead_id: UUID string for the lead
        version: Scoring algorithm version (e.g., 'v0')
        score: Integer score 0-100
        reasons: List of scoring reason strings
    """
    try:
        supabase = get_supabase_client()
        
        # Insert into gold.lead_scores table
        result = supabase.table('gold.lead_scores').insert({
            'lead_id': lead_id,
            'version': version,
            'score': score,
            'reasons': reasons,  # This will be stored as JSONB
            'created_at': datetime.now().isoformat()
        }).execute()
        
        if not result.data:
            raise Exception("No data returned from insert")
            
        logger.info(f"Persisted score for lead {lead_id}: {score}/100 (version {version})")
        
    except Exception as e:
        logger.error(f"Failed to persist lead score: {str(e)}")
        raise


# ===== DEBUG TRACE API ROUTE =====

@app.get("/api/leads/trace/{trace_id}")
async def get_trace_debug(
    trace_id: str,
    request: Request,
    x_debug_key: str = Header(None, alias="X-Debug-Key")
):
    """
    Debug endpoint to retrieve trace information for a specific trace_id.
    
    Protected with X-Debug-Key header authentication.
    Returns all ingest_logs and related processing information for debugging.
    
    Args:
        trace_id: UUID trace identifier to look up
        x_debug_key: Debug API key provided in X-Debug-Key header
        
    Returns:
        Dict containing ingest_logs, related leads, and processing summary
    """
    start_time = time.time()
    path = request.url.path
    
    # Validate debug API key
    debug_api_key = os.getenv("DEBUG_API_KEY")
    if not debug_api_key:
        logger.error({
            "trace_id": trace_id, 
            "path": path,
            "error": "DEBUG_API_KEY not configured",
            "status": 503
        })
        raise HTTPException(
            status_code=503, 
            detail="Debug endpoint not configured"
        )
    
    if not x_debug_key or x_debug_key != debug_api_key:
        logger.warning({
            "trace_id": trace_id,
            "path": path,
            "provided_key": x_debug_key if x_debug_key else "none",
            "status": 401
        })
        raise HTTPException(
            status_code=401, 
            detail="Unauthorized. X-Debug-Key header required."
        )
    
    logger.info({
        "trace_id": trace_id, 
        "path": path, 
        "method": "GET"
    })
    
    try:
        # For testing purposes, create a mock response structure
        # In production, this would connect to real Supabase
        
        # Mock Supabase response for testing
        if trace_id == "test-trace-123":
            # Mock ingest logs for demo
            logs = [
                {
                    "id": 1,
                    "trace_id": trace_id,
                    "stage": "validate",
                    "ok": True,
                    "details": {"message": "Lead validation passed"},
                    "created_at": "2024-01-01T12:00:00Z"
                },
                {
                    "id": 2,
                    "trace_id": trace_id,
                    "stage": "db_insert",
                    "ok": True,
                    "details": {"lead_id": "12345"},
                    "created_at": "2024-01-01T12:00:01Z"
                }
            ]
            
            # Mock related leads
            related_leads = [
                {
                    "id": 12345,
                    "address": "123 Test St, Houston, TX",
                    "description": "Test permit for roofing",
                    "created_at": "2024-01-01T12:00:02Z"
                }
            ]
        else:
            # For other trace IDs, try to connect to Supabase
            try:
                supabase = get_supabase_client()
                
                # Get all ingest_logs for this trace_id
                logs_response = supabase.table("ingest_logs").select("*").eq("trace_id", trace_id).order("created_at", desc=False).execute()
                
                if logs_response.data is None:
                    logs = []
                else:
                    logs = logs_response.data
                
                # Try to find related leads by trace_id (if leads table has trace_id field)
                # or by looking for leads created around the same time
                related_leads = []
                
                # First try direct trace_id match (if the leads table has a trace_id field)
                try:
                    leads_response = supabase.table("leads").select("*").eq("id", trace_id).execute()
                    if leads_response.data:
                        related_leads = leads_response.data
                except Exception:
                    # If direct match fails, try time-based lookup
                    pass
                
                # If no direct match and we have logs, look for leads created around the same time
                if not related_leads and logs:
                    try:
                        first_log_time = logs[0]["created_at"]
                        # Look for leads created within 1 minute of the trace
                        
                        # Calculate time window (1 minute before and after)
                        from datetime import datetime, timedelta
                        log_dt = datetime.fromisoformat(first_log_time.replace('Z', '+00:00'))
                        start_window = (log_dt - timedelta(minutes=1)).isoformat()
                        end_window = (log_dt + timedelta(minutes=1)).isoformat()
                        
                        nearby_leads_response = supabase.table("leads").select("*").gte("created_at", start_window).lte("created_at", end_window).order("created_at", desc=True).limit(10).execute()
                        
                        if nearby_leads_response.data:
                            related_leads = nearby_leads_response.data
                    except Exception as e:
                        logger.warning({
                            "trace_id": trace_id,
                            "error": str(e)
                        })
            except Exception as e:
                # If Supabase connection fails, return empty but valid response
                logger.warning({
                    "trace_id": trace_id,
                    "error": f"Supabase connection failed: {str(e)}"
                })
                logs = []
                related_leads = []
        
        duration_ms = round((time.time() - start_time) * 1000, 2)
        
        # Build response summary
        successful_stages = [log for log in logs if log.get("ok", False)]
        failed_stages = [log for log in logs if not log.get("ok", True)]
        
        logger.info({
            "trace_id": trace_id,
            "path": path,
            "logs_count": len(logs),
            "leads_count": len(related_leads),
            "duration_ms": duration_ms,
            "status": 200
        })
        
        return {
            "trace_id": trace_id,
            "ingest_logs": logs,
            "related_leads": related_leads,
            "summary": {
                "total_logs": len(logs),
                "successful_stages": len(successful_stages),
                "failed_stages": len(failed_stages),
                "stages": [log.get("stage") for log in logs],
                "duration_ms": duration_ms
            }
        }
        
    except Exception as e:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.error({
            "trace_id": trace_id,

            "path": path,


            "error": str(e),
            "duration_ms": duration_ms,
            "status": 500
        })
        
        raise HTTPException(

            status_code=500,
            detail="Internal server error"
        )


def verify_debug_key(x_debug_key: str = Header(None)) -> bool:
    """
    Verify X-Debug-Key header for trace endpoint access.
    
    Args:
        x_debug_key: Debug key from X-Debug-Key header
        
    Returns:
        True if authentication successful
        
    Raises:
        HTTPException: If authentication fails
    """
    expected_debug_key = os.getenv("X_DEBUG_KEY")
    
    if not expected_debug_key:
        raise HTTPException(
            status_code=503, 
            detail="Debug key not configured on server"
        )
    
    if not x_debug_key:
        raise HTTPException(
            status_code=401,
            detail="X-Debug-Key header required"
        )
    
    if not secrets.compare_digest(x_debug_key, expected_debug_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid debug key"
        )
    
    return True



@app.get("/api/leads/trace/{trace_id}")
async def get_trace_logs_endpoint(
    trace_id: str,
    debug_auth: bool = Depends(verify_debug_key)
):
    """
    Retrieve all ingest logs for a specific trace ID.
    
    This endpoint is protected by X-Debug-Key header and returns all rows
    from ingest_logs table for the given trace ID.
    
    Args:
        trace_id: The trace ID to retrieve logs for
        debug_auth: Debug authentication (injected by dependency)
        
    Returns:
        List of ingest log entries for the trace ID
    """
    try:
        logs = get_trace_logs(trace_id)
        
        if logs is None:
            raise HTTPException(
                status_code=500,
                detail="Error retrieving trace logs"
            )
        
        return {
            "trace_id": trace_id,
            "logs": logs,
            "total_logs": len(logs)
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error in trace logs endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


# ===================================================================
# LEAD SCORING V0 API ENDPOINTS
# ===================================================================

class LeadScoreRequest(BaseModel):
    """Request model for lead scoring."""
    lead: Dict[str, Any]
    
class LeadScoreResponse(BaseModel):
    """Response model for lead scoring."""
    score: int
    reasons: List[str]
    version: str

@app.post("/v1/lead-score", response_model=LeadScoreResponse)
async def score_lead(request: LeadScoreRequest, user: AuthUser = Depends(auth_user)):
    """
    Score a lead using the v0 algorithm.
    
    This endpoint takes a lead payload and returns a score (0-100) with 
    detailed reasons using the frozen v0 scoring algorithm.
    """
    try:
        # Validate and score the lead
        from scoring.v0 import score_v0, validate_lead_input
        
        # Validate input
        validation_errors = validate_lead_input(request.lead)
        if validation_errors:
            raise HTTPException(
                status_code=400,
                detail=f"Lead validation failed: {'; '.join(validation_errors)}"
            )
        
        # Score the lead
        result = score_v0(request.lead)
        
        return LeadScoreResponse(
            score=result["score"],
            reasons=result["reasons"],
            version="v0"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scoring lead: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to score lead"
        )

@app.get("/v1/leads/{lead_id}/score")
async def get_lead_score(
    lead_id: str, 
    version: str = Query("v0", description="Scoring version"),
    user: AuthUser = Depends(auth_user)
):
    """
    Get the cached score for a specific lead.
    
    This endpoint retrieves the score from gold.lead_scores table
    for the specified lead and version.
    """
    try:
        # Validate lead_id as UUID
        try:
            uuid_obj = uuid.UUID(lead_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid lead_id format - must be UUID"
            )
        
        # Query the lead_scores table
        supabase = get_supabase_client()
        
        response = supabase.table("gold.lead_scores").select("*").eq(
            "lead_id", str(uuid_obj)
        ).eq("version", version).order("created_at", desc=True).limit(1).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=404,
                detail=f"No score found for lead {lead_id} version {version}"
            )
        
        score_record = response.data[0]
        
        return {
            "lead_id": lead_id,
            "version": version,
            "score": score_record["score"],
            "reasons": score_record["reasons"],
            "created_at": score_record["created_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving lead score: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve lead score"
        )


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

