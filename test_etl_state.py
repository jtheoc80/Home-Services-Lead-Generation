#!/usr/bin/env python3
"""
Test script for ETL state management functionality.

This script tests the ETL state manager and demonstrates
how it tracks last run timestamps for Harris County permits.
"""
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add permit_leads to path
sys.path.append(str(Path(__file__).parent.parent))

from permit_leads.etl_state import ETLStateManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_etl_state_manager():
    """Test the ETL state manager functionality."""
    logger.info("Testing ETL State Manager...")

    # Initialize state manager
    state_manager = ETLStateManager()

    source = "harris_issued_permits"

    # Test getting last run (should be None initially)
    logger.info(f"Getting last run for {source}...")
    last_run = state_manager.get_last_run(source)
    logger.info(f"Last run: {last_run}")

    # Test getting since timestamp with fallback
    logger.info("Getting since timestamp...")
    since = state_manager.get_since_timestamp(source, fallback_days=7)
    logger.info(f"Since timestamp: {since}")

    # Test updating last run
    current_time = datetime.utcnow()
    logger.info(f"Updating last run to: {current_time}")
    success = state_manager.update_last_run(source, current_time)
    logger.info(f"Update successful: {success}")

    if success:
        # Verify the update
        logger.info("Verifying update...")
        last_run = state_manager.get_last_run(source)
        logger.info(f"New last run: {last_run}")

        # Test since timestamp with existing last run
        since = state_manager.get_since_timestamp(source)
        logger.info(f"Since timestamp with buffer: {since}")

        # Verify buffer is applied
        if last_run:
            expected_since = last_run - timedelta(minutes=1)
            if abs((since - expected_since).total_seconds()) < 1:
                logger.info("✅ Buffer correctly applied")
            else:
                logger.warning("❌ Buffer not correctly applied")


if __name__ == "__main__":
    test_etl_state_manager()
