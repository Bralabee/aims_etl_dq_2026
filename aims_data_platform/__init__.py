"""AIMS Data Platform - Cloud-ready data ingestion with data quality."""
from .config import config, Config
from .fabric_config import FabricConfig
from .watermark_manager import WatermarkManager
from .ingestion import DataIngester
from .data_quality import DataQualityValidator

__version__ = "1.0.0"
__all__ = [
    "config",
    "Config",
    "FabricConfig",
    "WatermarkManager",
    "DataIngester",
    "DataQualityValidator",
]
