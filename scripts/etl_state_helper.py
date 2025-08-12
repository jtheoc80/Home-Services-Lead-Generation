#!/usr/bin/env python3
"""
ETL State Helper
Python helper to manage ETL state persistence and querying
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    from supabase import create_client, Client
except ImportError:
    print("Error: supabase library not found. Install with: pip install supabase")
    sys.exit(1)

class ETLStateManager:
    """Manages ETL state persistence in Supabase"""
    
    def __init__(self, supabase_client: Optional[Client] = None):
        if supabase_client:
            self.client = supabase_client
        else:
            # Initialize from environment variables
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            
            if not supabase_url or not supabase_key:
                raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables are required")
            
            self.client = create_client(supabase_url, supabase_key)
    
    def get_last_run(self, source: str, overlap_minutes: int = 1) -> Optional[datetime]:
        """
        Get the last run timestamp for a source with optional overlap
        
        Args:
            source: The ETL source identifier
            overlap_minutes: Minutes to subtract for overlap (default 1)
            
        Returns:
            datetime: The timestamp to query from, or None if no previous run
        """
        try:
            response = self.client.table("etl_state").select("last_run").eq("source", source).single().execute()
            
            if response.data and response.data.get("last_run"):
                last_run = datetime.fromisoformat(response.data["last_run"].replace("Z", "+00:00"))
                # Subtract overlap to avoid gaps
                return last_run - timedelta(minutes=overlap_minutes)
            
            return None
            
        except Exception as e:
            print(f"Warning: Could not get last run for {source}: {e}")
            return None
    
    def update_state(self, 
                    source: str, 
                    status: str,
                    records_processed: int = 0,
                    error_message: Optional[str] = None) -> bool:
        """
        Update the ETL state for a source
        
        Args:
            source: The ETL source identifier
            status: Status of the run ('success', 'failure', 'running')
            records_processed: Number of records processed
            error_message: Error message if failed
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            update_data = {
                "last_run": datetime.utcnow().isoformat(),
                "status": status,
                "records_processed": records_processed,
                "error_message": error_message
            }
            
            # Set last_success if status is success
            if status == "success":
                update_data["last_success"] = update_data["last_run"]
                update_data["error_message"] = None
            
            # Upsert the record
            response = self.client.table("etl_state").upsert(
                {**update_data, "source": source},
                on_conflict="source"
            ).execute()
            
            return True
            
        except Exception as e:
            print(f"Error updating state for {source}: {e}")
            return False
    
    def mark_running(self, source: str) -> bool:
        """Mark a source as currently running"""
        return self.update_state(source, "running")
    
    def mark_success(self, source: str, records_processed: int = 0) -> bool:
        """Mark a source run as successful"""
        return self.update_state(source, "success", records_processed)
    
    def mark_failure(self, source: str, error_message: str) -> bool:
        """Mark a source run as failed"""
        return self.update_state(source, "failure", 0, error_message)
    
    def get_source_status(self, source: str) -> Optional[Dict[str, Any]]:
        """Get full status information for a source"""
        try:
            response = self.client.table("etl_state").select("*").eq("source", source).single().execute()
            return response.data
        except Exception as e:
            print(f"Error getting status for {source}: {e}")
            return None
    
    def list_all_sources(self) -> list:
        """List all ETL sources and their statuses"""
        try:
            response = self.client.table("etl_state").select("*").order("source").execute()
            return response.data
        except Exception as e:
            print(f"Error listing sources: {e}")
            return []
    
    def initialize_source(self, source: str) -> bool:
        """Initialize a new ETL source"""
        try:
            self.client.table("etl_state").upsert({
                "source": source,
                "status": "unknown",
                "records_processed": 0
            }, on_conflict="source").execute()
            return True
        except Exception as e:
            print(f"Error initializing source {source}: {e}")
            return False

def main():
    """CLI interface for ETL state management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ETL State Manager")
    parser.add_argument("command", choices=["get", "update", "list", "init"], help="Command to execute")
    parser.add_argument("--source", help="ETL source identifier")
    parser.add_argument("--status", choices=["success", "failure", "running", "unknown"], help="Status to set")
    parser.add_argument("--records", type=int, default=0, help="Number of records processed")
    parser.add_argument("--error", help="Error message for failed runs")
    parser.add_argument("--overlap", type=int, default=1, help="Overlap minutes for get command")
    
    args = parser.parse_args()
    
    try:
        manager = ETLStateManager()
        
        if args.command == "get":
            if not args.source:
                print("Error: --source required for get command")
                sys.exit(1)
            
            last_run = manager.get_last_run(args.source, args.overlap)
            if last_run:
                print(f"Last run for {args.source}: {last_run.isoformat()}")
            else:
                print(f"No previous run found for {args.source}")
        
        elif args.command == "update":
            if not args.source or not args.status:
                print("Error: --source and --status required for update command")
                sys.exit(1)
            
            success = manager.update_state(args.source, args.status, args.records, args.error)
            if success:
                print(f"Updated state for {args.source}: {args.status}")
            else:
                print(f"Failed to update state for {args.source}")
                sys.exit(1)
        
        elif args.command == "list":
            sources = manager.list_all_sources()
            print(f"{'Source':<25} {'Status':<10} {'Last Run':<20} {'Records'}")
            print("-" * 70)
            for source in sources:
                last_run = source.get('last_run', 'Never')[:19] if source.get('last_run') else 'Never'
                print(f"{source['source']:<25} {source['status']:<10} {last_run:<20} {source['records_processed']}")
        
        elif args.command == "init":
            if not args.source:
                print("Error: --source required for init command")
                sys.exit(1)
            
            success = manager.initialize_source(args.source)
            if success:
                print(f"Initialized source: {args.source}")
            else:
                print(f"Failed to initialize source: {args.source}")
                sys.exit(1)
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()