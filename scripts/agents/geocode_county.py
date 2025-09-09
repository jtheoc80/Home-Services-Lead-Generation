# Geocode via US Census (no key), derive county if possible. Lightweight cache in-memory.
# Usage: python scripts/agents/geocode_county.py < artifacts/normalized.ndjson > artifacts/geocoded.ndjson
import sys
import json
import time
import requests
from urllib.parse import quote

cache = {}


def geocode_one(q):
    if q in cache:
        return cache[q]
    url = f"https://geocoding.geo.census.gov/geocoder/locations/onelineaddress?address={quote(q)}&benchmark=2020&format=json"
    try:
        r = requests.get(url, timeout=15).json()
        m = (r.get("result", {}).get("addressMatches") or [None])[0]
        if not m:
            cache[q] = (None, None, None)
            return cache[q]
        lat, lon = m["coordinates"]["y"], m["coordinates"]["x"]
        county = None
        geos = m.get("geographies") or {}
        if isinstance(geos, dict):
            counties = geos.get("Counties") or []
            if counties:
                county = counties[0].get("NAME")
        cache[q] = (lat, lon, county)
        return cache[q]
    except Exception:
        cache[q] = (None, None, None)
        return cache[q]


for line in sys.stdin:
    row = json.loads(line)
    parts = [
        row.get("address") or "",
        row.get("city") or "",
        row.get("state") or "",
        row.get("zipcode") or "",
    ]
    q = ", ".join([p for p in parts if p]).strip()
    if q:
        lat, lon, county = geocode_one(q)
        time.sleep(0.1)
        row["lat"], row["lon"], row["county"] = lat, lon, county or row.get("county")
    print(json.dumps(row, ensure_ascii=False))
