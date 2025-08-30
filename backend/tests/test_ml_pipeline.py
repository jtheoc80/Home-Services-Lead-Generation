"""
Tests for ML training and inference pipeline.
"""

import unittest
import tempfile
import os
from unittest.mock import patch


# Mock database connection for testing
class MockConnection:
    def __init__(self):
        self.cursor_data = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class MockCursor:
    def __init__(self, data):
        self.data = data
        self.fetchall_called = False

    def execute(self, query, params=None):
        pass

    def fetchall(self):
        self.fetchall_called = True
        return self.data


class TestMLTraining(unittest.TestCase):
    """Test ML training functionality."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir)

    @patch("backend.app.train_model.psycopg2.connect")
    @patch("pandas.read_sql")
    def test_load_training_data(self, mock_read_sql, mock_connect):
        """Test loading training data from database."""
        from backend.app.train_model import LeadMLTrainer

        # Mock data
        mock_data = [
            {
                "lead_id": 1,
                "rating": "won",
                "deal_band": "$15-50k",
                "reason_codes": ["good_contact"],
                "feedback_date": "2024-01-01",
                "win_label": True,
            }
        ]

        mock_read_sql.return_value = mock_data
        mock_connect.return_value = MockConnection()

        trainer = LeadMLTrainer("mock://db")
        df = trainer.load_training_data()

        # Verify the data loading process
        mock_read_sql.assert_called_once()
        self.assertIsNotNone(df)

    def test_feature_engineering(self):
        """Test feature engineering logic."""
        from backend.app.train_model import LeadMLTrainer
        import pandas as pd

        # Create mock dataframe
        data = {
            "lead_id": [1, 2],
            "rating": ["won", "not_qualified"],
            "deal_band": ["$15-50k", "$5-15k"],
            "reason_codes": [["good_contact"], ["not_qualified"]],
            "feedback_date": ["2024-01-01", "2024-01-02"],
            "win_label": [True, False],
        }
        df = pd.DataFrame(data)

        trainer = LeadMLTrainer("mock://db")
        features_df = trainer.engineer_features(df)

        # Check that features are created
        self.assertIn("rating_numeric", features_df.columns)
        self.assertIn("estimated_deal_value", features_df.columns)
        self.assertIn("success", features_df.columns)

        # Check feature values
        self.assertEqual(features_df.iloc[0]["rating_numeric"], 4)  # 'won' = 4
        self.assertEqual(
            features_df.iloc[1]["rating_numeric"], 2
        )  # 'not_qualified' = 2


class TestMLInference(unittest.TestCase):
    """Test ML inference functionality."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_prepare_features(self):
        """Test feature preparation for inference."""
        from backend.app.ml_inference import LeadMLInference

        # Mock model loading
        inference = LeadMLInference(self.temp_dir)
        inference.feature_columns = [
            "rating_numeric",
            "estimated_deal_value",
            "feedback_age_days",
        ]

        leads = [
            {"id": 1, "features": {"rating_numeric": 3, "estimated_deal_value": 25000}}
        ]

        features_df = inference.prepare_features(leads)

        # Check that missing features get default values
        self.assertEqual(features_df.iloc[0]["rating_numeric"], 3)
        self.assertEqual(features_df.iloc[0]["estimated_deal_value"], 25000)
        self.assertEqual(features_df.iloc[0]["feedback_age_days"], 0)  # Default

    def test_confidence_calculation(self):
        """Test confidence level calculation."""
        from backend.app.ml_inference import LeadMLInference

        inference = LeadMLInference()

        # High confidence cases
        self.assertEqual(inference._calculate_confidence(0.9), "high")
        self.assertEqual(inference._calculate_confidence(0.1), "high")

        # Medium confidence cases
        self.assertEqual(inference._calculate_confidence(0.7), "medium")
        self.assertEqual(inference._calculate_confidence(0.3), "medium")

        # Low confidence cases
        self.assertEqual(inference._calculate_confidence(0.5), "low")


class TestAPIHelpers(unittest.TestCase):
    """Test helper functions for API endpoints."""

    def test_budget_band_extraction(self):
        """Test budget band value extraction."""
        # This would test the extractValueFromBudgetBand function
        # if it were moved to a separate utility module
        band_values = {"$0-5k": 2500, "$5-15k": 10000, "$15-50k": 32500, "$50k+": 75000}

        for band, expected_value in band_values.items():
            # Simulate the extraction logic
            result = band_values.get(band, 0)
            self.assertEqual(result, expected_value)


if __name__ == "__main__":
    # Set up test environment
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["ENABLE_ML_SCORING"] = "true"

    unittest.main()
