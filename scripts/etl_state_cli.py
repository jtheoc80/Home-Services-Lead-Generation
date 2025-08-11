#!/usr/bin/env python3
"""
ETL State Management CLI tool.

Provides commands to check, update, and reset ETL state for different sources.
Useful for administrators and debugging ETL processes.
"""
import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from permit_leads.etl_state import ETLStateManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_last_run(args):
    """Check the last run timestamp for a source."""
    state_manager = ETLStateManager()
    last_run = state_manager.get_last_run(args.source)
    
    if last_run:
        print(f"Last run for '{args.source}': {last_run}")
        
        # Calculate next run timestamp
        since = state_manager.get_since_timestamp(args.source)
        print(f"Next run would start from: {since} (with 1-minute buffer)")
    else:
        print(f"No previous run found for '{args.source}'")
        
        # Show fallback timestamp
        since = state_manager.get_since_timestamp(args.source, fallback_days=args.fallback_days)
        print(f"Would use fallback timestamp: {since} ({args.fallback_days} days ago)")


def update_last_run(args):
    """Update the last run timestamp for a source."""
    state_manager = ETLStateManager()
    
    if args.timestamp:
        # Parse provided timestamp
        try:
            timestamp = datetime.fromisoformat(args.timestamp)
        except ValueError:
            print(f"Error: Invalid timestamp format '{args.timestamp}'. Use ISO format like '2025-01-15T10:30:00'")
            return
    else:
        # Use current time
        timestamp = datetime.utcnow()
    
    success = state_manager.update_last_run(args.source, timestamp)
    
    if success:
        print(f"✅ Updated last run for '{args.source}' to: {timestamp}")
    else:
        print(f"❌ Failed to update last run for '{args.source}'")


def list_sources(args):
    """List all known ETL sources and their last run timestamps."""
    state_manager = ETLStateManager()
    
    # Common sources that might exist
    sources = [
        'harris_issued_permits',
        'galveston_permits', 
        'houston_city_permits',
        'fort_bend_permits',
        'brazoria_permits'
    ]
    
    print("ETL State Summary:")
    print("==================")
    
    for source in sources:
        last_run = state_manager.get_last_run(source)
        if last_run:
            since = state_manager.get_since_timestamp(source)
            print(f"{source:<25} Last: {last_run}")
            print(f"{'':<25} Next: {since} (with buffer)")
        else:
            print(f"{source:<25} No previous run")
        print()


def reset_source(args):
    """Reset (delete) the ETL state for a source."""
    if not args.confirm:
        print(f"This will reset ETL state for '{args.source}'. Use --confirm to proceed.")
        return
    
    # Note: This would require a delete operation in the ETL state manager
    # For now, we'll just show what would happen
    print(f"⚠️  Would reset ETL state for '{args.source}'")
    print("Note: Reset functionality requires implementation of delete operation in ETL state manager")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="ETL State Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check last run for Harris County permits
  python etl_state_cli.py check harris_issued_permits
  
  # Update last run to current time
  python etl_state_cli.py update harris_issued_permits
  
  # Update last run to specific time
  python etl_state_cli.py update harris_issued_permits --timestamp "2025-01-15 14:30:00"
  
  # List all sources
  python etl_state_cli.py list
  
  # Reset a source (removes all state)
  python etl_state_cli.py reset harris_issued_permits --confirm
"""
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Check last run timestamp for a source')
    check_parser.add_argument('source', help='Source name (e.g., harris_issued_permits)')
    check_parser.add_argument('--fallback-days', type=int, default=7, 
                            help='Fallback days if no previous run (default: 7)')
    check_parser.set_defaults(func=check_last_run)
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update last run timestamp for a source')
    update_parser.add_argument('source', help='Source name (e.g., harris_issued_permits)')
    update_parser.add_argument('--timestamp', help='Specific timestamp (ISO format), current time if omitted')
    update_parser.set_defaults(func=update_last_run)
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all sources and their last run timestamps')
    list_parser.set_defaults(func=list_sources)
    
    # Reset command
    reset_parser = subparsers.add_parser('reset', help='Reset ETL state for a source')
    reset_parser.add_argument('source', help='Source name to reset')
    reset_parser.add_argument('--confirm', action='store_true', help='Confirm the reset operation')
    reset_parser.set_defaults(func=reset_source)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        args.func(args)
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()