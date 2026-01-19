"""
AIMS Data Platform - Shared Notebook Utilities
===============================================

This module provides shared utilities for notebooks that work seamlessly
across both Local development and Microsoft Fabric environments.

Usage:
    from notebooks.lib import platform_utils, config, logging_utils
    
    # Or import specific utilities
    from notebooks.lib.platform_utils import IS_FABRIC, get_data_paths, copy_file
    from notebooks.lib.config import NotebookConfig
    from notebooks.lib.logging_utils import setup_notebook_logger
    
    # New: Import centralized settings
    from notebooks.lib.settings import Settings, get_settings

Example:
    >>> from notebooks.lib import platform_utils
    >>> paths = platform_utils.get_data_paths()
    >>> print(paths['BRONZE_DIR'])
    
    >>> # Or use new Settings system
    >>> from notebooks.lib.settings import get_settings
    >>> settings = get_settings()
    >>> print(settings.bronze_dir)
"""

__version__ = "1.0.0"
__author__ = "AIMS Data Platform Team"

# Import submodules for convenient access
from . import platform_utils
from . import config
from . import logging_utils
from . import storage
from . import settings as settings_module

# Re-export commonly used items at package level
from .platform_utils import (
    IS_FABRIC,
    get_base_dir,
    get_data_paths,
    safe_import_mssparkutils,
    copy_file,
    ensure_directory,
    read_parquet_safe,
)

from .config import NotebookConfig

from .logging_utils import (
    setup_notebook_logger,
    log_phase_start,
    log_phase_end,
    ProgressTracker,
)

from .storage import (
    StorageManager,
    get_storage_format,
    infer_partition_columns,
    validate_schema_compatibility,
    create_storage_manager,
    DELTA_AVAILABLE,
    PYARROW_AVAILABLE,
    PYSPARK_AVAILABLE,
)

# New: Export Settings system
from .settings import (
    Settings,
    get_settings,
)

__all__ = [
    # Submodules
    "platform_utils",
    "config",
    "logging_utils",
    "storage",
    "settings_module",
    # Platform utilities
    "IS_FABRIC",
    "get_base_dir",
    "get_data_paths",
    "safe_import_mssparkutils",
    "copy_file",
    "ensure_directory",
    "read_parquet_safe",
    # Config (legacy)
    "NotebookConfig",
    # Settings (new centralized system)
    "Settings",
    "get_settings",
    # Logging
    "setup_notebook_logger",
    "log_phase_start",
    "log_phase_end",
    "ProgressTracker",
    # Storage
    "StorageManager",
    "get_storage_format",
    "infer_partition_columns",
    "validate_schema_compatibility",
    "create_storage_manager",
    "DELTA_AVAILABLE",
    "PYARROW_AVAILABLE",
    "PYSPARK_AVAILABLE",
]
