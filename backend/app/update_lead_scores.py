#!/usr/bin/env python3
"""
Lead Scoring Job with Feedback Integration

This script updates lead scores nightly, incorporating quality feedback events
with decay rules and personalized scoring adjustments.
"""

import os
import sys
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime
from typing import Dict
import math

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/tmp/lead_scoring.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class LeadScorer:
    def __init__(self, database_url: str):
        """Initialize with database connection."""
        self.database_url = database_url
        self.conn = None

    def connect(self):
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(self.database_url)
            self.conn.autocommit = False
            logger.info("Connected to database successfully")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def calculate_decay_factor(
        self, event_date: datetime, half_life_days: int = 90
    ) -> float:
        """
        Calculate decay factor using exponential decay with specified half-life.

        Args:
            event_date: When the event occurred
            half_life_days: Half-life in days (default 90 for feedback events)

        Returns:
            Decay factor between 0 and 1
        """
        days_old = (datetime.now() - event_date).days
        if days_old <= 0:
            return 1.0

        # Exponential decay: value = initial * (1/2)^(time/half_life)
        decay_factor = math.pow(0.5, days_old / half_life_days)
        return max(0.01, decay_factor)  # Minimum 1% weight

    def get_feedback_score(self, lead_id: int) -> float:
        """
        Calculate feedback score for a lead with decay.

        Args:
            lead_id: Lead identifier

        Returns:
            Weighted feedback score
        """
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Get all feedback events for this lead
                cur.execute(
                    """
                    SELECT event_type, weight, created_at
                    FROM lead_quality_events 
                    WHERE lead_id = %s
                    ORDER BY created_at DESC
                """,
                    (lead_id,),
                )

                events = cur.fetchall()

                if not events:
                    return 0.0

                total_weighted_score = 0.0
                total_weight = 0.0

                for event in events:
                    # Apply decay based on event age
                    decay_factor = self.calculate_decay_factor(event["created_at"])
                    weighted_score = event["weight"] * decay_factor

                    total_weighted_score += weighted_score
                    total_weight += decay_factor

                # Return average weighted score
                if total_weight > 0:
                    return total_weighted_score / total_weight
                else:
                    return 0.0

        except Exception as e:
            logger.error(f"Error calculating feedback score for lead {lead_id}: {e}")
            return 0.0

    def get_personalized_weights(self, account_id: str) -> Dict[str, float]:
        """
        Calculate personalized weights based on user's negative feedback patterns.

        Args:
            account_id: User account identifier

        Returns:
            Dictionary of trade/jurisdiction weights (lower = user tends to downvote)
        """
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Get user's negative feedback patterns by trade/jurisdiction
                cur.execute(
                    """
                    SELECT 
                        l.trade_tags,
                        l.jurisdiction,
                        COUNT(CASE WHEN lqe.event_type = 'feedback_negative' THEN 1 END) as negative_count,
                        COUNT(*) as total_feedback
                    FROM lead_quality_events lqe
                    JOIN leads l ON l.id = lqe.lead_id
                    WHERE lqe.account_id = %s
                      AND lqe.created_at >= NOW() - INTERVAL '180 days'  -- Last 6 months
                    GROUP BY l.trade_tags, l.jurisdiction
                    HAVING COUNT(*) >= 3  -- At least 3 feedback events
                """,
                    (account_id,),
                )

                patterns = cur.fetchall()
                weights = {}

                for pattern in patterns:
                    negative_ratio = (
                        pattern["negative_count"] / pattern["total_feedback"]
                    )

                    # If user has >60% negative feedback for a category, reduce weight
                    if negative_ratio > 0.6:
                        weight_reduction = min(
                            0.5, negative_ratio - 0.4
                        )  # Max 50% reduction
                        category_weight = 1.0 - weight_reduction

                        # Apply to trade tags
                        if pattern["trade_tags"]:
                            for tag in pattern["trade_tags"]:
                                weights[f"trade_{tag}"] = min(
                                    weights.get(f"trade_{tag}", 1.0), category_weight
                                )

                        # Apply to jurisdiction
                        if pattern["jurisdiction"]:
                            weights[f"jurisdiction_{pattern['jurisdiction']}"] = min(
                                weights.get(
                                    f"jurisdiction_{pattern['jurisdiction']}", 1.0
                                ),
                                category_weight,
                            )

                return weights

        except Exception as e:
            logger.error(
                f"Error calculating personalized weights for user {account_id}: {e}"
            )
            return {}

    def calculate_base_score(self, lead: Dict) -> float:
        """
        Calculate base lead score using existing rules-based scoring.
        This replicates the logic from score-leads.ts
        """
        score = 0.0

        # Recency scoring (max 25 points, 3x weight)
        if lead.get("created_at"):
            days_old = (datetime.now() - lead["created_at"]).days
            recency_score = max(0, min(25, 25 - days_old))
            score += recency_score * 3

        # Trade match scoring (max 25 points, 2x weight)
        trade_scores = {
            "roofing": 25,
            "kitchen": 24,
            "bath": 22,
            "pool": 20,
            "fence": 15,
            "windows": 18,
            "foundation": 22,
            "solar": 20,
            "hvac": 18,
            "electrical": 16,
            "plumbing": 16,
        }

        max_trade_score = 0
        if lead.get("trade_tags"):
            max_trade_score = max(
                [trade_scores.get(tag, 0) for tag in lead["trade_tags"]] + [0]
            )
        score += max_trade_score * 2

        # Project value scoring (max 25 points, 2x weight)
        value_score = 0
        if lead.get("value"):
            value = lead["value"]
            if value >= 50000:
                value_score = 25
            elif value >= 15000:
                value_score = 20
            elif value >= 5000:
                value_score = 15
            else:
                value_score = 10
        score += value_score * 2

        # Property age scoring (max 15 points, 1x weight)
        if lead.get("year_built"):
            age = datetime.now().year - lead["year_built"]
            if age >= 25:
                age_score = 15
            elif age >= 15:
                age_score = 12
            elif age >= 10:
                age_score = 8
            else:
                age_score = 5
            score += age_score

        # Owner type scoring (max 10 points, 1x weight)
        owner_score = 5  # default
        if lead.get("owner_kind") == "individual":
            owner_score = 10
        elif lead.get("owner_kind") == "llc":
            owner_score = 7
        score += owner_score

        return min(100, score)

    def update_lead_scores(self, batch_size: int = 1000):
        """
        Update lead scores for all leads, incorporating feedback.

        Args:
            batch_size: Number of leads to process in each batch
        """
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Get total count for progress tracking
                cur.execute("SELECT COUNT(*) as count FROM leads")
                total_leads = cur.fetchone()["count"]
                logger.info(
                    f"Processing {total_leads} leads in batches of {batch_size}"
                )

                processed = 0

                # Process leads in batches
                offset = 0
                while offset < total_leads:
                    cur.execute(
                        """
                        SELECT id, created_at, trade_tags, value, year_built, owner_kind, jurisdiction
                        FROM leads
                        ORDER BY id
                        LIMIT %s OFFSET %s
                    """,
                        (batch_size, offset),
                    )

                    leads = cur.fetchall()

                    if not leads:
                        break

                    for lead in leads:
                        try:
                            # Calculate base score
                            base_score = self.calculate_base_score(dict(lead))

                            # Calculate feedback adjustment
                            feedback_score = self.get_feedback_score(lead["id"])

                            # Combine scores (feedback can add/subtract up to 20 points)
                            final_score = base_score + min(20, max(-20, feedback_score))
                            final_score = max(0, min(100, final_score))

                            # Update lead_outcomes table
                            cur.execute(
                                """
                                INSERT INTO lead_outcomes (lead_id, calibrated_score, updated_at)
                                VALUES (%s, %s, %s)
                                ON CONFLICT (lead_id) DO UPDATE SET
                                    calibrated_score = EXCLUDED.calibrated_score,
                                    updated_at = EXCLUDED.updated_at
                            """,
                                (lead["id"], final_score, datetime.now()),
                            )

                            processed += 1

                            if processed % 100 == 0:
                                logger.info(
                                    f"Processed {processed}/{total_leads} leads"
                                )

                        except Exception as e:
                            logger.error(f"Error processing lead {lead['id']}: {e}")
                            continue

                    # Commit batch
                    self.conn.commit()
                    offset += batch_size

                logger.info(f"Successfully updated scores for {processed} leads")

        except Exception as e:
            logger.error(f"Error in update_lead_scores: {e}")
            if self.conn:
                self.conn.rollback()
            raise

    def run_scoring_job(self):
        """Run the complete scoring job."""
        start_time = datetime.now()
        logger.info("Starting lead scoring job")

        try:
            self.connect()
            self.update_lead_scores()

            duration = datetime.now() - start_time
            logger.info(f"Lead scoring job completed successfully in {duration}")

        except Exception as e:
            logger.error(f"Lead scoring job failed: {e}")
            raise
        finally:
            self.close()


def main():
    """Main entry point for the scoring job."""
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable is required")
        sys.exit(1)

    # Initialize and run scorer
    scorer = LeadScorer(database_url)

    try:
        scorer.run_scoring_job()
        logger.info("Lead scoring job completed successfully")

    except Exception as e:
        logger.error(f"Lead scoring job failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
