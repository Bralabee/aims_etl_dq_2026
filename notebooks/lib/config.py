"""
AIMS Data Platform - Configuration Module
==========================================

Centralized configuration management for notebooks with environment variable
overrides and sensible defaults.

Usage:
    from notebooks.lib.config import NotebookConfig
    
    # Use defaults
    config = NotebookConfig()
    
    # Or customize
    config = NotebookConfig(
        dq_threshold=0.98,
        storage_format="delta"
    )
    
    # Access settings
    print(f"DQ Threshold: {config.dq_threshold}")
    print(f"Output format: {config.storage_format}")
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Literal, Optional, Union


def _get_env_float(key: str, default: float) -> float:
    """Get float value from environment variable."""
    value = os.environ.get(key)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _get_env_int(key: str, default: int) -> int:
    """Get integer value from environment variable."""
    value = os.environ.get(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_env_bool(key: str, default: bool) -> bool:
    """Get boolean value from environment variable."""
    value = os.environ.get(key)
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes", "on")


def _get_env_str(key: str, default: str) -> str:
    """Get string value from environment variable."""
    return os.environ.get(key, default)


@dataclass
class NotebookConfig:
    """
    Configuration class for AIMS Data Platform notebooks.
    
    Provides centralized configuration with sensible defaults and
    environment variable overrides. All settings can be customized
    via constructor arguments or environment variables.
    
    Environment Variables:
        AIMS_DQ_THRESHOLD: Data quality pass threshold (0.0-1.0)
        AIMS_NULL_TOLERANCE: Maximum null percentage allowed (0.0-1.0)
        AIMS_MAX_WORKERS: Maximum parallel workers
        AIMS_STORAGE_FORMAT: Output format (parquet/delta)
        AIMS_COMPRESSION: Compression codec
        AIMS_LOG_LEVEL: Logging level
        AIMS_BATCH_SIZE: Processing batch size
        AIMS_ENABLE_PROFILING: Enable performance profiling
        AIMS_CACHE_ENABLED: Enable data caching
    
    Attributes:
        dq_threshold: Minimum data quality score to pass (default: 0.95)
        null_tolerance: Maximum allowed null ratio (default: 0.1)
        max_workers: Maximum parallel processing workers (default: 4)
        storage_format: Output storage format (default: "parquet")
        compression: Compression algorithm (default: "snappy")
        log_level: Logging verbosity level (default: "INFO")
        batch_size: Processing batch size (default: 10000)
        enable_profiling: Enable performance profiling (default: False)
        cache_enabled: Enable intermediate caching (default: True)
    
    Example:
        >>> # Use defaults with env var overrides
        >>> config = NotebookConfig()
        >>> print(f"DQ Threshold: {config.dq_threshold}")
        DQ Threshold: 0.95
        
        >>> # Custom configuration
        >>> config = NotebookConfig(
        ...     dq_threshold=0.99,
        ...     storage_format="delta",
        ...     max_workers=8
        ... )
        
        >>> # Access as dictionary
        >>> config_dict = config.to_dict()
    """
    
    # Data Quality Settings
    dq_threshold: float = field(
        default_factory=lambda: _get_env_float("AIMS_DQ_THRESHOLD", 0.95)
    )
    null_tolerance: float = field(
        default_factory=lambda: _get_env_float("AIMS_NULL_TOLERANCE", 0.1)
    )
    duplicate_tolerance: float = field(
        default_factory=lambda: _get_env_float("AIMS_DUPLICATE_TOLERANCE", 0.01)
    )
    
    # Processing Settings
    max_workers: int = field(
        default_factory=lambda: _get_env_int("AIMS_MAX_WORKERS", 4)
    )
    batch_size: int = field(
        default_factory=lambda: _get_env_int("AIMS_BATCH_SIZE", 10000)
    )
    chunk_size: int = field(
        default_factory=lambda: _get_env_int("AIMS_CHUNK_SIZE", 50000)
    )
    
    # Storage Settings
    storage_format: Literal["parquet", "delta"] = field(
        default_factory=lambda: _get_env_str("AIMS_STORAGE_FORMAT", "parquet")  # type: ignore
    )
    compression: str = field(
        default_factory=lambda: _get_env_str("AIMS_COMPRESSION", "snappy")
    )
    
    # Logging Settings
    log_level: str = field(
        default_factory=lambda: _get_env_str("AIMS_LOG_LEVEL", "INFO")
    )
    log_format: str = field(
        default_factory=lambda: _get_env_str(
            "AIMS_LOG_FORMAT",
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        )
    )
    
    # Feature Flags
    enable_profiling: bool = field(
        default_factory=lambda: _get_env_bool("AIMS_ENABLE_PROFILING", False)
    )
    cache_enabled: bool = field(
        default_factory=lambda: _get_env_bool("AIMS_CACHE_ENABLED", True)
    )
    verbose: bool = field(
        default_factory=lambda: _get_env_bool("AIMS_VERBOSE", False)
    )
    
    # Timeout Settings (seconds)
    read_timeout: int = field(
        default_factory=lambda: _get_env_int("AIMS_READ_TIMEOUT", 300)
    )
    write_timeout: int = field(
        default_factory=lambda: _get_env_int("AIMS_WRITE_TIMEOUT", 600)
    )
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self._validate()
    
    def _validate(self) -> None:
        """
        Validate configuration values.
        
        Raises:
            ValueError: If any configuration value is invalid.
        """
        if not 0.0 <= self.dq_threshold <= 1.0:
            raise ValueError(
                f"dq_threshold must be between 0 and 1, got {self.dq_threshold}"
            )
        
        if not 0.0 <= self.null_tolerance <= 1.0:
            raise ValueError(
                f"null_tolerance must be between 0 and 1, got {self.null_tolerance}"
            )
        
        if not 0.0 <= self.duplicate_tolerance <= 1.0:
            raise ValueError(
                f"duplicate_tolerance must be between 0 and 1, got {self.duplicate_tolerance}"
            )
        
        if self.max_workers < 1:
            raise ValueError(
                f"max_workers must be at least 1, got {self.max_workers}"
            )
        
        if self.batch_size < 1:
            raise ValueError(
                f"batch_size must be at least 1, got {self.batch_size}"
            )
        
        if self.storage_format not in ("parquet", "delta"):
            raise ValueError(
                f"storage_format must be 'parquet' or 'delta', got {self.storage_format}"
            )
        
        valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.log_level.upper() not in valid_log_levels:
            raise ValueError(
                f"log_level must be one of {valid_log_levels}, got {self.log_level}"
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dict[str, Any]: Configuration as dictionary.
        
        Example:
            >>> config = NotebookConfig()
            >>> d = config.to_dict()
            >>> print(d['dq_threshold'])
            0.95
        """
        return {
            "dq_threshold": self.dq_threshold,
            "null_tolerance": self.null_tolerance,
            "duplicate_tolerance": self.duplicate_tolerance,
            "max_workers": self.max_workers,
            "batch_size": self.batch_size,
            "chunk_size": self.chunk_size,
            "storage_format": self.storage_format,
            "compression": self.compression,
            "log_level": self.log_level,
            "log_format": self.log_format,
            "enable_profiling": self.enable_profiling,
            "cache_enabled": self.cache_enabled,
            "verbose": self.verbose,
            "read_timeout": self.read_timeout,
            "write_timeout": self.write_timeout,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NotebookConfig":
        """
        Create configuration from dictionary.
        
        Args:
            data: Dictionary with configuration values.
        
        Returns:
            NotebookConfig: New configuration instance.
        
        Example:
            >>> config = NotebookConfig.from_dict({
            ...     'dq_threshold': 0.99,
            ...     'max_workers': 8
            ... })
        """
        # Filter to only valid fields
        valid_fields = {
            "dq_threshold", "null_tolerance", "duplicate_tolerance",
            "max_workers", "batch_size", "chunk_size",
            "storage_format", "compression",
            "log_level", "log_format",
            "enable_profiling", "cache_enabled", "verbose",
            "read_timeout", "write_timeout",
        }
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)
    
    @classmethod
    def from_file(cls, path: Union[str, Path]) -> "NotebookConfig":
        """
        Load configuration from a JSON or YAML file.
        
        Args:
            path: Path to configuration file.
        
        Returns:
            NotebookConfig: New configuration instance.
        
        Raises:
            FileNotFoundError: If config file doesn't exist.
            ValueError: If file format is unsupported.
        
        Example:
            >>> config = NotebookConfig.from_file("config/notebook_config.json")
        """
        import json
        
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        suffix = path.suffix.lower()
        
        if suffix == ".json":
            with open(path, "r") as f:
                data = json.load(f)
        elif suffix in (".yaml", ".yml"):
            try:
                import yaml
                with open(path, "r") as f:
                    data = yaml.safe_load(f)
            except ImportError:
                raise ImportError(
                    "PyYAML is required to load YAML config files. "
                    "Install with: pip install pyyaml"
                )
        else:
            raise ValueError(
                f"Unsupported config file format: {suffix}. "
                "Use .json or .yaml/.yml"
            )
        
        return cls.from_dict(data)
    
    def save(self, path: Union[str, Path]) -> Path:
        """
        Save configuration to a JSON file.
        
        Args:
            path: Output file path.
        
        Returns:
            Path: The saved file path.
        
        Example:
            >>> config = NotebookConfig(dq_threshold=0.99)
            >>> config.save("config/my_config.json")
        """
        import json
        
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        
        return path
    
    def update(self, **kwargs: Any) -> "NotebookConfig":
        """
        Create a new config with updated values.
        
        Args:
            **kwargs: Configuration values to update.
        
        Returns:
            NotebookConfig: New configuration with updates applied.
        
        Example:
            >>> config = NotebookConfig()
            >>> new_config = config.update(dq_threshold=0.99, max_workers=8)
        """
        current = self.to_dict()
        current.update(kwargs)
        return NotebookConfig.from_dict(current)
    
    def __repr__(self) -> str:
        """String representation of config."""
        return (
            f"NotebookConfig("
            f"dq_threshold={self.dq_threshold}, "
            f"storage_format='{self.storage_format}', "
            f"max_workers={self.max_workers})"
        )


# =============================================================================
# PRESET CONFIGURATIONS
# =============================================================================

class ConfigPresets:
    """
    Pre-defined configuration presets for common scenarios.
    
    Example:
        >>> from notebooks.lib.config import ConfigPresets
        >>> config = ConfigPresets.development()
        >>> production_config = ConfigPresets.production()
    """
    
    @staticmethod
    def development() -> NotebookConfig:
        """
        Development configuration with relaxed settings.
        
        Returns:
            NotebookConfig: Development-optimized configuration.
        """
        return NotebookConfig(
            dq_threshold=0.8,
            null_tolerance=0.2,
            max_workers=2,
            batch_size=1000,
            log_level="DEBUG",
            verbose=True,
            enable_profiling=True,
        )
    
    @staticmethod
    def production() -> NotebookConfig:
        """
        Production configuration with strict settings.
        
        Returns:
            NotebookConfig: Production-optimized configuration.
        """
        return NotebookConfig(
            dq_threshold=0.99,
            null_tolerance=0.05,
            duplicate_tolerance=0.001,
            max_workers=8,
            batch_size=50000,
            log_level="WARNING",
            verbose=False,
            enable_profiling=False,
            cache_enabled=True,
        )
    
    @staticmethod
    def testing() -> NotebookConfig:
        """
        Testing configuration with minimal resources.
        
        Returns:
            NotebookConfig: Test-optimized configuration.
        """
        return NotebookConfig(
            dq_threshold=0.9,
            max_workers=1,
            batch_size=100,
            log_level="DEBUG",
            verbose=True,
            cache_enabled=False,
        )
    
    @staticmethod
    def high_performance() -> NotebookConfig:
        """
        High-performance configuration for large datasets.
        
        Returns:
            NotebookConfig: Performance-optimized configuration.
        """
        return NotebookConfig(
            max_workers=16,
            batch_size=100000,
            chunk_size=500000,
            compression="zstd",
            cache_enabled=True,
            enable_profiling=False,
        )


# Default global config instance
_default_config: Optional[NotebookConfig] = None


def get_config() -> NotebookConfig:
    """
    Get the global default configuration.
    
    Returns:
        NotebookConfig: The global configuration instance.
    
    Example:
        >>> from notebooks.lib.config import get_config
        >>> config = get_config()
        >>> print(config.dq_threshold)
    """
    global _default_config
    if _default_config is None:
        _default_config = NotebookConfig()
    return _default_config


def set_config(config: NotebookConfig) -> None:
    """
    Set the global default configuration.
    
    Args:
        config: Configuration instance to set as default.
    
    Example:
        >>> from notebooks.lib.config import set_config, ConfigPresets
        >>> set_config(ConfigPresets.production())
    """
    global _default_config
    _default_config = config
