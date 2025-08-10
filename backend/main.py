
#!/usr/bin/env python3
"""
FastAPI application entry point for Home Services Lead Generation backend.

This module creates and configures the FastAPI application with all necessary
endpoints for subscription management and lead generation services.
"""

import logging
import os
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Import existing subscription API
from app.subscription_api import get_subscription_api
from app.auth import auth_user, AuthUser
from app.middleware import RequestLoggingMiddleware, setup_json_logging

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

