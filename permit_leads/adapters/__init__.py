"""Adapter package for permit data sources."""

from .base import SourceAdapter, BaseAdapter
from .arcgis_adapter import ArcGISAdapter
from .accela_adapter import AccelaAdapter
from .opengov_adapter import OpenGovAdapter
from .html_adapter import HTMLAdapter
from .socrata_adapter import SocrataAdapter
from .simple_socrata_adapter import SimpleSocrataAdapter
from .arcgis_feature_service import ArcGISFeatureServiceAdapter
from .tpia_adapter import TPIAAdapter
from .html_table_adapter import HTMLTableAdapter
from .accela_html_adapter import AccelaHTMLAdapter

__all__ = [
    'SourceAdapter', 'BaseAdapter',
    'ArcGISAdapter', 'AccelaAdapter', 'OpenGovAdapter', 'HTMLAdapter', 
    'SocrataAdapter', 'SimpleSocrataAdapter',
    'ArcGISFeatureServiceAdapter', 'TPIAAdapter', 
    'HTMLTableAdapter', 'AccelaHTMLAdapter'
]