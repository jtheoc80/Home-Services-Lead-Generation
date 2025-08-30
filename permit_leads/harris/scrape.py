#!/usr/bin/env python3
"""
Harris County permit scraper module

This module provides the main entry point for scraping Harris County permits.
It wraps the existing permit_leads CLI with proper argument handling.
"""

import os
import sys
import subprocess
import argparse
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Harris County permit scraper")
    parser.add_argument("--days", type=int, default=1, help="Days back to scrape (default: 1)")
    parser.add_argument("--sample", action="store_true", help="Use sample data mode")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    return parser.parse_args()


def main():
    """Main entry point for Harris County permit scraping."""
    args = parse_args()
    
    # Set up logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logger.info("Starting Harris County permit scraper")
    logger.info(f"Days back: {args.days}")
    logger.info(f"Sample mode: {args.sample}")
    
    # Set environment variables
    if args.sample:
        os.environ["SAMPLE_DATA"] = "1"
    
    # Build the permit_leads command
    cmd = [
        sys.executable, "-m", "permit_leads", "scrape",
        "--jurisdiction", "tx-harris",
        "--days", str(args.days),
        "--formats", "csv", "sqlite", "jsonl",
        "--retries", "5"
    ]
    if args.verbose:
        cmd.insert(6, "--verbose")  # Insert after --formats ... "jsonl"
    
    logger.info(f"Running command: {' '.join(cmd)}")
    
    # Get the project root directory (parent of permit_leads)
    project_root = Path(__file__).parent.parent.parent
    
    try:
        # Run the command
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=False,  # Let output go to stdout/stderr
            check=True
        )
        logger.info("Harris County permit scraping completed successfully")
        return result.returncode
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Harris County permit scraping failed with exit code {e.returncode}")
        return e.returncode
    except Exception as e:
        logger.error(f"Error running Harris County permit scraper: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())