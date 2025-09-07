#!/usr/bin/env python3
"""
ML inference script for lead scoring.

Reads lead data from stdin, applies trained model, and outputs predictions.
"""

import sys
import json
import pickle
import logging
import os
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd

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

            with open(latest_model_file, "r") as f:
                self.model_metadata = json.load(f)

            model_file = Path(self.model_metadata["model_file"])

            with open(model_file, "rb") as f:
                model_data = pickle.load(f)

            self.model = model_data["model"]
            self.scaler = model_data["scaler"]
            self.feature_columns = model_data["feature_columns"]

            logger.info(f"Loaded model version: {self.model_metadata['model_version']}")
            return True

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False

    def prepare_features(self, leads: List[Dict[str, Any]]) -> pd.DataFrame:
        """Prepare lead features for inference."""
        features_list = []

        for lead in leads:
            lead_features = lead.get("features", {})

            # Ensure all required features are present
            feature_row = {}
            for col in self.feature_columns:
                if col in lead_features:
                    feature_row[col] = lead_features[col]
                else:
                    # Default values for missing features
                    if col == "rating_numeric":
                        feature_row[col] = 0
                    elif col == "estimated_deal_value":
                        feature_row[col] = 0
                    elif col == "feedback_age_days":
                        feature_row[col] = 0
                    elif col in [
                        "has_contact_issues",
                        "has_qualification_issues",
                        "is_weekend_feedback",
                    ]:
                        feature_row[col] = False
                    elif col == "feedback_hour":
                        feature_row[col] = 12
                    elif col in [
                        "source_cancellation_rate",
                        "source_avg_cancellation_score",
                    ]:
                        feature_row[col] = 0.0
                    elif col in [
                        "contractor_canceled",
                        "canceled_for_quality",
                        "canceled_for_wrong_type",
                    ]:
                        feature_row[col] = False
                    elif col == "contractor_win_rate":
                        feature_row[col] = 0.1  # Default reasonable win rate
                    elif col == "lead_value_log":
                        feature_row[col] = 0.0
                    else:
                        feature_row[col] = 0

            features_list.append(feature_row)

        return pd.DataFrame(features_list)

    def predict(
        self, leads: List[Dict[str, Any]], account_id: str = None
    ) -> List[Dict[str, Any]]:
        """Generate predictions for leads with optional personalized cancellation adjustments."""
        if not self.model:
            raise RuntimeError("Model not loaded")

        # Import cancellation service for personalized adjustments
        try:
            # Try absolute import first, then fallback to relative import
            try:
                from cancellation_feedback import CancellationFeedbackService
            except ImportError:
                from .cancellation_feedback import CancellationFeedbackService
            cancellation_service = CancellationFeedbackService(
                os.getenv("DATABASE_URL")
            )
        except ImportError:
            cancellation_service = None
            logger.warning("Cancellation feedback service not available")

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
            base_probability = probabilities[i]

            # Apply personalized cancellation adjustment if available
            personalized_adjustment = 0.0
            if cancellation_service and account_id:
                try:
                    personalized_adjustment = (
                        cancellation_service.calculate_personalized_adjustments(
                            account_id, lead
                        )
                    )
                except Exception as e:
                    logger.warning(f"Error calculating personalized adjustment: {e}")

            # Apply adjustment to probability (convert to score, adjust, convert back)
            adjusted_score = (base_probability * 100) + personalized_adjustment
            adjusted_score = max(0, min(100, adjusted_score))  # Clamp to 0-100
            adjusted_probability = adjusted_score / 100.0

            results.append(
                {
                    "lead_id": lead["id"],
                    "win_probability": float(base_probability),
                    "adjusted_probability": float(adjusted_probability),
                    "calibrated_score": float(adjusted_score),
                    "personalized_adjustment": float(personalized_adjustment),
                    "predicted_success": bool(adjusted_probability > 0.5),
                    "model_version": self.model_metadata["model_version"],
                    "confidence": self._calculate_confidence(adjusted_probability),
                }
            )

        return results

    def _calculate_confidence(self, probability: float) -> str:
        """Calculate confidence level based on probability."""
        if probability > 0.8 or probability < 0.2:
            return "high"
        elif probability > 0.6 or probability < 0.4:
            return "medium"
        else:
            return "low"


def main():
    """Main inference entry point."""
    try:
        # Read input from stdin
        input_data = json.loads(sys.stdin.read())

        # Initialize inference
        inference = LeadMLInference()

        # Load model
        if not inference.load_model():
            print(json.dumps({"error": "Failed to load model"}))
            sys.exit(1)

        # Run inference
        account_id = input_data.get("account_id")
        results = inference.predict(input_data["leads"], account_id)

        # Output results
        print(
            json.dumps(
                {
                    "status": "success",
                    "predictions": results,
                    "model_metadata": inference.model_metadata.get("metrics", {}),
                }
            )
        )

    except Exception as e:
        logger.error(f"Inference error: {e}")
        print(json.dumps({"error": str(e), "status": "error"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
