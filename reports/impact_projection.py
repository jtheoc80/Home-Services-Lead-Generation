"""
Impact Projection Report Generator

Generates reports comparing p_surge for current year vs last year by mega-city region.
Provides narrative like "Region X projected 40% surge risk vs 10% last year."

This module creates:
- Comparison tables and maps
- Narrative summaries
- HTML/PDF reports
- API endpoints for report data
"""

import logging
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

# Visualization
import plotly.express as px

# Database
from app.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class ImpactProjectionReporter:
    """Generates impact projection reports comparing surge forecasts year-over-year"""

    def __init__(self):
        self.supabase = get_supabase_client()

    def generate_impact_report(
        self,
        regions: Optional[List[str]] = None,
        target_date: Optional[date] = None,
        output_format: str = "json",
    ) -> Dict[str, Any]:
        """
        Generate impact projection report comparing current vs prior year surge forecasts.

        Args:
            regions: List of region slugs to include (None for all)
            target_date: Target date for comparison (defaults to current week)
            output_format: Output format ("json", "html", "csv")

        Returns:
            Dictionary containing report data and visualizations
        """
        if target_date is None:
            target_date = date.today()

        logger.info(f"Generating impact projection report for {target_date}")

        # Get current and prior year data
        current_data = self._get_forecast_data(regions, target_date)
        prior_data = self._get_forecast_data(regions, target_date - timedelta(days=365))

        # Merge and calculate changes
        comparison_data = self._merge_and_calculate_changes(current_data, prior_data)

        if comparison_data.empty:
            logger.warning("No comparison data available for impact report")
            return {"error": "No data available for comparison"}

        # Generate narrative
        narrative = self._generate_narrative(comparison_data)

        # Create visualizations
        visualizations = self._create_visualizations(comparison_data)

        # Compile report
        report = {
            "report_date": datetime.now().isoformat(),
            "target_week": target_date.isoformat(),
            "comparison_week": (target_date - timedelta(days=365)).isoformat(),
            "total_regions": len(comparison_data),
            "summary": {
                "regions_with_increased_risk": len(
                    comparison_data[comparison_data["change_pct"] > 0]
                ),
                "regions_with_decreased_risk": len(
                    comparison_data[comparison_data["change_pct"] < 0]
                ),
                "avg_change_pct": float(comparison_data["change_pct"].mean()),
                "max_increase": {
                    "region": comparison_data.loc[
                        comparison_data["change_pct"].idxmax(), "region_name"
                    ],
                    "current_risk": float(
                        comparison_data.loc[
                            comparison_data["change_pct"].idxmax(), "current_p_surge"
                        ]
                    ),
                    "prior_risk": float(
                        comparison_data.loc[
                            comparison_data["change_pct"].idxmax(), "prior_p_surge"
                        ]
                    ),
                    "change_pct": float(
                        comparison_data.loc[
                            comparison_data["change_pct"].idxmax(), "change_pct"
                        ]
                    ),
                },
                "max_decrease": {
                    "region": comparison_data.loc[
                        comparison_data["change_pct"].idxmin(), "region_name"
                    ],
                    "current_risk": float(
                        comparison_data.loc[
                            comparison_data["change_pct"].idxmin(), "current_p_surge"
                        ]
                    ),
                    "prior_risk": float(
                        comparison_data.loc[
                            comparison_data["change_pct"].idxmin(), "prior_p_surge"
                        ]
                    ),
                    "change_pct": float(
                        comparison_data.loc[
                            comparison_data["change_pct"].idxmin(), "change_pct"
                        ]
                    ),
                },
            },
            "narrative": narrative,
            "data": comparison_data.to_dict(orient="records"),
            "visualizations": visualizations,
        }

        # Save report if requested
        if output_format != "json":
            self._save_report(report, output_format, target_date)

        logger.info(f"Generated impact report with {len(comparison_data)} regions")
        return report

    def _get_forecast_data(
        self, regions: Optional[List[str]], target_date: date
    ) -> pd.DataFrame:
        """Get forecast data for specified regions and date"""
        try:
            # Calculate week bounds
            week_start = target_date - timedelta(days=target_date.weekday())

            # Build query
            region_filter = ""
            if regions:
                region_list = "', '".join(regions)
                region_filter = f"AND region_slug IN ('{region_list}')"

            query = f"""
                SELECT 
                    region_slug,
                    region_name,
                    p_surge,
                    confidence_score,
                    forecast_week_start,
                    model_version,
                    last_updated
                FROM gold.forecast_nowx
                WHERE forecast_week_start = '{week_start}'
                {region_filter}
                ORDER BY region_slug
            """

            result = self.supabase.rpc("sql_query", {"query": query}).execute()

            if result.data:
                df = pd.DataFrame(result.data)
                df["p_surge"] = df["p_surge"].astype(float)
                df["confidence_score"] = df["confidence_score"].astype(float)
                return df
            else:
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error getting forecast data: {str(e)}")
            return pd.DataFrame()

    def _merge_and_calculate_changes(
        self, current_data: pd.DataFrame, prior_data: pd.DataFrame
    ) -> pd.DataFrame:
        """Merge current and prior year data and calculate changes"""
        if current_data.empty or prior_data.empty:
            return pd.DataFrame()

        # Merge on region
        merged = current_data.merge(
            prior_data[["region_slug", "p_surge"]],
            on="region_slug",
            how="inner",
            suffixes=("_current", "_prior"),
        )

        if merged.empty:
            return pd.DataFrame()

        # Rename columns for clarity
        merged = merged.rename(
            columns={
                "p_surge_current": "current_p_surge",
                "p_surge_prior": "prior_p_surge",
            }
        )

        # Calculate changes
        merged["change_pct"] = (
            (merged["current_p_surge"] - merged["prior_p_surge"])
            / merged["prior_p_surge"]
        ) * 100
        merged["change_abs"] = merged["current_p_surge"] - merged["prior_p_surge"]

        # Risk levels
        merged["current_risk_level"] = merged["current_p_surge"].apply(
            self._get_risk_level
        )
        merged["prior_risk_level"] = merged["prior_p_surge"].apply(self._get_risk_level)

        # Risk direction
        merged["risk_direction"] = np.where(
            merged["change_pct"] > 10,
            "Significantly Increased",
            np.where(
                merged["change_pct"] > 0,
                "Increased",
                np.where(
                    merged["change_pct"] < -10, "Significantly Decreased", "Decreased"
                ),
            ),
        )

        return merged

    def _get_risk_level(self, p_surge: float) -> str:
        """Convert surge probability to risk level"""
        if p_surge >= 0.7:
            return "High"
        elif p_surge >= 0.3:
            return "Medium"
        else:
            return "Low"

    def _generate_narrative(self, comparison_data: pd.DataFrame) -> Dict[str, str]:
        """Generate narrative summaries of the comparison"""
        narratives = {}

        # Overall summary
        total_regions = len(comparison_data)
        increased_regions = len(comparison_data[comparison_data["change_pct"] > 0])
        avg_change = comparison_data["change_pct"].mean()

        narratives["overall"] = (
            f"Across {total_regions} regions analyzed, {increased_regions} regions "
            f"({increased_regions/total_regions*100:.1f}%) show increased surge risk compared to the same week last year. "
            f"The average change in surge probability is {avg_change:+.1f} percentage points."
        )

        # Top changes
        top_increases = comparison_data.nlargest(3, "change_pct")
        top_decreases = comparison_data.nsmallest(3, "change_pct")

        # Highest increase narrative
        if not top_increases.empty:
            top_region = top_increases.iloc[0]
            narratives["highest_increase"] = (
                f"{top_region['region_name']} shows the highest surge risk increase, with "
                f"{top_region['current_p_surge']*100:.0f}% projected surge probability vs "
                f"{top_region['prior_p_surge']*100:.0f}% last year "
                f"({top_region['change_pct']:+.1f} percentage point change)."
            )

        # Lowest change narrative
        if not top_decreases.empty:
            bottom_region = top_decreases.iloc[0]
            narratives["highest_decrease"] = (
                f"{bottom_region['region_name']} shows the largest risk reduction, with "
                f"{bottom_region['current_p_surge']*100:.0f}% projected surge probability vs "
                f"{bottom_region['prior_p_surge']*100:.0f}% last year "
                f"({bottom_region['change_pct']:+.1f} percentage point change)."
            )

        # Regional highlights
        high_risk_regions = comparison_data[
            comparison_data["current_risk_level"] == "High"
        ]
        if not high_risk_regions.empty:
            high_risk_names = high_risk_regions["region_name"].tolist()
            narratives["high_risk_regions"] = (
                f"Regions currently at high surge risk (≥70% probability): "
                f"{', '.join(high_risk_names[:3])}{'...' if len(high_risk_names) > 3 else ''}."
            )

        # Significant changes
        sig_increases = comparison_data[comparison_data["change_pct"] > 50]
        if not sig_increases.empty:
            narratives["significant_increases"] = (
                f"{len(sig_increases)} regions show significant surge risk increases (>50% relative change): "
                f"{', '.join(sig_increases['region_name'].tolist())}."
            )

        return narratives

    def _create_visualizations(self, comparison_data: pd.DataFrame) -> Dict[str, Any]:
        """Create visualizations for the report"""
        visualizations = {}

        try:
            # 1. Comparison scatter plot
            fig_scatter = px.scatter(
                comparison_data,
                x="prior_p_surge",
                y="current_p_surge",
                hover_name="region_name",
                hover_data=["change_pct", "current_risk_level"],
                title="Current vs Prior Year Surge Risk by Region",
                labels={
                    "prior_p_surge": "Prior Year Surge Probability",
                    "current_p_surge": "Current Year Surge Probability",
                },
            )

            # Add diagonal line (no change)
            fig_scatter.add_shape(
                type="line",
                x0=0,
                y0=0,
                x1=1,
                y1=1,
                line=dict(color="gray", dash="dash"),
            )

            visualizations["comparison_scatter"] = fig_scatter.to_json()

            # 2. Change distribution histogram
            fig_hist = px.histogram(
                comparison_data,
                x="change_pct",
                nbins=20,
                title="Distribution of Surge Risk Changes (% Change)",
                labels={"change_pct": "Percentage Change in Surge Risk"},
            )

            visualizations["change_distribution"] = fig_hist.to_json()

            # 3. Top/bottom regions bar chart
            top_bottom = pd.concat(
                [
                    comparison_data.nlargest(5, "change_pct"),
                    comparison_data.nsmallest(5, "change_pct"),
                ]
            )

            fig_bar = px.bar(
                top_bottom,
                x="region_name",
                y="change_pct",
                color="risk_direction",
                title="Largest Changes in Surge Risk by Region",
                labels={"change_pct": "Change in Surge Risk (%)"},
            )

            fig_bar.update_xaxes(tickangle=45)
            visualizations["top_changes"] = fig_bar.to_json()

            # 4. Risk level transition matrix
            risk_transitions = (
                comparison_data.groupby(["prior_risk_level", "current_risk_level"])
                .size()
                .reset_index(name="count")
            )

            if not risk_transitions.empty:
                fig_transition = px.bar(
                    risk_transitions,
                    x="prior_risk_level",
                    y="count",
                    color="current_risk_level",
                    title="Risk Level Transitions (Prior → Current)",
                    labels={
                        "count": "Number of Regions",
                        "prior_risk_level": "Prior Risk Level",
                    },
                )

                visualizations["risk_transitions"] = fig_transition.to_json()

            # 5. Summary table
            summary_table = comparison_data[
                [
                    "region_name",
                    "current_p_surge",
                    "prior_p_surge",
                    "change_pct",
                    "current_risk_level",
                    "risk_direction",
                ]
            ].round(3)

            visualizations["summary_table"] = summary_table.to_dict(orient="records")

        except Exception as e:
            logger.error(f"Error creating visualizations: {str(e)}")
            visualizations["error"] = f"Error creating visualizations: {str(e)}"

        return visualizations

    def _save_report(
        self, report: Dict[str, Any], output_format: str, target_date: date
    ):
        """Save report to file"""
        try:
            # Create reports directory
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)

            filename = f"impact_projection_{target_date.strftime('%Y%m%d')}"

            if output_format == "html":
                self._save_html_report(report, reports_dir / f"{filename}.html")
            elif output_format == "csv":
                self._save_csv_report(report, reports_dir / f"{filename}.csv")

            logger.info(f"Saved report to {reports_dir / filename}")

        except Exception as e:
            logger.error(f"Error saving report: {str(e)}")

    def _save_html_report(self, report: Dict[str, Any], filepath: Path):
        """Save report as HTML"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Impact Projection Report - {report['target_week']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
                .summary {{ background-color: #e9ecef; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                .narrative {{ margin: 20px 0; }}
                .data-table {{ border-collapse: collapse; width: 100%; }}
                .data-table th, .data-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .data-table th {{ background-color: #f2f2f2; }}
                .increase {{ color: #d63384; font-weight: bold; }}
                .decrease {{ color: #198754; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Demand Surge Impact Projection Report</h1>
                <p><strong>Report Date:</strong> {report['report_date']}</p>
                <p><strong>Target Week:</strong> {report['target_week']}</p>
                <p><strong>Comparison Week:</strong> {report['comparison_week']}</p>
            </div>
            
            <div class="summary">
                <h2>Executive Summary</h2>
                <ul>
                    <li><strong>Total Regions Analyzed:</strong> {report['total_regions']}</li>
                    <li><strong>Regions with Increased Risk:</strong> {report['summary']['regions_with_increased_risk']}</li>
                    <li><strong>Average Change:</strong> {report['summary']['avg_change_pct']:.1f}%</li>
                    <li><strong>Largest Increase:</strong> {report['summary']['max_increase']['region']} 
                        ({report['summary']['max_increase']['current_risk']*100:.0f}% vs {report['summary']['max_increase']['prior_risk']*100:.0f}%)</li>
                </ul>
            </div>
            
            <div class="narrative">
                <h2>Key Insights</h2>
        """

        for key, narrative in report["narrative"].items():
            html_content += (
                f"<p><strong>{key.replace('_', ' ').title()}:</strong> {narrative}</p>"
            )

        html_content += """
            </div>
            
            <div>
                <h2>Regional Comparison Data</h2>
                <table class="data-table">
                    <tr>
                        <th>Region</th>
                        <th>Current Risk</th>
                        <th>Prior Risk</th>
                        <th>Change (%)</th>
                        <th>Risk Level</th>
                        <th>Direction</th>
                    </tr>
        """

        for row in report["data"]:
            change_class = "increase" if row["change_pct"] > 0 else "decrease"
            html_content += f"""
                    <tr>
                        <td>{row['region_name']}</td>
                        <td>{row['current_p_surge']*100:.1f}%</td>
                        <td>{row['prior_p_surge']*100:.1f}%</td>
                        <td class="{change_class}">{row['change_pct']:+.1f}%</td>
                        <td>{row['current_risk_level']}</td>
                        <td>{row['risk_direction']}</td>
                    </tr>
            """

        html_content += """
                </table>
            </div>
        </body>
        </html>
        """

        with open(filepath, "w") as f:
            f.write(html_content)

    def _save_csv_report(self, report: Dict[str, Any], filepath: Path):
        """Save report data as CSV"""
        df = pd.DataFrame(report["data"])
        df.to_csv(filepath, index=False)

    def generate_weekly_report(
        self, target_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Generate the standard weekly impact projection report.

        This is the main entry point for the weekly inference job.
        """
        return self.generate_impact_report(
            regions=None, target_date=target_date, output_format="json"  # All regions
        )


# Helper function for API usage
def get_impact_projection_reporter() -> ImpactProjectionReporter:
    """Get configured impact projection reporter instance"""
    return ImpactProjectionReporter()


def generate_example_report() -> Dict[str, Any]:
    """Generate an example report with sample data for testing"""
    # Create sample data
    sample_data = pd.DataFrame(
        {
            "region_slug": ["tx-harris", "tx-galveston", "tx-fort-bend"],
            "region_name": ["Harris County", "Galveston County", "Fort Bend County"],
            "current_p_surge": [0.45, 0.12, 0.28],
            "prior_p_surge": [0.15, 0.08, 0.31],
            "confidence_score": [0.85, 0.82, 0.88],
        }
    )

    # Calculate changes
    sample_data["change_pct"] = (
        (sample_data["current_p_surge"] - sample_data["prior_p_surge"])
        / sample_data["prior_p_surge"]
    ) * 100
    sample_data["change_abs"] = (
        sample_data["current_p_surge"] - sample_data["prior_p_surge"]
    )

    reporter = ImpactProjectionReporter()
    sample_data["current_risk_level"] = sample_data["current_p_surge"].apply(
        reporter._get_risk_level
    )
    sample_data["prior_risk_level"] = sample_data["prior_p_surge"].apply(
        reporter._get_risk_level
    )

    sample_data["risk_direction"] = np.where(
        sample_data["change_pct"] > 10,
        "Significantly Increased",
        np.where(
            sample_data["change_pct"] > 0,
            "Increased",
            np.where(
                sample_data["change_pct"] < -10, "Significantly Decreased", "Decreased"
            ),
        ),
    )

    # Generate sample report
    narrative = reporter._generate_narrative(sample_data)
    visualizations = reporter._create_visualizations(sample_data)

    return {
        "report_date": datetime.now().isoformat(),
        "target_week": date.today().isoformat(),
        "comparison_week": (date.today() - timedelta(days=365)).isoformat(),
        "total_regions": len(sample_data),
        "summary": {
            "regions_with_increased_risk": len(
                sample_data[sample_data["change_pct"] > 0]
            ),
            "regions_with_decreased_risk": len(
                sample_data[sample_data["change_pct"] < 0]
            ),
            "avg_change_pct": float(sample_data["change_pct"].mean()),
        },
        "narrative": narrative,
        "data": sample_data.to_dict(orient="records"),
        "visualizations": visualizations,
        "note": "This is a sample report with mock data for demonstration purposes.",
    }
