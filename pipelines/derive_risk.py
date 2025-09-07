"""
Risk derivation pipeline.

This module creates risk indicators by overlaying FEMA flood data,
NWS weather alerts, and other risk factors to generate demand pressure metrics.
"""

import logging
import yaml
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import psycopg2
from psycopg2.extras import Json, RealDictCursor

logger = logging.getLogger(__name__)

# Optional dependencies for enhanced geospatial analysis
try:
    from shapely.geometry import Point, shape
    from shapely.ops import transform

    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False
    logger.warning("Shapely not available - some geospatial features will be limited")

try:
    import geopandas
    import pandas as pd

    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False
    logger.warning(
        "GeoPandas/Pandas not available - some analysis features will be limited"
    )


class RiskDeriver:
    """Pipeline for deriving risk indicators and demand pressure metrics."""

    def __init__(self, db_url: str, sources_config_path: str):
        """
        Initialize the risk deriver.

        Args:
            db_url: PostgreSQL connection URL
            sources_config_path: Path to sources_tx.yaml configuration
        """
        self.db_url = db_url
        self.sources_config_path = sources_config_path
        self.sources_config = self._load_sources_config()
        self.risk_overlays = self.sources_config.get("risk_overlays", [])

        # Weather API settings
        self.nws_api_base = "https://api.weather.gov"
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "HomeServicesLeadGen/1.0 (Texas Risk Analysis)"}
        )

    def _load_sources_config(self) -> Dict[str, Any]:
        """Load sources configuration from YAML file."""
        try:
            with open(self.sources_config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load sources config: {e}")
            raise

    def _get_db_connection(self):
        """Create database connection."""
        return psycopg2.connect(self.db_url)

    def _ensure_risk_tables_exist(self):
        """Ensure risk analysis tables exist in database."""
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()

            # Create flood risk overlay table
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS flood_risk (
                    id SERIAL PRIMARY KEY,
                    permit_id INTEGER REFERENCES permits(id),
                    flood_zone TEXT,
                    flood_risk_level TEXT,
                    base_flood_elevation NUMERIC,
                    effective_date DATE,
                    confidence NUMERIC,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(permit_id)
                )
            """
            )

            # Create weather alerts table
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS weather_alerts (
                    id SERIAL PRIMARY KEY,
                    alert_id TEXT UNIQUE,
                    event_type TEXT,
                    severity TEXT,
                    urgency TEXT,
                    certainty TEXT,
                    headline TEXT,
                    description TEXT,
                    instruction TEXT,
                    areas TEXT[],
                    effective_time TIMESTAMPTZ,
                    expires_time TIMESTAMPTZ,
                    sent_time TIMESTAMPTZ,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """
            )

            # Create demand pressure metrics table
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS demand_pressure (
                    id SERIAL PRIMARY KEY,
                    permit_id INTEGER REFERENCES permits(id),
                    
                    -- Risk factors
                    flood_risk_score NUMERIC DEFAULT 0,
                    weather_risk_score NUMERIC DEFAULT 0,
                    seasonal_factor NUMERIC DEFAULT 1.0,
                    market_density_factor NUMERIC DEFAULT 1.0,
                    
                    -- Combined metrics
                    total_risk_score NUMERIC DEFAULT 0,
                    demand_pressure_score NUMERIC DEFAULT 0,
                    urgency_multiplier NUMERIC DEFAULT 1.0,
                    
                    -- Calculation metadata
                    calculated_at TIMESTAMPTZ DEFAULT NOW(),
                    calculation_version TEXT DEFAULT '1.0',
                    factors_used JSONB,
                    
                    UNIQUE(permit_id)
                )
            """
            )

            # Create risk events log table
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS risk_events (
                    id SERIAL PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    event_subtype TEXT,
                    severity TEXT,
                    affected_area TEXT,
                    coordinates POINT,
                    radius_miles NUMERIC,
                    start_time TIMESTAMPTZ,
                    end_time TIMESTAMPTZ,
                    impact_score NUMERIC,
                    description TEXT,
                    source_data JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """
            )

            # Create indexes for performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_flood_risk_permit_id ON flood_risk(permit_id)",
                "CREATE INDEX IF NOT EXISTS idx_weather_alerts_event_type ON weather_alerts(event_type)",
                "CREATE INDEX IF NOT EXISTS idx_weather_alerts_effective_time ON weather_alerts(effective_time)",
                "CREATE INDEX IF NOT EXISTS idx_demand_pressure_permit_id ON demand_pressure(permit_id)",
                "CREATE INDEX IF NOT EXISTS idx_demand_pressure_total_risk ON demand_pressure(total_risk_score)",
                "CREATE INDEX IF NOT EXISTS idx_risk_events_event_type ON risk_events(event_type)",
                "CREATE INDEX IF NOT EXISTS idx_risk_events_start_time ON risk_events(start_time)",
                "CREATE INDEX IF NOT EXISTS idx_risk_events_coordinates ON risk_events USING GIST(coordinates)",
            ]

            for index_sql in indexes:
                cur.execute(index_sql)

            conn.commit()
            logger.info("Risk analysis tables initialized")

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to create risk tables: {e}")
            raise
        finally:
            conn.close()

    def fetch_nws_alerts(self, area: str = "TX") -> List[Dict[str, Any]]:
        """Fetch current weather alerts from National Weather Service."""
        try:
            url = f"{self.nws_api_base}/alerts/active"
            params = {"area": area}

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            features = data.get("features", [])

            alerts = []
            for feature in features:
                properties = feature.get("properties", {})

                alert = {
                    "alert_id": properties.get("id"),
                    "event_type": properties.get("event"),
                    "severity": properties.get("severity"),
                    "urgency": properties.get("urgency"),
                    "certainty": properties.get("certainty"),
                    "headline": properties.get("headline"),
                    "description": properties.get("description"),
                    "instruction": properties.get("instruction"),
                    "areas": (
                        properties.get("areaDesc", "").split(";")
                        if properties.get("areaDesc")
                        else []
                    ),
                    "effective_time": self._parse_iso_datetime(
                        properties.get("effective")
                    ),
                    "expires_time": self._parse_iso_datetime(properties.get("expires")),
                    "sent_time": self._parse_iso_datetime(properties.get("sent")),
                }

                alerts.append(alert)

            logger.info(f"Fetched {len(alerts)} weather alerts")
            return alerts

        except Exception as e:
            logger.error(f"Failed to fetch NWS alerts: {e}")
            return []

    def _parse_iso_datetime(self, iso_string: str) -> Optional[datetime]:
        """Parse ISO 8601 datetime string."""
        if not iso_string:
            return None

        try:
            return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        except ValueError:
            return None

    def store_weather_alerts(self, alerts: List[Dict[str, Any]]) -> int:
        """Store weather alerts in database."""
        if not alerts:
            return 0

        conn = self._get_db_connection()
        try:
            cur = conn.cursor()

            insert_sql = """
                INSERT INTO weather_alerts (
                    alert_id, event_type, severity, urgency, certainty,
                    headline, description, instruction, areas,
                    effective_time, expires_time, sent_time
                ) VALUES (
                    %(alert_id)s, %(event_type)s, %(severity)s, %(urgency)s, %(certainty)s,
                    %(headline)s, %(description)s, %(instruction)s, %(areas)s,
                    %(effective_time)s, %(expires_time)s, %(sent_time)s
                )
                ON CONFLICT (alert_id) DO UPDATE SET
                    event_type = EXCLUDED.event_type,
                    severity = EXCLUDED.severity,
                    urgency = EXCLUDED.urgency,
                    certainty = EXCLUDED.certainty,
                    headline = EXCLUDED.headline,
                    description = EXCLUDED.description,
                    instruction = EXCLUDED.instruction,
                    areas = EXCLUDED.areas,
                    effective_time = EXCLUDED.effective_time,
                    expires_time = EXCLUDED.expires_time,
                    sent_time = EXCLUDED.sent_time
            """

            cur.executemany(insert_sql, alerts)
            conn.commit()

            rows_affected = cur.rowcount
            logger.info(f"Stored {rows_affected} weather alerts")
            return rows_affected

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to store weather alerts: {e}")
            raise
        finally:
            conn.close()

    def analyze_flood_risk(self, permit_ids: Optional[List[int]] = None) -> int:
        """Analyze flood risk for permits based on FEMA flood zones."""
        conn = self._get_db_connection()
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Build query for permits with coordinates
            where_clause = "WHERE p.latitude IS NOT NULL AND p.longitude IS NOT NULL"
            params = []

            if permit_ids:
                where_clause += " AND p.id = ANY(%s)"
                params.append(permit_ids)

            # Get permits that need flood risk analysis
            cur.execute(
                f"""
                SELECT p.id, p.latitude, p.longitude, p.address
                FROM permits p
                LEFT JOIN flood_risk fr ON p.id = fr.permit_id
                {where_clause}
                AND fr.id IS NULL  -- Only permits without existing flood risk data
                LIMIT 1000
            """,
                params,
            )

            permits = cur.fetchall()

            if not permits:
                logger.info("No permits need flood risk analysis")
                return 0

            logger.info(f"Analyzing flood risk for {len(permits)} permits")

            # For this implementation, we'll use a simplified flood risk model
            # In production, this would integrate with FEMA's flood map services
            flood_risk_records = []

            for permit in permits:
                flood_zone, risk_level = self._determine_flood_risk(
                    permit["latitude"], permit["longitude"]
                )

                flood_risk_records.append(
                    {
                        "permit_id": permit["id"],
                        "flood_zone": flood_zone,
                        "flood_risk_level": risk_level,
                        "confidence": 0.8,  # Placeholder confidence score
                        "effective_date": datetime.now().date(),
                    }
                )

            # Batch insert flood risk data
            if flood_risk_records:
                insert_sql = """
                    INSERT INTO flood_risk (
                        permit_id, flood_zone, flood_risk_level, confidence, effective_date
                    ) VALUES (
                        %(permit_id)s, %(flood_zone)s, %(flood_risk_level)s, %(confidence)s, %(effective_date)s
                    )
                    ON CONFLICT (permit_id) DO UPDATE SET
                        flood_zone = EXCLUDED.flood_zone,
                        flood_risk_level = EXCLUDED.flood_risk_level,
                        confidence = EXCLUDED.confidence,
                        effective_date = EXCLUDED.effective_date
                """

                cur.executemany(insert_sql, flood_risk_records)
                conn.commit()

                rows_affected = cur.rowcount
                logger.info(f"Analyzed flood risk for {rows_affected} permits")
                return rows_affected

            return 0

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to analyze flood risk: {e}")
            raise
        finally:
            conn.close()

    def _determine_flood_risk(
        self, latitude: float, longitude: float
    ) -> Tuple[str, str]:
        """
        Determine flood zone and risk level for coordinates.

        This is a simplified implementation. In production, this would:
        1. Query FEMA's National Flood Hazard Layer (NFHL) API
        2. Intersect coordinates with detailed flood zone polygons
        3. Return actual FEMA flood zone designations
        """
        # Simplified flood risk based on proximity to known flood-prone areas
        # Texas major flood zones: Houston bayous, San Antonio river, Dallas Trinity River

        houston_flood_zones = [
            (29.7604, -95.3698),  # Downtown Houston
            (29.5997, -95.0727),  # Clear Lake
            (30.0599, -95.5555),  # The Woodlands
        ]

        san_antonio_flood_zones = [
            (29.4241, -98.4936),  # Downtown San Antonio
            (29.5369, -98.6131),  # Stone Oak
        ]

        dallas_flood_zones = [
            (32.7767, -96.7970),  # Downtown Dallas
            (32.9483, -96.7297),  # Addison
        ]

        all_flood_zones = (
            houston_flood_zones + san_antonio_flood_zones + dallas_flood_zones
        )

        # Calculate minimum distance to known flood zones
        min_distance = float("inf")
        for zone_lat, zone_lon in all_flood_zones:
            distance = ((latitude - zone_lat) ** 2 + (longitude - zone_lon) ** 2) ** 0.5
            min_distance = min(min_distance, distance)

        # Assign flood zone based on distance (simplified)
        if min_distance < 0.05:  # ~3 miles
            return "AE", "HIGH"
        elif min_distance < 0.15:  # ~10 miles
            return "X", "MODERATE"
        else:
            return "X", "LOW"

    def calculate_demand_pressure(self, permit_ids: Optional[List[int]] = None) -> int:
        """Calculate demand pressure scores for permits."""
        conn = self._get_db_connection()
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Build query for permits
            where_clause = ""
            params = []

            if permit_ids:
                where_clause = "WHERE p.id = ANY(%s)"
                params.append(permit_ids)

            # Get permits with associated risk data
            cur.execute(
                f"""
                SELECT 
                    p.id, p.issue_date, p.work_class, p.estimated_cost,
                    p.latitude, p.longitude, p.trade_types,
                    fr.flood_risk_level, fr.flood_zone,
                    COALESCE(dp.calculation_version, '0') as current_version
                FROM permits p
                LEFT JOIN flood_risk fr ON p.id = fr.permit_id
                LEFT JOIN demand_pressure dp ON p.id = dp.permit_id
                {where_clause}
                AND (dp.id IS NULL OR dp.calculation_version != '1.0')  -- Recalc if version changed
                LIMIT 5000
            """,
                params,
            )

            permits = cur.fetchall()

            if not permits:
                logger.info("No permits need demand pressure calculation")
                return 0

            logger.info(f"Calculating demand pressure for {len(permits)} permits")

            # Get current weather alerts for context
            cur.execute(
                """
                SELECT event_type, severity, urgency, areas
                FROM weather_alerts
                WHERE effective_time <= NOW() AND (expires_time IS NULL OR expires_time > NOW())
            """
            )
            active_alerts = cur.fetchall()

            demand_pressure_records = []

            for permit in permits:
                scores = self._calculate_individual_demand_pressure(
                    permit, active_alerts
                )
                demand_pressure_records.append(
                    {
                        "permit_id": permit["id"],
                        **scores,
                        "calculation_version": "1.0",
                        "factors_used": Json(
                            {
                                "flood_risk_included": permit["flood_risk_level"]
                                is not None,
                                "weather_alerts_count": len(active_alerts),
                                "has_coordinates": permit["latitude"] is not None,
                                "has_cost_estimate": permit["estimated_cost"]
                                is not None,
                            }
                        ),
                    }
                )

            # Batch upsert demand pressure data
            if demand_pressure_records:
                upsert_sql = """
                    INSERT INTO demand_pressure (
                        permit_id, flood_risk_score, weather_risk_score, seasonal_factor,
                        market_density_factor, total_risk_score, demand_pressure_score,
                        urgency_multiplier, calculation_version, factors_used
                    ) VALUES (
                        %(permit_id)s, %(flood_risk_score)s, %(weather_risk_score)s, %(seasonal_factor)s,
                        %(market_density_factor)s, %(total_risk_score)s, %(demand_pressure_score)s,
                        %(urgency_multiplier)s, %(calculation_version)s, %(factors_used)s
                    )
                    ON CONFLICT (permit_id) DO UPDATE SET
                        flood_risk_score = EXCLUDED.flood_risk_score,
                        weather_risk_score = EXCLUDED.weather_risk_score,
                        seasonal_factor = EXCLUDED.seasonal_factor,
                        market_density_factor = EXCLUDED.market_density_factor,
                        total_risk_score = EXCLUDED.total_risk_score,
                        demand_pressure_score = EXCLUDED.demand_pressure_score,
                        urgency_multiplier = EXCLUDED.urgency_multiplier,
                        calculation_version = EXCLUDED.calculation_version,
                        factors_used = EXCLUDED.factors_used,
                        calculated_at = NOW()
                """

                cur.executemany(upsert_sql, demand_pressure_records)
                conn.commit()

                rows_affected = cur.rowcount
                logger.info(f"Calculated demand pressure for {rows_affected} permits")
                return rows_affected

            return 0

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to calculate demand pressure: {e}")
            raise
        finally:
            conn.close()

    def _calculate_individual_demand_pressure(
        self, permit: Dict[str, Any], active_alerts: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate demand pressure scores for a single permit."""

        # 1. Flood Risk Score (0-1)
        flood_risk_score = 0.0
        flood_risk_level = permit.get("flood_risk_level")
        if flood_risk_level == "HIGH":
            flood_risk_score = 1.0
        elif flood_risk_level == "MODERATE":
            flood_risk_score = 0.6
        elif flood_risk_level == "LOW":
            flood_risk_score = 0.2

        # 2. Weather Risk Score (0-1)
        weather_risk_score = 0.0
        severity_weights = {
            "Extreme": 1.0,
            "Severe": 0.8,
            "Moderate": 0.5,
            "Minor": 0.2,
        }
        urgency_weights = {"Immediate": 1.0, "Expected": 0.7, "Future": 0.3}

        for alert in active_alerts:
            severity_score = severity_weights.get(alert.get("severity"), 0.3)
            urgency_score = urgency_weights.get(alert.get("urgency"), 0.3)
            alert_score = (severity_score + urgency_score) / 2
            weather_risk_score = max(weather_risk_score, alert_score)

        # 3. Seasonal Factor (0.5-1.5)
        seasonal_factor = self._calculate_seasonal_factor(permit.get("issue_date"))

        # 4. Market Density Factor (0.8-1.2)
        market_density_factor = self._calculate_market_density_factor(
            permit.get("latitude"), permit.get("longitude")
        )

        # 5. Combined Risk Score
        base_risk = (flood_risk_score * 0.4) + (weather_risk_score * 0.6)
        total_risk_score = base_risk * seasonal_factor * market_density_factor

        # 6. Demand Pressure Score (incorporates trade types and cost)
        trade_multiplier = self._calculate_trade_multiplier(
            permit.get("trade_types", [])
        )
        cost_multiplier = self._calculate_cost_multiplier(permit.get("estimated_cost"))

        demand_pressure_score = total_risk_score * trade_multiplier * cost_multiplier

        # 7. Urgency Multiplier (for time-sensitive factors)
        urgency_multiplier = 1.0
        if weather_risk_score > 0.7:  # High weather risk
            urgency_multiplier = 1.5
        elif flood_risk_score > 0.8:  # High flood risk
            urgency_multiplier = 1.3

        return {
            "flood_risk_score": round(flood_risk_score, 3),
            "weather_risk_score": round(weather_risk_score, 3),
            "seasonal_factor": round(seasonal_factor, 3),
            "market_density_factor": round(market_density_factor, 3),
            "total_risk_score": round(total_risk_score, 3),
            "demand_pressure_score": round(demand_pressure_score, 3),
            "urgency_multiplier": round(urgency_multiplier, 3),
        }

    def _calculate_seasonal_factor(self, issue_date: datetime) -> float:
        """Calculate seasonal demand factor."""
        if not issue_date:
            return 1.0

        month = issue_date.month

        # Texas seasonal patterns:
        # Spring (Mar-May): High demand for roofing, HVAC prep
        # Summer (Jun-Aug): Peak HVAC, pool work
        # Fall (Sep-Nov): Roofing, preparation for winter
        # Winter (Dec-Feb): Lower overall activity, indoor work

        seasonal_factors = {
            1: 0.7,
            2: 0.6,
            3: 1.1,  # Winter -> Spring
            4: 1.3,
            5: 1.4,
            6: 1.5,  # Spring -> Summer
            7: 1.5,
            8: 1.4,
            9: 1.2,  # Summer -> Fall
            10: 1.1,
            11: 0.9,
            12: 0.8,  # Fall -> Winter
        }

        return seasonal_factors.get(month, 1.0)

    def _calculate_market_density_factor(
        self, latitude: Optional[float], longitude: Optional[float]
    ) -> float:
        """Calculate market density factor based on location."""
        if not latitude or not longitude:
            return 1.0

        # Major Texas metro areas (higher density = more competition = lower factor)
        metro_centers = {
            "Houston": (29.7604, -95.3698, 0.9),
            "Dallas": (32.7767, -96.7970, 0.9),
            "San Antonio": (29.4241, -98.4936, 0.95),
            "Austin": (30.2672, -97.7431, 0.9),
            "Fort Worth": (32.7555, -97.3308, 0.95),
        }

        min_factor = 1.2  # Rural/suburban areas have higher opportunity

        for city, (city_lat, city_lon, density_factor) in metro_centers.items():
            distance = ((latitude - city_lat) ** 2 + (longitude - city_lon) ** 2) ** 0.5
            if distance < 0.2:  # Within ~15 miles
                return density_factor

        return min_factor

    def _calculate_trade_multiplier(self, trade_types: List[str]) -> float:
        """Calculate multiplier based on trade types involved."""
        if not trade_types:
            return 1.0

        # Trade urgency weights
        trade_weights = {
            "ROOFING": 1.4,  # Weather-critical
            "HVAC": 1.3,  # Comfort-critical
            "ELECTRICAL": 1.2,  # Safety-critical
            "PLUMBING": 1.2,  # Essential service
            "POOL": 1.1,  # Seasonal
            "FLOORING": 1.0,  # Standard
            "PAINTING": 0.9,  # Cosmetic
            "FENCING": 0.9,  # Non-urgent
        }

        max_weight = max(trade_weights.get(trade, 1.0) for trade in trade_types)
        return max_weight

    def _calculate_cost_multiplier(self, estimated_cost: Optional[float]) -> float:
        """Calculate multiplier based on project cost."""
        if not estimated_cost or estimated_cost <= 0:
            return 1.0

        # Higher value projects generally have higher urgency
        if estimated_cost >= 100000:  # $100K+
            return 1.3
        elif estimated_cost >= 50000:  # $50K+
            return 1.2
        elif estimated_cost >= 25000:  # $25K+
            return 1.1
        elif estimated_cost >= 10000:  # $10K+
            return 1.0
        else:  # < $10K
            return 0.9

    def run_risk_analysis(
        self, permit_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Run complete risk analysis pipeline."""
        self._ensure_risk_tables_exist()

        results = {}

        try:
            # 1. Fetch and store weather alerts
            logger.info("Fetching weather alerts...")
            alerts = self.fetch_nws_alerts()
            alerts_stored = self.store_weather_alerts(alerts)
            results["weather_alerts_stored"] = alerts_stored

            # 2. Analyze flood risk
            logger.info("Analyzing flood risk...")
            flood_risk_analyzed = self.analyze_flood_risk(permit_ids)
            results["flood_risk_analyzed"] = flood_risk_analyzed

            # 3. Calculate demand pressure
            logger.info("Calculating demand pressure...")
            demand_pressure_calculated = self.calculate_demand_pressure(permit_ids)
            results["demand_pressure_calculated"] = demand_pressure_calculated

            results["status"] = "success"
            results["total_permits_processed"] = max(
                flood_risk_analyzed, demand_pressure_calculated
            )

            logger.info(f"Risk analysis complete: {results}")
            return results

        except Exception as e:
            logger.error(f"Risk analysis failed: {e}")
            results["status"] = "error"
            results["error"] = str(e)
            return results


def main():
    """CLI entry point for risk derivation."""
    import argparse
    import os

    parser = argparse.ArgumentParser(
        description="Derive risk indicators and demand pressure"
    )
    parser.add_argument(
        "--permit-ids", nargs="+", type=int, help="Specific permit IDs to process"
    )
    parser.add_argument(
        "--sources-config",
        default="config/sources_tx.yaml",
        help="Path to sources configuration file",
    )
    parser.add_argument(
        "--db-url", help="PostgreSQL connection URL (or set DATABASE_URL env var)"
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Get database URL
    db_url = args.db_url or os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("Database URL required (--db-url or DATABASE_URL env var)")
        return 1

    try:
        deriver = RiskDeriver(db_url, args.sources_config)
        result = deriver.run_risk_analysis(permit_ids=args.permit_ids)

        print(json.dumps(result, indent=2, default=str))

        return 0 if result.get("status") == "success" else 1

    except Exception as e:
        logger.error(f"Risk derivation failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
