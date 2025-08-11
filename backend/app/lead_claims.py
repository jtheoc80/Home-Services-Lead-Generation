"""
Lead claiming functionality with credit consumption.

This module extends the leads API to support claiming leads 
using credits from the billing system.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from fastapi import HTTPException, Depends
from pydantic import BaseModel

from .auth import AuthUser, auth_user
from .billing_api import use_credits, get_credit_balance
from .supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

class ClaimLeadRequest(BaseModel):
    lead_id: int
    notes: Optional[str] = None

class ClaimLeadResponse(BaseModel):
    lead_id: int
    claimed_by: str
    claimed_at: str
    credits_remaining: int
    success: bool

async def claim_lead(
    request: ClaimLeadRequest,
    user: AuthUser = Depends(auth_user)
) -> ClaimLeadResponse:
    """
    Claim a lead using credits.
    
    This function:
    1. Checks if user has sufficient credits
    2. Attempts to consume 1 credit
    3. Records the lead claim
    4. Returns updated credit balance
    
    Returns 402 Payment Required if insufficient credits.
    """
    try:
        client = get_supabase_client()
        
        # Check if lead exists and is available
        lead_result = client.table("leads").select("id, jurisdiction, permit_id, address").eq("id", request.lead_id).execute()
        
        if not lead_result.data:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        lead = lead_result.data[0]
        
        # Check if lead is already claimed
        existing_claim = client.table("lead_claims").select("*").eq("lead_id", request.lead_id).execute()
        
        if existing_claim.data:
            raise HTTPException(status_code=409, detail="Lead already claimed")
        
        # Attempt to use 1 credit
        credit_consumed = await use_credits(user.account_id, 1)
        
        if not credit_consumed:
            # Get current balance for error message
            current_balance = await get_credit_balance(user.account_id)
            raise HTTPException(
                status_code=402, 
                detail={
                    "message": "Insufficient credits to claim lead",
                    "current_balance": current_balance,
                    "required_credits": 1,
                    "upgrade_url": "/billing"
                }
            )
        
        # Record the lead claim
        claim_time = datetime.now(timezone.utc).isoformat()
        
        client.table("lead_claims").insert({
            "lead_id": request.lead_id,
            "user_id": user.account_id,
            "claimed_at": claim_time,
            "notes": request.notes
        }).execute()
        
        # Get updated credit balance
        remaining_credits = await get_credit_balance(user.account_id)
        
        logger.info(f"User {user.account_id} claimed lead {request.lead_id}, {remaining_credits} credits remaining")
        
        return ClaimLeadResponse(
            lead_id=request.lead_id,
            claimed_by=user.account_id,
            claimed_at=claim_time,
            credits_remaining=remaining_credits,
            success=True
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 402, 404, 409)
        raise
    except Exception as e:
        logger.error(f"Failed to claim lead {request.lead_id} for user {user.account_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to claim lead")

async def get_user_claims(user: AuthUser = Depends(auth_user)) -> Dict[str, Any]:
    """Get all leads claimed by the authenticated user."""
    try:
        client = get_supabase_client()
        
        # Get user's claims with lead details
        result = client.table("lead_claims").select("""
            *,
            leads (
                id,
                jurisdiction,
                permit_id,
                address,
                description,
                work_class,
                category,
                status,
                issue_date,
                applicant,
                owner,
                value,
                lead_score
            )
        """).eq("user_id", user.account_id).order("claimed_at", desc=True).execute()
        
        return {
            "claims": result.data,
            "total_claims": len(result.data),
            "credits_remaining": await get_credit_balance(user.account_id)
        }
        
    except Exception as e:
        logger.error(f"Failed to get claims for user {user.account_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve claims")