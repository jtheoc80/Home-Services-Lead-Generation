#!/usr/bin/env python3
"""
Test script for cancellation feedback integration.

Tests the cancellation feedback service and ML model integration.
"""

import sys
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add backend app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

def test_cancellation_feedback_service():
    """Test the cancellation feedback service functionality."""
    print("Testing cancellation feedback service...")
    
    # Mock database connection
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock query results for global adjustments
        mock_cursor.fetchall.return_value = [
            {
                'jurisdiction': 'city_of_houston',
                'cancellation_rate': 0.15,
                'avg_canceled_score': 45.0,
                'quality_complaint_rate': 0.3
            }
        ]
        
        from cancellation_feedback import CancellationFeedbackService
        
        service = CancellationFeedbackService('mock://db')
        adjustments = service.calculate_global_source_adjustments()
        
        assert 'city_of_houston' in adjustments
        assert adjustments['city_of_houston']['cancellation_rate'] == 0.15
        assert adjustments['city_of_houston']['score_adjustment'] < 0  # Should be negative
        
        print("✓ Global adjustments calculation works")
        
        # Test personalized adjustments
        mock_cursor.fetchone.return_value = {
            'primary_reason': 'poor_lead_quality',
            'secondary_reasons': ['wrong_lead_type'],
            'avg_lead_score': 40.0,
            'preferred_service_areas': ['houston'],
            'preferred_trade_types': ['roofing'],
            'total_leads_purchased': 20,
            'leads_won': 1
        }
        
        lead_features = {
            'jurisdiction': 'city_of_houston',
            'trade_tags': ['roofing'],
            'value': 15000
        }
        
        adjustment = service.calculate_personalized_adjustments('test-account', lead_features)
        
        # Should be negative due to poor lead quality history
        assert adjustment < 0
        print("✓ Personalized adjustments calculation works")

def test_ml_integration():
    """Test ML model integration with cancellation features."""
    print("Testing ML model integration...")
    
    # Mock the model file structure
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('sys.path', [temp_dir] + sys.path):
            # Create mock model data
            mock_model_data = {
                'model': Mock(),
                'scaler': Mock(),
                'feature_columns': [
                    'rating_numeric', 'estimated_deal_value', 'feedback_age_days',
                    'source_cancellation_rate', 'contractor_canceled', 'contractor_win_rate'
                ],
                'metrics': {'accuracy': 0.85}
            }
            
            # Mock model prediction
            mock_model_data['model'].predict_proba.return_value = [[0.3, 0.7], [0.8, 0.2]]
            mock_model_data['model'].predict.return_value = [True, False]
            mock_model_data['scaler'].transform.return_value = [[1, 2, 3, 0.1, 0, 0.15], [2, 3, 4, 0.2, 1, 0.05]]
            
            # Mock the latest_model.json
            latest_model = {
                'model_file': os.path.join(temp_dir, 'test_model.pkl'),
                'model_version': 'test_v1',
                'metrics': {'accuracy': 0.85}
            }
            
            with patch('pickle.load', return_value=mock_model_data), \
                 patch('json.load', return_value=latest_model), \
                 patch('builtins.open', mock_open_factory(latest_model)):
                
                from ml_inference import LeadMLInference
                
                inference = LeadMLInference(temp_dir)
                
                # Mock pathlib.Path.exists
                with patch('pathlib.Path.exists', return_value=True):
                    assert inference.load_model()
                    print("✓ Model loading works")
                
                # Test prediction with cancellation features
                test_leads = [
                    {
                        'id': 1,
                        'features': {
                            'source_cancellation_rate': 0.1,
                            'contractor_canceled': False,
                            'contractor_win_rate': 0.15
                        }
                    },
                    {
                        'id': 2,
                        'features': {
                            'source_cancellation_rate': 0.3,
                            'contractor_canceled': True,
                            'contractor_win_rate': 0.05
                        }
                    }
                ]
                
                # Mock cancellation service
                with patch.dict('sys.modules', {'cancellation_feedback': Mock()}):
                    results = inference.predict(test_leads, 'test-account')
                
                assert len(results) == 2
                assert 'personalized_adjustment' in results[0]
                assert 'adjusted_probability' in results[0]
                print("✓ ML inference with cancellation features works")

def mock_open_factory(content):
    """Factory to create mock open that returns different content."""
    from unittest.mock import mock_open
    return mock_open(read_data=json.dumps(content))

def test_schema_integration():
    """Test that the schema changes are compatible."""
    print("Testing schema integration...")
    
    # Check that migration file exists and has expected content
    migration_file = Path(__file__).parent.parent / 'app' / 'migrations' / '003_cancellations_table.sql'
    assert migration_file.exists(), "Migration file should exist"
    
    content = migration_file.read_text()
    assert 'CREATE TABLE IF NOT EXISTS cancellations' in content
    assert 'cancellation_reason' in content
    assert 'source_cancellation_rate' in content
    
    print("✓ Schema migration file is properly structured")

def main():
    """Run all tests."""
    print("Running cancellation feedback integration tests...\n")
    
    try:
        test_schema_integration()
        test_cancellation_feedback_service()
        test_ml_integration()
        
        print("\n✅ All tests passed! Cancellation feedback integration is working.")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())