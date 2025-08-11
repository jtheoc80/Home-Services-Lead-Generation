"""
Geographic API module for Houston area focus features.

Provides endpoints to:
- List available geographic areas (ZIP codes, council districts, super neighborhoods)
- Save/retrieve user focus area preferences
- Filter permits by geographic areas
"""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class FocusArea:
    """User's geographic focus area configuration."""
    account_id: str
    mode: str  # 'zip' | 'council' | 'neighborhood' | 'radius'
    codes: Optional[List[str]] = None  # for zip/council/neighborhood modes
    center_lat: Optional[float] = None  # for radius mode
    center_lon: Optional[float] = None  # for radius mode
    radius_miles: Optional[float] = None  # for radius mode
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class GeoAPI:
    """API for geographic area operations."""
    
    def __init__(self, db_path: str = None, geo_data_path: str = None):
        db_path = db_path or os.environ.get("PERMITS_DB_PATH", "data/permits/permits.db")
        geo_data_path = geo_data_path or os.environ.get("HOUSTON_GEO_DATA_PATH", "data/geo/houston")
        self.db_path = Path(db_path)
        self.geo_data_path = Path(geo_data_path)
    
    def get_available_areas(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Get all available geographic areas for selection.
        
        Returns:
            Dict with keys 'zips', 'council_districts', 'super_neighborhoods'
            Each containing list of areas with 'name' and 'code' fields.
        """
        areas = {}
        
        # Load ZIP codes
        zip_file = self.geo_data_path / "zips.geojson"
        if zip_file.exists():
            with open(zip_file) as f:
                data = json.load(f)
                areas['zips'] = [
                    {"name": feature["properties"]["name"], "code": feature["properties"]["code"]}
                    for feature in data["features"]
                ]
        
        # Load council districts
        council_file = self.geo_data_path / "council_districts.geojson"
        if council_file.exists():
            with open(council_file) as f:
                data = json.load(f)
                areas['council_districts'] = [
                    {"name": feature["properties"]["name"], "code": feature["properties"]["code"]}
                    for feature in data["features"]
                ]
        
        # Load super neighborhoods
        neighborhoods_file = self.geo_data_path / "super_neighborhoods.geojson"
        if neighborhoods_file.exists():
            with open(neighborhoods_file) as f:
                data = json.load(f)
                areas['super_neighborhoods'] = [
                    {"name": feature["properties"]["name"], "code": feature["properties"]["code"]}
                    for feature in data["features"]
                ]
        
        return areas
    
    def save_focus_area(self, focus_area: FocusArea) -> bool:
        """
        Save user's focus area preferences.
        
        Args:
            focus_area: FocusArea configuration to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now(timezone.utc).isoformat()
            codes_json = json.dumps(focus_area.codes) if focus_area.codes else None
            
            # Upsert focus area
            cursor.execute("""
                INSERT OR REPLACE INTO focus_areas 
                (account_id, mode, codes, center_lat, center_lon, radius_miles, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 
                        COALESCE((SELECT created_at FROM focus_areas WHERE account_id = ?), ?), 
                        ?)
            """, (
                focus_area.account_id,
                focus_area.mode,
                codes_json,
                focus_area.center_lat,
                focus_area.center_lon,
                focus_area.radius_miles,
                focus_area.account_id,  # for COALESCE subquery
                now,  # created_at if new record
                now   # updated_at
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error saving focus area: {e}")
            return False
    
    def get_focus_area(self, account_id: str) -> Optional[FocusArea]:
        """
        Retrieve user's focus area preferences.
        
        Args:
            account_id: User account identifier
            
        Returns:
            FocusArea configuration or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT account_id, mode, codes, center_lat, center_lon, radius_miles, created_at, updated_at
                FROM focus_areas WHERE account_id = ?
            """, (account_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                codes = json.loads(row[2]) if row[2] else None
                return FocusArea(
                    account_id=row[0],
                    mode=row[1],
                    codes=codes,
                    center_lat=row[3],
                    center_lon=row[4],
                    radius_miles=row[5],
                    created_at=row[6],
                    updated_at=row[7]
                )
                
            return None
            
        except Exception as e:
            print(f"Error retrieving focus area: {e}")
            return None
    
    def get_geometry_for_area(self, area_type: str, code: str) -> Optional[Dict]:
        """
        Get GeoJSON geometry for a specific area.
        
        Args:
            area_type: 'zip', 'council', or 'neighborhood'
            code: Area code to look up
            
        Returns:
            GeoJSON geometry or None if not found
        """
        file_mapping = {
            'zip': 'zips.geojson',
            'council': 'council_districts.geojson', 
            'neighborhood': 'super_neighborhoods.geojson'
        }
        
        filename = file_mapping.get(area_type)
        if not filename:
            return None
            
        geo_file = self.geo_data_path / filename
        if not geo_file.exists():
            return None
            
        try:
            with open(geo_file) as f:
                data = json.load(f)
                
            for feature in data["features"]:
                if feature["properties"]["code"] == code:
                    return feature["geometry"]
                    
            return None
            
        except Exception as e:
            print(f"Error loading geometry for {area_type}/{code}: {e}")
            return None
    
    def filter_permits_by_focus_area(self, account_id: str, limit: int = 100) -> List[Dict]:
        """
        Filter permits based on user's focus area preferences.
        
        Args:
            account_id: User account identifier
            limit: Maximum number of results to return
            
        Returns:
            List of permit records matching focus area
        """
        focus_area = self.get_focus_area(account_id)
        if not focus_area:
            # No focus area set, return all permits
            return self._get_all_permits(limit)
        
        if focus_area.mode == 'radius':
            return self._filter_permits_by_radius(
                focus_area.center_lat, 
                focus_area.center_lon, 
                focus_area.radius_miles, 
                limit
            )
        else:
            return self._filter_permits_by_codes(focus_area.codes or [], limit)
    
    def _get_all_permits(self, limit: int) -> List[Dict]:
        """Get all permits without geographic filtering."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM permits 
                ORDER BY scraped_at DESC 
                LIMIT ?
            """, (limit,))
            
            columns = [description[0] for description in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            conn.close()
            return results
            
        except Exception as e:
            print(f"Error fetching permits: {e}")
            return []
    
    def _filter_permits_by_radius(self, center_lat: float, center_lon: float, radius_miles: float, limit: int) -> List[Dict]:
        """Filter permits by radius from center point."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Simple distance calculation using Haversine formula approximation
            # Note: For production, consider using PostGIS or more accurate geospatial library
            cursor.execute("""
                SELECT * FROM permits 
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate bounding box for pre-filter
            # 1 degree latitude ~= 69 miles
            lat_delta = radius_miles / 69.0
            # 1 degree longitude ~= 69 * cos(latitude) miles
            lon_delta = radius_miles / (69.0 * abs(math.cos(math.radians(center_lat))) if abs(math.cos(math.radians(center_lat))) > 0 else 1)
            min_lat = center_lat - lat_delta
            max_lat = center_lat + lat_delta
            min_lon = center_lon - lon_delta
            max_lon = center_lon + lon_delta
            
            # Simple distance calculation using Haversine formula approximation
            # Note: For production, consider using PostGIS or more accurate geospatial library
            cursor.execute("""
                SELECT * FROM permits 
                WHERE latitude IS NOT NULL AND longitude IS NOT NULL
                AND latitude BETWEEN ? AND ?
                AND longitude BETWEEN ? AND ?
                AND (
                    6371 * acos(
                        cos(radians(?)) * cos(radians(latitude)) * cos(radians(longitude) - radians(?)) +
                        sin(radians(?)) * sin(radians(latitude))
                    ) * 0.621371
                ) <= ?
                ORDER BY scraped_at DESC 
                LIMIT ?
            """, (center_lat, center_lon, center_lat, radius_miles, limit))
            
            columns = [description[0] for description in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            conn.close()
            return results
            
        except Exception as e:
            print(f"Error filtering permits by radius: {e}")
            return []
            # Use bounding box to pre-filter permits, then apply Haversine in Python
            # This is much faster for large datasets than calculating distance for every row in SQL
            # Calculate bounding box
            import math
            # Earth radius in miles
            R = 3959.0
            lat_rad = math.radians(center_lat)
            delta_lat = radius_miles / R
            delta_lon = radius_miles / (R * math.cos(lat_rad))
            min_lat = center_lat - math.degrees(delta_lat)
            max_lat = center_lat + math.degrees(delta_lat)
            min_lon = center_lon - math.degrees(delta_lon)
            max_lon = center_lon + math.degrees(delta_lon)
            
            cursor.execute("""
                SELECT * FROM permits
                WHERE latitude IS NOT NULL AND longitude IS NOT NULL
                AND latitude BETWEEN ? AND ?
                AND longitude BETWEEN ? AND ?
                ORDER BY scraped_at DESC
                LIMIT ?
            """, (min_lat, max_lat, min_lon, max_lon, limit * 5))  # fetch more to allow for post-filtering
            
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            conn.close()
            
            # Filter using Haversine in Python
            results = []
            for row in rows:
                record = dict(zip(columns, row))
                lat = record.get("latitude")
                lon = record.get("longitude")
                if lat is not None and lon is not None:
                    distance = self._haversine_distance(center_lat, center_lon, lat, lon)
                    if distance <= radius_miles:
                        record["distance_miles"] = distance
                        results.append(record)
                if len(results) >= limit:
                    break
            return results
        except Exception as e:
            print(f"Error filtering permits by radius: {e}")
            return []
    
    @staticmethod
    def _haversine_distance(lat1, lon1, lat2, lon2):
        """
        Calculate the great-circle distance between two points on the Earth using the Haversine formula.
        Returns distance in miles.
        """
        import math
        R = 3959.0  # Earth radius in miles
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
    
    def _filter_permits_by_codes(self, codes: List[str], limit: int) -> List[Dict]:
        """Filter permits by area codes (ZIP, council district, etc.)."""
        # Note: This is a simplified implementation
        # In a real system, you'd do geospatial intersection queries
        # For now, we'll filter by address containing the ZIP code
        
        if not codes:
            return self._get_all_permits(limit)
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build dynamic query with multiple LIKE conditions
            placeholders = " OR ".join(["address LIKE ?" for _ in codes])
            search_terms = [f"%{code}%" for code in codes]
            
            cursor.execute(f"""
                SELECT * FROM permits 
                WHERE address IS NOT NULL AND ({placeholders})
                ORDER BY scraped_at DESC 
                LIMIT ?
            """, search_terms + [limit])
            
            columns = [description[0] for description in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            conn.close()
            return results
            
        except Exception as e:
            print(f"Error filtering permits by codes: {e}")
            return []


# Example usage functions for testing
def test_geo_api():
    """Test the geographic API functionality."""
    api = GeoAPI()
    
    # Test getting available areas
    print("Available areas:")
    areas = api.get_available_areas()
    for area_type, area_list in areas.items():
        print(f"  {area_type}: {len(area_list)} areas")
        for area in area_list[:2]:  # Show first 2
            print(f"    - {area['name']} ({area['code']})")
    
    # Test saving focus area
    test_focus = FocusArea(
        account_id="test_user_123",
        mode="zip",
        codes=["77008", "77019"]
    )
    
    success = api.save_focus_area(test_focus)
    print(f"\nSaved focus area: {success}")
    
    # Test retrieving focus area
    retrieved = api.get_focus_area("test_user_123")
    if retrieved:
        print(f"Retrieved focus area: {retrieved.mode}, codes: {retrieved.codes}")
    
    # Test filtering permits
    permits = api.filter_permits_by_focus_area("test_user_123", limit=5)
    print(f"\nFound {len(permits)} permits matching focus area")


if __name__ == "__main__":
    test_geo_api()