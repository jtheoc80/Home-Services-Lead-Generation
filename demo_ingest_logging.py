#!/usr/bin/env python3
"""
Demo script showing end-to-end ingest logging functionality.

This demonstrates:
1. Creating a trace ID
2. Logging steps through the ingestion pipeline
3. Retrieving trace logs via API
"""

import os
import sys
import uuid
import json
import time
from typing import Dict, Any

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def demo_ingest_tracer():
    """Demonstrate IngestTracer functionality."""
    print("🔍 Demonstrating IngestTracer functionality")
    print("=" * 50)
    
    try:
        from app.ingest_logger import IngestTracer
        
        # Demo complete workflow
        with IngestTracer() as tracer:
            print(f"📋 Starting trace: {tracer.trace_id}")
            
            # Simulate fetch_page step
            print("1. 📥 Fetching page...")
            success = tracer.log("fetch_page", True, {
                "url": "https://permits.example.com/search",
                "records_found": 42,
                "fetch_time_ms": 250
            })
            print(f"   {'✓' if success else '✗'} Logged fetch_page step")
            
            # Simulate parse step
            print("2. 📊 Parsing data...")
            success = tracer.log("parse", True, {
                "permits_parsed": 40,
                "parse_errors": 2,
                "parse_time_ms": 150
            })
            print(f"   {'✓' if success else '✗'} Logged parse step")
            
            # Simulate upsert step
            print("3. 🔄 Upserting to database...")
            success = tracer.log("upsert", True, {
                "records_inserted": 35,
                "records_updated": 5,
                "duplicates_skipped": 2,
                "upsert_time_ms": 500
            })
            print(f"   {'✓' if success else '✗'} Logged upsert step")
            
            # Simulate db_insert step
            print("4. 💾 Final database operations...")
            success = tracer.log("db_insert", True, {
                "final_count": 40,
                "total_time_ms": 900,
                "status": "completed"
            })
            print(f"   {'✓' if success else '✗'} Logged db_insert step")
            
            print(f"\n✅ Completed trace with {len(tracer.stages_logged)} stages")
            return tracer.trace_id
            
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return None

def demo_api_integration(trace_id: str):
    """Demonstrate API integration for trace retrieval."""
    print(f"\n🌐 Demonstrating API trace retrieval")
    print("=" * 50)
    
    try:
        import requests
        
        # Try to retrieve trace via API
        url = f"http://localhost:8000/api/leads/trace/{trace_id}"
        headers = {"X-Debug-Key": "test-debug-key-123"}
        
        print(f"📡 Requesting: {url}")
        print(f"🔑 Debug key: {headers['X-Debug-Key']}")
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API returned {data.get('total_logs', 0)} logs")
            
            # Pretty print the logs
            if data.get('logs'):
                print("\n📝 Trace logs:")
                for i, log in enumerate(data['logs'], 1):
                    print(f"   {i}. {log.get('stage', 'unknown')} - {'✓' if log.get('ok') else '✗'}")
                    if log.get('details'):
                        print(f"      Details: {json.dumps(log['details'], indent=6)}")
            
            return True
        else:
            print(f"❌ API returned {response.status_code}: {response.text}")
            return False
            
    except requests.ConnectionError:
        print("⚠️  API server not running - start with: cd backend && python main.py")
        return False
    except Exception as e:
        print(f"❌ API demo failed: {e}")
        return False

def demo_scraper_integration():
    """Demonstrate scraper integration with logging."""
    print(f"\n🔧 Demonstrating scraper integration")
    print("=" * 50)
    
    try:
        # This would be how to integrate with actual scrapers
        trace_id = str(uuid.uuid4())
        print(f"📋 Simulated scraper trace: {trace_id}")
        
        # Import the logging utilities
        from app.ingest_logger import log_ingest_step
        
        # Simulate scraper workflow
        stages = [
            ("fetch_page", True, {"jurisdiction": "Houston", "permits_found": 25}),
            ("parse", True, {"permits_parsed": 23, "errors": 2}),
            ("upsert", True, {"inserted": 20, "updated": 3}),
            ("db_insert", True, {"final_count": 23})
        ]
        
        for stage, ok, details in stages:
            success = log_ingest_step(trace_id, stage, ok, details)
            print(f"   {'✓' if success else '✗'} {stage}: {details}")
        
        print(f"✅ Scraper simulation completed for trace: {trace_id}")
        return trace_id
        
    except Exception as e:
        print(f"❌ Scraper demo failed: {e}")
        return None

def main():
    """Run the complete demo."""
    print("🏠 Home Services Lead Generation - Ingest Logging Demo")
    print("=" * 60)
    
    # Demo 1: IngestTracer
    trace_id = demo_ingest_tracer()
    
    # Demo 2: API integration (if server is running)
    if trace_id:
        demo_api_integration(trace_id)
    
    # Demo 3: Scraper integration
    demo_scraper_integration()
    
    print("\n🎉 Demo completed!")
    print("\nTo test the API endpoint:")
    print("1. Start the server: cd backend && python main.py")
    print("2. Set environment variables (especially X_DEBUG_KEY)")
    if trace_id:
        print(f"3. Visit: http://localhost:8000/api/leads/trace/{trace_id}")
        print(f"   With header: X-Debug-Key: test-debug-key-123")

if __name__ == "__main__":
    main()