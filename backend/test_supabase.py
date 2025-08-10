#!/usr/bin/env python3
"""
Test Supabase APIRouter for health checks and lead testing.

This module provides endpoints for testing Supabase connectivity and
basic lead insertion functionality.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

from app.supabase_client import get_supabase_client
from app.ingest import insert_lead

# Configure logging
logger = logging.getLogger(__name__)

# Create the APIRouter
router = APIRouter()


class TestLead(BaseModel):
    """Model for test lead creation."""
    jurisdiction: str
    permit_id: str
    address: str = "123 Test Street"
    description: str = "Test permit description"
    value: float = 10000.0
    is_residential: bool = True
    latitude: float = 29.7604
    longitude: float = -95.3698
    trade_tags: list[str] = ["test", "demo"]


@router.get("/health/supabase")
async def health_supabase() -> Dict[str, Any]:
    """
    Health check endpoint for Supabase connectivity.
    
    Returns the connection status and current row count in the leads table.
    
    Returns:
        Dict containing:
        - ok: boolean indicating successful connection
        - rows: count of rows in the leads table
        
    Raises:
        HTTPException: If Supabase connection fails
    """
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Query the leads table to get row count
        result = supabase.table('leads').select('id', count='exact').execute()
        
        row_count = result.count if result.count is not None else 0
        
        logger.info(f"Supabase health check successful. Leads table has {row_count} rows.")
        
        return {
            "ok": True,
            "rows": row_count
        }
        
    except Exception as e:
        logger.error(f"Supabase health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Supabase connection failed: {str(e)}"
        )


@router.post("/test/lead")
async def test_lead_insertion(lead: TestLead = None) -> Dict[str, Any]:
    """
    Test endpoint for inserting a simple lead into Supabase.
    
    This endpoint creates a test lead with either provided data or default values,
    inserts it into the leads table, and returns the inserted record.
    
    Args:
        lead: Optional TestLead model with lead data. If not provided, 
              a default test lead will be created.
    
    Returns:
        Dict containing the inserted lead data as returned by Supabase
        
    Raises:
        HTTPException: If lead insertion fails
    """
    try:
        # If no lead data provided, create a default test lead
        if lead is None:
            # Generate a unique permit_id using timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            lead = TestLead(
                jurisdiction="test_jurisdiction",
                permit_id=f"TEST_PERMIT_{timestamp}",
                address="123 Test Avenue, Test City, TX 77001",
                description="Test permit for API testing purposes",
                value=25000.0,
                is_residential=True,
                latitude=29.7604,
                longitude=-95.3698,
                trade_tags=["test", "api", "demo"]
            )
        
        # Convert Pydantic model to dict for the insert_lead function
        lead_data = lead.dict()
        
        # Add some additional fields that might be expected
        lead_data.update({
            "work_class": "test_work_class",
            "category": "test_category", 
            "status": "issued",
            "applicant": "Test Applicant",
            "owner": "Test Owner",
            "scraped_at": datetime.now().isoformat(),
            "scoring_version": "test_v1.0"
        })
        
        # Insert the lead using the existing insert_lead function
        inserted_lead = insert_lead(lead_data)
        
        logger.info(f"Successfully inserted test lead: {lead_data.get('jurisdiction')}/{lead_data.get('permit_id')}")
        
        return inserted_lead
        
    except Exception as e:
        logger.error(f"Test lead insertion failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to insert test lead: {str(e)}"
        )