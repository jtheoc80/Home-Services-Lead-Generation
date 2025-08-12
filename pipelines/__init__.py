"""
Pipelines package initialization.

This module provides the main data processing pipelines for Texas statewide
permit data ingestion, normalization, and risk analysis.
"""

from datetime import datetime
from .load_raw import RawDataLoader
from .normalize import DataNormalizer
from .derive_risk import RiskDeriver

__all__ = [
    'RawDataLoader',
    'DataNormalizer',
    'RiskDeriver'
]


def run_full_pipeline(db_url: str, sources_config_path: str, tier: str = '1') -> dict:
    """
    Run the complete data pipeline for Texas permit data.
    
    Args:
        db_url: PostgreSQL connection URL
        sources_config_path: Path to sources_tx.yaml configuration
        tier: Which tier to process ('1', '2', or 'all')
    
    Returns:
        Dictionary with results from each pipeline stage
    """
    results = {}
    
    try:
        # Stage 1: Load raw data
        loader = RawDataLoader(db_url, sources_config_path)
        
        if tier == '1':
            load_result = loader.run_tier1_ingests()
        elif tier == '2':
            load_result = loader.run_tier2_ingests()
        else:  # all
            load_result = {
                'tier_1': loader.run_tier1_ingests(),
                'tier_2': loader.run_tier2_ingests()
            }
        
        results['load_raw'] = load_result
        
        # Stage 2: Normalize data
        normalizer = DataNormalizer(db_url, sources_config_path)
        normalize_result = normalizer.normalize_permits()
        results['normalize'] = normalize_result
        
        # Stage 3: Derive risk indicators
        risk_deriver = RiskDeriver(db_url, sources_config_path)
        risk_result = risk_deriver.run_risk_analysis()
        results['derive_risk'] = risk_result
        
        results['status'] = 'success'
        results['pipeline_completed_at'] = str(datetime.now())
        
    except Exception as e:
        results['status'] = 'error'
        results['error'] = str(e)
        results['pipeline_failed_at'] = str(datetime.now())
    
    return results