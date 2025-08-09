import argparse
import logging
import os
import json
from pathlib import Path
from typing import List, Dict
import datetime as dt

from .adapters.storage import Storage
from .models.permit import PermitRecord  # noqa: F401
from .scrapers import SCRAPERS  # type: ignore
from .utils.robots import check_robots_txt
from .lead_export import export_leads
from .export_leads import export_enriched_leads
from .migrate_db import add_enrichment_columns

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
    date_str = dt.datetime.now().strftime('%Y-%m-%d')
    csv_file = output_paths['aggregate'] / f"permits_{date_str}.csv"
    latest_csv = output_paths['aggregate'] / "permits_latest.csv"
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


def write_sqlite_output(permits: List[PermitRecord], output_paths: Dict[str, Path]) -> None:
    if not permits:
        return
    storage = Storage(db_path=output_paths['db'])
    saved_count = storage.save_records(permits)
    logger.info(f"Saved {saved_count} new permits to SQLite database")


def run_scraper(source_name: str, args: argparse.Namespace, output_paths: Dict[str, Path]) -> List[PermitRecord]:
    if source_name not in SCRAPERS:
        logger.error(f"Unknown source: {source_name}. Available: {list(SCRAPERS.keys())}")
        return []
    scraper_class = SCRAPERS[source_name]
    scraper = scraper_class(
        user_agent=args.user_agent,
        delay_seconds=args.sleep,
        max_retries=3
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
  # Scrape one source
  python -m permit_leads scrape --source city_of_houston --days 3 --formats csv sqlite jsonl

  # Scrape all sources
  python -m permit_leads scrape --all

  # Export recent leads (past 14 days default)
  python -m permit_leads export-leads --lookback 14

  # Backward compatible (scrape) - still works:
  python -m permit_leads --source city_of_houston
"""
    )
    parser.set_defaults(command="__auto__")
    
    # Backward compatibility: Add old CLI arguments to main parser
    parser.add_argument("--source", choices=list(SCRAPERS.keys()), help="Specific source to scrape")
    parser.add_argument("--all", action="store_true", help="Run all available scrapers")
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
    parser.add_argument("--user-agent", default="PermitLeadBot/1.0 (+contact@example.com)", help="User-Agent string for requests")
    
    subparsers = parser.add_subparsers(dest="command")

    scrape = subparsers.add_parser("scrape", help="Scrape permit sources")
    scrape.add_argument("--source", choices=list(SCRAPERS.keys()), help="Specific source to scrape")
    scrape.add_argument("--all", action="store_true", help="Run all available scrapers")
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
    if args.command == "__auto__":
        if not getattr(args, "source", None) and not getattr(args, "all", False):
            raise SystemExit("Must specify either --source or --all (scrape mode).")
        output_dir = Path(getattr(args, "output_dir", "data"))
    else:
        if not args.source and not args.all:
            raise SystemExit("Must specify either --source or --all")
        if args.source and args.all:
            raise SystemExit("Cannot specify both --source and --all")
        output_dir = Path(args.output_dir)
    output_paths = setup_output_directories(output_dir)
    sources_to_run = list(SCRAPERS.keys()) if args.all else [args.source]
    all_permits: List[PermitRecord] = []
    for source_name in sources_to_run:
        logger.info(f"Running scraper: {source_name}")
        permits = run_scraper(source_name, args, output_paths)
        all_permits.extend(permits)
        if permits and not args.dry_run:
            if "jsonl" in args.formats:
                temp_jur = SCRAPERS[source_name]("").jurisdiction
                write_jsonl_output(permits, temp_jur, output_paths)
            if "csv" in args.formats:
                write_csv_output(permits, output_paths)
            if "sqlite" in args.formats:
                write_sqlite_output(permits, output_paths)
    total_permits = len(all_permits)
    residential_permits = sum(1 for p in all_permits if p.is_residential())
    print(f"\n=== SCRAPING SUMMARY ===")
    print(f"Total permits: {total_permits}")
    print(f"Residential permits: {residential_permits}")
    print(f"Sources processed: {len(sources_to_run)}")
    if not args.dry_run and total_permits > 0:
        print(f"Output directory: {output_dir}")
        print(f"Formats written: {', '.join(args.formats)}")
        if "sqlite" in args.formats:
            storage = Storage(db_path=output_paths['db'])
            latest = storage.get_latest(5)
            if latest:
                print(f"\nLatest permits:")
                for permit in latest:
                    print(f"  {permit.get('permit_id', 'N/A')} - {permit.get('address', 'N/A')}")


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