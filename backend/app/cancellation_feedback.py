#!/usr/bin/env python3
"""
Cancellation feedback service for lead scoring integration.

This service analyzes contractor cancellation patterns and provides:
1. Global scoring adjustments based on lead source cancellation rates
2. Personalized scoring adjustments based on individual contractor patterns
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any

import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CancellationFeedbackService:
    def __init__(self, db_url: str):
        """Initialize service with database connection."""
        self.db_url = db_url
        
    def connect_db(self):
        """Create database connection."""
        return psycopg2.connect(self.db_url)
    
    def calculate_global_source_adjustments(self, lookback_days: int = 90) -> Dict[str, Dict[str, float]]:
        """
        Calculate global cancellation rates by lead source.
        
        Returns:
            Dict mapping jurisdiction to cancellation metrics
        """
        logger.info("Calculating global source cancellation adjustments...")
        
        query = """
        WITH cancellation_stats AS (
            SELECT 
                l.jurisdiction,
                COUNT(DISTINCT c.account_id) as canceled_contractors,
                COUNT(DISTINCT lf.account_id) as total_contractors,
                AVG(c.avg_lead_score) as avg_canceled_lead_score,
                AVG(CASE WHEN c.primary_reason = 'poor_lead_quality' THEN 1.0 ELSE 0.0 END) as quality_complaint_rate
            FROM cancellations c
            JOIN lead_feedback lf ON c.account_id = lf.account_id
            JOIN leads l ON lf.lead_id = l.id
            WHERE c.canceled_at >= %s
            GROUP BY l.jurisdiction
        )
        SELECT 
            jurisdiction,
            CASE 
                WHEN total_contractors > 0 
                THEN CAST(canceled_contractors AS FLOAT) / total_contractors 
                ELSE 0.0 
            END as cancellation_rate,
            COALESCE(avg_canceled_lead_score, 0) as avg_canceled_score,
            COALESCE(quality_complaint_rate, 0) as quality_complaint_rate
        FROM cancellation_stats
        """
        
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        
        with self.connect_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, [cutoff_date])
                results = cursor.fetchall()
        
        adjustments = {}
        for row in results:
            jurisdiction = row['jurisdiction']
            cancellation_rate = row['cancellation_rate']
            quality_complaint_rate = row['quality_complaint_rate']
            
            # Calculate adjustment score (higher cancellation rate = lower score)
            # Scale: 0.0 cancellation rate = no adjustment, 0.5+ = -20 points max
            score_adjustment = min(0, -40 * cancellation_rate)
            
            # Additional penalty for quality complaints
            quality_penalty = -10 * quality_complaint_rate
            
            adjustments[jurisdiction] = {
                'cancellation_rate': cancellation_rate,
                'avg_canceled_score': row['avg_canceled_score'],
                'score_adjustment': score_adjustment + quality_penalty,
                'quality_complaint_rate': quality_complaint_rate
            }
        
        logger.info(f"Calculated adjustments for {len(adjustments)} jurisdictions")
        return adjustments
    
    def calculate_personalized_adjustments(self, account_id: str, lead_features: Dict[str, Any]) -> float:
        """
        Calculate personalized score adjustment based on contractor's cancellation history.
        
        Args:
            account_id: Contractor's account ID
            lead_features: Features of the lead being scored
            
        Returns:
            Score adjustment (-20 to +5)
        """
        query = """
        SELECT 
            primary_reason,
            secondary_reasons,
            avg_lead_score,
            preferred_service_areas,
            preferred_trade_types,
            total_leads_purchased,
            leads_won
        FROM cancellations
        WHERE account_id = %s
        ORDER BY canceled_at DESC
        LIMIT 1
        """
        
        with self.connect_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, [account_id])
                cancellation = cursor.fetchone()
        
        if not cancellation:
            return 0.0  # No cancellation history
        
        adjustment = 0.0
        
        # Analyze primary cancellation reason
        primary_reason = cancellation['primary_reason']
        if primary_reason == 'poor_lead_quality':
            adjustment -= 15.0  # Strong negative signal
        elif primary_reason in ['wrong_lead_type', 'leads_not_qualified']:
            adjustment -= 10.0  # Moderate negative signal
        elif primary_reason in ['leads_too_expensive', 'too_many_competitors']:
            adjustment -= 5.0   # Light negative signal
        elif primary_reason in ['seasonal_business', 'financial_issues']:
            adjustment += 2.0   # Not lead quality related
        
        # Check geographic preferences
        preferred_areas = cancellation.get('preferred_service_areas', [])
        lead_jurisdiction = lead_features.get('jurisdiction', '')
        if preferred_areas and lead_jurisdiction not in preferred_areas:
            adjustment -= 8.0
        
        # Check trade type preferences
        preferred_trades = cancellation.get('preferred_trade_types', [])
        lead_trade_tags = lead_features.get('trade_tags', [])
        if preferred_trades and not any(tag in preferred_trades for tag in lead_trade_tags):
            adjustment -= 5.0
        
        # Consider historical performance
        total_leads = cancellation.get('total_leads_purchased', 0)
        leads_won = cancellation.get('leads_won', 0)
        if total_leads > 10:  # Enough data
            win_rate = leads_won / total_leads
            if win_rate < 0.05:  # Very low win rate
                adjustment -= 10.0
            elif win_rate < 0.10:  # Low win rate
                adjustment -= 5.0
        
        # Clamp adjustment to reasonable range
        return max(-20.0, min(5.0, adjustment))
    
    def update_lead_cancellation_scores(self, batch_size: int = 1000):
        """
        Update cancellation feedback scores for all leads in batches.
        """
        logger.info("Updating lead cancellation scores...")
        
        # Get global adjustments
        global_adjustments = self.calculate_global_source_adjustments()
        
        # Update leads in batches
        with self.connect_db() as conn:
            with conn.cursor() as cursor:
                # Get total count
                cursor.execute("SELECT COUNT(*) FROM leads WHERE created_at >= %s", 
                             [datetime.now() - timedelta(days=30)])
                total_leads = cursor.fetchone()[0]
                
                # Process in batches
                offset = 0
                updated_count = 0
                
                while offset < total_leads:
                    # Get batch of leads
                    cursor.execute("""
                        SELECT id, jurisdiction, trade_tags, value, address
                        FROM leads 
                        WHERE created_at >= %s
                        ORDER BY id
                        LIMIT %s OFFSET %s
                    """, [datetime.now() - timedelta(days=30), batch_size, offset])
                    
                    leads = cursor.fetchall()
                    if not leads:
                        break
                    
                    # Update each lead
                    for lead in leads:
                        lead_id, jurisdiction, trade_tags, value, address = lead
                        
                        # Get global adjustment for this jurisdiction
                        global_adj = global_adjustments.get(jurisdiction, {})
                        cancellation_rate = global_adj.get('cancellation_rate', 0)
                        avg_canceled_score = global_adj.get('avg_canceled_score', 0)
                        
                        # Update the lead
                        cursor.execute("""
                            UPDATE leads 
                            SET 
                                source_cancellation_rate = %s,
                                source_avg_cancellation_score = %s,
                                updated_at = now()
                            WHERE id = %s
                        """, [cancellation_rate, avg_canceled_score, lead_id])
                        
                        updated_count += 1
                    
                    conn.commit()
                    offset += batch_size
                    
                    if offset % 5000 == 0:
                        logger.info(f"Updated {updated_count} leads...")
        
        logger.info(f"Updated cancellation scores for {updated_count} leads")
        return updated_count

def main():
    """Main entry point for cancellation feedback service."""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return
    
    service = CancellationFeedbackService(db_url)
    
    # Update lead scores with cancellation feedback
    service.update_lead_cancellation_scores()
    
    logger.info("Cancellation feedback service completed")

if __name__ == "__main__":
    main()