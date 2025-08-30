"""
Demand Index API endpoints for the forecast system

Provides /v1/signals/demand-index route returning region, score, confidence
"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
import json

from app.demand_forecast import get_demand_surge_forecaster
from app.supabase_client import get_supabase_client
from app.auth import auth_user, AuthUser

logger = logging.getLogger(__name__)

# Create router for demand index endpoints
router = APIRouter(prefix="/v1/signals", tags=["forecast", "demand-index"])


class DemandIndexResponse(BaseModel):
    """Response model for demand index API"""

    region: str
    region_name: str
    score: float  # p_surge probability
    confidence: float  # model confidence
    risk_level: str  # "low", "medium", "high"
    week_start: str  # ISO date
    week_end: str  # ISO date
    forecast_date: str  # When forecast was generated
    model_version: str
    bounds: Dict[str, float]  # p80/p20 confidence intervals


class RegionDemandIndex(BaseModel):
    """Individual region demand index"""

    region_slug: str
    region_name: str
    p_surge: float
    confidence_score: float
    risk_level: str
    forecast_week_start: str
    forecast_week_end: str
    p80_bounds: Dict[str, float]
    p20_bounds: Dict[str, float]
    last_updated: str


class DemandIndexListResponse(BaseModel):
    """Response for multiple regions"""

    regions: List[RegionDemandIndex]
    total_regions: int
    forecast_date: str
    model_versions: List[str]


def _calculate_risk_level(p_surge: float) -> str:
    """Calculate risk level from surge probability"""
    if p_surge >= 0.7:
        return "high"
    elif p_surge >= 0.3:
        return "medium"
    else:
        return "low"


@router.get("/demand-index", response_model=DemandIndexListResponse)
async def get_demand_index(
    region: Optional[str] = Query(None, description="Specific region slug to query"),
    user: AuthUser = Depends(auth_user),
):
    """
    Get demand surge index for regions.

    Returns current demand surge forecasts with probabilities and confidence intervals.
    If region is specified, returns data for that region only.
    Otherwise returns data for all available regions.

    Args:
        region: Optional region slug filter
        user: Authenticated user

    Returns:
        DemandIndexListResponse with demand index data
    """
    try:
        supabase = get_supabase_client()

        # Build query
        if region:
            query = f"""
                SELECT * FROM gold.forecast_nowx 
                WHERE region_slug = '{region}'
                ORDER BY last_updated DESC
                LIMIT 1
            """
        else:
            # Get latest forecast for each region
            query = """
                SELECT DISTINCT ON (region_slug) *
                FROM gold.forecast_nowx 
                ORDER BY region_slug, last_updated DESC
            """

        # Execute query
        result = supabase.rpc("sql_query", {"query": query}).execute()

        if not result.data:
            # If no data in gold table, generate fresh forecasts
            logger.warning(
                "No forecast data found in gold.forecast_nowx, generating fresh forecasts"
            )
            await _generate_fresh_forecasts()

            # Retry query
            result = supabase.rpc("sql_query", {"query": query}).execute()

            if not result.data:
                raise HTTPException(
                    status_code=404, detail="No forecast data available"
                )

        # Transform data
        regions = []
        model_versions = set()

        for row in result.data:
            region_data = RegionDemandIndex(
                region_slug=row["region_slug"],
                region_name=row["region_name"],
                p_surge=float(row["p_surge"]),
                confidence_score=float(row["confidence_score"]),
                risk_level=_calculate_risk_level(float(row["p_surge"])),
                forecast_week_start=row["forecast_week_start"],
                forecast_week_end=row["forecast_week_end"],
                p80_bounds={
                    "lower": float(row["p80_lower"]),
                    "upper": float(row["p80_upper"]),
                },
                p20_bounds={
                    "lower": float(row.get("p20_lower", row["p80_lower"])),
                    "upper": float(row.get("p20_upper", row["p80_upper"])),
                },
                last_updated=row["last_updated"],
            )
            regions.append(region_data)
            model_versions.add(row["model_version"])

        response = DemandIndexListResponse(
            regions=regions,
            total_regions=len(regions),
            forecast_date=datetime.now().isoformat(),
            model_versions=list(model_versions),
        )

        logger.info(f"Returned demand index for {len(regions)} regions")
        return response

    except Exception as e:
        logger.error(f"Error getting demand index: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving demand index: {str(e)}"
        )


@router.get("/demand-index/{region_slug}", response_model=DemandIndexResponse)
async def get_region_demand_index(
    region_slug: str, user: AuthUser = Depends(auth_user)
):
    """
    Get demand index for a specific region.

    Args:
        region_slug: Region identifier (e.g., 'tx-harris', 'tx-houston')
        user: Authenticated user

    Returns:
        DemandIndexResponse for the specified region
    """
    try:
        supabase = get_supabase_client()

        # Get latest forecast for the region
        query = f"""
            SELECT * FROM gold.forecast_nowx 
            WHERE region_slug = '{region_slug}'
            ORDER BY last_updated DESC
            LIMIT 1
        """

        result = supabase.rpc("sql_query", {"query": query}).execute()

        if not result.data:
            # Try to generate forecast for this region
            logger.info(
                f"No forecast found for region {region_slug}, attempting to generate"
            )

            # Get region ID
            region_result = (
                supabase.table("regions").select("*").eq("slug", region_slug).execute()
            )

            if not region_result.data:
                raise HTTPException(
                    status_code=404, detail=f"Region {region_slug} not found"
                )

            region_id = region_result.data[0]["id"]

            # Generate fresh forecast
            forecaster = get_demand_surge_forecaster()
            forecast_result = forecaster.generate_forecast(region_id)

            # Store in gold table
            await _update_gold_forecast(
                region_slug, region_result.data[0]["name"], forecast_result
            )

            # Re-query
            result = supabase.rpc("sql_query", {"query": query}).execute()

            if not result.data:
                raise HTTPException(
                    status_code=500, detail="Failed to generate forecast"
                )

        row = result.data[0]

        response = DemandIndexResponse(
            region=row["region_slug"],
            region_name=row["region_name"],
            score=float(row["p_surge"]),
            confidence=float(row["confidence_score"]),
            risk_level=_calculate_risk_level(float(row["p_surge"])),
            week_start=row["forecast_week_start"],
            week_end=row["forecast_week_end"],
            forecast_date=row["last_updated"],
            model_version=row["model_version"],
            bounds={
                "p80_lower": float(row["p80_lower"]),
                "p80_upper": float(row["p80_upper"]),
                "p20_lower": float(row.get("p20_lower", row["p80_lower"])),
                "p20_upper": float(row.get("p20_upper", row["p80_upper"])),
            },
        )

        logger.info(
            f"Returned demand index for region {region_slug}: score={response.score:.3f}"
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting demand index for region {region_slug}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving demand index for region {region_slug}",
        )


@router.post("/demand-index/refresh")
async def refresh_demand_index(
    region: Optional[str] = Query(None, description="Specific region to refresh"),
    user: AuthUser = Depends(auth_user),
):
    """
    Manually refresh demand index forecasts.

    Triggers fresh forecast generation for specified region or all regions.
    This is typically called by the weekly inference job.

    Args:
        region: Optional region slug to refresh
        user: Authenticated user

    Returns:
        Status of refresh operation
    """
    try:
        forecaster = get_demand_surge_forecaster()
        supabase = get_supabase_client()

        # Get regions to refresh
        if region:
            regions_query = f"SELECT * FROM regions WHERE slug = '{region}'"
        else:
            regions_query = "SELECT * FROM regions WHERE active = true"

        regions_result = supabase.rpc("sql_query", {"query": regions_query}).execute()

        if not regions_result.data:
            raise HTTPException(
                status_code=404,
                detail=f"No {'region ' + region if region else 'active regions'} found",
            )

        refreshed_regions = []
        errors = []

        for region_data in regions_result.data:
            try:
                region_id = region_data["id"]
                region_slug = region_data["slug"]
                region_name = region_data["name"]

                logger.info(f"Refreshing forecast for region {region_slug}")

                # Generate forecast
                forecast_result = forecaster.generate_forecast(region_id)

                # Update gold table
                await _update_gold_forecast(region_slug, region_name, forecast_result)

                refreshed_regions.append(region_slug)

            except Exception as e:
                error_msg = f"Failed to refresh region {region_data['slug']}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        return {
            "status": "completed",
            "refreshed_regions": refreshed_regions,
            "total_refreshed": len(refreshed_regions),
            "errors": errors,
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing demand index: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error refreshing demand index: {str(e)}"
        )


async def _generate_fresh_forecasts():
    """Generate fresh forecasts for all active regions"""
    try:
        forecaster = get_demand_surge_forecaster()
        supabase = get_supabase_client()

        # Get all active regions
        regions_result = (
            supabase.table("regions").select("*").eq("active", True).execute()
        )

        for region_data in regions_result.data:
            try:
                region_id = region_data["id"]
                region_slug = region_data["slug"]
                region_name = region_data["name"]

                # Generate forecast
                forecast_result = forecaster.generate_forecast(region_id)

                # Update gold table
                await _update_gold_forecast(region_slug, region_name, forecast_result)

            except Exception as e:
                logger.error(
                    f"Error generating forecast for region {region_slug}: {str(e)}"
                )

    except Exception as e:
        logger.error(f"Error generating fresh forecasts: {str(e)}")


async def _update_gold_forecast(
    region_slug: str, region_name: str, forecast_result: Dict[str, Any]
):
    """Update the gold.forecast_nowx table with new forecast"""
    try:
        supabase = get_supabase_client()

        # Calculate week bounds
        target_date = date.today() + timedelta(days=7)
        week_start = target_date - timedelta(days=target_date.weekday())
        week_end = week_start + timedelta(days=6)

        # Get prior year comparison if available
        prior_year_date = week_start - timedelta(days=365)
        prior_query = f"""
            SELECT p_surge FROM gold.forecast_nowx 
            WHERE region_slug = '{region_slug}' 
                AND forecast_week_start = '{prior_year_date}'
            ORDER BY last_updated DESC
            LIMIT 1
        """

        prior_result = supabase.rpc("sql_query", {"query": prior_query}).execute()
        prior_year_p_surge = (
            prior_result.data[0]["p_surge"] if prior_result.data else None
        )

        # Calculate change percentage
        surge_risk_change_pct = None
        if prior_year_p_surge:
            surge_risk_change_pct = (
                (forecast_result["p_surge"] - prior_year_p_surge) / prior_year_p_surge
            ) * 100

        # Prepare API response cache
        api_response_cache = {
            "region": region_slug,
            "region_name": region_name,
            "score": forecast_result["p_surge"],
            "confidence": forecast_result["confidence_score"],
            "risk_level": _calculate_risk_level(forecast_result["p_surge"]),
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "forecast_date": datetime.now().isoformat(),
            "bounds": {
                "p80_lower": forecast_result["p80_lower"],
                "p80_upper": forecast_result["p80_upper"],
                "p20_lower": forecast_result["p20_lower"],
                "p20_upper": forecast_result["p20_upper"],
            },
        }

        # Update gold table
        gold_record = {
            "region_slug": region_slug,
            "region_name": region_name,
            "forecast_week_start": week_start.isoformat(),
            "forecast_week_end": week_end.isoformat(),
            "p_surge": forecast_result["p_surge"],
            "p80_lower": forecast_result["p80_lower"],
            "p80_upper": forecast_result["p80_upper"],
            "p20_lower": forecast_result.get("p20_lower", forecast_result["p80_lower"]),
            "p20_upper": forecast_result.get("p20_upper", forecast_result["p80_upper"]),
            "prior_year_p_surge": prior_year_p_surge,
            "surge_risk_change_pct": surge_risk_change_pct,
            "confidence_score": forecast_result["confidence_score"],
            "model_version": forecast_result.get("model_version", "unknown"),
            "api_response_cache": json.dumps(api_response_cache),
        }

        # Upsert to gold table
        result = supabase.table("gold.forecast_nowx").upsert([gold_record]).execute()
        logger.info(f"Updated gold forecast for region {region_slug}")

    except Exception as e:
        logger.error(f"Error updating gold forecast: {str(e)}")
        raise
