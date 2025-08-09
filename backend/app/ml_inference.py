#!/usr/bin/env python3
"""
ML inference script for lead scoring.

Reads lead data from stdin, applies trained model, and outputs predictions.
"""

import sys
import json
import pickle
import logging
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LeadMLInference:
    def __init__(self, model_dir: str = "./models"):
        """Initialize inference with model directory."""
        self.model_dir = Path(model_dir)
        self.model = None
        self.scaler = None
        self.feature_columns = []
        self.model_metadata = {}
        
    def load_model(self) -> bool:
        """Load the latest trained model."""
        try:
            latest_model_file = self.model_dir / "latest_model.json"
            
            if not latest_model_file.exists():
                logger.error("No trained model found")
                return False
                
            with open(latest_model_file, 'r') as f:
                self.model_metadata = json.load(f)
            
            model_file = Path(self.model_metadata['model_file'])
            
            with open(model_file, 'rb') as f:
                model_data = pickle.load(f)
                
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_columns = model_data['feature_columns']
            
            logger.info(f"Loaded model version: {self.model_metadata['model_version']}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def prepare_features(self, leads: List[Dict[str, Any]]) -> pd.DataFrame:
        """Prepare lead features for inference."""
        features_list = []
        
        for lead in leads:
            lead_features = lead.get('features', {})
            
            # Ensure all required features are present
            feature_row = {}
            for col in self.feature_columns:
                if col in lead_features:
                    feature_row[col] = lead_features[col]
                else:
                    # Default values for missing features
                    if col == 'rating_numeric':
                        feature_row[col] = 0
                    elif col == 'estimated_deal_value':
                        feature_row[col] = 0
                    elif col == 'feedback_age_days':
                        feature_row[col] = 0
                    elif col in ['has_contact_issues', 'has_qualification_issues', 'is_weekend_feedback']:
                        feature_row[col] = False
                    elif col == 'feedback_hour':
                        feature_row[col] = 12
                    else:
                        feature_row[col] = 0
                        
            features_list.append(feature_row)
        
        return pd.DataFrame(features_list)
    
    def predict(self, leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate predictions for leads."""
        if not self.model:
            raise RuntimeError("Model not loaded")
        
        # Prepare features
        features_df = self.prepare_features(leads)
        
        # Scale features
        features_scaled = self.scaler.transform(features_df)
        
        # Get predictions
        probabilities = self.model.predict_proba(features_scaled)[:, 1]
        predictions = self.model.predict(features_scaled)
        
        # Prepare results
        results = []
        for i, lead in enumerate(leads):
            # Convert probability to calibrated score (0-100)
            calibrated_score = min(100, max(0, probabilities[i] * 100))
            
            results.append({
                'lead_id': lead['id'],
                'win_probability': float(probabilities[i]),
                'calibrated_score': float(calibrated_score),
                'predicted_success': bool(predictions[i]),
                'model_version': self.model_metadata['model_version'],
                'confidence': self._calculate_confidence(probabilities[i])
            })
        
        return results
    
    def _calculate_confidence(self, probability: float) -> str:
        """Calculate confidence level based on probability."""
        if probability > 0.8 or probability < 0.2:
            return 'high'
        elif probability > 0.6 or probability < 0.4:
            return 'medium'
        else:
            return 'low'

def main():
    """Main inference entry point."""
    try:
        # Read input from stdin
        input_data = json.loads(sys.stdin.read())
        
        # Initialize inference
        inference = LeadMLInference()
        
        # Load model
        if not inference.load_model():
            print(json.dumps({'error': 'Failed to load model'}))
            sys.exit(1)
        
        # Run inference
        results = inference.predict(input_data['leads'])
        
        # Output results
        print(json.dumps({
            'status': 'success',
            'predictions': results,
            'model_metadata': inference.model_metadata.get('metrics', {})
        }))
        
    except Exception as e:
        logger.error(f"Inference error: {e}")
        print(json.dumps({
            'error': str(e),
            'status': 'error'
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()