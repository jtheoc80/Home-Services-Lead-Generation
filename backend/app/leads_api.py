#!/usr/bin/env python3
"""
Leads API for LeadLedgerPro multi-region system.

Provides region/jurisdiction-aware lead querying with optional PostGIS support
for geographic filtering.
"""

import os
import logging
import math
from typing import List, Dict, Any, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class LeadsAPI:
    """API for querying leads with regional filtering."""

    def __init__(self, db_url: str):
        """Initialize API with database connection."""
        self.db_url = db_url
        self.use_postgis = os.environ.get("USE_POSTGIS", "false").lower() == "true"

    def connect_db(self):
        """Create database connection."""
        return psycopg2.connect(self.db_url)

    def _haversine_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Calculate distance between two points using Haversine formula (km)."""
        R = 6371  # Earth's radius in kilometers

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(
            math.radians(lat1)
        ) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) * math.sin(dlon / 2)

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def get_leads(
        self,
        region: Optional[str] = None,
        state: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        radius_km: Optional[float] = None,
        min_score: Optional[float] = None,
        trade_tags: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Query leads with regional and geographic filters.

        Args:
            region: Region slug to filter by
            state: State code to filter by (e.g., 'TX')
            jurisdiction: Jurisdiction slug to filter by
            lat: Latitude for geographic search
            lon: Longitude for geographic search
            radius_km: Search radius in kilometers (requires lat/lon)
            min_score: Minimum lead score threshold
            trade_tags: List of trade tags to filter by
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            Dict with 'leads' list and 'total' count
        """

        conn = self.connect_db()
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Build WHERE clause
            where_conditions = []
            params = {}

            if region:
                where_conditions.append("r.slug = %(region)s")
                params["region"] = region

            if state:
                where_conditions.append("l.state = %(state)s")
                params["state"] = state

            if jurisdiction:
                where_conditions.append("j.slug = %(jurisdiction)s")
                params["jurisdiction"] = jurisdiction

            if min_score is not None:
                where_conditions.append("l.lead_score >= %(min_score)s")
                params["min_score"] = min_score

            if trade_tags:
                where_conditions.append("l.trade_tags && %(trade_tags)s")
                params["trade_tags"] = trade_tags

            # Geographic filtering
            geo_select = ""
            geo_where = ""
            if lat is not None and lon is not None and radius_km is not None:
                if self.use_postgis:
                    # Use PostGIS ST_DWithin for efficient spatial queries
                    geo_where = """
                        AND ST_DWithin(
                            l.geom::geography,
                            ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)::geography,
                            %(radius_m)s
                        )
                    """
                    params["lat"] = lat
                    params["lon"] = lon
                    params["radius_m"] = radius_km * 1000  # Convert to meters

                    geo_select = ", ST_Distance(l.geom::geography, ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)::geography) / 1000.0 as distance_km"
                else:
                    # Fallback to basic lat/lon filtering (less efficient but works without PostGIS)
                    # Simple bounding box filter first
                    lat_delta = radius_km / 111.0  # Rough km to degrees conversion
                    lon_delta = radius_km / (111.0 * math.cos(math.radians(lat)))

                    where_conditions.append(
                        """
                        (l.lat BETWEEN %(lat_min)s AND %(lat_max)s 
                         AND l.lon BETWEEN %(lon_min)s AND %(lon_max)s)
                    """
                    )

                    params["lat_min"] = lat - lat_delta
                    params["lat_max"] = lat + lat_delta
                    params["lon_min"] = lon - lon_delta
                    params["lon_max"] = lon + lon_delta

            where_clause = (
                "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            )

            # Build the query
            base_query = f"""
                SELECT 
                    l.*,
                    r.slug as region_slug,
                    r.name as region_name,
                    r.level as region_level,
                    j.slug as jurisdiction_slug,
                    j.name as jurisdiction_name
                    {geo_select}
                FROM leads l
                LEFT JOIN jurisdictions j ON l.jurisdiction_id = j.id
                LEFT JOIN regions r ON l.region_id = r.id
                {where_clause}
                {geo_where}
            """

            # Count query for pagination
            count_query = f"""
                SELECT COUNT(*) as total
                FROM leads l
                LEFT JOIN jurisdictions j ON l.jurisdiction_id = j.id
                LEFT JOIN regions r ON l.region_id = r.id
                {where_clause}
                {geo_where}
            """

            # Get total count
            cur.execute(count_query, params)
            total = cur.fetchone()["total"]

            # Get paginated results
            params["limit"] = limit
            params["offset"] = offset

            results_query = (
                base_query
                + """
                ORDER BY l.lead_score DESC NULLS LAST, l.created_at DESC
                LIMIT %(limit)s OFFSET %(offset)s
            """
            )

            cur.execute(results_query, params)
            leads = cur.fetchall()

            # If using Haversine fallback, calculate distances and filter
            if (
                lat is not None
                and lon is not None
                and radius_km is not None
                and not self.use_postgis
            ):
                filtered_leads = []
                for lead in leads:
                    if lead["lat"] and lead["lon"]:
                        distance = self._haversine_distance(
                            lat, lon, lead["lat"], lead["lon"]
                        )
                        if distance <= radius_km:
                            lead_dict = dict(lead)
                            lead_dict["distance_km"] = distance
                            filtered_leads.append(lead_dict)
                leads = filtered_leads

            # Convert to list of dicts for JSON serialization
            leads_list = [dict(lead) for lead in leads]

            return {
                "leads": leads_list,
                "total": total,
                "limit": limit,
                "offset": offset,
                "filters": {
                    "region": region,
                    "state": state,
                    "jurisdiction": jurisdiction,
                    "lat": lat,
                    "lon": lon,
                    "radius_km": radius_km,
                    "min_score": min_score,
                    "trade_tags": trade_tags,
                },
            }

        except Exception as e:
            logger.error(f"Error querying leads: {e}")
            raise
        finally:
            conn.close()

    def get_regions(self) -> List[Dict[str, Any]]:
        """Get all regions."""
        conn = self.connect_db()
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                """
                SELECT r.*, 
                       COUNT(j.id) as jurisdiction_count,
                       COUNT(l.id) as lead_count
                FROM regions r
                LEFT JOIN jurisdictions j ON r.id = j.region_id
                LEFT JOIN leads l ON r.id = l.region_id
                GROUP BY r.id, r.slug, r.name, r.level, r.parent_id, r.created_at
                ORDER BY r.level, r.name
            """
            )
            return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def get_jurisdictions(
        self, region_slug: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get jurisdictions, optionally filtered by region."""
        conn = self.connect_db()
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            query = """
                SELECT j.*,
                       r.slug as region_slug,
                       r.name as region_name,
                       COUNT(l.id) as lead_count
                FROM jurisdictions j
                LEFT JOIN regions r ON j.region_id = r.id
                LEFT JOIN leads l ON j.id = l.jurisdiction_id
            """

            params = {}
            if region_slug:
                query += " WHERE r.slug = %(region_slug)s"
                params["region_slug"] = region_slug

            query += """
                GROUP BY j.id, j.slug, j.name, j.region_id, j.state, j.fips, 
                         j.timezone, j.data_provider, j.source_config, j.active, j.created_at,
                         r.slug, r.name
                ORDER BY j.state, j.name
            """

            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()


def main():
    """CLI interface for testing the leads API."""
    import sys
    import json
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Query leads API")
    parser.add_argument("--region", help="Region slug")
    parser.add_argument("--state", help="State code")
    parser.add_argument("--jurisdiction", help="Jurisdiction slug")
    parser.add_argument("--lat", type=float, help="Latitude")
    parser.add_argument("--lon", type=float, help="Longitude")
    parser.add_argument("--radius", type=float, help="Radius in km")
    parser.add_argument("--min-score", type=float, help="Minimum score")
    parser.add_argument("--trade-tags", nargs="+", help="Trade tags")
    parser.add_argument("--limit", type=int, default=10, help="Result limit")
    parser.add_argument("--list-regions", action="store_true", help="List all regions")
    parser.add_argument(
        "--list-jurisdictions", action="store_true", help="List all jurisdictions"
    )

    args = parser.parse_args()

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)

    api = LeadsAPI(db_url)

    try:
        if args.list_regions:
            regions = api.get_regions()
            print(json.dumps(regions, indent=2, default=str))
        elif args.list_jurisdictions:
            jurisdictions = api.get_jurisdictions(args.region)
            print(json.dumps(jurisdictions, indent=2, default=str))
        else:
            result = api.get_leads(
                region=args.region,
                state=args.state,
                jurisdiction=args.jurisdiction,
                lat=args.lat,
                lon=args.lon,
                radius_km=args.radius,
                min_score=args.min_score,
                trade_tags=args.trade_tags,
                limit=args.limit,
            )
            print(json.dumps(result, indent=2, default=str))

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
