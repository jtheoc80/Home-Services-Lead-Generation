#!/usr/bin/env python3
"""
Harris County permit scraper fallback script

This script serves as a fallback entry point for Harris County permit scraping
when the module-based approach is not available.
"""

import os
import sys
import subprocess
import argparse
import logging
from pathlib import Path

# Add the project root to Python path to import permit_leads
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Harris County permit scraper (fallback)")
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
    
    logger.info("Starting Harris County permit scraper (fallback)")
    logger.info(f"Days back: {args.days}")
    logger.info(f"Sample mode: {args.sample}")
    
    # Set environment variables
    if args.sample:
        os.environ["SAMPLE_DATA"] = "1"
    
    # Try to import and use the permit_leads module directly
    try:
        # Import the permit_leads module
        import permit_leads.main
        
        # Simulate command line arguments for permit_leads
        sys.argv = [
            "permit_leads",
            "scrape",
            "--jurisdiction", "tx-harris", 
            "--days", str(args.days),
            "--formats", "csv", "sqlite", "jsonl",
            "--retries", "5"
        ]
        if args.verbose:
            sys.argv.append("--verbose")
        
        logger.info(f"Calling permit_leads with args: {sys.argv[1:]}")
        
        # Call the main function
        parser = permit_leads.main.build_parser()
        parsed_args = parser.parse_args(sys.argv[1:])
        
        if hasattr(parsed_args, 'command') and parsed_args.command == 'scrape':
            permit_leads.main.handle_scrape(parsed_args)
        else:
            # Fallback to legacy mode
            permit_leads.main.main()
            
        logger.info("Harris County permit scraping completed successfully")
        return 0
        
    except ImportError as e:
        logger.error(f"Failed to import permit_leads: {e}")
        logger.info("Falling back to subprocess call")
        
        # Fallback to subprocess call
        cmd = [
            sys.executable, "-m", "permit_leads", "scrape",
            "--jurisdiction", "tx-harris",
            "--days", str(args.days),
            "--formats", "csv", "sqlite", "jsonl",
            "--retries", "5"
        ]
        if args.verbose:
            cmd.append("--verbose")
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=False,
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
    
    except Exception as e:
        logger.error(f"Error in Harris County permit scraper: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())