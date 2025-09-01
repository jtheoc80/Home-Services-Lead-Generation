"""
ETL State Management for tracking last successful scraping runs.

This module provides functionality to persist and retrieve last successful
run timestamps for different data sources to prevent data gaps and ensure
incremental data loading.
"""

import importlib.util
import logging
from datetime import datetime, timedelta
from typing import Optional
import os
from pathlib import Path

# Import Supabase client with better error handling
SUPABASE_AVAILABLE = False
supabase_client = None

try:
    import sys

    # Try multiple ways to import Supabase client
    backend_path_env = os.environ.get("BACKEND_PATH")
    if backend_path_env:
        backend_path = Path(backend_path_env)
    else:
        backend_path = Path(__file__).parent.parent / "backend"

    sys.path.insert(0, str(backend_path))

    # Test for availability without importing to avoid F401 errors
    try:
        spec = importlib.util.find_spec("app.supabase_client")
        if spec is not None:
            SUPABASE_AVAILABLE = True
    except ImportError:
        # Try alternative import test
        try:
            spec = importlib.util.find_spec("supabase")
            if spec is not None:
                SUPABASE_AVAILABLE = True
        except ImportError:
            pass
except ImportError:
    pass

logger = logging.getLogger(__name__)


class ETLStateManager:
    """
    Manages ETL state tracking using Supabase backend.

    Stores and retrieves last successful run timestamps for different
    data sources to enable incremental data loading and prevent gaps.
    """

    def __init__(self):
        """Initialize ETL state manager."""
        self.supabase = None
        self._init_supabase()

    def _init_supabase(self):
        """Initialize Supabase client if available."""
        if not SUPABASE_AVAILABLE:
            logger.warning(
                "Supabase client not available. ETL state tracking disabled."
            )
            return

        try:
            # Try to get client from backend first
            try:
                from app.supabase_client import get_supabase_client

                self.supabase = get_supabase_client()
                logger.debug("Supabase client initialized via backend")
            except ImportError:
                # Fallback to direct initialization
                from supabase import create_client

                supabase_url = os.getenv("SUPABASE_URL")
                supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv(
                    "SUPABASE_ANON_KEY"
                )

                if supabase_url and supabase_key:
                    self.supabase = create_client(supabase_url, supabase_key)
                    logger.debug("Supabase client initialized directly")
                else:
                    logger.warning("Supabase credentials not found in environment")

        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.supabase = None

    def get_last_run(self, source: str) -> Optional[datetime]:
        """
        Get the last successful run timestamp for a source.

        Args:
            source: Source identifier (e.g., 'harris_issued_permits')

        Returns:
            Last run timestamp or None if no previous run recorded
        """
        if not self.supabase:
            logger.warning(
                f"Supabase not available, cannot retrieve last run for {source}"
            )
            return None

        try:
            result = (
                self.supabase.table("etl_state")
                .select("last_run")
                .eq("source", source)
                .execute()
            )

            if result.data and len(result.data) > 0:
                last_run_str = result.data[0]["last_run"]
                # Parse ISO timestamp with timezone
                return datetime.fromisoformat(last_run_str.replace("Z", "+00:00"))
            else:
                logger.info(f"No previous run found for source: {source}")
                return None

        except Exception as e:
            logger.error(f"Failed to get last run for {source}: {e}")
            return None

    def update_last_run(self, source: str, timestamp: datetime) -> bool:
        """
        Update the last successful run timestamp for a source.

        This should only be called after a successful upsert operation,
        not after just fetching data.

        Args:
            source: Source identifier (e.g., 'harris_issued_permits')
            timestamp: Timestamp of the successful run

        Returns:
            True if update was successful, False otherwise
        """
        if not self.supabase:
            logger.warning(
                f"Supabase not available, cannot update last run for {source}"
            )
            return False

        try:
            # Use upsert to insert or update
            data = {
                "source": source,
                "last_run": timestamp.isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

            result = (
                self.supabase.table("etl_state")
                .upsert(data, on_conflict=["source"])
                .execute()
            )

            if result.data:
                logger.info(f"Updated last run for {source}: {timestamp}")
                return True
            else:
                logger.error(f"Failed to update last run for {source}")
                return False

        except Exception as e:
            logger.error(f"Failed to update last run for {source}: {e}")
            return False

    def get_since_timestamp(self, source: str, fallback_days: int = 7) -> datetime:
        """
        Get the timestamp to use for 'since' parameter with gap prevention.

        Args:
            source: Source identifier
            fallback_days: Days to look back if no previous run found

        Returns:
            Timestamp to use for incremental loading with 1-minute buffer
        """
        last_run = self.get_last_run(source)

        if last_run:
            # Subtract 1 minute to avoid gaps
            since_timestamp = last_run - timedelta(minutes=1)
            logger.info(
                f"Using last run minus 1 minute for {source}: {since_timestamp}"
            )
            return since_timestamp
        else:
            # First run, use fallback
            since_timestamp = datetime.utcnow() - timedelta(days=fallback_days)
            logger.info(
                f"No previous run for {source}, using {fallback_days} day fallback: {since_timestamp}"
            )
            return since_timestamp
