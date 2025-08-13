#!/usr/bin/env python3
"""
Test script for Dallas, Austin, and Arlington API endpoints
Based on the curl commands from the problem statement.
"""

import requests
import json
import time
from typing import Dict, Any, Optional


def test_dallas_socrata():
    """Test Dallas Socrata API endpoints."""
    print("🌟 Testing Dallas Socrata API")
    print("-" * 40)
    
    base_url = "https://www.dallasopendata.com/resource/e7gq-4sah.json"
    
    # Test count query
    try:
        count_url = f"{base_url}?$select=count(1)"
        print(f"📊 Count URL: {count_url}")
        
        response = requests.get(count_url, timeout=30)
        if response.status_code == 200:
            count_data = response.json()
            print(f"✓ Count query successful: {count_data}")
        else:
            print(f"✗ Count query failed: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Count query error: {e}")
    
    # Test sample query
    try:
        sample_url = f"{base_url}?$limit=5"
        print(f"📝 Sample URL: {sample_url}")
        
        response = requests.get(sample_url, timeout=30)
        if response.status_code == 200:
            sample_data = response.json()
            print(f"✓ Sample query successful: {len(sample_data)} records")
            if sample_data:
                print(f"   First record keys: {list(sample_data[0].keys())}")
        else:
            print(f"✗ Sample query failed: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Sample query error: {e}")


def test_austin_socrata():
    """Test Austin Socrata API endpoints."""
    print("\n🌟 Testing Austin Socrata API")
    print("-" * 40)
    
    base_url = "https://data.austintexas.gov/resource/3syk-w9eu.json"
    
    # Test count query
    try:
        count_url = f"{base_url}?$select=count(1)"
        print(f"📊 Count URL: {count_url}")
        
        response = requests.get(count_url, timeout=30)
        if response.status_code == 200:
            count_data = response.json()
            print(f"✓ Count query successful: {count_data}")
        else:
            print(f"✗ Count query failed: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Count query error: {e}")
    
    # Test sample query
    try:
        sample_url = f"{base_url}?$limit=5"
        print(f"📝 Sample URL: {sample_url}")
        
        response = requests.get(sample_url, timeout=30)
        if response.status_code == 200:
            sample_data = response.json()
            print(f"✓ Sample query successful: {len(sample_data)} records")
            if sample_data:
                print(f"   First record keys: {list(sample_data[0].keys())}")
        else:
            print(f"✗ Sample query failed: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Sample query error: {e}")


def test_arlington_arcgis():
    """Test Arlington ArcGIS API endpoints."""
    print("\n🌟 Testing Arlington ArcGIS API")
    print("-" * 40)
    
    base_url = "https://gis2.arlingtontx.gov/agsext2/rest/services/OpenData/OD_Property/MapServer/1/query"
    
    # Test count query
    try:
        count_params = {
            'where': '1=1',
            'returnCountOnly': 'true',
            'f': 'json'
        }
        print(f"📊 Count URL: {base_url}")
        print(f"   Params: {count_params}")
        
        response = requests.get(base_url, params=count_params, timeout=30)
        if response.status_code == 200:
            count_data = response.json()
            print(f"✓ Count query successful: {count_data}")
        else:
            print(f"✗ Count query failed: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Count query error: {e}")
    
    # Test sample query
    try:
        sample_params = {
            'where': '1=1',
            'outFields': '*',
            'resultRecordCount': '5',
            'f': 'json'
        }
        print(f"📝 Sample URL: {base_url}")
        print(f"   Params: {sample_params}")
        
        response = requests.get(base_url, params=sample_params, timeout=30)
        if response.status_code == 200:
            sample_data = response.json()
            features = sample_data.get('features', [])
            print(f"✓ Sample query successful: {len(features)} features")
            if features:
                attributes = features[0].get('attributes', {})
                print(f"   First feature attributes: {list(attributes.keys())}")
        else:
            print(f"✗ Sample query failed: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Sample query error: {e}")


def test_api_integration():
    """Test integration with existing adapters."""
    print("\n🌟 Testing API Integration with Adapters")
    print("-" * 40)
    
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent))
        
        from ingest.socrata import fetch
        from ingest.arcgis import query_layer
        
        # Test Dallas with fetch function
        print("Testing Dallas with ingest.socrata.fetch...")
        try:
            dallas_data = fetch(
                domain="www.dallasopendata.com",
                dataset="e7gq-4sah",
                limit=5
            )
            print(f"✓ Dallas fetch successful: {len(dallas_data)} records")
        except Exception as e:
            print(f"✗ Dallas fetch failed: {e}")
        
        # Test Austin with fetch function
        print("Testing Austin with ingest.socrata.fetch...")
        try:
            austin_data = fetch(
                domain="data.austintexas.gov",
                dataset="3syk-w9eu",
                limit=5
            )
            print(f"✓ Austin fetch successful: {len(austin_data)} records")
        except Exception as e:
            print(f"✗ Austin fetch failed: {e}")
        
        # Test Arlington with query_layer function
        print("Testing Arlington with ingest.arcgis.query_layer...")
        try:
            arlington_data = query_layer(
                base_url="https://gis2.arlingtontx.gov/agsext2/rest/services/OpenData/OD_Property/MapServer",
                layer=1,
                result_record_count=5
            )
            features = arlington_data.get('features', [])
            print(f"✓ Arlington query successful: {len(features)} features")
        except Exception as e:
            print(f"✗ Arlington query failed: {e}")
            
    except ImportError as e:
        print(f"✗ Failed to import adapters: {e}")


if __name__ == "__main__":
    print("🏠 Texas Permits API Endpoint Testing")
    print("=" * 50)
    
    test_dallas_socrata()
    test_austin_socrata()
    test_arlington_arcgis()
    test_api_integration()
    
    print("\n" + "=" * 50)
    print("API endpoint testing completed!")