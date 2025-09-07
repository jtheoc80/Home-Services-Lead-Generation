#!/usr/bin/env python3
"""
ETL Freshness Check Script

Checks the freshness of ETL processes by querying the Supabase API for the count
of rows issued in the last 24 hours. Uses the content-range header to get the count.

Required Environment Variables:
- SUPABASE_URL: Supabase project URL
- SUPABASE_SERVICE_ROLE_KEY: Supabase service role key

Output: Count of rows from today using the content-range header
"""

import os
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone
import sys
import json


def main():
    """Check ETL freshness by querying Supabase API for recent permit counts."""

    # Get required environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not service_role_key:
        print(
            "❌ Missing required environment variables: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY"
        )
        sys.exit(1)

    # Calculate 24 hours ago timestamp
    twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
    iso_timestamp = twenty_four_hours_ago.isoformat().replace("+00:00", "Z")

    try:
        # Construct the Supabase REST API URL for permits count
        # Filter for permits issued in the last 24 hours
        base_url = supabase_url.rstrip("/")

        # Build query parameters for filtering by issue_date in the last 24 hours
        params = {
            "select": "id",  # Only select id to minimize data transfer
            "issue_date": f"gte.{iso_timestamp}",  # Filter for issue_date >= 24 hours ago
            "limit": "1",  # We only need the count, not the actual data
        }

        query_string = urllib.parse.urlencode(params)
        api_url = f"{base_url}/rest/v1/permits?{query_string}"

        print(f"🔍 Checking ETL freshness: permits issued since {iso_timestamp}")
        print(f"📡 Querying: {api_url}")

        # Create request with proper headers
        req = urllib.request.Request(api_url)
        req.add_header("Authorization", f"Bearer {service_role_key}")
        req.add_header("apikey", service_role_key)
        req.add_header("Accept", "application/json")
        req.add_header(
            "Prefer", "count=exact"
        )  # Request exact count in content-range header

        # Send the GET request
        with urllib.request.urlopen(req, timeout=30) as response:
            # Parse the content-range header to get the count
            content_range = response.headers.get("content-range", "")

            if content_range:
                # content-range format: "0-0/123" where 123 is the total count
                if "/" in content_range:
                    count_str = content_range.split("/")[-1]
                    try:
                        count = int(count_str)
                        print(
                            f"✅ ETL freshness check complete: {count} permits issued in last 24 hours"
                        )
                        print(f"📊 Count from content-range header: {count}")
                        return count
                    except ValueError:
                        print(
                            f"⚠️  Could not parse count from content-range: {content_range}"
                        )
                        return 0
                else:
                    print(f"⚠️  Unexpected content-range format: {content_range}")
                    return 0
            else:
                print("⚠️  No content-range header found in response")
                # Fallback: try to parse response body if it's a small dataset
                data = json.loads(response.read().decode("utf-8"))
                count = len(data) if isinstance(data, list) else 0
                print(f"📊 Fallback count from response body: {count}")
                return count

    except urllib.error.HTTPError as e:
        print(f"❌ HTTP error checking ETL freshness: {e.code} - {e.reason}")
        if e.code == 401:
            print("   Check SUPABASE_SERVICE_ROLE_KEY is correct")
        elif e.code == 404:
            print("   Check SUPABASE_URL and permits table exists")
        return 0
    except urllib.error.URLError as e:
        print(f"❌ Connection error checking ETL freshness: {e.reason}")
        return 0
    except Exception as e:
        print(f"❌ Unexpected error checking ETL freshness: {e}")
        return 0


if __name__ == "__main__":
    count = main()
    sys.exit(0 if count > 0 else 1)
