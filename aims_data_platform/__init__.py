"""AIMS Data Platform - Cloud-ready data ingestion with data quality."""
from .config import config, Config
from .fabric_config import FabricConfig
from .watermark_manager import WatermarkManager
from .ingestion import DataIngester
from .data_quality import DataQualityValidator
from .schema_reconciliation import (
    parse_data_model,
    get_parquet_metadata,
    format_size,
    map_arrow_type,
    check_relationship,
    analyze_comparison,
    analyze_extra_files,
    generate_model,
    reconcile
)

__version__ = "1.0.0"
__all__ = [
    "config",
    "Config",
    "FabricConfig",
    "WatermarkManager",
    "DataIngester",
    "DataQualityValidator",
    "parse_data_model",
    "get_parquet_metadata",
    "format_size",
    "map_arrow_type",
    "check_relationship",
    "analyze_comparison",
    "analyze_extra_files",
    "generate_model",
    "reconcile"
]
