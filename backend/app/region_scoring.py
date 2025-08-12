"""
Region-aware scoring enhancements for LeadLedgerPro.

Adds region-specific calibration and scoring adjustments to the ML pipeline.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

import pandas as pd
from sklearn.isotonic import IsotonicRegression
import psycopg2

logger = logging.getLogger(__name__)


class RegionAwareScoring:
    """Region-aware scoring calibration and adjustments."""
    
    def __init__(self, db_url: str):
        """Initialize region-aware scoring."""
        self.db_url = db_url
        self.region_calibrators = {}
        self.state_calibrators = {}
        self.regional_score_adjustments = {}
    
    def connect_db(self):
        """Create database connection."""
        return psycopg2.connect(self.db_url)
    
    def load_regional_performance_data(self) -> pd.DataFrame:
        """Load performance data by region for calibration."""
        conn = self.connect_db()
        try:
            query = """
                SELECT 
                    l.lead_score,
                    l.state,
                    l.region_id,
                    r.slug as region_slug,
                    r.level as region_level,
                    j.slug as jurisdiction_slug,
                    j.data_provider,
                    
                    f.rating,
                    CASE 
                        WHEN f.rating IN ('quoted', 'won') THEN 1 
                        ELSE 0 
                    END as success
                    
                FROM leads l
                JOIN lead_feedback f ON l.id = f.lead_id
                LEFT JOIN regions r ON l.region_id = r.id
                LEFT JOIN jurisdictions j ON l.jurisdiction_id = j.id
                
                WHERE f.rating IS NOT NULL
                AND l.lead_score IS NOT NULL
                AND l.created_at >= NOW() - INTERVAL '6 months'
            """
            
            df = pd.read_sql(query, conn)
            logger.info(f"Loaded {len(df)} regional performance records")
            return df
            
        except Exception as e:
            logger.error(f"Error loading regional performance data: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    
    def train_region_calibrators(self) -> None:
        """Train per-region score calibrators."""
        df = self.load_regional_performance_data()
        
        if df.empty:
            logger.warning("No performance data available for calibration")
            return
        
        # Train state-level calibrators
        for state in df['state'].dropna().unique():
            state_data = df[df['state'] == state]
            
            if len(state_data) >= 10:  # Minimum sample size
                try:
                    calibrator = IsotonicRegression(out_of_bounds='clip')
                    calibrator.fit(state_data['lead_score'], state_data['success'])
                    self.state_calibrators[state] = calibrator
                    
                    logger.info(f"Trained calibrator for state {state} with {len(state_data)} samples")
                except Exception as e:
                    logger.warning(f"Failed to train calibrator for state {state}: {e}")
        
        # Train region-level calibrators for regions with sufficient data
        for region_slug in df['region_slug'].dropna().unique():
            region_data = df[df['region_slug'] == region_slug]
            
            if len(region_data) >= 20:  # Higher threshold for region-specific
                try:
                    calibrator = IsotonicRegression(out_of_bounds='clip')
                    calibrator.fit(region_data['lead_score'], region_data['success'])
                    self.region_calibrators[region_slug] = calibrator
                    
                    logger.info(f"Trained calibrator for region {region_slug} with {len(region_data)} samples")
                except Exception as e:
                    logger.warning(f"Failed to train calibrator for region {region_slug}: {e}")
    
    def calculate_regional_adjustments(self) -> None:
        """Calculate regional scoring adjustments based on performance data."""
        df = self.load_regional_performance_data()
        
        if df.empty:
            return
        
        # Calculate overall baseline performance
        baseline_conversion = df['success'].mean()
        
        # Calculate regional performance adjustments
        for region_slug in df['region_slug'].dropna().unique():
            region_data = df[df['region_slug'] == region_slug]
            
            if len(region_data) >= 10:
                region_conversion = region_data['success'].mean()
                
                # Calculate adjustment factor (multiplicative)
                if baseline_conversion > 0:
                    adjustment = region_conversion / baseline_conversion
                    self.regional_score_adjustments[region_slug] = adjustment
                    
                    logger.info(f"Region {region_slug}: conversion {region_conversion:.3f} vs baseline {baseline_conversion:.3f}, adjustment {adjustment:.3f}")
    
    def apply_region_calibration(self, lead_score: float, state: Optional[str] = None, 
                               region_slug: Optional[str] = None) -> float:
        """Apply region-specific calibration to a lead score."""
        
        # Try region-specific calibrator first
        if region_slug and region_slug in self.region_calibrators:
            calibrator = self.region_calibrators[region_slug]
            calibrated_score = calibrator.predict([lead_score])[0] * 100
            logger.debug(f"Applied region calibration for {region_slug}: {lead_score} -> {calibrated_score}")
            return calibrated_score
        
        # Fall back to state-level calibrator
        if state and state in self.state_calibrators:
            calibrator = self.state_calibrators[state]
            calibrated_score = calibrator.predict([lead_score])[0] * 100
            logger.debug(f"Applied state calibration for {state}: {lead_score} -> {calibrated_score}")
            return calibrated_score
        
        # No calibration available, return original score scaled to 0-100
        return min(100, max(0, lead_score))
    
    def apply_regional_adjustment(self, lead_score: float, region_slug: Optional[str] = None) -> float:
        """Apply regional scoring adjustment."""
        if region_slug and region_slug in self.regional_score_adjustments:
            adjustment = self.regional_score_adjustments[region_slug]
            adjusted_score = lead_score * adjustment
            
            # Clamp to 0-100 range
            adjusted_score = min(100, max(0, adjusted_score))
            
            logger.debug(f"Applied regional adjustment for {region_slug}: {lead_score} -> {adjusted_score}")
            return adjusted_score
        
        return lead_score
    
    def save_calibration_model(self, model_path: str) -> None:
        """Save calibration models to disk."""
        import pickle
        
        model_data = {
            'region_calibrators': self.region_calibrators,
            'state_calibrators': self.state_calibrators,
            'regional_score_adjustments': self.regional_score_adjustments,
            'created_at': pd.Timestamp.now().isoformat()
        }
        
        Path(model_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Saved calibration model to {model_path}")
    
    def load_calibration_model(self, model_path: str) -> bool:
        """Load calibration models from disk."""
        import pickle
        
        if not Path(model_path).exists():
            logger.warning(f"Calibration model not found: {model_path}")
            return False
        
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.region_calibrators = model_data.get('region_calibrators', {})
            self.state_calibrators = model_data.get('state_calibrators', {})
            self.regional_score_adjustments = model_data.get('regional_score_adjustments', {})
            
            logger.info(f"Loaded calibration model from {model_path}")
            logger.info(f"Loaded {len(self.region_calibrators)} region calibrators, {len(self.state_calibrators)} state calibrators")
            return True
            
        except Exception as e:
            logger.error(f"Error loading calibration model: {e}")
            return False
    
    def get_model_stats(self) -> Dict[str, Any]:
        """Get statistics about the calibration models."""
        return {
            'region_calibrators_count': len(self.region_calibrators),
            'state_calibrators_count': len(self.state_calibrators),
            'regional_adjustments_count': len(self.regional_score_adjustments),
            'available_regions': list(self.region_calibrators.keys()),
            'available_states': list(self.state_calibrators.keys()),
            'regional_adjustments': self.regional_score_adjustments
        }


def main():
    """CLI interface for region-aware scoring."""
    import sys
    from argparse import ArgumentParser
    
    parser = ArgumentParser(description="Region-aware scoring utilities")
    parser.add_argument("--train", action="store_true", help="Train regional calibrators")
    parser.add_argument("--save", help="Save calibration model to path")
    parser.add_argument("--load", help="Load calibration model from path")
    parser.add_argument("--stats", action="store_true", help="Show calibration model stats")
    parser.add_argument("--score", type=float, help="Test score to calibrate")
    parser.add_argument("--region", help="Region slug for testing")
    parser.add_argument("--state", help="State code for testing")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    scorer = RegionAwareScoring(db_url)
    
    try:
        if args.load:
            scorer.load_calibration_model(args.load)
        
        if args.train:
            logger.info("Training regional calibrators...")
            scorer.train_region_calibrators()
            scorer.calculate_regional_adjustments()
        
        if args.save:
            scorer.save_calibration_model(args.save)
        
        if args.stats:
            stats = scorer.get_model_stats()
            print(json.dumps(stats, indent=2))
        
        if args.score is not None:
            calibrated = scorer.apply_region_calibration(args.score, args.state, args.region)
            adjusted = scorer.apply_regional_adjustment(calibrated, args.region)
            
            print(f"Original score: {args.score}")
            print(f"Calibrated score: {calibrated:.2f}")
            print(f"Region-adjusted score: {adjusted:.2f}")
    
    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()