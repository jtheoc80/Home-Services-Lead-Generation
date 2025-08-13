"""
Ingest state management for tracking incremental data loads.

This module provides functionality to read and write ingest state to the
meta.ingest_state table, enabling incremental data loading by remembering
the last successfully processed record timestamp for each source.
"""

import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class IngestStateManager:
    """Manages ingest state for incremental data loading."""
    
    def __init__(self, db_url: Optional[str] = None):
        """Initialize state manager with database connection."""
        self.db_url = db_url or os.environ.get('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL must be provided or set as environment variable")
    
    def _get_connection(self):
        """Get database connection."""
        return psycopg2.connect(self.db_url)
    
    def get_last_updated_seen(self, source_id: str) -> Optional[datetime]:
        """
        Get the last updated timestamp seen for a source.
        
        Args:
            source_id: Source identifier
            
        Returns:
            Last updated timestamp or None if no state exists
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        "SELECT last_updated_seen FROM meta.ingest_state WHERE source_id = %s",
                        (source_id,)
                    )
                    result = cur.fetchone()
                    return result['last_updated_seen'] if result else None
        except Exception as e:
            logger.error(f"Failed to get last updated seen for {source_id}: {e}")
            return None
    
    def update_state(
        self, 
        source_id: str, 
        last_updated_seen: Optional[datetime] = None,
        status: str = 'success'
    ) -> bool:
        """
        Update ingest state for a source.
        
        Args:
            source_id: Source identifier
            last_updated_seen: Latest record timestamp seen during this run
            status: Status of the ingest run ('success', 'error', 'partial')
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Use UPSERT to handle both new and existing records
                    cur.execute("""
                        INSERT INTO meta.ingest_state (source_id, last_run_at, last_updated_seen, last_status)
                        VALUES (%s, NOW(), %s, %s)
                        ON CONFLICT (source_id) DO UPDATE SET
                            last_run_at = NOW(),
                            last_updated_seen = COALESCE(EXCLUDED.last_updated_seen, meta.ingest_state.last_updated_seen),
                            last_status = EXCLUDED.last_status
                    """, (source_id, last_updated_seen, status))
                    conn.commit()
                    logger.info(f"Updated ingest state for {source_id}: status={status}")
                    return True
        except Exception as e:
            logger.error(f"Failed to update ingest state for {source_id}: {e}")
            return False
    
    def get_state(self, source_id: str) -> Optional[Dict[str, Any]]:
        """
        Get complete ingest state for a source.
        
        Args:
            source_id: Source identifier
            
        Returns:
            Dictionary with state information or None if not found
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        "SELECT * FROM meta.ingest_state WHERE source_id = %s",
                        (source_id,)
                    )
                    result = cur.fetchone()
                    return dict(result) if result else None
        except Exception as e:
            logger.error(f"Failed to get state for {source_id}: {e}")
            return None
    
    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """
        Get ingest states for all sources.
        
        Returns:
            Dictionary mapping source_id to state information
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT * FROM meta.ingest_state ORDER BY source_id")
                    results = cur.fetchall()
                    return {row['source_id']: dict(row) for row in results}
        except Exception as e:
            logger.error(f"Failed to get all states: {e}")
            return {}
    
    def reset_state(self, source_id: str) -> bool:
        """
        Reset ingest state for a source (for full refresh).
        
        Args:
            source_id: Source identifier
            
        Returns:
            True if reset successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM meta.ingest_state WHERE source_id = %s",
                        (source_id,)
                    )
                    conn.commit()
                    logger.info(f"Reset ingest state for {source_id}")
                    return True
        except Exception as e:
            logger.error(f"Failed to reset state for {source_id}: {e}")
            return False


def get_state_manager() -> IngestStateManager:
    """Get singleton state manager instance."""
    return IngestStateManager()


# Convenience functions for common operations
def get_last_updated_seen(source_id: str) -> Optional[datetime]:
    """Get last updated timestamp for a source."""
    return get_state_manager().get_last_updated_seen(source_id)


def update_last_updated_seen(source_id: str, timestamp: datetime, status: str = 'success') -> bool:
    """Update last updated timestamp for a source."""
    return get_state_manager().update_state(source_id, timestamp, status)


def reset_source_state(source_id: str) -> bool:
    """Reset state for a source (forces full refresh on next run)."""
    return get_state_manager().reset_state(source_id)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python state.py <command> [source_id]")
        print("Commands: list, get <source_id>, reset <source_id>")
        sys.exit(1)
    
    command = sys.argv[1]
    state_mgr = get_state_manager()
    
    if command == "list":
        states = state_mgr.get_all_states()
        print(f"Found {len(states)} source states:")
        for source_id, state in states.items():
            print(f"  {source_id}: last_run={state.get('last_run_at')}, status={state.get('last_status')}")
    
    elif command == "get" and len(sys.argv) > 2:
        source_id = sys.argv[2]
        state = state_mgr.get_state(source_id)
        if state:
            print(f"State for {source_id}:")
            for key, value in state.items():
                print(f"  {key}: {value}")
        else:
            print(f"No state found for {source_id}")
    
    elif command == "reset" and len(sys.argv) > 2:
        source_id = sys.argv[2]
        if state_mgr.reset_state(source_id):
            print(f"Reset state for {source_id}")
        else:
            print(f"Failed to reset state for {source_id}")
    
    else:
        print("Invalid command or missing source_id")
        sys.exit(1)