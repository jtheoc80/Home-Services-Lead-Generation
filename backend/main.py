"""
FastAPI main application for LeadLedgerPro backend.

This module sets up the FastAPI application with authentication
and API routes including the /api/me endpoint.
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.auth import auth_user, AuthUser

# Create FastAPI application
app = FastAPI(
    title="LeadLedgerPro API",
    description="Home Services Lead Generation API with Supabase Authentication",
    version="1.0.0"
)

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {"message": "LeadLedgerPro API is running", "status": "healthy"}


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


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "leadledderpro-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)