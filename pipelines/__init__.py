
"""Texas data processing pipelines package."""

from .load_raw import main as load_raw_main
from .normalize_permits import main as normalize_permits_main  
from .publish import main as publish_main

__all__ = [
    "load_raw_main",
    "normalize_permits_main", 
    "publish_main"
]

