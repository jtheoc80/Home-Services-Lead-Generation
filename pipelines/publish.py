"""
Publishing pipeline for computing lead scores and publishing to gold.lead_scores.

This module processes newly normalized permits, computes lead scores using
scoring.v0.score_v0, and upserts results into gold.lead_scores table.
"""

import logging
import os
import sys
import hashlib
import psycopg2
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from psycopg2.extras import RealDictCursor

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scoring.v0 import score_v0

logger = logging.getLogger(__name__)


class LeadPublisher:
    """Pipeline for computing and publishing lead scores."""

    def __init__(self, db_url: Optional[str] = None):
        """Initialize publisher with database connection."""
        self.db_url = db_url or os.environ.get("DATABASE_URL")
        if not self.db_url:
            raise ValueError(
                "DATABASE_URL must be provided or set as environment variable"
            )

    def _get_connection(self):
        """Get database connection."""
        return psycopg2.connect(self.db_url)

    def _ensure_lead_scores_exists(self):
        """Ensure gold.lead_scores table exists."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'gold' 
                            AND table_name = 'lead_scores'
                        )
                    """
                    )
                    exists = cur.fetchone()[0]

                    if not exists:
                        logger.error(
                            "gold.lead_scores table does not exist. Run 'make db-migrate' first."
                        )
                        raise Exception("gold.lead_scores table not found")

                    logger.info("gold.lead_scores table exists")
        except Exception as e:
            logger.error(f"Failed to check gold.lead_scores table: {e}")
            raise

    def get_new_or_updated_permits(
        self, since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get permits that are new or updated since last scoring run.

        Args:
            since: Timestamp to get permits since (default: last 24 hours)

        Returns:
            List of permit records
        """
        if since is None:
            since = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )  # Today

        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Get permits updated since the specified time
                    cur.execute(
                        """
                        SELECT 
                            source_id, permit_id, jurisdiction, city, county,
                            status, permit_type, subtype, work_class, description,
                            applied_at, issued_at, finaled_at,
                            address_full, postal_code, parcel_id, valuation,
                            contractor_name, contractor_license,
                            latitude, longitude, updated_at
                        FROM gold.permits 
                        WHERE updated_at >= %s
                        ORDER BY updated_at DESC
                    """,
                        (since,),
                    )

                    results = cur.fetchall()
                    logger.info(f"Found {len(results)} permits updated since {since}")

                    return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Failed to get new permits: {e}")
            raise

    def convert_permit_to_lead(self, permit: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a permit record to lead format for scoring.

        Args:
            permit: Permit record from gold.permits

        Returns:
            Lead record compatible with scoring.v0.score_v0
        """
        # Generate lead ID from permit
        lead_id = hashlib.sha1(
            f"{permit['source_id']}||{permit['permit_id']}".encode()
        ).hexdigest()

        # Convert permit to lead format
        lead = {
            "lead_id": lead_id,
            "permit_id": permit["permit_id"],
            "source_id": permit["source_id"],
            "jurisdiction": permit["jurisdiction"],
            "city": permit["city"],
            # Scoring fields
            "created_at": permit.get("issued_at")
            or permit.get("applied_at")
            or datetime.now(),
            "value": permit.get("valuation"),
            "trade_tags": self._extract_trade_tags(permit),
            "year_built": None,  # Not available in permit data typically
            "owner_kind": self._infer_owner_kind(permit),
            # Additional context
            "address": permit.get("address_full"),
            "description": permit.get("description"),
            "permit_type": permit.get("permit_type"),
            "work_class": permit.get("work_class"),
            "status": permit.get("status"),
            "contractor_name": permit.get("contractor_name"),
        }

        return lead

    def _extract_trade_tags(self, permit: Dict[str, Any]) -> List[str]:
        """
        Extract trade tags from permit data for scoring.

        Args:
            permit: Permit record

        Returns:
            List of trade category tags
        """
        tags = []

        # Combine relevant text fields
        text_fields = [
            permit.get("description", ""),
            permit.get("permit_type", ""),
            permit.get("work_class", ""),
            permit.get("subtype", ""),
        ]

        combined_text = " ".join(str(field) for field in text_fields if field).upper()

        # Trade detection patterns
        trade_patterns = {
            "roofing": ["ROOF", "ROOFING", "SHINGLE", "REROOF"],
            "kitchen": ["KITCHEN", "REMODEL", "CABINET", "COUNTERTOP"],
            "bath": ["BATH", "BATHROOM", "SHOWER", "TUB"],
            "pool": ["POOL", "SPA", "SWIMMING"],
            "fence": ["FENCE", "FENCING"],
            "windows": ["WINDOW", "WINDOWS", "GLASS"],
            "foundation": ["FOUNDATION", "CONCRETE", "SLAB"],
            "solar": ["SOLAR", "PHOTOVOLTAIC", "PV"],
            "hvac": ["HVAC", "AIR CONDITIONING", "HEATING", "AC"],
            "electrical": ["ELECTRICAL", "ELECTRIC", "WIRING"],
            "plumbing": ["PLUMBING", "PLUMBER", "WATER", "SEWER"],
        }

        for trade, patterns in trade_patterns.items():
            if any(pattern in combined_text for pattern in patterns):
                tags.append(trade)

        return tags

    def _infer_owner_kind(self, permit: Dict[str, Any]) -> str:
        """
        Infer owner type from available permit data.

        Args:
            permit: Permit record

        Returns:
            Owner kind ('individual', 'llc', or 'unknown')
        """
        # Look at contractor name for clues
        contractor_name = permit.get("contractor_name", "").upper()

        if any(
            suffix in contractor_name for suffix in ["LLC", "CORP", "INC", "COMPANY"]
        ):
            return "llc"
        elif contractor_name and any(
            indicator in contractor_name for indicator in ["OWNER", "SELF"]
        ):
            return "individual"
        else:
            return "unknown"  # Default when we can't determine

    def compute_and_publish_scores(
        self, permits: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compute lead scores and publish to gold.lead_scores.

        Args:
            permits: List of permit records to score

        Returns:
            Publishing results
        """
        self._ensure_lead_scores_exists()

        if not permits:
            logger.info("No permits to score")
            return {"processed": 0, "published": 0, "errors": 0}

        processed = 0
        published = 0
        errors = 0

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    for permit in permits:
                        try:
                            # Convert permit to lead format
                            lead = self.convert_permit_to_lead(permit)

                            # Compute score using v0 algorithm
                            score_result = score_v0(lead)

                            # Upsert score to gold.lead_scores
                            self._upsert_lead_score(
                                cur,
                                lead_id=lead["lead_id"],
                                version="v0",
                                score=score_result["score"],
                                reasons=score_result["reasons"],
                            )

                            processed += 1
                            published += 1

                            if processed % 100 == 0:
                                logger.info(f"Processed {processed} permits...")

                        except Exception as e:
                            logger.error(
                                f"Failed to score permit {permit.get('permit_id')}: {e}"
                            )
                            errors += 1

                    # Commit all changes
                    conn.commit()
                    logger.info(f"Published {published} lead scores, {errors} errors")

        except Exception as e:
            logger.error(f"Failed to publish scores: {e}")
            raise

        return {"processed": processed, "published": published, "errors": errors}

    def _upsert_lead_score(
        self, cursor, lead_id: str, version: str, score: int, reasons: List[str]
    ):
        """
        Upsert a lead score into gold.lead_scores.

        Args:
            cursor: Database cursor
            lead_id: Unique lead identifier
            version: Scoring version (e.g., 'v0')
            score: Computed score (0-100)
            reasons: List of scoring reason strings
        """
        upsert_sql = """
            INSERT INTO gold.lead_scores (lead_id, version, score, reasons, created_at)
            VALUES (%s, %s, %s, %s, NOW())
            ON CONFLICT (lead_id, version) DO UPDATE SET
                score = EXCLUDED.score,
                reasons = EXCLUDED.reasons,
                created_at = NOW()
        """

        cursor.execute(upsert_sql, (lead_id, version, score, reasons))


def publish_from_normalization_results(
    normalization_results: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Publish lead scores from normalization pipeline results.

    Args:
        normalization_results: Results from pipelines.normalize_permits

    Returns:
        Publishing results
    """
    if normalization_results.get("total_upserted", 0) == 0:
        logger.info("No new permits to score")
        return {"processed": 0, "published": 0, "errors": 0}

    # Get permits updated in the last day (covers this run)
    publisher = LeadPublisher()
    permits = publisher.get_new_or_updated_permits()

    return publisher.compute_and_publish_scores(permits)


def main():
    """
    Main entry point for lead score publishing.

    Can be run standalone to score recent permits.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Compute and publish lead scores")
    parser.add_argument(
        "--db-url", help="PostgreSQL connection URL (or set DATABASE_URL env var)"
    )
    parser.add_argument("--since", help="Score permits since this date (YYYY-MM-DD)")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Check database URL
    db_url = args.db_url or os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL required (--db-url or DATABASE_URL env var)")
        return 1

    try:
        publisher = LeadPublisher(db_url)

        # Parse since date if provided
        since = None
        if args.since:
            since = datetime.strptime(args.since, "%Y-%m-%d")

        # Get permits to score
        permits = publisher.get_new_or_updated_permits(since)

        if not permits:
            logger.info("No permits found to score")
            return 0

        # Compute and publish scores
        results = publisher.compute_and_publish_scores(permits)

        print("Lead scoring complete:")
        print(f"  Processed: {results['processed']}")
        print(f"  Published: {results['published']}")
        print(f"  Errors: {results['errors']}")

        return 0

    except Exception as e:
        logger.error(f"Publishing failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
