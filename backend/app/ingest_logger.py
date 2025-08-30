#!/usr/bin/env python3
"""
Ingest logging utility for tracking critical steps in the lead processing pipeline.

This module provides a utility function to log critical steps (fetch_page, parse, upsert, db_insert)
with a trace ID to enable debugging and monitoring of the lead processing flow.
"""

import logging
import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from .supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


def log_ingest_step(
    trace_id: str, stage: str, ok: bool, details: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Log a critical step in the lead ingestion pipeline.

    Args:
        trace_id: UUID to trace a specific lead through the ingestion pipeline
        stage: Stage name (e.g., "fetch_page", "parse", "upsert", "db_insert")
        ok: Whether the stage completed successfully
        details: Additional details about the stage execution (optional)

    Returns:
        True if logging was successful, False otherwise
    """
    try:
        # Validate inputs
        if not trace_id:
            logger.error("trace_id is required for ingest logging")
            return False

        if not stage:
            logger.error("stage is required for ingest logging")
            return False

        # Validate trace_id is a valid UUID
        try:
            uuid.UUID(trace_id)
        except ValueError:
            logger.error(f"Invalid trace_id format: {trace_id}")
            return False

        # Prepare log entry
        log_entry = {
            "trace_id": trace_id,
            "stage": stage,
            "ok": ok,
            "details": details or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # Insert into Supabase
        supabase = get_supabase_client()
        result = supabase.table("ingest_logs").insert(log_entry).execute()

        if result.data:
            logger.debug(
                f"Logged ingest step: trace_id={trace_id}, stage={stage}, ok={ok}"
            )
            return True
        else:
            logger.error("Failed to log ingest step: no data returned from Supabase")
            return False

    except Exception as e:
        logger.error(f"Error logging ingest step: {e}")
        logger.error(f"trace_id={trace_id}, stage={stage}, ok={ok}, details={details}")
        return False


def generate_trace_id() -> str:
    """
    Generate a new trace ID for tracking a lead through the ingestion pipeline.

    Returns:
        A new UUID4 string
    """
    return str(uuid.uuid4())


def get_trace_logs(trace_id: str) -> Optional[list]:
    """
    Retrieve all logs for a specific trace ID.

    Args:
        trace_id: The trace ID to retrieve logs for

    Returns:
        List of log entries for the trace ID, or None if error
    """
    try:
        # Validate trace_id is a valid UUID
        try:
            uuid.UUID(trace_id)
        except ValueError:
            logger.error(f"Invalid trace_id format: {trace_id}")
            return None

        supabase = get_supabase_client()
        result = (
            supabase.table("ingest_logs")
            .select("*")
            .eq("trace_id", trace_id)
            .order("created_at")
            .execute()
        )

        if result.data:
            return result.data
        else:
            logger.info(f"No logs found for trace_id: {trace_id}")
            return []

    except Exception as e:
        logger.error(f"Error retrieving trace logs: {e}")
        return None


class IngestTracer:
    """
    Context manager for tracking a lead through the ingestion pipeline with automatic logging.

    Usage:
        with IngestTracer() as tracer:
            tracer.log("fetch_page", True, {"url": "https://example.com"})
            tracer.log("parse", True, {"records_found": 50})
            tracer.log("upsert", False, {"error": "Database connection failed"})
    """

    def __init__(self, trace_id: Optional[str] = None):
        """
        Initialize tracer with optional existing trace_id.

        Args:
            trace_id: Existing trace ID, or None to generate a new one
        """
        self.trace_id = trace_id or generate_trace_id()
        self.stages_logged = []

    def __enter__(self):
        """Enter context manager."""
        logger.info(f"Starting ingest trace: {self.trace_id}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager with summary logging."""
        if exc_type is not None:
            # An exception occurred
            logger.error(
                f"Ingest trace {self.trace_id} ended with exception: {exc_type.__name__}: {exc_val}"
            )
            # Log the failure
            self.log(
                "exception",
                False,
                {
                    "exception_type": exc_type.__name__,
                    "exception_message": str(exc_val),
                    "stages_completed": self.stages_logged,
                },
            )
        else:
            logger.info(
                f"Ingest trace {self.trace_id} completed successfully with {len(self.stages_logged)} stages"
            )

    def log(
        self, stage: str, ok: bool, details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Log a stage in the current trace.

        Args:
            stage: Stage name (e.g., "fetch_page", "parse", "upsert", "db_insert")
            ok: Whether the stage completed successfully
            details: Additional details about the stage execution

        Returns:
            True if logging was successful, False otherwise
        """
        success = log_ingest_step(self.trace_id, stage, ok, details)
        if success:
            self.stages_logged.append(stage)
        return success
