"""AIMS Data Platform - Cloud-ready data ingestion with data quality."""
from .config import config, Config
from .fabric_config import FabricConfig
from .watermark_manager import WatermarkManager
from .ingestion import DataIngester, BaseDataIngester
from .landing_zone_manager import (
    LandingZoneManager,
    NotificationManager,
    RunSummary,
    PlatformFileOps,
    create_landing_zone_manager,
    IS_FABRIC,
)
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
    ConfigLoader,
    FileSystemHandler,
)

__version__ = "1.3.1"
__all__ = [
    "config",
    "Config",
    "FabricConfig",
    "WatermarkManager",
    "DataIngester",
    "BaseDataIngester",
    "DataQualityValidator",
    "BatchProfiler",
    "DataProfiler",
    "DataLoader",
    "ConfigLoader",
    "FileSystemHandler",
    "LandingZoneManager",
    "NotificationManager",
    "RunSummary",
    "PlatformFileOps",
    "create_landing_zone_manager",
    "IS_FABRIC",
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
