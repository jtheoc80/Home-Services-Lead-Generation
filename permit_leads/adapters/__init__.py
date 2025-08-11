"""Adapter package for permit data sources."""

from .arcgis_adapter import ArcGISAdapter
from .accela_adapter import AccelaAdapter
from .opengov_adapter import OpenGovAdapter
from .html_adapter import HTMLAdapter

__all__ = ['ArcGISAdapter', 'AccelaAdapter', 'OpenGovAdapter', 'HTMLAdapter']