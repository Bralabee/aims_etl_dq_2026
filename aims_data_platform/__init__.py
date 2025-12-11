"""AIMS Data Platform - Cloud-ready data ingestion with data quality."""
from .config import config, Config
from .fabric_config import FabricConfig
from .watermark_manager import WatermarkManager
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

# Import core functionality from the shared library
from dq_framework import (
    DataQualityValidator,
    BatchProfiler,
    DataProfiler,
    DataLoader,
    ConfigLoader
)

__version__ = "1.0.2"
__all__ = [
    "config",
    "Config",
    "FabricConfig",
    "WatermarkManager",
    "DataIngester",
    "DataQualityValidator",
    "BatchProfiler",
    "DataProfiler",
    "DataLoader",
    "ConfigLoader",
    "FileSystemHandler",
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
