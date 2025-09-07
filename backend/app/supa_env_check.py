"""
Supabase environment and connectivity check endpoint
"""

from fastapi import APIRouter
from typing import Dict, Any
import os
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/api/supa-env-check")
async def supa_env_check() -> Dict[str, Any]:
    """
    Check Supabase environment variables and database connectivity
    """
    result = {
        "status": "ok",
        "env_status": "ok",
        "database_status": "unknown",
        "checks": {},
    }

    # Check required environment variables
    required_env_vars = [
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_JWT_SECRET",
    ]

    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
        result["checks"][var] = "present" if os.getenv(var) else "missing"

    if missing_vars:
        result["env_status"] = "missing_vars"
        result["missing_variables"] = missing_vars
        result["status"] = "degraded"

    # Test database connectivity if env vars are present
    if not missing_vars:
        try:
            # Import here to avoid startup errors if not available
            from supabase import create_client

            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

            client = create_client(supabase_url, supabase_key)

            # Simple test query
            response = (
                client.table("leads").select("count", count="exact").limit(1).execute()
            )

            result["database_status"] = "connected"
            result["checks"]["database_query"] = "success"

        except Exception as e:
            logger.error(f"Database connectivity test failed: {e}")
            result["database_status"] = "error"
            result["checks"]["database_query"] = f"failed: {str(e)}"
            result["status"] = "degraded"

    return result
