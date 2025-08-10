#!/usr/bin/env python3
"""
Validation script to check ML pipeline components.

This script validates that all components can be imported and basic
functionality works without requiring a full database setup.
"""

import sys
import json
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        # Test standard library imports
        import pickle
        import logging
        from datetime import datetime, timedelta
        print("✓ Standard library imports successful")
        
        # Test data science imports (may not be installed)
        try:
            import pandas as pd
            import numpy as np
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.preprocessing import StandardScaler
            print("✓ Data science imports successful")
            data_science_available = True
        except ImportError as e:
            print(f"⚠ Data science imports failed: {e}")
            print("  Run: pip install -r requirements.txt")
            data_science_available = False
        
        return data_science_available
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_inference_logic():
    """Test ML inference logic without actual model."""
    print("\nTesting inference logic...")
    
    try:
        # Import our modules
        sys.path.append(str(Path(__file__).parent))
        from app.ml_inference import LeadMLInference
        
        # Test initialization
        inference = LeadMLInference("./test_models")
        print("✓ LeadMLInference initialization successful")
        
        # Test feature preparation with mock data
        inference.feature_columns = [
            'rating_numeric', 'estimated_deal_value', 'feedback_age_days'
        ]
        
        mock_leads = [
            {
                'id': 1,
                'features': {
                    'rating_numeric': 3,
                    'estimated_deal_value': 25000
                }
            }
        ]
        
        features_df = inference.prepare_features(mock_leads)
        print("✓ Feature preparation successful")
        
        # Test confidence calculation
        confidence = inference._calculate_confidence(0.8)
        assert confidence == 'high'
        print("✓ Confidence calculation successful")
        
        return True
        
    except Exception as e:
        print(f"✗ Inference logic test failed: {e}")
        return False

def test_training_logic():
    """Test training logic without actual database."""
    print("\nTesting training logic...")
    
    try:
        # Import our modules
        from app.train_model import LeadMLTrainer
        
        # Test initialization
        trainer = LeadMLTrainer("sqlite:///:memory:")
        print("✓ LeadMLTrainer initialization successful")
        
        # Test feature engineering with mock data
        import pandas as pd
        
        mock_data = {
            'lead_id': [1, 2, 3],
            'rating': ['won', 'not_qualified', 'quoted'],
            'deal_band': ['$15-50k', '$5-15k', '$50k+'],
            'reason_codes': [['good'], ['bad'], ['good']],
            'feedback_date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'win_label': [True, False, True]
        }
        df = pd.DataFrame(mock_data)
        
        features_df = trainer.engineer_features(df)
        print("✓ Feature engineering successful")
        
        # Check required columns exist
        required_cols = ['rating_numeric', 'estimated_deal_value', 'success']
        for col in required_cols:
            assert col in features_df.columns, f"Missing column: {col}"
        print("✓ Required feature columns present")
        
        return True
        
    except Exception as e:
        print(f"✗ Training logic test failed: {e}")
        return False

def test_api_structure():
    """Test API endpoint structure."""
    print("\nTesting API structure...")
    
    try:
        # Check that API files exist
        api_dir = Path(__file__).parent.parent / "frontend" / "pages" / "api"
        
        required_apis = ['feedback.ts', 'score-leads.ts', 'ml-inference.ts']
        for api_file in required_apis:
            api_path = api_dir / api_file
            assert api_path.exists(), f"Missing API file: {api_file}"
            
            # Basic syntax check - ensure it's valid TypeScript
            content = api_path.read_text()
            assert 'export default' in content, f"Invalid API structure in {api_file}"
            assert 'NextApiRequest' in content, f"Missing Next.js types in {api_file}"
        
        print("✓ All API files present and valid")
        return True
        
    except Exception as e:
        print(f"✗ API structure test failed: {e}")
        return False

def test_database_schema():
    """Test database schema file."""
    print("\nTesting database schema...")
    
    try:
        # Test feedback tables migration
        feedback_schema_file = Path(__file__).parent / "app" / "migrations" / "001_feedback_tables.sql"
        assert feedback_schema_file.exists(), "Missing feedback migration file"
        
        feedback_content = feedback_schema_file.read_text()
        
        # Check for required tables and types in feedback migration
        feedback_required_elements = [
            'CREATE TYPE lead_rating',
            'CREATE TABLE IF NOT EXISTS lead_feedback',
            'CREATE TABLE IF NOT EXISTS lead_outcomes',
            'account_id UUID NOT NULL REFERENCES auth.users',
            'PRIMARY KEY'
        ]
        
        for element in feedback_required_elements:
            assert element in feedback_content, f"Missing feedback schema element: {element}"
        
        print("✓ Feedback tables schema is valid")
        
        # Test notifications table migration
        notifications_schema_file = Path(__file__).parent / "app" / "migrations" / "002_notifications_table.sql"
        assert notifications_schema_file.exists(), "Missing notifications migration file"
        
        notifications_content = notifications_schema_file.read_text()
        
        # Check for required elements in notifications migration
        notifications_required_elements = [
            'CREATE TABLE IF NOT EXISTS notifications',
            'account_id UUID NOT NULL',
            'lead_id BIGINT NOT NULL',
            'channel TEXT NOT NULL',
            'status TEXT NOT NULL DEFAULT',
            'PRIMARY KEY',
            'CREATE INDEX'
        ]
        
        for element in notifications_required_elements:
            assert element in notifications_content, f"Missing notifications schema element: {element}"
        
        print("✓ Notifications table schema is valid")
        
        # Test main models.sql file includes notifications
        models_file = Path(__file__).parent / "app" / "models.sql"
        assert models_file.exists(), "Missing models.sql file"
        
        models_content = models_file.read_text()
        assert 'CREATE TABLE IF NOT EXISTS notifications' in models_content, "Notifications table missing from models.sql"
        
        print("✓ Main models schema includes notifications")
        return True
        
    except Exception as e:
        print(f"✗ Database schema test failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("=" * 50)
    print("LeadLedgerPro Backend Validation")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_database_schema,
        test_api_structure,
        test_inference_logic,
        test_training_logic,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All validations passed!")
        print("\nNext steps:")
        print("1. Run database migration: psql \"$DATABASE_URL\" -v ON_ERROR_STOP=1 -b -e -f backend/app/migrations/001_feedback_tables.sql")
        print("2. Install Python dependencies: pip install -r backend/requirements.txt")
        print("3. Configure environment variables in frontend/.env")
        print("4. Start the Next.js development server: npm run dev")
        return 0
    else:
        print("❌ Some validations failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())