#!/usr/bin/env python3
"""
Prometheus metrics collection for Home Services Lead Generation backend.

This module provides Prometheus-style counters and histograms for monitoring
HTTP requests, request durations, and data ingestion metrics.
"""

import time
from typing import Dict
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client.registry import REGISTRY
import logging

logger = logging.getLogger(__name__)

# HTTP request metrics
http_requests_total = Counter(
    "http_requests_total", "Total number of HTTP requests", ["method", "path", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=(
        0.001,
        0.005,
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
        float("inf"),
    ),
)

# Data ingestion metrics
ingest_rows_total = Counter(
    "ingest_rows_total", "Total number of rows ingested", ["source", "status"]
)


class MetricsTracker:
    """Helper class for tracking metrics across the application."""

    def __init__(self):
        self.request_start_times: Dict[str, float] = {}

    def track_request_start(self, request_id: str) -> None:
        """Record the start time of a request."""
        self.request_start_times[request_id] = time.time()

    def track_request_end(
        self, request_id: str, method: str, path: str, status_code: int
    ) -> None:
        """Record the end of a request and update metrics."""
        # Clean up path to avoid high cardinality
        cleaned_path = self._clean_path(path)

        # Update request counter
        http_requests_total.labels(
            method=method, path=cleaned_path, status=str(status_code)
        ).inc()

        # Update duration histogram if we have start time
        if request_id in self.request_start_times:
            duration = time.time() - self.request_start_times[request_id]
            http_request_duration_seconds.labels(
                method=method, path=cleaned_path
            ).observe(duration)

            # Clean up start time
            del self.request_start_times[request_id]

        logger.debug(f"Tracked request: {method} {cleaned_path} -> {status_code}")

    def track_ingestion(
        self, source: str, rows_count: int, status: str = "success"
    ) -> None:
        """Track data ingestion metrics."""
        ingest_rows_total.labels(source=source, status=status).inc(rows_count)

        logger.debug(f"Tracked ingestion: {source} -> {rows_count} rows ({status})")

    def _clean_path(self, path: str) -> str:
        """Clean up path to avoid high cardinality in metrics."""
        # Remove query parameters
        if "?" in path:
            path = path.split("?")[0]

        # Replace UUIDs and IDs with placeholders to reduce cardinality
        import re

        # Replace UUID patterns
        path = re.sub(
            r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "/{uuid}",
            path,
        )

        # Replace numeric IDs
        path = re.sub(r"/\d+(?=/|$)", "/{id}", path)

        # Replace user IDs that might be strings
        path = re.sub(
            r"/api/subscription/status/[^/]+",
            "/api/subscription/status/{user_id}",
            path,
        )

        return path


# Global metrics tracker instance
metrics_tracker = MetricsTracker()


def get_metrics() -> str:
    """Generate Prometheus metrics output."""
    try:
        return generate_latest(REGISTRY).decode("utf-8")
    except Exception as e:
        logger.error(f"Error generating metrics: {str(e)}")
        raise


def get_metrics_content_type() -> str:
    """Get the content type for Prometheus metrics."""
    return CONTENT_TYPE_LATEST


def track_request_start(request_id: str) -> None:
    """Track the start of an HTTP request."""
    metrics_tracker.track_request_start(request_id)


def track_request_end(
    request_id: str, method: str, path: str, status_code: int
) -> None:
    """Track the end of an HTTP request."""
    metrics_tracker.track_request_end(request_id, method, path, status_code)


def track_ingestion(source: str, rows_count: int, status: str = "success") -> None:
    """Track data ingestion."""
    metrics_tracker.track_ingestion(source, rows_count, status)
