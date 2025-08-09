#!/usr/bin/env python3
"""
Nightly lead scoring update job.

This script processes lead quality events from the last 30 days and updates
global lead scores with decay over time. It also identifies jurisdictions
that may need manual review based on score trends.
"""

import os
import sys
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class LeadScoreUpdate:
    """Data class for lead score updates."""
    lead_id: int
    current_score: float
    new_score: float
    total_weight: float
    event_count: int


@dataclass
class JurisdictionScore:
    """Data class for jurisdiction scoring metrics."""
    jurisdiction: str
    trade: Optional[str]
    avg_score: float
    lead_count: int
    score_change: float
    needs_review: bool


class LeadScoringJob:
    """Nightly lead scoring update job."""
    
    # Configuration constants
    MIN_SCORE = 0
    MAX_SCORE = 150
    DEFAULT_SCORE = 50
    DECAY_THRESHOLD_DAYS = 90
    DECAY_FACTOR = 0.5
    REVIEW_THRESHOLD = 30  # Avg score below this triggers review
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize the scoring job."""
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Connect to the database."""
        try:
            self.conn = psycopg2.connect(self.database_url)
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            logger.info("Connected to database")
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            raise
    
    def disconnect(self):
        """Disconnect from the database."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Disconnected from database")
    
    def get_quality_events_last_30_days(self) -> List[Dict]:
        """Fetch all lead quality events from the last 30 days."""
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        
        query = """
        SELECT 
            lead_id,
            event_type,
            weight,
            reason_code,
            created_at
        FROM lead_quality_events 
        WHERE created_at >= %s
        ORDER BY lead_id, created_at
        """
        
        self.cursor.execute(query, (thirty_days_ago,))
        events = self.cursor.fetchall()
        
        logger.info(f"Found {len(events)} quality events in last 30 days")
        return events
    
    def apply_decay_to_old_events(self) -> int:
        """Apply exponential decay to events older than 90 days."""
        decay_threshold = datetime.now(timezone.utc) - timedelta(days=self.DECAY_THRESHOLD_DAYS)
        
        # Update weights for old events
        update_query = """
        UPDATE lead_quality_events 
        SET weight = weight * %s
        WHERE created_at < %s 
        AND weight != 0  -- Don't decay already zero weights
        """
        
        self.cursor.execute(update_query, (self.DECAY_FACTOR, decay_threshold))
        updated_count = self.cursor.rowcount
        
        logger.info(f"Applied decay to {updated_count} events older than 90 days")
        return updated_count
    
    def calculate_lead_score_updates(self, events: List[Dict]) -> List[LeadScoreUpdate]:
        """Calculate new scores for leads based on quality events."""
        # Group events by lead_id
        lead_events = {}
        for event in events:
            lead_id = event['lead_id']
            if lead_id not in lead_events:
                lead_events[lead_id] = []
            lead_events[lead_id].append(event)
        
        # Get current scores for affected leads
        lead_ids = list(lead_events.keys())
        if not lead_ids:
            return []
        
        placeholders = ','.join(['%s'] * len(lead_ids))
        score_query = f"""
        SELECT id, global_score 
        FROM leads 
        WHERE id IN ({placeholders})
        """
        
        self.cursor.execute(score_query, lead_ids)
        current_scores = {row['id']: row['global_score'] or self.DEFAULT_SCORE 
                         for row in self.cursor.fetchall()}
        
        # Calculate updates
        updates = []
        for lead_id, lead_event_list in lead_events.items():
            current_score = current_scores.get(lead_id, self.DEFAULT_SCORE)
            
            # Sum up all weights for this lead
            total_weight = sum(event['weight'] for event in lead_event_list)
            
            # Calculate new score with bounds
            new_score = max(self.MIN_SCORE, 
                           min(self.MAX_SCORE, current_score + total_weight))
            
            updates.append(LeadScoreUpdate(
                lead_id=lead_id,
                current_score=current_score,
                new_score=new_score,
                total_weight=total_weight,
                event_count=len(lead_event_list)
            ))
        
        logger.info(f"Calculated score updates for {len(updates)} leads")
        return updates
    
    def update_lead_scores(self, updates: List[LeadScoreUpdate]) -> int:
        """Update lead scores in the database."""
        if not updates:
            return 0
        
        update_query = """
        UPDATE leads 
        SET global_score = %s, last_quality_update = %s
        WHERE id = %s
        """
        
        now = datetime.now(timezone.utc)
        update_data = [
            (update.new_score, now, update.lead_id)
            for update in updates
        ]
        
        self.cursor.executemany(update_query, update_data)
        updated_count = self.cursor.rowcount
        
        logger.info(f"Updated scores for {updated_count} leads")
        return updated_count
    
    def analyze_jurisdiction_scores(self) -> List[JurisdictionScore]:
        """Analyze average scores by jurisdiction and trade for manual review flags."""
        # Get current jurisdiction averages
        current_query = """
        SELECT 
            jurisdiction,
            unnest(trade_tags) as trade,
            AVG(global_score) as avg_score,
            COUNT(*) as lead_count
        FROM leads 
        WHERE global_score IS NOT NULL
        AND trade_tags IS NOT NULL
        GROUP BY jurisdiction, unnest(trade_tags)
        HAVING COUNT(*) >= 5  -- Only consider jurisdictions with enough data
        ORDER BY avg_score ASC
        """
        
        self.cursor.execute(current_query)
        current_stats = self.cursor.fetchall()
        
        # Calculate changes (for now, just mark low scores for review)
        # In a future enhancement, we could compare with historical averages
        jurisdiction_scores = []
        for stat in current_stats:
            needs_review = stat['avg_score'] < self.REVIEW_THRESHOLD
            
            jurisdiction_scores.append(JurisdictionScore(
                jurisdiction=stat['jurisdiction'],
                trade=stat['trade'],
                avg_score=float(stat['avg_score']),
                lead_count=stat['lead_count'],
                score_change=0.0,  # Would need historical data to calculate
                needs_review=needs_review
            ))
        
        review_count = sum(1 for js in jurisdiction_scores if js.needs_review)
        logger.info(f"Analyzed {len(jurisdiction_scores)} jurisdiction/trade combinations, "
                   f"{review_count} flagged for review")
        
        return jurisdiction_scores
    
    def log_review_flags(self, jurisdiction_scores: List[JurisdictionScore]):
        """Log jurisdictions flagged for manual review."""
        flagged = [js for js in jurisdiction_scores if js.needs_review]
        
        if flagged:
            logger.warning(f"MANUAL REVIEW REQUIRED: {len(flagged)} jurisdiction/trade combinations")
            for js in flagged:
                logger.warning(f"  {js.jurisdiction} - {js.trade}: "
                              f"avg_score={js.avg_score:.1f} ({js.lead_count} leads)")
        else:
            logger.info("No jurisdictions flagged for manual review")
    
    def run(self):
        """Execute the complete scoring update process."""
        logger.info("Starting nightly lead scoring update job")
        
        try:
            self.connect()
            
            # Apply decay to old events first
            self.apply_decay_to_old_events()
            
            # Get recent quality events
            events = self.get_quality_events_last_30_days()
            
            # Calculate score updates
            updates = self.calculate_lead_score_updates(events)
            
            # Update lead scores
            updated_count = self.update_lead_scores(updates)
            
            # Analyze jurisdiction scores
            jurisdiction_scores = self.analyze_jurisdiction_scores()
            
            # Log review flags
            self.log_review_flags(jurisdiction_scores)
            
            # Commit all changes
            self.conn.commit()
            
            logger.info(f"Job completed successfully. Updated {updated_count} lead scores.")
            
            # Return summary for external use
            return {
                'leads_updated': updated_count,
                'events_processed': len(events),
                'jurisdictions_analyzed': len(jurisdiction_scores),
                'review_flags': sum(1 for js in jurisdiction_scores if js.needs_review)
            }
            
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            logger.error(f"Job failed: {str(e)}")
            raise
        finally:
            self.disconnect()


def main():
    """Main entry point for command line execution."""
    try:
        job = LeadScoringJob()
        result = job.run()
        
        print(f"Lead scoring job completed:")
        print(f"  Leads updated: {result['leads_updated']}")
        print(f"  Events processed: {result['events_processed']}")
        print(f"  Jurisdictions analyzed: {result['jurisdictions_analyzed']}")
        print(f"  Review flags: {result['review_flags']}")
        
    except Exception as e:
        print(f"Job failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()