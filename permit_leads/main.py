#!/usr/bin/env python3
"""
CLI entrypoint for Houston-area permit leads scraper.

Usage:
    python -m permit_leads --source city_of_houston --days 3 --formats csv sqlite jsonl
    python -m permit_leads --all
    python permit_leads/main.py --source city_of_houston --sample
"""
import argparse
import datetime as dt
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from models.permit import PermitRecord
from adapters.storage import Storage
from scrapers.houston_city import HoustonCityScraper
from utils.http import get_session, PoliteSession
from utils.robots import check_robots_txt

# Available scrapers
SCRAPERS = {
    "city_of_houston": HoustonCityScraper,
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_output_directories(output_dir: Path) -> Dict[str, Path]:
    """
    Create output directory structure as per specification.
    
    Returns:
        Dictionary of output paths
    """
    paths = {
        'base': output_dir,
        'raw': output_dir / 'permits' / 'raw',
        'aggregate': output_dir / 'permits' / 'aggregate',
        'db': output_dir / 'permits' / 'permits.db'
    }
    
    # Create directories
    for path_type, path in paths.items():
        if path_type != 'db':  # Don't create file paths, just directories
            path.mkdir(parents=True, exist_ok=True)
    
    return paths


def write_jsonl_output(permits: List[PermitRecord], jurisdiction: str, output_paths: Dict[str, Path]) -> None:
    """Write permits to JSONL format with date-based naming."""
    if not permits:
        return
    
    date_str = dt.datetime.now().strftime('%Y-%m-%d')
    
    # Create jurisdiction directory
    jurisdiction_dir = output_paths['raw'] / jurisdiction.lower().replace(' ', '_')
    jurisdiction_dir.mkdir(parents=True, exist_ok=True)
    
    jsonl_file = jurisdiction_dir / f"{date_str}.jsonl"
    
    with open(jsonl_file, 'a', encoding='utf-8') as f:
        for permit in permits:
            json_data = permit.dict()
            # Convert datetime objects to ISO strings for JSON serialization
            for key, value in json_data.items():
                if isinstance(value, dt.datetime):
                    json_data[key] = value.isoformat()
            f.write(json.dumps(json_data) + '\n')
    
    logger.info(f"Wrote {len(permits)} permits to {jsonl_file}")


def write_csv_output(permits: List[PermitRecord], output_paths: Dict[str, Path]) -> None:
    """Write permits to consolidated CSV files."""
    if not permits:
        return
    
    date_str = dt.datetime.now().strftime('%Y-%m-%d')
    
    # Date-stamped CSV
    csv_file = output_paths['aggregate'] / f"permits_{date_str}.csv"
    
    # Latest CSV (symlink or copy)
    latest_csv = output_paths['aggregate'] / "permits_latest.csv"
    
    # Use storage to write CSV
    storage = Storage(csv_path=csv_file)
    storage.save_records(permits)
    
    # Create/update latest symlink
    if latest_csv.is_symlink():
        latest_csv.unlink()
    elif latest_csv.exists():
        latest_csv.unlink()
    
    try:
        latest_csv.symlink_to(csv_file.name)
    except OSError:
        # Fallback to copy if symlinks not supported
        import shutil
        shutil.copy2(csv_file, latest_csv)
    
    logger.info(f"Wrote {len(permits)} permits to {csv_file} and {latest_csv}")


def write_sqlite_output(permits: List[PermitRecord], output_paths: Dict[str, Path]) -> None:
    """Write permits to SQLite database."""
    if not permits:
        return
    
    storage = Storage(db_path=output_paths['db'])
    saved_count = storage.save_records(permits)
    
    logger.info(f"Saved {saved_count} new permits to SQLite database")


def run_scraper(source_name: str, args: argparse.Namespace, output_paths: Dict[str, Path]) -> List[PermitRecord]:
    """
    Run a specific scraper and return permits.
    
    Args:
        source_name: Name of scraper to run
        args: Command line arguments
        output_paths: Output directory paths
        
    Returns:
        List of scraped permits
    """
    if source_name not in SCRAPERS:
        logger.error(f"Unknown source: {source_name}. Available: {list(SCRAPERS.keys())}")
        return []
    
    scraper_class = SCRAPERS[source_name]
    
    # Initialize scraper
    scraper = scraper_class(
        user_agent=args.user_agent,
        delay_seconds=args.sleep,
        max_retries=3
    )
    
    # Check robots.txt if not disabled
    if not args.no_robots:
        if not check_robots_txt(scraper.base_url, args.user_agent):
            logger.warning(f"robots.txt check failed for {scraper.base_url}")
            if not args.force:
                logger.error("Use --force to override robots.txt restrictions")
                return []
    
    # Set sample data mode if requested
    if args.sample:
        os.environ['SAMPLE_DATA'] = '1'
    
    try:
        # Calculate since date
        since = dt.datetime.now() - dt.timedelta(days=args.days)
        
        # Run scraper
        if args.dry_run:
            logger.info(f"DRY RUN: Would scrape {source_name} since {since}")
            permits = scraper.scrape_permits(since, limit=args.limit)
            logger.info(f"DRY RUN: Would save {len(permits)} permits")
            return permits
        else:
            logger.info(f"Scraping {source_name} since {since}")
            permits = scraper.scrape_permits(since, limit=args.limit)
            logger.info(f"Scraped {len(permits)} permits from {source_name}")
            return permits
            
    except Exception as e:
        logger.error(f"Error scraping {source_name}: {e}")
        return []
    finally:
        # Clean up environment
        if 'SAMPLE_DATA' in os.environ:
            del os.environ['SAMPLE_DATA']


def main():
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Houston-area permit leads scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m permit_leads --source city_of_houston --days 3 --formats csv sqlite jsonl
    python -m permit_leads --all --sample
    python permit_leads/main.py --source city_of_houston --limit 100 --dry-run
        """
    )
    
    # Source selection
    parser.add_argument("--source", choices=list(SCRAPERS.keys()),
                       help="Specific source to scrape")
    parser.add_argument("--all", action="store_true",
                       help="Run all available scrapers")
    
    # Time and limits
    parser.add_argument("--days", type=int, default=7,
                       help="Look-back window in days (default: 7)")
    parser.add_argument("--limit", type=int,
                       help="Limit number of records per source")
    
    # Output options
    parser.add_argument("--formats", nargs="+", choices=["csv", "sqlite", "jsonl"],
                       default=["csv", "sqlite"], 
                       help="Output formats (default: csv sqlite)")
    parser.add_argument("--output-dir", default="data",
                       help="Output directory (default: data)")
    
    # Behavior options
    parser.add_argument("--sample", action="store_true",
                       help="Use sample/fixture data instead of live scraping")
    parser.add_argument("--no-robots", action="store_true",
                       help="Skip robots.txt check")
    parser.add_argument("--force", action="store_true",
                       help="Force scraping even if robots.txt disallows")
    parser.add_argument("--dry-run", action="store_true",
                       help="Parse data but don't persist to files")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable debug logging")
    
    # HTTP options
    parser.add_argument("--sleep", type=float, default=2.0,
                       help="Polite delay between requests in seconds (default: 2.0)")
    parser.add_argument("--user-agent", default="PermitLeadBot/1.0 (+contact@example.com)",
                       help="User-Agent string for requests")
    
    args = parser.parse_args()
    
    # Setup logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Validate arguments
    if not args.source and not args.all:
        parser.error("Must specify either --source or --all")
    
    if args.source and args.all:
        parser.error("Cannot specify both --source and --all")
    
    # Setup output directories
    output_dir = Path(args.output_dir)
    output_paths = setup_output_directories(output_dir)
    
    # Determine sources to run
    if args.all:
        sources_to_run = list(SCRAPERS.keys())
    else:
        sources_to_run = [args.source]
    
    # Run scrapers
    all_permits = []
    for source_name in sources_to_run:
        logger.info(f"Running scraper: {source_name}")
        permits = run_scraper(source_name, args, output_paths)
        all_permits.extend(permits)
        
        if permits and not args.dry_run:
            # Write outputs in requested formats
            if "jsonl" in args.formats:
                write_jsonl_output(permits, SCRAPERS[source_name]("").jurisdiction, output_paths)
            
            if "csv" in args.formats:
                write_csv_output(permits, output_paths)
            
            if "sqlite" in args.formats:
                write_sqlite_output(permits, output_paths)
    
    # Summary
    total_permits = len(all_permits)
    residential_permits = sum(1 for p in all_permits if p.is_residential())
    
    print(f"\n=== SCRAPING SUMMARY ===")
    print(f"Total permits: {total_permits}")
    print(f"Residential permits: {residential_permits}")
    print(f"Sources processed: {len(sources_to_run)}")
    
    if not args.dry_run and total_permits > 0:
        print(f"Output directory: {output_dir}")
        print(f"Formats written: {', '.join(args.formats)}")
        
        # Show latest permits
        if "sqlite" in args.formats:
            storage = Storage(db_path=output_paths['db'])
            latest = storage.get_latest(5)
            if latest:
                print(f"\nLatest permits:")
                for permit in latest:
                    print(f"  {permit.get('permit_id', 'N/A')} - {permit.get('address', 'N/A')}")


if __name__ == "__main__":
    main()