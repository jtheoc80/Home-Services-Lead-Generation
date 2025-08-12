"""
Authentication module for FastAPI with Supabase JWT verification.

This module provides JWT token verification using Supabase's JWT secret
and dependency injection for protecting routes.
"""

import os
import jwt
from typing import Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Security scheme for Bearer token
security = HTTPBearer()

# Get Supabase JWT secret from environment
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

if not SUPABASE_JWT_SECRET:
    raise ValueError("SUPABASE_JWT_SECRET environment variable is required")


class AuthUser:
    """Represents an authenticated user from JWT token."""
    
    def __init__(self, account_id: str, email: str, payload: Dict[str, Any]):
        self.account_id = account_id
        self.email = email
        self.payload = payload


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode a JWT token using Supabase JWT secret.
    
    Args:
        token: The JWT token to verify
        
    Returns:
        Dict containing the decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Decode the JWT token using HS256 algorithm and Supabase secret
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"  # Supabase audience
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def auth_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> AuthUser:
    """
    FastAPI dependency to extract and verify the authenticated user from JWT token.
    
    Args:
        credentials: HTTP Authorization credentials containing the Bearer token
        
    Returns:
        AuthUser: The authenticated user object
        
    Raises:
        HTTPException: If token is missing, invalid, or expired
    """
    token = credentials.credentials
    
    # Verify the JWT token
    payload = verify_jwt_token(token)
    
    # Extract user information from the token payload
    # Supabase JWT typically contains 'sub' (user ID) and 'email'
    user_id = payload.get("sub")
    email = payload.get("email")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing email",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return AuthUser(account_id=user_id, email=email, payload=payload)


# Optional: Dependency for admin users (example implementation)
def admin_user(user: AuthUser = Depends(auth_user)) -> AuthUser:
    """
    FastAPI dependency to ensure the authenticated user has admin privileges.
    
    Args:
        user: The authenticated user
        
    Returns:
        AuthUser: The authenticated admin user
        
    Raises:
        HTTPException: If user is not an admin
    """
    # Example: Check if user has admin role in the JWT token
    user_role = user.payload.get("user_metadata", {}).get("role")
    
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return user