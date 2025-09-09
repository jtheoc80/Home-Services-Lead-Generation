"""
Weekly Inference Job for Demand Surge Forecasting

This module runs the weekly inference job that:
1. Generates fresh forecasts for all regions
2. Updates the gold.forecast_nowx table
3. Generates impact projection reports
4. Logs job execution and results

This is designed to be run as a scheduled job (cron, GitHub Actions, etc.)
"""

import logging
import asyncio
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import traceback

from app.demand_forecast import get_demand_surge_forecaster
from app.supabase_client import get_supabase_client
from reports.impact_projection import get_impact_projection_reporter

logger = logging.getLogger(__name__)


class WeeklyInferenceJob:
    """Weekly inference job for demand surge forecasting"""

    def __init__(self):
        self.forecaster = get_demand_surge_forecaster()
        self.reporter = get_impact_projection_reporter()
        self.supabase = get_supabase_client()

    async def run_weekly_inference(
        self, target_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Run the complete weekly inference pipeline.

        Args:
            target_date: Date to run inference for (defaults to next week)

        Returns:
            Dictionary with job results and metrics
        """
        if target_date is None:
            target_date = date.today() + timedelta(days=7)

        job_start = datetime.now()
        job_id = self._start_job_tracking(target_date)

        logger.info(f"Starting weekly inference job for {target_date}")

        try:
            # Phase 1: Get active regions
            regions = await self._get_active_regions()
            logger.info(f"Processing {len(regions)} regions")

            # Phase 2: Generate forecasts for each region
            forecast_results = await self._generate_region_forecasts(
                regions, target_date
            )

            # Phase 3: Update gold forecast table
            await self._update_gold_forecasts(forecast_results, target_date)

            # Phase 4: Generate impact projection report
            impact_report = await self._generate_impact_report(target_date)

            # Phase 5: Complete job tracking
            job_duration = (datetime.now() - job_start).total_seconds()
            await self._complete_job_tracking(job_id, forecast_results, job_duration)

            # Compile results
            results = {
                "job_id": job_id,
                "status": "completed",
                "target_date": target_date.isoformat(),
                "duration_seconds": job_duration,
                "regions_processed": len(regions),
                "forecasts_generated": len(forecast_results["successful"]),
                "forecasts_failed": len(forecast_results["failed"]),
                "impact_report_generated": impact_report is not None,
                "successful_regions": forecast_results["successful"],
                "failed_regions": forecast_results["failed"],
                "impact_report_summary": (
                    impact_report.get("summary") if impact_report else None
                ),
            }

            logger.info(
                f"Weekly inference job completed successfully in {job_duration:.1f}s"
            )
            return results

        except Exception as e:
            logger.error(f"Weekly inference job failed: {str(e)}")
            logger.error(traceback.format_exc())

            job_duration = (datetime.now() - job_start).total_seconds()
            await self._fail_job_tracking(job_id, str(e), job_duration)

            return {
                "job_id": job_id,
                "status": "failed",
                "error": str(e),
                "duration_seconds": job_duration,
                "target_date": target_date.isoformat(),
            }

    async def _get_active_regions(self) -> List[Dict[str, Any]]:
        """Get all active regions for processing"""
        try:
            result = (
                self.supabase.table("regions").select("*").eq("active", True).execute()
            )
            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Error getting active regions: {str(e)}")
            return []

    async def _generate_region_forecasts(
        self, regions: List[Dict[str, Any]], target_date: date
    ) -> Dict[str, List]:
        """Generate forecasts for all regions"""
        successful = []
        failed = []

        for region in regions:
            try:
                region_id = region["id"]
                region_slug = region["slug"]
                region_name = region["name"]

                logger.info(f"Generating forecast for {region_slug}")

                # Generate forecast
                forecast_result = self.forecaster.generate_forecast(
                    region_id, target_date
                )

                # Add region metadata
                forecast_result["region_id"] = region_id
                forecast_result["region_slug"] = region_slug
                forecast_result["region_name"] = region_name

                successful.append(
                    {
                        "region_slug": region_slug,
                        "region_name": region_name,
                        "forecast": forecast_result,
                    }
                )

                logger.info(
                    f"Generated forecast for {region_slug}: p_surge={forecast_result['p_surge']:.3f}"
                )

            except Exception as e:
                error_msg = f"Failed to generate forecast for {region.get('slug', 'unknown')}: {str(e)}"
                logger.error(error_msg)

                failed.append(
                    {
                        "region_slug": region.get("slug", "unknown"),
                        "region_name": region.get("name", "unknown"),
                        "error": str(e),
                    }
                )

        return {"successful": successful, "failed": failed}

    async def _update_gold_forecasts(
        self, forecast_results: Dict[str, List], target_date: date
    ):
        """Update the gold.forecast_nowx table with new forecasts"""
        try:
            # Calculate week bounds
            week_start = target_date - timedelta(days=target_date.weekday())
            week_end = week_start + timedelta(days=6)

            gold_records = []

            for result in forecast_results["successful"]:
                forecast = result["forecast"]
                region_slug = result["region_slug"]
                region_name = result["region_name"]

                # Get prior year comparison if available
                prior_year_date = week_start - timedelta(days=365)
                prior_query = f"""
                    SELECT p_surge FROM gold.forecast_nowx 
                    WHERE region_slug = '{region_slug}' 
                        AND forecast_week_start = '{prior_year_date}'
                    ORDER BY last_updated DESC
                    LIMIT 1
                """

                try:
                    prior_result = self.supabase.rpc(
                        "sql_query", {"query": prior_query}
                    ).execute()
                    prior_year_p_surge = (
                        prior_result.data[0]["p_surge"] if prior_result.data else None
                    )
                except:
                    prior_year_p_surge = None

                # Calculate change percentage
                surge_risk_change_pct = None
                if prior_year_p_surge:
                    surge_risk_change_pct = (
                        (forecast["p_surge"] - prior_year_p_surge) / prior_year_p_surge
                    ) * 100

                # Prepare API response cache
                api_response_cache = {
                    "region": region_slug,
                    "region_name": region_name,
                    "score": forecast["p_surge"],
                    "confidence": forecast["confidence_score"],
                    "risk_level": self._get_risk_level(forecast["p_surge"]),
                    "week_start": week_start.isoformat(),
                    "week_end": week_end.isoformat(),
                    "forecast_date": datetime.now().isoformat(),
                    "bounds": {
                        "p80_lower": forecast["p80_lower"],
                        "p80_upper": forecast["p80_upper"],
                        "p20_lower": forecast["p20_lower"],
                        "p20_upper": forecast["p20_upper"],
                    },
                }

                # Create gold record
                gold_record = {
                    "region_slug": region_slug,
                    "region_name": region_name,
                    "forecast_week_start": week_start.isoformat(),
                    "forecast_week_end": week_end.isoformat(),
                    "p_surge": forecast["p_surge"],
                    "p80_lower": forecast["p80_lower"],
                    "p80_upper": forecast["p80_upper"],
                    "p20_lower": forecast.get("p20_lower", forecast["p80_lower"]),
                    "p20_upper": forecast.get("p20_upper", forecast["p80_upper"]),
                    "prior_year_p_surge": prior_year_p_surge,
                    "surge_risk_change_pct": surge_risk_change_pct,
                    "confidence_score": forecast["confidence_score"],
                    "model_version": forecast.get("model_version", "unknown"),
                    "api_response_cache": json.dumps(api_response_cache),
                }

                gold_records.append(gold_record)

            # Batch upsert to gold table
            if gold_records:
                result = (
                    self.supabase.table("gold.forecast_nowx")
                    .upsert(gold_records)
                    .execute()
                )
                logger.info(
                    f"Updated {len(gold_records)} records in gold.forecast_nowx"
                )

        except Exception as e:
            logger.error(f"Error updating gold forecasts: {str(e)}")
            raise

    def _get_risk_level(self, p_surge: float) -> str:
        """Convert surge probability to risk level"""
        if p_surge >= 0.7:
            return "high"
        elif p_surge >= 0.3:
            return "medium"
        else:
            return "low"

    async def _generate_impact_report(
        self, target_date: date
    ) -> Optional[Dict[str, Any]]:
        """Generate impact projection report"""
        try:
            logger.info("Generating impact projection report")

            # Generate the report
            report = self.reporter.generate_weekly_report(target_date)

            if report and "error" not in report:
                # Save report to file
                self.reporter._save_report(report, "html", target_date)
                self.reporter._save_report(report, "csv", target_date)

                logger.info(
                    f"Generated impact report with {report.get('total_regions', 0)} regions"
                )
                return report
            else:
                logger.warning("Impact report generation returned no data or error")
                return None

        except Exception as e:
            logger.error(f"Error generating impact report: {str(e)}")
            return None

    def _start_job_tracking(self, target_date: date) -> str:
        """Start job tracking in the database"""
        try:
            job_record = {
                "job_type": "weekly_inference",
                "job_status": "running",
                "target_date": target_date.isoformat(),
                "regions_processed": [],
                "models_used": [],
                "predictions_generated": 0,
            }

            result = self.supabase.table("forecast_jobs").insert(job_record).execute()
            job_id = result.data[0]["id"] if result.data else None

            logger.info(f"Started job tracking with ID: {job_id}")
            return job_id

        except Exception as e:
            logger.error(f"Error starting job tracking: {str(e)}")
            return f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    async def _complete_job_tracking(
        self, job_id: str, forecast_results: Dict[str, List], duration_seconds: float
    ):
        """Complete job tracking with results"""
        try:
            regions_processed = [
                r["region_slug"] for r in forecast_results["successful"]
            ]
            models_used = list(
                set(
                    [
                        r["forecast"].get("model_version", "unknown")
                        for r in forecast_results["successful"]
                    ]
                )
            )

            update_data = {
                "job_status": "completed",
                "regions_processed": regions_processed,
                "models_used": models_used,
                "predictions_generated": len(forecast_results["successful"]),
                "total_runtime_seconds": duration_seconds,
                "completed_at": datetime.now().isoformat(),
            }

            self.supabase.table("forecast_jobs").update(update_data).eq(
                "id", job_id
            ).execute()
            logger.info(f"Completed job tracking for job {job_id}")

        except Exception as e:
            logger.error(f"Error completing job tracking: {str(e)}")

    async def _fail_job_tracking(
        self, job_id: str, error_message: str, duration_seconds: float
    ):
        """Mark job as failed in tracking"""
        try:
            update_data = {
                "job_status": "failed",
                "error_message": error_message,
                "total_runtime_seconds": duration_seconds,
                "completed_at": datetime.now().isoformat(),
            }

            self.supabase.table("forecast_jobs").update(update_data).eq(
                "id", job_id
            ).execute()
            logger.info(f"Marked job {job_id} as failed")

        except Exception as e:
            logger.error(f"Error failing job tracking: {str(e)}")


# CLI entry point
async def main():
    """Main entry point for running the weekly inference job"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run weekly demand surge inference job"
    )
    parser.add_argument(
        "--target-date", type=str, help="Target date in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Run without updating database"
    )

    args = parser.parse_args()

    # Parse target date
    target_date = None
    if args.target_date:
        try:
            target_date = datetime.strptime(args.target_date, "%Y-%m-%d").date()
        except ValueError:
            print(f"Invalid date format: {args.target_date}. Use YYYY-MM-DD.")
            return

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run the job
    job = WeeklyInferenceJob()

    if args.dry_run:
        print("DRY RUN: Would run weekly inference job")
        print(f"Target date: {target_date or 'next week'}")
        return

    try:
        results = await job.run_weekly_inference(target_date)

        print("\n=== Weekly Inference Job Results ===")
        print(f"Status: {results['status']}")
        print(f"Duration: {results['duration_seconds']:.1f} seconds")
        print(f"Regions processed: {results['regions_processed']}")
        print(f"Forecasts generated: {results['forecasts_generated']}")

        if results["forecasts_failed"] > 0:
            print(f"Failed forecasts: {results['forecasts_failed']}")
            for failed in results["failed_regions"]:
                print(f"  - {failed['region_slug']}: {failed['error']}")

        if results.get("impact_report_generated"):
            print("Impact projection report generated successfully")

        print(f"\nJob ID: {results['job_id']}")

    except Exception as e:
        print(f"Job failed: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(asyncio.run(main()))
