
"""Texas data ingestion connectors package."""

"""
Ingest package initialization.

This module provides the main connectors for different data source types
and utilities for creating connectors from configuration.
"""


from .arcgis import ArcGISConnector, create_arcgis_connector
from .socrata import SocrataConnector, create_socrata_connector
from .csv_http import CSVHTTPConnector, create_csv_http_connector

__all__ = [

    "ArcGISConnector",
    "SocrataConnector", 
    "CSVHTTPConnector",
    "create_arcgis_connector",
    "create_socrata_connector",
    "create_csv_http_connector"
]

    'ArcGISConnector',
    'SocrataConnector', 
    'CSVHTTPConnector',
    'create_arcgis_connector',
    'create_socrata_connector',
    'create_csv_http_connector',
    'create_connector'
]


def create_connector(source_config):
    """
    Factory function to create appropriate connector based on source kind.
    
    Args:
        source_config: Source configuration dictionary from sources_tx.yaml
        
    Returns:
        Configured connector instance
        
    Raises:
        ValueError: If source kind is not supported
    """
    kind = source_config.get('kind')
    
    if kind == 'arcgis':
        return create_arcgis_connector(source_config)
    elif kind == 'socrata':
        return create_socrata_connector(source_config)
    elif kind == 'csv_http':
        return create_csv_http_connector(source_config)
    elif kind == 'tpia':
        # TPIA sources require manual handling - return None for now
        # Will be handled by separate TPIA workflow
        return None
    else:
        raise ValueError(f"Unsupported source kind: {kind}")

