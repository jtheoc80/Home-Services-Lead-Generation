#!/usr/bin/env python3
"""
Nightly ML training script for lead success prediction.

This script trains a machine learning model to predict lead success based on
contractor feedback and lead characteristics. It produces a calibrated model
that can be used for API inference.
"""

import os
import json
import pickle
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import classification_report, roc_auc_score
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LeadMLTrainer:
    def __init__(self, db_url: str):
        """Initialize trainer with database connection."""
        self.db_url = db_url
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_columns = []
        self.model_version = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def connect_db(self):
        """Create database connection."""
        return psycopg2.connect(self.db_url)
    
    def load_training_data(self) -> pd.DataFrame:
        """Load feedback and lead data for training."""
        logger.info("Loading training data...")
        
        query = """
        SELECT 
            lf.lead_id,
            lf.rating,
            lf.deal_band,
            lf.reason_codes,
            lf.created_at as feedback_date,
            lo.win_label
        FROM lead_feedback lf
        LEFT JOIN lead_outcomes lo ON lf.lead_id = lo.lead_id
        WHERE lf.created_at >= %s
        ORDER BY lf.created_at DESC
        """
        
        # Get data from last 90 days
        cutoff_date = datetime.now() - timedelta(days=90)
        
        with self.connect_db() as conn:
            df = pd.read_sql(query, conn, params=[cutoff_date])
        
        logger.info(f"Loaded {len(df)} feedback records")
        return df
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create features for ML training."""
        logger.info("Engineering features...")
        
        # Basic features from feedback
        df['feedback_age_days'] = (datetime.now() - pd.to_datetime(df['feedback_date'])).dt.days
        
        # Rating-based features
        rating_mapping = {
            'no_answer': 0,
            'bad_contact': 1, 
            'not_qualified': 2,
            'quoted': 3,
            'won': 4
        }
        df['rating_numeric'] = df['rating'].map(rating_mapping)
        
        # Deal band features
        deal_band_mapping = {
            '$0-5k': 2500,
            '$5-15k': 10000,
            '$15-50k': 32500,
            '$50k+': 75000
        }
        df['estimated_deal_value'] = df['deal_band'].map(deal_band_mapping).fillna(0)
        
        # Reason codes features (simplified)
        df['has_contact_issues'] = df['reason_codes'].apply(
            lambda x: 'contact' in str(x).lower() if x else False
        )
        df['has_qualification_issues'] = df['reason_codes'].apply(
            lambda x: 'qualified' in str(x).lower() if x else False
        )
        
        # Time-based features
        df['is_weekend_feedback'] = pd.to_datetime(df['feedback_date']).dt.weekday >= 5
        df['feedback_hour'] = pd.to_datetime(df['feedback_date']).dt.hour
        
        # Target variable
        df['success'] = df['win_label'].fillna(df['rating'].isin(['quoted', 'won']))
        
        feature_cols = [
            'rating_numeric', 'estimated_deal_value', 'feedback_age_days',
            'has_contact_issues', 'has_qualification_issues', 
            'is_weekend_feedback', 'feedback_hour'
        ]
        
        self.feature_columns = feature_cols
        return df[feature_cols + ['success']].dropna()
    
    def train_model(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Train and calibrate the ML model."""
        logger.info("Training ML model...")
        
        X = df[self.feature_columns]
        y = df['success']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train base model
        base_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        
        # Calibrate model for better probability estimates
        self.model = CalibratedClassifierCV(base_model, method='isotonic', cv=3)
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate model
        y_pred = self.model.predict(X_test_scaled)
        y_prob = self.model.predict_proba(X_test_scaled)[:, 1]
        
        metrics = {
            'model_version': self.model_version,
            'training_samples': len(X_train),
            'test_samples': len(X_test),
            'accuracy': self.model.score(X_test_scaled, y_test),
            'roc_auc': roc_auc_score(y_test, y_prob),
            'feature_importance': dict(zip(
                self.feature_columns,
                base_model.feature_importances_
            )) if hasattr(base_model, 'feature_importances_') else {},
            'training_date': datetime.now().isoformat()
        }
        
        logger.info(f"Model trained - Accuracy: {metrics['accuracy']:.3f}, AUC: {metrics['roc_auc']:.3f}")
        return metrics
    
    def save_model(self, model_dir: str, metrics: Dict[str, Any]):
        """Save trained model and metadata."""
        model_path = Path(model_dir)
        model_path.mkdir(parents=True, exist_ok=True)
        
        # Save model
        model_file = model_path / f"lead_model_{self.model_version}.pkl"
        with open(model_file, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'feature_columns': self.feature_columns,
                'metrics': metrics
            }, f)
        
        # Save latest model reference
        latest_file = model_path / "latest_model.json"
        with open(latest_file, 'w') as f:
            json.dump({
                'model_file': str(model_file),
                'model_version': self.model_version,
                'metrics': metrics
            }, f, indent=2)
        
        logger.info(f"Model saved to {model_file}")
        return str(model_file)
    
    def run_training(self, model_dir: str = "./models") -> Dict[str, Any]:
        """Run complete training pipeline."""
        try:
            logger.info("Starting ML training pipeline...")
            
            # Load and prepare data
            df = self.load_training_data()
            
            if len(df) < 50:  # Minimum samples needed
                logger.warning(f"Insufficient training data: {len(df)} samples. Skipping training.")
                return {'status': 'skipped', 'reason': 'insufficient_data', 'samples': len(df)}
            
            df_features = self.engineer_features(df)
            
            # Train model
            metrics = self.train_model(df_features)
            
            # Save model
            model_file = self.save_model(model_dir, metrics)
            
            logger.info("Training pipeline completed successfully")
            return {
                'status': 'success',
                'model_file': model_file,
                **metrics
            }
            
        except Exception as e:
            logger.error(f"Training failed: {str(e)}")
            return {'status': 'error', 'error': str(e)}

def main():
    """Main training script entry point."""
    # Get database URL from environment
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return
    
    # Initialize trainer
    trainer = LeadMLTrainer(db_url)
    
    # Run training
    model_dir = os.getenv('MODEL_DIR', './backend/models')
    result = trainer.run_training(model_dir)
    
    # Log results
    logger.info(f"Training result: {json.dumps(result, indent=2)}")
    
    # Exit with appropriate code
    exit(0 if result['status'] == 'success' else 1)

if __name__ == "__main__":
    main()