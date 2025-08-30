#!/usr/bin/env python3
"""
Dallas County permit scraping fallback script
Converts --since=3d format to --days argument for permit_leads CLI
"""

import argparse
import subprocess
import sys
import re
import math


def parse_time_string(time_str):
    """Convert time string like 3d, 24h, 5m to days."""
    match = re.match(r"^(\d+)([dhm])$", time_str)
    if not match:
        raise ValueError(
            f"Invalid time format: {time_str}. Use format like 3d, 24h, 5m"
        )

    value, unit = match.groups()
    num = int(value)

    if unit == "d":
        return num  # days
    elif unit == "h":
        return max(1, math.ceil(num / 24))  # hours to days (round up, at least 1)
    elif unit == "m":
        return max(
            1, math.ceil(num / (24 * 60))
        )  # minutes to days (round up, at least 1)
    else:
        raise ValueError(f"Unknown time unit: {unit}")


def main():
    parser = argparse.ArgumentParser(
        description="Dallas County permit scraping wrapper"
    )
    parser.add_argument("--since", default="7d", help="Time period (e.g., 3d, 24h, 5m)")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--sample", action="store_true", help="Use sample data")
    parser.add_argument("--retries", type=int, default=3, help="Number of retries")
    parser.add_argument(
        "--formats",
        nargs="+",
        default=["csv", "sqlite", "jsonl"],
        help="Output formats",
    )

    args, unknown_args = parser.parse_known_args()

    # Convert since to days
    try:
        days = parse_time_string(args.since)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Build permit_leads command
    cmd = [
        "python",
        "-m",
        "permit_leads",
        "scrape",
        "--jurisdiction",
        "tx-dallas",
        "--days",
        str(days),
    ]

    # Add formats
    if args.formats:
        cmd.extend(["--formats"] + args.formats)

    # Add optional flags
    if args.verbose:
        cmd.append("--verbose")
    if args.dry_run:
        cmd.append("--dry-run")
    if args.sample:
        cmd.append("--sample")
    if args.retries != 3:
        cmd.extend(["--retries", str(args.retries)])

    # Add any unknown arguments
    cmd.extend(unknown_args)

    print(f"Running: {' '.join(cmd)}")

    # Execute the permit_leads command
    try:
        result = subprocess.run(cmd, check=True)
        sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        print(f"Failed to run permit_leads: {e}", file=sys.stderr)
        sys.exit(e.returncode)
    except Exception as e:
        print(f"Failed to start permit_leads: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
