"""
AIMS Data Platform - Configuration Package
============================================

Provides centralized access to platform settings and configuration.

This package exposes a singleton `settings` object that is automatically
configured based on the detected environment (local or Fabric).

Quick Start:
    >>> from notebooks.config import settings
    >>> 
    >>> # Access environment info
    >>> print(f"Environment: {settings.environment}")
    >>> 
    >>> # Access paths (all are Path objects)
    >>> print(f"Bronze dir: {settings.bronze_dir}")
    >>> print(f"Silver dir: {settings.silver_dir}")
    >>> 
    >>> # Access data quality thresholds
    >>> threshold = settings.get_dq_threshold("high")
    >>> print(f"High severity threshold: {threshold}%")

Available Imports:
    - settings: Pre-loaded Settings singleton
    - Settings: Settings class for explicit instantiation
    - get_settings: Function to get/reload settings
    - reload_settings: Function to force reload settings

Environment Detection:
    The environment is auto-detected based on:
    1. AIMS_ENVIRONMENT env var (if set)
    2. Platform detection (Fabric vs local)
    
    Override via environment variable:
        export AIMS_ENVIRONMENT=fabric_dev

Configuration Files:
    - notebooks/config/notebook_settings.yaml: Main configuration
    - .env: Environment variable overrides (local development)

Example Usage in Notebooks:
    ```python
    # Cell 1: Import settings
    from notebooks.config import settings
    
    # Cell 2: Use paths
    bronze_path = settings.bronze_dir
    silver_path = settings.silver_dir
    
    # Cell 3: Check environment
    if settings.environment == "local":
        print("Running locally - using sample data")
        sample_size = settings.sample_size
    else:
        print(f"Running in {settings.environment}")
    
    # Cell 4: Get DQ thresholds
    threshold = settings.get_dq_threshold("medium")
    print(f"Quality threshold: {threshold}%")
    ```

See Also:
    - notebooks.lib.settings: Full Settings class documentation
    - notebooks/config/notebook_settings.yaml: Configuration options
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

# Ensure the lib module can be imported
_package_dir = Path(__file__).parent.parent
if str(_package_dir) not in sys.path:
    sys.path.insert(0, str(_package_dir))

# Import from settings module
from notebooks.lib.settings import Settings, get_settings

# Pre-load settings singleton on import
# This makes `from notebooks.config import settings` work
settings: Settings = Settings.load()


def reload_settings(
    environment: str = "auto",
    config_path: str | Path | None = None,
) -> Settings:
    """
    Reload settings, optionally with a different environment or config.
    
    Use this when you need to refresh settings after changing configuration
    files or environment variables.
    
    Args:
        environment: Environment name or "auto" for detection.
                    Valid: auto, local, fabric_dev, fabric_prod
        config_path: Optional path to alternative config file
        
    Returns:
        New Settings instance
        
    Example:
        >>> from notebooks.config import reload_settings
        >>> settings = reload_settings(environment="fabric_dev")
    """
    global settings
    Settings.reset()
    settings = Settings.load(environment=environment, config_path=config_path)
    return settings


# Module exports
__all__ = [
    "settings",
    "Settings", 
    "get_settings",
    "reload_settings",
]

# Version info
__version__ = "1.0.0"
