"""
AIMS Data Platform - Platform Utilities
=======================================

Cross-platform utilities that work seamlessly on both Local and MS Fabric environments.

This module provides platform detection, path management, and file operations
that automatically adapt to the execution environment.

Usage:
    from notebooks.lib.platform_utils import IS_FABRIC, get_data_paths, copy_file
    
    # Check platform
    if IS_FABRIC:
        print("Running in Microsoft Fabric")
    else:
        print("Running locally")
    
    # Get standardized paths
    paths = get_data_paths()
    bronze_dir = paths['BRONZE_DIR']
    
    # Platform-aware file copy
    copy_file(source_path, dest_path)
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, Union

# =============================================================================
# PLATFORM DETECTION
# =============================================================================

def _detect_fabric_environment() -> bool:
    """
    Detect if running in Microsoft Fabric environment.
    
    Detection is based on the existence of the Fabric lakehouse path.
    
    Returns:
        bool: True if running in Fabric, False otherwise.
    
    Example:
        >>> is_fabric = _detect_fabric_environment()
        >>> print(f"Running in Fabric: {is_fabric}")
    """
    fabric_path = Path("/lakehouse/default/Files")
    return fabric_path.exists()


# Global platform detection - evaluated once at import time
IS_FABRIC: bool = _detect_fabric_environment()
"""
Boolean flag indicating whether code is running in Microsoft Fabric.

True if running in MS Fabric environment, False for local development.

Example:
    >>> from notebooks.lib.platform_utils import IS_FABRIC
    >>> if IS_FABRIC:
    ...     print("Fabric mode")
    ... else:
    ...     print("Local mode")
"""


# =============================================================================
# MSSPARKUTILS HANDLING
# =============================================================================

_mssparkutils_cache: Optional[Any] = None
_mssparkutils_checked: bool = False


def safe_import_mssparkutils() -> Optional[Any]:
    """
    Safely import mssparkutils for Fabric environments.
    
    Returns the mssparkutils module if available (Fabric), or None (local).
    The result is cached for performance.
    
    Returns:
        Optional[Any]: mssparkutils module or None if not available.
    
    Example:
        >>> mssparkutils = safe_import_mssparkutils()
        >>> if mssparkutils:
        ...     mssparkutils.fs.ls("/lakehouse/default/Files")
        ... else:
        ...     print("mssparkutils not available locally")
    """
    global _mssparkutils_cache, _mssparkutils_checked
    
    if _mssparkutils_checked:
        return _mssparkutils_cache
    
    _mssparkutils_checked = True
    
    if not IS_FABRIC:
        _mssparkutils_cache = None
        return None
    
    try:
        from notebookutils import mssparkutils
        _mssparkutils_cache = mssparkutils
        return mssparkutils
    except ImportError:
        try:
            # Alternative import path in some Fabric versions
            import mssparkutils as msu
            _mssparkutils_cache = msu
            return msu
        except ImportError:
            _mssparkutils_cache = None
            return None


# =============================================================================
# PATH MANAGEMENT
# =============================================================================

def get_base_dir() -> Path:
    """
    Get the appropriate base directory for the current platform.
    
    Returns:
        Path: Base directory path.
            - Fabric: /lakehouse/default/Files
            - Local: Project root directory (1_AIMS_LOCAL_2026)
    
    Example:
        >>> base = get_base_dir()
        >>> print(f"Base directory: {base}")
        Base directory: /home/user/projects/1_AIMS_LOCAL_2026
    """
    if IS_FABRIC:
        return Path("/lakehouse/default/Files")
    
    # For local development, find project root
    # Start from this file's location and navigate up to find project root
    current = Path(__file__).resolve()
    
    # Navigate up to find the project root (contains 'notebooks' folder)
    for parent in [current] + list(current.parents):
        if (parent / "notebooks").exists() and (parent / "config").exists():
            return parent
        if parent.name == "1_AIMS_LOCAL_2026":
            return parent
    
    # Fallback: environment variable or current working directory
    env_base = os.environ.get("AIMS_BASE_DIR")
    if env_base:
        return Path(env_base)
    
    return Path.cwd()


def get_data_paths() -> Dict[str, Path]:
    """
    Get standardized data directory paths for the current platform.
    
    Returns a dictionary with paths to all standard data directories,
    automatically adjusted for the execution environment.
    
    Returns:
        Dict[str, Path]: Dictionary containing:
            - BRONZE_DIR: Raw data landing zone
            - SILVER_DIR: Cleaned/transformed data
            - GOLD_DIR: Business-ready data
            - CONFIG_DIR: Configuration files
            - STATE_DIR: Pipeline state/checkpoints
            - BASE_DIR: Root directory
            - DATA_DIR: Parent data directory
    
    Example:
        >>> paths = get_data_paths()
        >>> print(paths['BRONZE_DIR'])
        /home/user/projects/1_AIMS_LOCAL_2026/data/bronze
        >>> 
        >>> # Access all paths
        >>> for name, path in paths.items():
        ...     print(f"{name}: {path}")
    """
    base_dir = get_base_dir()
    
    if IS_FABRIC:
        # Fabric uses lakehouse structure - Capitalized folder names
        data_dir = base_dir
        return {
            "BASE_DIR": base_dir,
            "DATA_DIR": data_dir,
            "BRONZE_DIR": data_dir / "Bronze",
            "SILVER_DIR": data_dir / "Silver",
            "GOLD_DIR": data_dir / "Gold",
            "CONFIG_DIR": data_dir / "config",
            "STATE_DIR": data_dir / "state",
        }
    else:
        # Local uses project structure
        data_dir = base_dir / "data"
        return {
            "BASE_DIR": base_dir,
            "DATA_DIR": data_dir,
            "BRONZE_DIR": data_dir / "Samples_LH_Bronze_Aims_26_parquet",
            "SILVER_DIR": data_dir / "Silver",
            "GOLD_DIR": data_dir / "Gold",
            "CONFIG_DIR": base_dir / "config",
            "STATE_DIR": data_dir / "state",
        }


# =============================================================================
# FILE OPERATIONS
# =============================================================================

def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Platform-aware directory creation that works on both Local and Fabric.
    
    Args:
        path: Directory path to ensure exists.
    
    Returns:
        Path: The ensured directory path.
    
    Raises:
        OSError: If directory cannot be created.
    
    Example:
        >>> output_dir = ensure_directory("/path/to/output")
        >>> print(f"Directory ready: {output_dir}")
    """
    path = Path(path)
    
    if IS_FABRIC:
        mssparkutils = safe_import_mssparkutils()
        if mssparkutils:
            try:
                # Use mssparkutils for Fabric
                path_str = str(path)
                if not mssparkutils.fs.exists(path_str):
                    mssparkutils.fs.mkdirs(path_str)
            except Exception:
                # Fallback to standard mkdir
                path.mkdir(parents=True, exist_ok=True)
        else:
            path.mkdir(parents=True, exist_ok=True)
    else:
        path.mkdir(parents=True, exist_ok=True)
    
    return path


def copy_file(
    src: Union[str, Path],
    dest: Union[str, Path],
    overwrite: bool = True
) -> Path:
    """
    Copy a file with platform-aware implementation.
    
    Uses shutil locally and mssparkutils in Fabric for optimal performance.
    
    Args:
        src: Source file path.
        dest: Destination file path.
        overwrite: Whether to overwrite existing destination file.
    
    Returns:
        Path: The destination path.
    
    Raises:
        FileNotFoundError: If source file doesn't exist.
        FileExistsError: If destination exists and overwrite=False.
    
    Example:
        >>> copy_file("data/input.parquet", "data/backup/input.parquet")
        PosixPath('data/backup/input.parquet')
    """
    src_path = Path(src)
    dest_path = Path(dest)
    
    # Validate source exists
    if not src_path.exists():
        raise FileNotFoundError(f"Source file not found: {src_path}")
    
    # Check destination
    if dest_path.exists() and not overwrite:
        raise FileExistsError(f"Destination already exists: {dest_path}")
    
    # Ensure destination directory exists
    ensure_directory(dest_path.parent)
    
    if IS_FABRIC:
        mssparkutils = safe_import_mssparkutils()
        if mssparkutils:
            try:
                mssparkutils.fs.cp(str(src_path), str(dest_path), recurse=False)
                return dest_path
            except Exception:
                # Fallback to shutil
                pass
    
    # Local or fallback: use shutil
    shutil.copy2(str(src_path), str(dest_path))
    return dest_path


def copy_directory(
    src: Union[str, Path],
    dest: Union[str, Path],
    overwrite: bool = True
) -> Path:
    """
    Copy a directory recursively with platform-aware implementation.
    
    Args:
        src: Source directory path.
        dest: Destination directory path.
        overwrite: Whether to overwrite existing destination.
    
    Returns:
        Path: The destination path.
    
    Example:
        >>> copy_directory("data/bronze/raw", "data/backup/raw")
        PosixPath('data/backup/raw')
    """
    src_path = Path(src)
    dest_path = Path(dest)
    
    if not src_path.exists():
        raise FileNotFoundError(f"Source directory not found: {src_path}")
    
    if dest_path.exists():
        if overwrite:
            shutil.rmtree(str(dest_path))
        else:
            raise FileExistsError(f"Destination already exists: {dest_path}")
    
    if IS_FABRIC:
        mssparkutils = safe_import_mssparkutils()
        if mssparkutils:
            try:
                mssparkutils.fs.cp(str(src_path), str(dest_path), recurse=True)
                return dest_path
            except Exception:
                pass
    
    shutil.copytree(str(src_path), str(dest_path))
    return dest_path


def file_exists(path: Union[str, Path]) -> bool:
    """
    Check if a file exists with platform-aware implementation.
    
    Args:
        path: File path to check.
    
    Returns:
        bool: True if file exists, False otherwise.
    
    Example:
        >>> if file_exists("data/bronze/data.parquet"):
        ...     print("File found!")
    """
    path = Path(path)
    
    if IS_FABRIC:
        mssparkutils = safe_import_mssparkutils()
        if mssparkutils:
            try:
                return mssparkutils.fs.exists(str(path))
            except Exception:
                pass
    
    return path.exists()


def list_files(
    directory: Union[str, Path],
    pattern: str = "*"
) -> list[Path]:
    """
    List files in a directory with optional pattern matching.
    
    Args:
        directory: Directory to list files from.
        pattern: Glob pattern for filtering (default: "*" for all files).
    
    Returns:
        list[Path]: List of file paths matching the pattern.
    
    Example:
        >>> parquet_files = list_files("data/bronze", "*.parquet")
        >>> for f in parquet_files:
        ...     print(f.name)
    """
    dir_path = Path(directory)
    
    if not dir_path.exists():
        return []
    
    return list(dir_path.glob(pattern))


# =============================================================================
# DATA READING UTILITIES
# =============================================================================

def read_parquet_safe(
    path: Union[str, Path],
    sample_size: Optional[int] = None,
    columns: Optional[list[str]] = None
) -> "pd.DataFrame":
    """
    Read a parquet file with automatic engine selection and optional sampling.
    
    Handles both local files and Fabric lakehouse paths. Automatically selects
    the appropriate parquet engine (pyarrow preferred, fastparquet fallback).
    
    Args:
        path: Path to the parquet file or directory.
        sample_size: Optional number of rows to sample (None = all rows).
        columns: Optional list of columns to read (None = all columns).
    
    Returns:
        pd.DataFrame: The loaded DataFrame.
    
    Raises:
        FileNotFoundError: If the parquet file doesn't exist.
        ImportError: If neither pyarrow nor fastparquet is available.
    
    Example:
        >>> # Read full file
        >>> df = read_parquet_safe("data/bronze/sales.parquet")
        >>> 
        >>> # Read sample with specific columns
        >>> df_sample = read_parquet_safe(
        ...     "data/bronze/sales.parquet",
        ...     sample_size=1000,
        ...     columns=['date', 'amount']
        ... )
    """
    import pandas as pd
    
    path = Path(path)
    
    # Validate path exists
    if not file_exists(path):
        raise FileNotFoundError(f"Parquet file not found: {path}")
    
    # Determine engine
    engine = "pyarrow"
    try:
        import pyarrow  # noqa: F401
    except ImportError:
        try:
            import fastparquet  # noqa: F401
            engine = "fastparquet"
        except ImportError:
            raise ImportError(
                "Neither pyarrow nor fastparquet is installed. "
                "Install one with: pip install pyarrow"
            )
    
    # Build read arguments
    read_kwargs: Dict[str, Any] = {
        "engine": engine,
    }
    
    if columns:
        read_kwargs["columns"] = columns
    
    # Read the parquet file
    df = pd.read_parquet(str(path), **read_kwargs)
    
    # Apply sampling if requested
    if sample_size is not None and len(df) > sample_size:
        df = df.sample(n=sample_size, random_state=42)
    
    return df


def write_parquet_safe(
    df: "pd.DataFrame",
    path: Union[str, Path],
    partition_cols: Optional[list[str]] = None,
    compression: str = "snappy"
) -> Path:
    """
    Write a DataFrame to parquet with platform-aware implementation.
    
    Args:
        df: DataFrame to write.
        path: Output path for the parquet file.
        partition_cols: Optional columns to partition by.
        compression: Compression codec (default: snappy).
    
    Returns:
        Path: The written file path.
    
    Example:
        >>> write_parquet_safe(df, "data/silver/processed.parquet")
        PosixPath('data/silver/processed.parquet')
    """
    path = Path(path)
    
    # Ensure parent directory exists
    ensure_directory(path.parent)
    
    # Write parquet
    write_kwargs = {
        "compression": compression,
        "index": False,
    }
    
    if partition_cols:
        write_kwargs["partition_cols"] = partition_cols
    
    df.to_parquet(str(path), **write_kwargs)
    
    return path


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_platform_info() -> Dict[str, Any]:
    """
    Get comprehensive platform information.
    
    Returns:
        Dict[str, Any]: Dictionary with platform details.
    
    Example:
        >>> info = get_platform_info()
        >>> print(f"Platform: {'Fabric' if info['is_fabric'] else 'Local'}")
    """
    import sys
    
    mssparkutils = safe_import_mssparkutils()
    paths = get_data_paths()
    
    return {
        "is_fabric": IS_FABRIC,
        "platform": "Microsoft Fabric" if IS_FABRIC else "Local",
        "python_version": sys.version,
        "base_dir": str(paths["BASE_DIR"]),
        "mssparkutils_available": mssparkutils is not None,
        "paths": {k: str(v) for k, v in paths.items()},
    }
