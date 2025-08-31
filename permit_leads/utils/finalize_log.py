"""
Utility for finalizing ETL logging with standardized exit codes and record counts.

Provides a consistent way to:
- Write final summary to logs/etl_output.log
- Print RECORDS_PROCESSED=<n> for workflow parsing
- Exit with proper codes: 0 for success/no-data, 1 for failures
"""

from pathlib import Path
import sys


def finalize_log(records: int, ok: bool = True):
    """
    Finalize ETL logging and exit with appropriate code.

    Args:
        records: Number of records processed
        ok: True for success (exit 0), False for failure (exit 1)

    Exit codes:
        0: Success or "no new data" (expected empty result)
        1: Real failures/exceptions
    """
    # Ensure logs directory exists
    Path("logs").mkdir(parents=True, exist_ok=True)

    # Write final summary line to log file
    with open("logs/etl_output.log", "a", encoding="utf-8") as f:
        f.write(f"RECORDS_PROCESSED={records}\n")

    # Print summary for workflow parsing
    print(f"RECORDS_PROCESSED={records}")

    # Exit with appropriate code
    sys.exit(0 if ok else 1)
