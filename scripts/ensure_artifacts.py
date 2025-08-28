#!/usr/bin/env python3
"""
Ensure artifacts script for ETL pipeline.

This script:
- Creates logs/ and artifacts/ directories if missing
- Ensures logs/etl_output.log exists (create if missing)
- Handles ETL_ALLOW_EMPTY environment variable to make process exit code 0 instead of 1
  when pipeline found 0 records (downshift a known-empty condition)
"""

import os
import sys
from pathlib import Path


def ensure_directories():
    """Create logs/ and artifacts/ directories if they don't exist."""
    base_dir = Path.cwd()
    
    logs_dir = base_dir / "logs"
    artifacts_dir = base_dir / "artifacts"
    
    # Create directories if they don't exist
    logs_dir.mkdir(exist_ok=True)
    artifacts_dir.mkdir(exist_ok=True)
    
    print(f"✓ Ensured directories exist: {logs_dir}, {artifacts_dir}")
    
    return logs_dir, artifacts_dir


def ensure_log_file(logs_dir: Path):
    """Ensure logs/etl_output.log exists."""
    log_file = logs_dir / "etl_output.log"
    
    if not log_file.exists():
        log_file.touch()
        print(f"✓ Created log file: {log_file}")
    else:
        print(f"✓ Log file exists: {log_file}")
    
    return log_file


def handle_empty_pipeline_exit():
    """
    Check ETL_ALLOW_EMPTY environment variable and handle graceful exits.
    
    If ETL_ALLOW_EMPTY="1" and we detect this is a known-empty condition,
    exit with code 0 instead of 1.
    """
    etl_allow_empty = os.getenv("ETL_ALLOW_EMPTY", "").strip()
    
    if etl_allow_empty == "1":
        print("✓ ETL_ALLOW_EMPTY=1 detected - will handle empty pipeline gracefully")
        return True
    else:
        print("✓ ETL_ALLOW_EMPTY not set or not '1' - standard exit behavior")
        return False


def main():
    """Main function to ensure artifacts and handle empty pipeline conditions."""
    print("🔧 Running ensure_artifacts.py")
    print("=" * 50)
    
    try:
        # Ensure directories exist
        logs_dir, artifacts_dir = ensure_directories()
        
        # Ensure log file exists
        log_file = ensure_log_file(logs_dir)
        
        # Check ETL_ALLOW_EMPTY setting
        allow_empty = handle_empty_pipeline_exit()
        
        print("=" * 50)
        print("✅ ensure_artifacts.py completed successfully")
        
        # If called with a specific argument to indicate empty pipeline
        if len(sys.argv) > 1 and sys.argv[1] == "--empty-pipeline" and allow_empty:
            print("📋 Empty pipeline detected with ETL_ALLOW_EMPTY=1, exiting with code 0")
            sys.exit(0)
        
        return logs_dir, artifacts_dir, log_file, allow_empty
        
    except Exception as error:
        print(f"❌ Error in ensure_artifacts.py: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()