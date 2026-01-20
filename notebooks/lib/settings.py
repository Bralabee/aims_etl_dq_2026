"""
AIMS Data Platform - Settings Manager
======================================

Singleton settings manager with environment detection and YAML configuration.

This module provides a centralized, immutable settings object that:
- Auto-detects the execution environment (local vs Fabric)
- Loads settings from YAML configuration
- Supports environment variable overrides
- Provides type-safe path accessors

Usage:
    from notebooks.lib.settings import Settings
    
    # Auto-detect environment
    settings = Settings.load()
    
    # Explicit environment
    settings = Settings.load(environment="fabric_dev")
    
    # Access settings
    print(f"Environment: {settings.environment}")
    print(f"Bronze dir: {settings.bronze_dir}")
    print(f"DQ threshold: {settings.get_dq_threshold('high')}")
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Literal, Optional, Union

# Try to import yaml, provide helpful error if not available
try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

# Try to load dotenv
try:
    from dotenv import load_dotenv
    _HAS_DOTENV = True
except ImportError:
    _HAS_DOTENV = False


# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

EnvironmentType = Literal["local", "fabric_dev", "fabric_prod"]
SeverityType = Literal["critical", "high", "medium", "low"]
StorageFormatType = Literal["parquet", "delta"]


# =============================================================================
# SETTINGS CLASS
# =============================================================================

@dataclass(frozen=True)
class Settings:
    """
    Immutable settings container with environment-aware configuration.
    
    This is a frozen dataclass - settings cannot be modified after creation.
    Use Settings.load() to create an instance with proper initialization.
    
    Attributes:
        environment: Current environment (local, fabric_dev, fabric_prod)
        base_dir: Base directory for all paths
        storage_format: Default storage format (parquet/delta)
        max_workers: Maximum parallel workers
        sample_size: Sample size for data processing (None = full data)
        
        dq_threshold: Data quality pass threshold
        null_tolerance: Maximum null percentage tolerance
        severity_levels: Quality thresholds by severity
        
        paths: Dictionary of path templates
        pipeline: Pipeline phase configuration
        storage: Storage configuration
        logging_config: Logging configuration
        
    Example:
        >>> settings = Settings.load()
        >>> print(settings.bronze_dir)
        >>> print(settings.get_dq_threshold("high"))
    """
    
    # Core settings
    environment: EnvironmentType
    base_dir: Path
    storage_format: StorageFormatType
    max_workers: int
    sample_size: Optional[int]
    enable_profiling: bool
    cache_enabled: bool
    log_level: str
    
    # Data quality settings
    dq_threshold: float
    null_tolerance: float
    duplicate_tolerance: float
    severity_levels: Dict[str, float]
    
    # Path templates (stored as strings, accessed via properties)
    _paths: Dict[str, str] = field(repr=False)
    
    # Pipeline configuration
    pipeline: Dict[str, Any] = field(repr=False)
    
    # Storage configuration
    storage_config: Dict[str, Any] = field(repr=False)
    
    # Incremental load settings
    incremental: Dict[str, Any] = field(repr=False)
    
    # Logging configuration
    logging_config: Dict[str, Any] = field(repr=False)
    
    # Alerting configuration
    alerting: Dict[str, Any] = field(repr=False)
    
    # Table-specific overrides
    table_overrides: Dict[str, Dict[str, Any]] = field(repr=False)
    
    # Singleton instance storage (class-level)
    _instance: Optional["Settings"] = field(default=None, repr=False, compare=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)
    
    # -------------------------------------------------------------------------
    # Path Properties
    # -------------------------------------------------------------------------
    
    @property
    def bronze_dir(self) -> Path:
        """Get the bronze layer data directory."""
        return self.base_dir / self._paths.get("bronze", "data/bronze")
    
    @property
    def silver_dir(self) -> Path:
        """Get the silver layer data directory."""
        return self.base_dir / self._paths.get("silver", "data/silver")
    
    @property
    def silver_layer_dir(self) -> Path:
        """Get the silver_layer data directory."""
        return self.base_dir / self._paths.get("silver_layer", "data/silver_layer")
    
    @property
    def gold_dir(self) -> Path:
        """Get the gold layer data directory."""
        return self.base_dir / self._paths.get("gold", "data/gold")
    
    @property
    def config_dir(self) -> Path:
        """Get the configuration directory."""
        return self.base_dir / self._paths.get("config", "config/data_quality")
    
    @property
    def state_dir(self) -> Path:
        """Get the state directory for checkpoints and watermarks."""
        return self.base_dir / self._paths.get("state", "data/state")
    
    @property
    def quarantine_dir(self) -> Path:
        """Get the quarantine directory for failed records."""
        return self.base_dir / self._paths.get("quarantine", "data/quarantine")
    
    @property
    def ge_root_dir(self) -> Path:
        """Get the Great Expectations root directory."""
        return self.base_dir / self._paths.get("ge_root", "great_expectations")
    
    @property
    def ge_configs_dir(self) -> Path:
        """Get the generated GE configs directory."""
        return self.base_dir / self._paths.get("ge_configs", "dq_great_expectations/generated_configs")
    
    @property
    def reports_dir(self) -> Path:
        """Get the reports output directory."""
        return self.base_dir / self._paths.get("reports", "data/reports")
    
    @property
    def validation_results_dir(self) -> Path:
        """Get the validation results directory."""
        return self.base_dir / self._paths.get("validation_results", "notebooks/config/validation_results")
    
    @property
    def logs_dir(self) -> Path:
        """Get the logs directory."""
        return self.base_dir / self._paths.get("logs", "logs")
    
    @property
    def watermark_db_path(self) -> Path:
        """Get the watermark database path."""
        return self.base_dir / self.incremental.get("watermark_db", "watermarks.db")
    
    # -------------------------------------------------------------------------
    # DQ Threshold Methods
    # -------------------------------------------------------------------------
    
    def get_dq_threshold(self, severity: str = "medium") -> float:
        """
        Get data quality threshold for a severity level.
        
        Args:
            severity: Severity level (critical, high, medium, low)
            
        Returns:
            Quality threshold as a percentage (0-100)
            
        Example:
            >>> threshold = settings.get_dq_threshold("high")
            >>> print(f"High severity threshold: {threshold}%")
        """
        severity_lower = severity.lower()
        return self.severity_levels.get(severity_lower, self.dq_threshold)
    
    def get_table_config(self, table_name: str) -> Dict[str, Any]:
        """
        Get table-specific configuration with fallback to defaults.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Configuration dictionary for the table
            
        Example:
            >>> config = settings.get_table_config("AIMS_ASSETS")
            >>> print(f"DQ threshold: {config.get('dq_threshold')}")
        """
        default_config = {
            "dq_threshold": self.dq_threshold,
            "null_tolerance": self.null_tolerance,
            "watermark_column": self.incremental.get("default_watermark_column", "LASTUPDATED"),
        }
        
        table_specific = self.table_overrides.get(table_name, {})
        return {**default_config, **table_specific}
    
    # -------------------------------------------------------------------------
    # Pipeline Phase Methods
    # -------------------------------------------------------------------------
    
    def is_phase_enabled(self, phase_name: str) -> bool:
        """
        Check if a pipeline phase is enabled.
        
        Args:
            phase_name: Name of the phase (profiling, validation, etc.)
            
        Returns:
            True if the phase is enabled
        """
        phases = self.pipeline.get("phases", {})
        return phases.get(phase_name, False)
    
    @property
    def enabled_phases(self) -> list[str]:
        """Get list of enabled pipeline phases."""
        phases = self.pipeline.get("phases", {})
        return [name for name, enabled in phases.items() if enabled]
    
    @property
    def pipeline_phases(self) -> Dict[str, bool]:
        """
        Get pipeline phases configuration dictionary.
        
        Returns:
            Dictionary mapping phase names to enabled status.
            
        Example:
            >>> settings.pipeline_phases.get("profiling", True)
            True
        """
        return self.pipeline.get("phases", {})
    
    # -------------------------------------------------------------------------
    # Path Helper Methods
    # -------------------------------------------------------------------------
    
    def get_path(self, path_key: str) -> Path:
        """
        Get a path by key from the paths configuration.
        
        Args:
            path_key: Key from the paths configuration
            
        Returns:
            Absolute Path object
            
        Raises:
            KeyError: If path_key not found in configuration
        """
        if path_key not in self._paths:
            raise KeyError(f"Unknown path key: {path_key}")
        return self.base_dir / self._paths[path_key]
    
    def resolve_path(self, relative_path: Union[str, Path]) -> Path:
        """
        Resolve a relative path against the base directory.
        
        Args:
            relative_path: Path relative to base_dir
            
        Returns:
            Absolute Path object
        """
        return self.base_dir / relative_path
    
    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert settings to a dictionary for serialization or display.
        
        Returns:
            Dictionary representation of all settings
        """
        return {
            "environment": self.environment,
            "base_dir": str(self.base_dir),
            "storage_format": self.storage_format,
            "max_workers": self.max_workers,
            "sample_size": self.sample_size,
            "enable_profiling": self.enable_profiling,
            "cache_enabled": self.cache_enabled,
            "log_level": self.log_level,
            "data_quality": {
                "threshold": self.dq_threshold,
                "null_tolerance": self.null_tolerance,
                "duplicate_tolerance": self.duplicate_tolerance,
                "severity_levels": self.severity_levels,
            },
            "paths": {
                "bronze": str(self.bronze_dir),
                "silver": str(self.silver_dir),
                "silver_layer": str(self.silver_layer_dir),
                "gold": str(self.gold_dir),
                "config": str(self.config_dir),
                "state": str(self.state_dir),
                "quarantine": str(self.quarantine_dir),
                "reports": str(self.reports_dir),
                "logs": str(self.logs_dir),
            },
            "pipeline": self.pipeline,
            "storage": self.storage_config,
            "incremental": self.incremental,
            "logging": self.logging_config,
        }
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        return (
            f"Settings(environment={self.environment}, "
            f"base_dir={self.base_dir}, "
            f"storage_format={self.storage_format})"
        )
    
    # -------------------------------------------------------------------------
    # Factory Method (Singleton)
    # -------------------------------------------------------------------------
    
    @classmethod
    def load(
        cls,
        environment: str = "auto",
        config_path: Optional[Union[str, Path]] = None,
        force_reload: bool = False,
    ) -> "Settings":
        """
        Load settings for the specified environment.
        
        This is the primary way to create a Settings instance. It implements
        a singleton pattern - subsequent calls return the same instance unless
        force_reload is True.
        
        Args:
            environment: Environment name or "auto" for detection.
                        Valid values: auto, local, fabric_dev, fabric_prod
            config_path: Optional path to YAML config file.
                        Defaults to notebooks/config/notebook_settings.yaml
            force_reload: Force reloading settings even if already loaded
            
        Returns:
            Settings instance for the specified environment
            
        Example:
            >>> # Auto-detect environment
            >>> settings = Settings.load()
            
            >>> # Explicit environment
            >>> settings = Settings.load(environment="fabric_dev")
            
            >>> # Force reload
            >>> settings = Settings.load(force_reload=True)
        """
        # Check singleton cache (use module-level since frozen dataclass)
        global _settings_instance
        
        if not force_reload and _settings_instance is not None:
            return _settings_instance
        
        # Load .env file if available
        if _HAS_DOTENV:
            env_file = _find_env_file()
            if env_file:
                load_dotenv(env_file, override=True)
        
        # Detect environment
        detected_env = _detect_environment(environment)
        
        # Find and load config file
        config_file = _find_config_file(config_path)
        config_data = _load_yaml_config(config_file)
        
        # Merge environment-specific settings
        env_config = config_data.get("environments", {}).get(detected_env, {})
        
        # Determine base directory
        base_dir = _determine_base_dir(env_config, detected_env)
        
        # Get data quality settings
        dq_config = config_data.get("data_quality", {})
        
        # Create immutable settings instance
        instance = cls(
            environment=detected_env,
            base_dir=base_dir,
            storage_format=_get_env_override(
                "AIMS_STORAGE_FORMAT",
                env_config.get("storage_format", "parquet")
            ),
            max_workers=int(_get_env_override(
                "AIMS_MAX_WORKERS",
                env_config.get("max_workers", 4)
            )),
            sample_size=_get_optional_int(
                "AIMS_SAMPLE_SIZE",
                env_config.get("sample_size")
            ),
            enable_profiling=_get_env_bool(
                "AIMS_ENABLE_PROFILING",
                env_config.get("enable_profiling", False)
            ),
            cache_enabled=_get_env_bool(
                "AIMS_CACHE_ENABLED",
                env_config.get("cache_enabled", True)
            ),
            log_level=_get_env_override(
                "AIMS_LOG_LEVEL",
                env_config.get("log_level", "INFO")
            ),
            dq_threshold=float(_get_env_override(
                "AIMS_DQ_THRESHOLD",
                dq_config.get("threshold", 85.0)
            )),
            null_tolerance=float(_get_env_override(
                "AIMS_NULL_TOLERANCE",
                dq_config.get("null_tolerance", 5.0)
            )),
            duplicate_tolerance=float(_get_env_override(
                "AIMS_DUPLICATE_TOLERANCE",
                dq_config.get("duplicate_tolerance", 1.0)
            )),
            severity_levels=dq_config.get("severity_levels", {
                "critical": 100.0,
                "high": 95.0,
                "medium": 85.0,
                "low": 70.0,
            }),
            _paths=_get_platform_paths(config_data, detected_env),
            pipeline=config_data.get("pipeline", {}),
            storage_config=config_data.get("storage", {}),
            incremental=config_data.get("incremental", {}),
            logging_config=config_data.get("logging", {}),
            alerting=config_data.get("alerting", {}),
            table_overrides=config_data.get("table_overrides", {}),
        )
        
        # Cache the instance
        _settings_instance = instance
        
        return instance
    
    @classmethod
    def reset(cls) -> None:
        """
        Reset the singleton instance.
        
        Use this to force Settings.load() to create a new instance.
        Useful for testing or when configuration files have changed.
        """
        global _settings_instance
        _settings_instance = None


# =============================================================================
# MODULE-LEVEL SINGLETON CACHE
# =============================================================================

_settings_instance: Optional[Settings] = None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _detect_environment(requested: str) -> EnvironmentType:
    """
    Detect the execution environment.
    
    Priority:
    1. Environment variable AIMS_ENVIRONMENT
    2. Explicit requested value (if not "auto")
    3. Auto-detection based on platform
    """
    # Check environment variable first
    env_override = os.environ.get("AIMS_ENVIRONMENT")
    if env_override and env_override in ("local", "fabric_dev", "fabric_prod"):
        return env_override  # type: ignore
    
    # Use requested if explicitly specified
    if requested != "auto" and requested in ("local", "fabric_dev", "fabric_prod"):
        return requested  # type: ignore
    
    # Auto-detect based on platform
    fabric_path = Path("/lakehouse/default/Files")
    if fabric_path.exists():
        # In Fabric - check if dev or prod via environment variable
        is_prod = os.environ.get("AIMS_IS_PRODUCTION", "").lower() in ("true", "1", "yes")
        return "fabric_prod" if is_prod else "fabric_dev"
    
    return "local"


def _find_config_file(config_path: Optional[Union[str, Path]]) -> Optional[Path]:
    """Find the YAML configuration file."""
    if config_path:
        path = Path(config_path)
        if path.exists():
            return path
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    # Search for config file in standard locations
    search_paths = [
        # Fabric: Check Files/notebooks/config first (user-uploaded config)
        Path("/lakehouse/default/Files/notebooks/config/notebook_settings.yaml"),
        # Package location (relative to this file)
        Path(__file__).parent.parent / "config" / "notebook_settings.yaml",
        # Current working directory
        Path.cwd() / "notebooks" / "config" / "notebook_settings.yaml",
        # Project root
        _get_project_root() / "notebooks" / "config" / "notebook_settings.yaml",
    ]
    
    for path in search_paths:
        if path.exists():
            return path
    
    # Return None if not found - will use defaults
    return None


def _find_env_file() -> Optional[Path]:
    """Find the .env file."""
    search_paths = [
        Path.cwd() / ".env",
        _get_project_root() / ".env",
    ]
    
    for path in search_paths:
        if path.exists():
            return path
    
    return None


def _get_project_root() -> Path:
    """Get the project root directory."""
    # Navigate up from this file to find project root
    current = Path(__file__).resolve()
    
    # Look for markers of project root
    markers = ["pyproject.toml", "setup.py", ".git", "requirements.txt"]
    
    for parent in current.parents:
        if any((parent / marker).exists() for marker in markers):
            return parent
    
    # Fallback to current working directory
    return Path.cwd()


def _get_platform_paths(config_data: Dict[str, Any], environment: str) -> Dict[str, str]:
    """
    Get the appropriate paths based on environment.
    
    For Fabric environments, uses fabric_paths section.
    For local environments, uses paths section.
    """
    base_paths = config_data.get("paths", {})
    
    if environment.startswith("fabric"):
        # Merge fabric_paths over base paths
        fabric_paths = config_data.get("fabric_paths", {})
        return {**base_paths, **fabric_paths}
    
    return base_paths


def _determine_base_dir(env_config: Dict[str, Any], environment: str) -> Path:
    """Determine the base directory for paths."""
    # Check environment variable first
    env_base = os.environ.get("AIMS_BASE_DIR")
    if env_base:
        return Path(env_base)
    
    # Check config value
    config_base = env_config.get("base_dir")
    if config_base:
        return Path(config_base)
    
    # Auto-detect
    if environment.startswith("fabric"):
        return Path("/lakehouse/default/Files")
    
    return _get_project_root()


def _load_yaml_config(config_path: Optional[Path]) -> Dict[str, Any]:
    """Load YAML configuration file, with fallback to package resources."""
    if yaml is None:
        # YAML not available, return empty config (will use defaults)
        import warnings
        warnings.warn(
            "PyYAML not installed. Using default settings. "
            "Install with: pip install pyyaml"
        )
        return {}
    
    # Try loading from file path first
    if config_path and config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            import warnings
            warnings.warn(f"Failed to load config from {config_path}: {e}")
    
    # Fallback: Try to load from package resources (for wheel installations)
    try:
        try:
            # Python 3.9+
            from importlib.resources import files
            config_text = files("notebooks.config").joinpath("notebook_settings.yaml").read_text()
        except (ImportError, TypeError):
            # Python 3.7-3.8 fallback
            import importlib.resources as pkg_resources
            config_text = pkg_resources.read_text("notebooks.config", "notebook_settings.yaml")
        return yaml.safe_load(config_text) or {}
    except Exception:
        pass
    
    # Final fallback: return hardcoded Fabric-compatible defaults
    return _get_default_config()


def _get_env_override(env_var: str, default: Any) -> Any:
    """Get environment variable override or return default."""
    value = os.environ.get(env_var)
    return value if value is not None else default


def _get_env_bool(env_var: str, default: bool) -> bool:
    """Get boolean from environment variable."""
    value = os.environ.get(env_var)
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes", "on")


def _get_optional_int(env_var: str, default: Optional[int]) -> Optional[int]:
    """Get optional integer from environment variable."""
    value = os.environ.get(env_var)
    if value is None:
        return default
    if value.lower() in ("none", "null", ""):
        return None
    try:
        return int(value)
    except ValueError:
        return default


def _get_default_config() -> Dict[str, Any]:
    """Return hardcoded default configuration when YAML fails to load."""
    return {
        "environments": {
            "local": {
                "base_dir": None,
                "storage_format": "parquet",
                "max_workers": 4,
            },
            "fabric_dev": {
                "base_dir": "/lakehouse/default/Files",
                "storage_format": "delta",
                "max_workers": 8,
            },
            "fabric_prod": {
                "base_dir": "/lakehouse/default/Files",
                "storage_format": "delta",
                "max_workers": 16,
            },
        },
        "data_quality": {
            "threshold": 85.0,
            "null_tolerance": 5.0,
            "duplicate_tolerance": 1.0,
        },
        "paths": {
            "bronze": "data/Samples_LH_Bronze_Aims_26_parquet",
            "silver": "data/Silver",
            "gold": "data/Gold",
            "config": "config/data_quality",
            "state": "data/state",
        },
        "fabric_paths": {
            "bronze": "Bronze",
            "silver": "Silver",
            "gold": "Gold",
            "config": "config/data_quality",
            "state": "state",
        },
        "pipeline": {},
        "storage": {},
        "incremental": {},
        "logging": {},
        "alerting": {},
        "table_overrides": {},
    }


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def get_settings(
    environment: str = "auto",
    force_reload: bool = False,
) -> Settings:
    """
    Convenience function to get settings instance.
    
    This is a shorthand for Settings.load() for more concise imports.
    
    Args:
        environment: Environment name or "auto" for detection
        force_reload: Force reloading settings
        
    Returns:
        Settings instance
        
    Example:
        >>> from notebooks.lib.settings import get_settings
        >>> settings = get_settings()
    """
    return Settings.load(environment=environment, force_reload=force_reload)
