import argparse
import logging
import os
import json
import hashlib
import uuid
from pathlib import Path
from typing import List, Dict, Tuple, Union
import datetime as dt

from .adapters.storage import Storage
from .models.permit import PermitRecord  # noqa: F401
from .scrapers import SCRAPERS  # type: ignore
from .utils.robots import check_robots_txt
from .lead_export import export_leads
from .export_leads import export_enriched_leads
from .migrate_db import add_enrichment_columns
from .region_adapter import RegionAwareAdapter
from .sinks.supabase_sink import SupabaseSink
from .utils.finalize_log import finalize_log

logger = logging.getLogger(__name__)


def setup_output_directories(output_dir: Path) -> Dict[str, Path]:
    paths = {
        'base': output_dir,
        'raw': output_dir / 'permits' / 'raw',
        'aggregate': output_dir / 'permits' / 'aggregate',
        'db': output_dir / 'permits' / 'permits.db'
    }
    for path_type, path in paths.items():
        if path_type != 'db':
            path.mkdir(parents=True, exist_ok=True)
    return paths


def write_jsonl_output(permits: List[PermitRecord], jurisdiction: str, output_paths: Dict[str, Path]) -> None:
    if not permits:
        return
    date_str = dt.datetime.now().strftime('%Y-%m-%d')
    jurisdiction_dir = output_paths['raw'] / jurisdiction.lower().replace(' ', '_')
    jurisdiction_dir.mkdir(parents=True, exist_ok=True)
    jsonl_file = jurisdiction_dir / f"{date_str}.jsonl"
    with open(jsonl_file, 'a', encoding='utf-8') as f:
        for permit in permits:
            json_data = permit.dict()
            for key, value in json_data.items():
                if isinstance(value, dt.datetime):
                    json_data[key] = value.isoformat()
            f.write(json.dumps(json_data) + '\n')
    logger.info(f"Wrote {len(permits)} permits to {jsonl_file}")


def write_csv_output(permits: List[PermitRecord], output_paths: Dict[str, Path]) -> None:
    if not permits:
        return
    
    # Save CSV to artifacts directory instead of output_paths
    artifacts_dir = Path.cwd() / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    
    date_str = dt.datetime.now().strftime('%Y-%m-%d')
    csv_file = artifacts_dir / f"permits_{date_str}.csv"
    latest_csv = artifacts_dir / "permits_latest.csv"
    
    storage = Storage(csv_path=csv_file)
    storage.save_records(permits)
    if latest_csv.is_symlink():
        latest_csv.unlink()
    elif latest_csv.exists():
        latest_csv.unlink()
    try:
        latest_csv.symlink_to(csv_file.name)
    except OSError:
        import shutil
        shutil.copy2(csv_file, latest_csv)
    
    logger.info(f"Wrote {len(permits)} permits to {csv_file} and {latest_csv}")
    
    # Write summary to log file
    write_summary_to_log(len(permits), f"CSV output: {len(permits)} permits written to {csv_file.name}")


def write_summary_to_log(record_count: int, message: str) -> None:
    """Write summary line to logs/etl_output.log"""
    try:
        logs_dir = Path.cwd() / "logs"
        logs_dir.mkdir(exist_ok=True)
        log_file = logs_dir / "etl_output.log"
        
        timestamp = dt.datetime.now().isoformat()
        log_entry = f"{timestamp} - Permit Leads ETL: {record_count} records - {message}\n"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        print(f"📝 Summary logged to {log_file}")
    except Exception as e:
        logger.warning(f"Failed to write to log file: {e}")


def write_json_summary(summary_path: str, record_count: int, sources_processed: List[str], success: bool) -> None:
    """
    Write a JSON summary file for ETL monitoring.

    Args:
        summary_path (str): The file path where the summary JSON will be written.
        record_count (int): The number of records processed in the ETL run.
        sources_processed (List[str]): A list of source names that were processed.
        success (bool): Whether the ETL run was successful.
    """
    try:
        summary_data = {
            "timestamp": dt.datetime.now().isoformat(),
            "record_count": record_count,
            "sources_processed": sources_processed,
            "success": success,
            "status": "success" if success else "failed"
        }
        
        summary_file = Path(summary_path)
        summary_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2)
        
        print(f"📊 Summary written to {summary_file}")
    except Exception as e:
        logger.warning(f"Failed to write JSON summary: {e}")


def convert_sources_to_jurisdictions(sources: str) -> List[str]:
    """Convert comma-separated source names to jurisdiction slugs"""
    source_to_jurisdiction = {
        # Only include active jurisdictions from registry
        'dallas': 'tx-dallas',
        'houston': 'tx-harris',  # Harris County covers Houston
        'harris_county': 'tx-harris',
        'fort_bend': 'tx-fort-bend',
        'brazoria': 'tx-brazoria',
        'galveston': 'tx-galveston',
        # Future areas (commented out in registry) - warn but skip
        'austin': None,  # tx-travis not active yet  
        'san_antonio': None,  # tx-bexar not active yet
    }
    
    source_list = [s.strip() for s in sources.split(',')]
    jurisdictions = []
    
    for source in source_list:
        if source in source_to_jurisdiction:
            jurisdiction = source_to_jurisdiction[source]
            if jurisdiction is None:
                logger.warning(f"Source '{source}' maps to inactive jurisdiction, skipping")
            elif jurisdiction not in jurisdictions:  # Avoid duplicates
                jurisdictions.append(jurisdiction)
        else:
            logger.warning(f"Unknown source '{source}', skipping")
    
    return jurisdictions


def write_sqlite_output(permits: List[PermitRecord], output_paths: Dict[str, Path]) -> None:
    if not permits:
        return
    storage = Storage(db_path=output_paths['db'])
    saved_count = storage.save_records(permits)
    logger.info(f"Saved {saved_count} new permits to SQLite database")


def write_supabase_output(permits: List[PermitRecord], jurisdiction: str = None) -> None:
    """Write permits to Supabase using the SupabaseSink."""
    if not permits:
        return
    
    # Determine table name based on jurisdiction (keeping existing logic for compatibility)
    jurisdiction_table_map = {
        'tx-harris': 'permits_raw_harris',
        'tx-fort-bend': 'permits_raw_fort_bend',
        'tx-brazoria': 'permits_raw_brazoria', 
        'tx-galveston': 'permits_raw_galveston',
        'tx-dallas': 'permits_raw_dallas'
    }
    
    # Default to permits table for new upsert behavior
    table_name = jurisdiction_table_map.get(jurisdiction, 'permits')
    
    try:
        # Initialize SupabaseSink - use "permits" table for RPC calls
        sink = SupabaseSink(
            upsert_table="permits",
            conflict_col="source,source_record_id",  # Updated for new upsert strategy
            chunk_size=500
        )
        
        # Convert PermitRecord objects to the required payload format
        permit_dicts = []
        for permit in permits:
            permit_dict = permit.dict()
            
            # Generate UUID for id field
            record_id = str(uuid.uuid4())
            
            # Extract source and source_record_id 
            source = jurisdiction or permit_dict.get('jurisdiction', 'unknown')
            source_record_id = permit_dict.get('permit_id', permit_dict.get('event_id'))
            
            # If no source_record_id available, generate one from permit data
            if not source_record_id:
                permit_json = json.dumps(permit_dict, sort_keys=True, default=str)
                permit_hash = hashlib.sha256(permit_json.encode('utf-8')).hexdigest()
                source_record_id = f"permit_{permit_hash[:16]}"
            
            # Create payload with required fields plus permit data
            payload = {
                "id": record_id,
                "source": source,
                "source_record_id": str(source_record_id),
                "jurisdiction": jurisdiction or permit_dict.get('jurisdiction', 'unknown'),
                "created_at": "now()",
                # Include all permit data for the upsert function to process
                **permit_dict
            }
            
            permit_dicts.append(payload)
        
        # Upsert to Supabase using RPC endpoint for proper (source, source_record_id) conflict resolution
        result = sink.upsert_records(permit_dicts, use_rpc=True)
        logger.info(f"Supabase upsert completed: {result['success']} success, {result['failed']} failed")
        
    except ImportError:
        logger.warning("Supabase client not available. Skipping Supabase output.")
    except ValueError as e:
        if "environment variables" in str(e):
            logger.warning("Supabase environment variables not configured. Skipping Supabase output.")
        else:
            logger.error(f"Supabase configuration error: {e}")
    except Exception as e:
        logger.error(f"Failed to write to Supabase: {e}")
        # Don't raise - allow other outputs to succeed


def run_region_aware_scraper(
    args: argparse.Namespace,
    output_paths: Dict[str, Path],
    return_jurisdiction_map: bool = False
) -> Union[List[PermitRecord], Tuple[List[PermitRecord], Dict[str, List[PermitRecord]]]]:
    """Run region-aware scraper using registry configuration.

    If return_jurisdiction_map is False (default), returns List[PermitRecord].
    If True, returns (List[PermitRecord], Dict[str, List[PermitRecord]]).
    """
    try:
        adapter = RegionAwareAdapter()
        since = dt.datetime.now() - dt.timedelta(days=args.days)
        
        if args.jurisdiction:
            # Scrape specific jurisdiction
            logger.info(f"Scraping jurisdiction: {args.jurisdiction}")
            permits = adapter.scrape_jurisdiction(args.jurisdiction, since, limit=args.limit, max_retries=getattr(args, 'retries', 3))
            # Return permits and a dict mapping the jurisdiction to its permits
            return permits, {args.jurisdiction: permits}
        else:
            # Scrape all active jurisdictions
            logger.info("Scraping all active jurisdictions")
            results = adapter.scrape_all_jurisdictions(since, limit=args.limit, max_retries=getattr(args, 'retries', 3))
            permits = []
            for jurisdiction_permits in results.values():
                permits.extend(jurisdiction_permits)
            # Return combined permits and the jurisdiction-specific results
            return permits, results
        
    except Exception as e:
        logger.error(f"Error in region-aware scraper: {e}")
        return [], {}


def run_legacy_scraper(source_name: str, args: argparse.Namespace, output_paths: Dict[str, Path]) -> List[PermitRecord]:
    """Run legacy single-source scraper for backward compatibility."""
    if source_name not in SCRAPERS:
        logger.error(f"Unknown source: {source_name}. Available: {list(SCRAPERS.keys())}")
        return []
    scraper_class = SCRAPERS[source_name]
    scraper = scraper_class(
        user_agent=args.user_agent,
        delay_seconds=args.sleep,
        max_retries=getattr(args, 'retries', 3)
    )
    if not args.no_robots:
        if not check_robots_txt(scraper.base_url, args.user_agent):
            logger.warning(f"robots.txt check failed for {scraper.base_url}")
            if not args.force:
                logger.error("Use --force to override robots.txt restrictions")
                return []
    if args.sample:
        os.environ['SAMPLE_DATA'] = '1'
    try:
        since = dt.datetime.now() - dt.timedelta(days=args.days)
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
        if 'SAMPLE_DATA' in os.environ:
            del os.environ['SAMPLE_DATA']


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Permit scraping & lead export CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Multi-source ETL (new interface)
  python -m permit_leads --sources "austin,san_antonio,dallas,houston,harris_county" --days 1 --sink supabase
  
  # Scrape using new region-aware system
  python -m permit_leads scrape --region-aware --days 3 --formats csv sqlite jsonl
  
  # Scrape specific jurisdiction
  python -m permit_leads scrape --jurisdiction tx-harris --days 3

  # Scrape one source (legacy)
  python -m permit_leads scrape --source city_of_houston --days 3 --formats csv sqlite jsonl

  # Scrape all sources (legacy)
  python -m permit_leads scrape --all

  # Export recent leads (past 14 days default)
  python -m permit_leads export-leads --lookback 14

  # Backward compatible (scrape) - still works:
  python -m permit_leads --source city_of_houston
"""
    )
    parser.set_defaults(command="__auto__")
    
    # Backward compatibility: Add old CLI arguments to main parser
    parser.add_argument("--source", choices=list(SCRAPERS.keys()), help="Specific source to scrape (legacy)")
    parser.add_argument("--all", action="store_true", help="Run all available scrapers (legacy)")
    parser.add_argument("--region-aware", action="store_true", help="Use new region-aware scraping system")
    parser.add_argument("--jurisdiction", help="Specific jurisdiction slug to scrape")
    parser.add_argument("--sources", help="Comma-separated list of sources (e.g., 'austin,dallas,harris_county')")
    parser.add_argument("--sink", choices=["supabase", "csv", "sqlite", "jsonl"], help="Primary output destination")
    parser.add_argument("--summary", help="Path to write JSON summary file")
    parser.add_argument("--days", type=int, default=7, help="Look-back window in days (default: 7)")
    parser.add_argument("--limit", type=int, help="Limit number of records per source")
    parser.add_argument("--formats", nargs="+", choices=["csv", "sqlite", "jsonl"], default=["csv", "sqlite"], help="Output formats (default: csv sqlite)")
    parser.add_argument("--output-dir", default="data", help="Output directory (default: data)")
    parser.add_argument("--sample", action="store_true", help="Use sample/fixture data instead of live scraping")
    parser.add_argument("--no-robots", action="store_true", help="Skip robots.txt check")
    parser.add_argument("--force", action="store_true", help="Force scraping even if robots.txt disallows")
    parser.add_argument("--dry-run", action="store_true", help="Parse data but don't persist to files")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    parser.add_argument("--sleep", type=float, default=2.0, help="Delay between requests seconds (default: 2.0)")
    parser.add_argument("--retries", type=int, default=3, help="Maximum number of retry attempts for HTTP requests (default: 3)")
    parser.add_argument("--user-agent", default="PermitLeadBot/1.0 (+contact@example.com)", help="User-Agent string for requests")
    
    subparsers = parser.add_subparsers(dest="command")

    scrape = subparsers.add_parser("scrape", help="Scrape permit sources")
    scrape.add_argument("--source", choices=list(SCRAPERS.keys()), help="Specific source to scrape (legacy)")
    scrape.add_argument("--all", action="store_true", help="Run all available scrapers (legacy)")
    scrape.add_argument("--region-aware", action="store_true", help="Use new region-aware scraping system")
    scrape.add_argument("--jurisdiction", help="Specific jurisdiction slug to scrape")
    scrape.add_argument("--days", type=int, default=7, help="Look-back window in days (default: 7)")
    scrape.add_argument("--limit", type=int, help="Limit number of records per source")
    scrape.add_argument("--formats", nargs="+", choices=["csv", "sqlite", "jsonl"], default=["csv", "sqlite"], help="Output formats (default: csv sqlite)")
    scrape.add_argument("--output-dir", default="data", help="Output directory (default: data)")
    scrape.add_argument("--sample", action="store_true", help="Use sample/fixture data instead of live scraping")
    scrape.add_argument("--no-robots", action="store_true", help="Skip robots.txt check")
    scrape.add_argument("--force", action="store_true", help="Force scraping even if robots.txt disallows")
    scrape.add_argument("--dry-run", action="store_true", help="Parse data but don't persist to files")
    scrape.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    scrape.add_argument("--sleep", type=float, default=2.0, help="Delay between requests seconds (default: 2.0)")
    scrape.add_argument("--retries", type=int, default=3, help="Maximum number of retry attempts for HTTP requests (default: 3)")
    scrape.add_argument("--user-agent", default="PermitLeadBot/1.0 (+contact@example.com)", help="User-Agent string for requests")

    export = subparsers.add_parser("export-leads", help="Generate scored lead CSVs from existing permits DB")
    export.add_argument("--db", default="data/permits/permits.db", help="Path to permits SQLite DB")
    export.add_argument("--out", default="data/leads", help="Output directory for lead CSVs")
    export.add_argument("--lookback", type=int, default=14, help="Lookback window in days (default: 14)")
    export.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")

    enrich = subparsers.add_parser("export-enriched", help="Generate enriched & scored leads with geocoding, parcel data, etc.")
    enrich.add_argument("--db", default="data/permits/permits.db", help="Path to permits SQLite DB")
    enrich.add_argument("--out", default="data/leads", help="Output directory for lead CSVs")
    enrich.add_argument("--lookback", type=int, default=14, help="Lookback window in days (default: 14)")
    enrich.add_argument("--migrate", action="store_true", help="Update database schema to support enrichment")
    enrich.add_argument("--no-enrich", action="store_true", help="Skip enrichment pipeline (use existing data)")
    enrich.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")

    migrate = subparsers.add_parser("migrate-db", help="Update database schema to support enrichment")
    migrate.add_argument("--db", default="data/permits/permits.db", help="Path to permits SQLite DB")
    migrate.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")

    return parser


def handle_scrape(args: argparse.Namespace):
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    try:
        # Print current working directory and discovered CSVs
        import glob as glob_module
        current_dir = Path.cwd()
        print(f"📂 Current working directory: {current_dir}")
        
        # Discover CSV files in data/**/*.csv recursively
        csv_files = glob_module.glob('data/**/*.csv', recursive=True)
        print(f"📋 Discovered {len(csv_files)} CSV files:")
        for csv_file in csv_files:
            print(f"  - {csv_file}")
        print()
        
        # Determine scraping mode - check new multi-source interface first
        use_multi_source = getattr(args, 'sources', None)
        use_region_aware = getattr(args, 'region_aware', False) or getattr(args, 'jurisdiction', None)
        
        # Set up output configuration based on sink argument
        sink = getattr(args, 'sink', None)
        if sink:
            if sink == 'supabase':
                # Override formats to prioritize Supabase output 
                args.formats = ['csv']  # Still generate CSV for artifacts
            elif sink in ['csv', 'sqlite', 'jsonl']:
                args.formats = [sink]
        
        if args.command == "__auto__":
            if not getattr(args, "source", None) and not getattr(args, "all", False) and not use_region_aware and not use_multi_source:
                raise SystemExit("Must specify either --source, --all, --region-aware, --jurisdiction, or --sources (scrape mode).")
            output_dir = Path(getattr(args, "output_dir", "data"))
        else:
            if not args.source and not args.all and not use_region_aware and not use_multi_source:
                raise SystemExit("Must specify either --source, --all, --region-aware, --jurisdiction, or --sources")
            if args.source and args.all:
                raise SystemExit("Cannot specify both --source and --all")
            output_dir = Path(args.output_dir)
        
        output_paths = setup_output_directories(output_dir)
        all_permits: List[PermitRecord] = []
        jurisdiction_results = {}  # Initialize for legacy compatibility
        sources_processed = []
        
        if use_multi_source:
            # New multi-source interface
            logger.info(f"Using multi-source interface with sources: {args.sources}")
            jurisdictions = convert_sources_to_jurisdictions(args.sources)
            logger.info(f"Converted to jurisdictions: {jurisdictions}")
            
            # Process each jurisdiction
            for jurisdiction in jurisdictions:
                logger.info(f"Processing jurisdiction: {jurisdiction}")
                args.jurisdiction = jurisdiction  # Set for the region-aware scraper
                permits, jur_results = run_region_aware_scraper(args, output_paths, return_jurisdiction_map=True)
                all_permits.extend(permits)
                jurisdiction_results.update(jur_results)
                sources_processed.append(jurisdiction)
            
        elif use_region_aware:
            # Use new region-aware system
            logger.info("Using region-aware scraping system")
            permits, jurisdiction_results = run_region_aware_scraper(args, output_paths, return_jurisdiction_map=True)
            all_permits.extend(permits)
            sources_processed = ["region-aware"]
        else:
            # Use legacy system
            sources_to_run = list(SCRAPERS.keys()) if args.all else [args.source]
            sources_processed = sources_to_run
            
            for source_name in sources_to_run:
                logger.info(f"Running legacy scraper: {source_name}")
                permits = run_legacy_scraper(source_name, args, output_paths)
                all_permits.extend(permits)
        
        # Save output files
        if all_permits and not args.dry_run:
            if "jsonl" in args.formats:
                # For region-aware, use first permit's jurisdiction or fallback
                if use_region_aware or use_multi_source:
                    temp_jur = "multi-jurisdiction"
                else:
                    temp_jur = SCRAPERS[sources_to_run[0]]("").jurisdiction
                write_jsonl_output(all_permits, temp_jur, output_paths)
            if "csv" in args.formats:
                write_csv_output(all_permits, output_paths)
            if "sqlite" in args.formats:
                write_sqlite_output(all_permits, output_paths)
            
            # Handle Supabase sink (either via --sink supabase or for region-aware TX counties)
            if sink == 'supabase' or (use_region_aware or use_multi_source):
                # Support all Texas counties that have Supabase tables
                tx_counties = ['tx-harris', 'tx-fort-bend', 'tx-brazoria', 'tx-galveston', 'tx-dallas']
                
                if use_multi_source:
                    # Multi-source case - write each jurisdiction separately
                    for jurisdiction, permits_list in jurisdiction_results.items():
                        if jurisdiction in tx_counties and permits_list:
                            write_supabase_output(permits_list, jurisdiction)
                elif args.jurisdiction and args.jurisdiction in tx_counties:
                    # Single jurisdiction case
                    write_supabase_output(all_permits, args.jurisdiction)
                elif not args.jurisdiction:
                    # All jurisdictions case - write each jurisdiction separately
                    for jurisdiction, permits_list in jurisdiction_results.items():
                        if jurisdiction in tx_counties and permits_list:
                            write_supabase_output(permits_list, jurisdiction)
        
        total_permits = len(all_permits)
        residential_permits = sum(1 for p in all_permits if p.is_residential())
        
        # Handle empty pipeline results
        if total_permits == 0:
            print("\n=== SCRAPING SUMMARY ===")
            print("No permits found to process")
            
            # Write summary to log file
            write_summary_to_log(0, "No input found")
            
            # Handle ETL_ALLOW_EMPTY environment variable
            import os
            allow_empty = os.getenv("ETL_ALLOW_EMPTY", "").strip() == "1"
            if allow_empty:
                print("🔧 ETL_ALLOW_EMPTY=1 detected, calling ensure_artifacts.py for graceful exit")
                call_ensure_artifacts("--empty-pipeline")
            else:
                call_ensure_artifacts()
            
            # Write JSON summary if requested
            if getattr(args, 'summary', None):
                write_json_summary(args.summary, 0, sources_processed, True)
            
            # Use finalize_log for "no new data" case - exit with 0 (expected empty)
            finalize_log(0, True)
            return
        
        print("\n=== SCRAPING SUMMARY ===")
        print(f"Total permits: {total_permits}")
        print(f"Residential permits: {residential_permits}")
        print(f"Sources processed: {len(sources_processed)}")
        if not args.dry_run and total_permits > 0:
            print(f"Output directory: {output_dir}")
            print(f"Formats written: {', '.join(args.formats)}")
            if sink:
                print(f"Primary sink: {sink}")
            if "sqlite" in args.formats:
                storage = Storage(db_path=output_paths['db'])
                latest = storage.get_latest(5)
                if latest:
                    print("\nLatest permits:")
                    for permit in latest:
                        print(f"  {permit.get('permit_id', 'N/A')} - {permit.get('address', 'N/A')}")
        
        # Write final summary to log file
        write_summary_to_log(total_permits, f"Scraping completed: {total_permits} total permits, {residential_permits} residential")
        
        # Write JSON summary if requested
        if getattr(args, 'summary', None):
            write_json_summary(args.summary, total_permits, sources_processed, True)
        
        # Call ensure_artifacts.py at the end
        call_ensure_artifacts()
        
        # Use finalize_log for successful completion
        finalize_log(total_permits, True)
        
    except Exception as e:
        logger.error(f"Scraping failed with error: {e}")
        
        # Write JSON summary for failure if requested
        if getattr(args, 'summary', None):
            write_json_summary(args.summary, 0, [], False)
        
        # Use finalize_log for failure case - exit with 1
        finalize_log(0, False)


def call_ensure_artifacts(args: str = "") -> None:
    """Call scripts/ensure_artifacts.py"""
    try:
        import subprocess
        import sys
        
        cmd = [sys.executable, "scripts/ensure_artifacts.py"]
        if args:
            cmd.append(args)
        
        print(f"🔧 Calling ensure_artifacts.py{' ' + args if args else ''}")
        
        result = subprocess.run(cmd, cwd=Path.cwd(), capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ ensure_artifacts.py completed successfully")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ ensure_artifacts.py exited with code {result.returncode}")
            if result.stderr:
                print(f"Error: {result.stderr}")
            if result.stdout:
                print(f"Output: {result.stdout}")
    except Exception as e:
        logger.warning(f"Failed to call ensure_artifacts.py: {e}")


def handle_export(args: argparse.Namespace):
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    db_path = Path(args.db)
    out_dir = Path(args.out)
    master_csv, count = export_leads(db_path=db_path, out_dir=out_dir, lookback_days=args.lookback)
    print(f"Generated {count} leads -> {master_csv}")
    by_dir = out_dir / "by_jurisdiction"
    if by_dir.exists():
        per_files = sorted(p.name for p in by_dir.glob("*_leads.csv"))
        if per_files:
            print("Per-jurisdiction files:")
            for f in per_files:
                print(f"  {f}")


def handle_export_enriched(args: argparse.Namespace):
    """Handle enriched lead export with optional database migration."""
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    db_path = Path(args.db)
    if not db_path.exists():
        raise SystemExit(f"Database not found: {db_path}")
    
    # Migrate database schema if requested
    if args.migrate:
        logger.info("Migrating database schema...")
        add_enrichment_columns(db_path)
    
    out_dir = Path(args.out)
    enrich_data = not args.no_enrich
    
    logger.info(f"Exporting enriched leads (enrichment={'on' if enrich_data else 'off'})...")
    master_csv, count = export_enriched_leads(
        db_path=db_path, 
        out_dir=out_dir, 
        lookback_days=args.lookback,
        enrich_data=enrich_data
    )
    
    print(f"Generated {count} enriched leads -> {master_csv}")
    by_dir = out_dir / "by_jurisdiction"
    if by_dir.exists():
        per_files = sorted(p.name for p in by_dir.glob("*_enriched_leads.csv"))
        if per_files:
            print("Per-jurisdiction files:")
            for f in per_files:
                print(f"  {f}")


def handle_migrate(args: argparse.Namespace):
    """Handle database schema migration."""
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    db_path = Path(args.db)
    if not db_path.exists():
        raise SystemExit(f"Database not found: {db_path}")
    
    logger.info("Migrating database schema...")
    add_enrichment_columns(db_path)
    print("Database migration completed successfully!")


def main():
    parser = build_parser()
    args, unknown = parser.parse_known_args()
    
    # If no subcommand is provided but we have old-style arguments, treat as scrape
    if args.command is None:
        args.command = "__auto__"
    
    if args.command in ("scrape", "__auto__"):
        if unknown:
            print(f"Warning: Unrecognized arguments ignored: {unknown}")
        handle_scrape(args)
    elif args.command == "export-leads":
        handle_export(args)
    elif args.command == "export-enriched":
        handle_export_enriched(args)
    elif args.command == "migrate-db":
        handle_migrate(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()