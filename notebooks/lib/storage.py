"""
AIMS Data Platform - Storage Abstraction Layer
================================================

Platform-aware storage operations for medallion architecture supporting both
Parquet (local development) and Delta Lake (Microsoft Fabric) formats.

This module provides a unified interface for reading and writing data across
the Bronze, Silver, and Gold layers of the medallion architecture, with
automatic format detection based on the execution environment.

Key Features:
    - Automatic platform detection (Local vs Fabric)
    - Support for Parquet (always available) and Delta Lake (when installed)
    - Schema evolution and compatibility checking
    - Data validation integration with quarantine support
    - Partition inference and management
    - Comprehensive metadata tracking

Usage:
    from notebooks.lib.storage import StorageManager, get_storage_format
    
    # Create storage manager with auto-detection
    sm = StorageManager()
    
    # Write to Silver layer
    output_path = sm.write_to_silver(df, "customers", partition_cols=["year", "month"])
    
    # Read from Bronze layer with sampling
    bronze_df = sm.read_from_bronze("raw_transactions", sample_size=10000)
    
    # Write validated data with metadata
    result = sm.write_validated_data(df, "orders", validation_result)
    
    # Quarantine failed data
    quarantine_path = sm.quarantine_data(failed_df, "orders", "Schema mismatch")

Environment Variables:
    AIMS_STORAGE_FORMAT: Override automatic format detection ("parquet" or "delta")
    AIMS_DEFAULT_COMPRESSION: Compression codec (default: "snappy")
    AIMS_ENABLE_SCHEMA_EVOLUTION: Allow schema evolution (default: True)

Dependencies:
    Required: pandas, pyarrow
    Optional: deltalake (for Delta Lake support), pyspark (for Spark integration)
"""

from __future__ import annotations

import hashlib
import json
import os
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

import pandas as pd

# =============================================================================
# OPTIONAL IMPORTS - Graceful fallback when not available
# =============================================================================

# PyArrow - Required for Parquet support
try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    PYARROW_AVAILABLE = True
except ImportError:
    PYARROW_AVAILABLE = False
    pa = None
    pq = None

# Delta Lake - Optional for Delta format support
try:
    from deltalake import DeltaTable, write_deltalake
    DELTA_AVAILABLE = True
except ImportError:
    DELTA_AVAILABLE = False
    DeltaTable = None
    write_deltalake = None

# PySpark - Optional for Spark DataFrame support
try:
    from pyspark.sql import DataFrame as SparkDataFrame
    from pyspark.sql import SparkSession
    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False
    SparkDataFrame = None
    SparkSession = None

# Import platform utilities from existing module
try:
    from notebooks.lib.platform_utils import (
        IS_FABRIC,
        ensure_directory,
        get_base_dir,
        get_data_paths,
    )
except ImportError:
    # Fallback for standalone usage
    IS_FABRIC = Path("/lakehouse/default/Files").exists()
    
    def get_base_dir() -> Path:
        """Fallback base directory detection."""
        if IS_FABRIC:
            return Path("/lakehouse/default/Files")
        current = Path(__file__).resolve()
        for parent in [current] + list(current.parents):
            if (parent / "notebooks").exists():
                return parent
        return Path.cwd()
    
    def get_data_paths() -> Dict[str, Path]:
        """Fallback data paths."""
        base = get_base_dir()
        data_dir = base if IS_FABRIC else base / "data"
        return {
            "BASE_DIR": base,
            "DATA_DIR": data_dir,
            "BRONZE_DIR": data_dir / "bronze",
            "SILVER_DIR": data_dir / "silver",
            "GOLD_DIR": data_dir / "gold",
            "CONFIG_DIR": base / "config" if not IS_FABRIC else data_dir / "config",
            "STATE_DIR": data_dir / "state",
            "QUARANTINE_DIR": data_dir / "quarantine",
        }
    
    def ensure_directory(path: Union[str, Path]) -> Path:
        """Fallback directory creation."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path


# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

StorageFormat = Literal["parquet", "delta", "auto"]
MedallionLayer = Literal["bronze", "silver", "gold", "quarantine"]
DataFrameType = Union[pd.DataFrame, "SparkDataFrame"]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_storage_format() -> str:
    """
    Get the appropriate storage format based on the execution environment.
    
    Returns "delta" when running in Microsoft Fabric (if Delta Lake is installed),
    otherwise returns "parquet" for local development.
    
    Environment variable AIMS_STORAGE_FORMAT can override auto-detection.
    
    Returns:
        str: Either "delta" or "parquet"
    
    Example:
        >>> fmt = get_storage_format()
        >>> print(f"Using storage format: {fmt}")
        Using storage format: parquet
    """
    # Check for environment variable override
    env_format = os.environ.get("AIMS_STORAGE_FORMAT", "").lower()
    if env_format in ("parquet", "delta"):
        if env_format == "delta" and not DELTA_AVAILABLE:
            warnings.warn(
                "Delta Lake requested but deltalake package not installed. "
                "Falling back to parquet.",
                UserWarning
            )
            return "parquet"
        return env_format
    
    # Auto-detect based on platform
    if IS_FABRIC and DELTA_AVAILABLE:
        return "delta"
    return "parquet"


def infer_partition_columns(
    df: pd.DataFrame,
    max_partitions: int = 3,
    cardinality_threshold: int = 100
) -> List[str]:
    """
    Suggest partition columns based on DataFrame content analysis.
    
    Analyzes column types and cardinality to identify good partition candidates.
    Prioritizes date-based columns, then categorical columns with moderate cardinality.
    
    Args:
        df: DataFrame to analyze for partition candidates
        max_partitions: Maximum number of partition columns to suggest (default: 3)
        cardinality_threshold: Maximum unique values for a good partition column
    
    Returns:
        List[str]: Suggested partition column names, ordered by priority
    
    Example:
        >>> df = pd.DataFrame({
        ...     'date': pd.date_range('2024-01-01', periods=100),
        ...     'category': ['A', 'B', 'C'] * 33 + ['A'],
        ...     'value': range(100)
        ... })
        >>> infer_partition_columns(df)
        ['date', 'category']
    """
    if df.empty:
        return []
    
    candidates: List[Tuple[str, int, str]] = []  # (col_name, priority, reason)
    
    for col in df.columns:
        dtype = df[col].dtype
        col_lower = col.lower()
        n_unique = df[col].nunique()
        
        # Skip columns with too many unique values or only one value
        if n_unique > cardinality_threshold or n_unique <= 1:
            continue
        
        # Priority 1: Date-related columns (extract year/month for partitioning)
        if pd.api.types.is_datetime64_any_dtype(dtype):
            candidates.append((col, 1, "datetime"))
            continue
        
        # Priority 2: Columns with date-like names
        date_keywords = ["date", "year", "month", "day", "period", "quarter"]
        if any(kw in col_lower for kw in date_keywords):
            candidates.append((col, 2, "date_named"))
            continue
        
        # Priority 3: Categorical columns with low cardinality
        category_keywords = ["category", "type", "status", "region", "country", "state"]
        if any(kw in col_lower for kw in category_keywords):
            candidates.append((col, 3, "category_named"))
            continue
        
        # Priority 4: Object/string columns with moderate cardinality
        if dtype == "object" or pd.api.types.is_categorical_dtype(dtype):
            if 2 <= n_unique <= cardinality_threshold // 2:
                candidates.append((col, 4, "categorical"))
    
    # Sort by priority and return top candidates
    candidates.sort(key=lambda x: x[1])
    return [c[0] for c in candidates[:max_partitions]]


def validate_schema_compatibility(
    source_df: pd.DataFrame,
    target_schema: Union[Dict[str, str], pd.DataFrame, "pa.Schema"],
    strict: bool = False
) -> Dict[str, Any]:
    """
    Check schema compatibility between source DataFrame and target schema.
    
    Performs schema evolution checks to determine if source data can be safely
    written to an existing target with schema evolution support.
    
    Args:
        source_df: Source DataFrame to validate
        target_schema: Target schema as dict {col: dtype}, DataFrame, or PyArrow Schema
        strict: If True, require exact match; if False, allow compatible evolution
    
    Returns:
        Dict containing:
            - compatible: bool - Whether schemas are compatible
            - new_columns: List[str] - Columns in source but not in target
            - missing_columns: List[str] - Columns in target but not in source
            - type_changes: Dict[str, tuple] - Columns with type differences
            - message: str - Human-readable compatibility summary
    
    Example:
        >>> source = pd.DataFrame({'a': [1, 2], 'b': ['x', 'y'], 'c': [1.0, 2.0]})
        >>> target = pd.DataFrame({'a': [1], 'b': ['z']})
        >>> result = validate_schema_compatibility(source, target)
        >>> print(result['compatible'])
        True
        >>> print(result['new_columns'])
        ['c']
    """
    # Extract source schema
    source_schema = {col: str(source_df[col].dtype) for col in source_df.columns}
    
    # Extract target schema based on input type
    if isinstance(target_schema, pd.DataFrame):
        target_schema_dict = {col: str(target_schema[col].dtype) for col in target_schema.columns}
    elif PYARROW_AVAILABLE and isinstance(target_schema, pa.Schema):
        target_schema_dict = {
            field.name: str(field.type) for field in target_schema
        }
    elif isinstance(target_schema, dict):
        target_schema_dict = {k: str(v) for k, v in target_schema.items()}
    else:
        raise ValueError(f"Unsupported target_schema type: {type(target_schema)}")
    
    # Find differences
    source_cols = set(source_schema.keys())
    target_cols = set(target_schema_dict.keys())
    
    new_columns = list(source_cols - target_cols)
    missing_columns = list(target_cols - source_cols)
    common_columns = source_cols & target_cols
    
    # Check type compatibility for common columns
    type_changes = {}
    for col in common_columns:
        source_type = source_schema[col]
        target_type = target_schema_dict[col]
        if source_type != target_type:
            # Check for compatible type promotions
            if not _is_compatible_type_promotion(source_type, target_type):
                type_changes[col] = (source_type, target_type)
    
    # Determine compatibility
    if strict:
        compatible = not (new_columns or missing_columns or type_changes)
    else:
        # Allow new columns and compatible type promotions
        compatible = not type_changes
    
    # Build message
    messages = []
    if new_columns:
        messages.append(f"New columns will be added: {new_columns}")
    if missing_columns:
        messages.append(f"Columns missing from source: {missing_columns}")
    if type_changes:
        messages.append(f"Incompatible type changes: {type_changes}")
    
    message = "; ".join(messages) if messages else "Schemas are compatible"
    
    return {
        "compatible": compatible,
        "new_columns": new_columns,
        "missing_columns": missing_columns,
        "type_changes": type_changes,
        "message": message,
    }


def _is_compatible_type_promotion(source_type: str, target_type: str) -> bool:
    """
    Check if source type can be safely promoted to target type.
    
    Allows widening conversions like int32 -> int64 or float32 -> float64.
    """
    # Define compatible promotions
    promotions = {
        ("int32", "int64"): True,
        ("int16", "int32"): True,
        ("int16", "int64"): True,
        ("float32", "float64"): True,
        ("int32", "float64"): True,
        ("int64", "float64"): True,
    }
    return promotions.get((source_type, target_type), False)


def _get_current_timestamp() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def _compute_data_hash(df: pd.DataFrame) -> str:
    """Compute a hash of DataFrame content for deduplication/tracking."""
    # Use a sample for large DataFrames to keep it fast
    if len(df) > 10000:
        sample = df.sample(n=10000, random_state=42)
    else:
        sample = df
    
    content = pd.util.hash_pandas_object(sample).values.tobytes()
    return hashlib.md5(content).hexdigest()[:12]


# =============================================================================
# STORAGE MANAGER CLASS
# =============================================================================

@dataclass
class StorageManager:
    """
    Platform-aware storage operations for medallion architecture.
    
    Provides a unified interface for reading and writing data across the
    Bronze, Silver, and Gold layers, automatically adapting to the execution
    environment (local vs Microsoft Fabric).
    
    Attributes:
        base_dir: Base directory for data operations
        storage_format: Active storage format ("parquet" or "delta")
        compression: Compression codec for writes
        enable_schema_evolution: Allow schema changes during writes
        paths: Dictionary of medallion layer paths
    
    Example:
        >>> sm = StorageManager()
        >>> print(f"Format: {sm.storage_format}, Base: {sm.base_dir}")
        Format: parquet, Base: /home/user/project/data
        
        >>> # Write to Silver with partitioning
        >>> path = sm.write_to_silver(df, "customers", partition_cols=["year"])
        
        >>> # Read from Bronze with sampling
        >>> sample_df = sm.read_from_bronze("transactions", sample_size=1000)
    """
    
    base_dir: Optional[Path] = field(default=None)
    storage_format: str = field(default="auto")
    compression: str = field(default="snappy")
    enable_schema_evolution: bool = field(default=True)
    
    # Internal state
    paths: Dict[str, Path] = field(default_factory=dict, repr=False)
    _metadata_cache: Dict[str, Dict] = field(default_factory=dict, repr=False)
    
    def __post_init__(self):
        """Initialize storage manager with resolved paths and format."""
        # Resolve storage format
        if self.storage_format == "auto":
            self.storage_format = get_storage_format()
        elif self.storage_format == "delta" and not DELTA_AVAILABLE:
            warnings.warn(
                "Delta Lake not available, falling back to parquet format",
                UserWarning
            )
            self.storage_format = "parquet"
        
        # Get environment overrides
        self.compression = os.environ.get("AIMS_DEFAULT_COMPRESSION", self.compression)
        self.enable_schema_evolution = os.environ.get(
            "AIMS_ENABLE_SCHEMA_EVOLUTION", "true"
        ).lower() == "true"
        
        # Initialize paths
        self.paths = get_data_paths()
        if self.base_dir is None:
            self.base_dir = self.paths.get("DATA_DIR", get_base_dir())
        else:
            self.base_dir = Path(self.base_dir)
        
        # Add quarantine path if not present
        if "QUARANTINE_DIR" not in self.paths:
            self.paths["QUARANTINE_DIR"] = self.base_dir / "quarantine"
    
    # =========================================================================
    # CORE READ/WRITE OPERATIONS
    # =========================================================================
    
    def write_to_silver(
        self,
        df: DataFrameType,
        table_name: str,
        partition_cols: Optional[List[str]] = None,
        mode: Literal["append", "overwrite", "error"] = "overwrite"
    ) -> Path:
        """
        Write DataFrame to Silver layer with appropriate format.
        
        Automatically converts PySpark DataFrames to Pandas if needed,
        and writes using the configured storage format (Parquet or Delta).
        
        Args:
            df: DataFrame to write (Pandas or PySpark)
            table_name: Name of the table/dataset
            partition_cols: Columns to partition by (optional)
            mode: Write mode - "append", "overwrite", or "error"
        
        Returns:
            Path: Location where data was written
        
        Raises:
            ValueError: If DataFrame is empty or table_name is invalid
            IOError: If write operation fails
        
        Example:
            >>> sm = StorageManager()
            >>> df = pd.DataFrame({'id': [1, 2], 'value': ['a', 'b']})
            >>> path = sm.write_to_silver(df, "customers")
            >>> print(f"Written to: {path}")
        """
        return self._write_to_layer(
            df=df,
            layer="silver",
            table_name=table_name,
            partition_cols=partition_cols,
            mode=mode
        )
    
    def write_to_gold(
        self,
        df: DataFrameType,
        table_name: str,
        partition_cols: Optional[List[str]] = None,
        mode: Literal["append", "overwrite", "error"] = "overwrite"
    ) -> Path:
        """
        Write DataFrame to Gold layer with appropriate format.
        
        Similar to write_to_silver but targets the Gold (business-ready) layer.
        
        Args:
            df: DataFrame to write (Pandas or PySpark)
            table_name: Name of the table/dataset
            partition_cols: Columns to partition by (optional)
            mode: Write mode - "append", "overwrite", or "error"
        
        Returns:
            Path: Location where data was written
        """
        return self._write_to_layer(
            df=df,
            layer="gold",
            table_name=table_name,
            partition_cols=partition_cols,
            mode=mode
        )
    
    def clear_layer(
        self,
        layer: MedallionLayer,
        table_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Clear all data from a medallion layer or a specific table.
        
        Use this before pipeline runs to ensure complete overwrite behavior.
        Raw data is preserved in the archived landing zone with date stamps.
        
        Works on both local filesystem and Microsoft Fabric (mssparkutils).
        
        Args:
            layer: The layer to clear ("bronze", "silver", or "gold")
            table_name: Optional specific table to clear. If None, clears all tables.
        
        Returns:
            Dict with cleared file count and paths
        
        Example:
            >>> sm = StorageManager()
            >>> sm.clear_layer("silver")  # Clear entire Silver layer
            >>> sm.clear_layer("gold", "customers")  # Clear specific table
        """
        layer_path = self._get_layer_path(layer)
        cleared = {"layer": layer, "files_cleared": 0, "tables_cleared": [], "errors": []}
        
        if not layer_path.exists():
            return cleared
        
        def remove_path(path: Path) -> bool:
            """Platform-aware path removal."""
            path_str = str(path)
            try:
                if IS_FABRIC and (path_str.startswith("/lakehouse") or path_str.startswith("abfss://")):
                    # Use mssparkutils for Fabric paths
                    try:
                        from notebookutils import mssparkutils
                    except ImportError:
                        import mssparkutils
                    mssparkutils.fs.rm(path_str, recurse=True)
                else:
                    # Local filesystem
                    import shutil
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
                return True
            except Exception as e:
                cleared["errors"].append(f"{path.name}: {e}")
                return False
        
        if table_name:
            # Clear specific table
            table_path = layer_path / table_name
            if table_path.exists():
                if remove_path(table_path):
                    cleared["tables_cleared"].append(table_name)
                    cleared["files_cleared"] += 1
        else:
            # Clear all tables/files in layer
            for item in layer_path.iterdir():
                if remove_path(item):
                    cleared["tables_cleared"].append(item.name)
                    cleared["files_cleared"] += 1
        
        return cleared
    
    def read_from_bronze(
        self,
        table_name: str,
        sample_size: Optional[int] = None,
        columns: Optional[List[str]] = None,
        filters: Optional[List[Tuple]] = None
    ) -> pd.DataFrame:
        """
        Read from Bronze layer with optional sampling.
        
        Reads raw data from the Bronze layer, with options for sampling
        large datasets and filtering columns/rows.
        
        Args:
            table_name: Name of the table/dataset to read
            sample_size: Number of rows to sample (None for all rows)
            columns: Specific columns to read (None for all columns)
            filters: PyArrow-style filters for predicate pushdown
        
        Returns:
            pd.DataFrame: Data from Bronze layer
        
        Raises:
            FileNotFoundError: If table doesn't exist
        
        Example:
            >>> sm = StorageManager()
            >>> # Read full dataset
            >>> df = sm.read_from_bronze("raw_transactions")
            >>> # Read sample with specific columns
            >>> sample = sm.read_from_bronze("raw_transactions", 
            ...     sample_size=1000, columns=["id", "amount"])
        """
        return self._read_from_layer(
            layer="bronze",
            table_name=table_name,
            sample_size=sample_size,
            columns=columns,
            filters=filters
        )
    
    def read_from_silver(
        self,
        table_name: str,
        sample_size: Optional[int] = None,
        columns: Optional[List[str]] = None,
        filters: Optional[List[Tuple]] = None
    ) -> pd.DataFrame:
        """
        Read from Silver layer with optional sampling.
        
        Args:
            table_name: Name of the table/dataset to read
            sample_size: Number of rows to sample (None for all rows)
            columns: Specific columns to read (None for all columns)
            filters: PyArrow-style filters for predicate pushdown
        
        Returns:
            pd.DataFrame: Data from Silver layer
        """
        return self._read_from_layer(
            layer="silver",
            table_name=table_name,
            sample_size=sample_size,
            columns=columns,
            filters=filters
        )
    
    def read_from_gold(
        self,
        table_name: str,
        sample_size: Optional[int] = None,
        columns: Optional[List[str]] = None,
        filters: Optional[List[Tuple]] = None
    ) -> pd.DataFrame:
        """
        Read from Gold layer with optional sampling.
        
        Args:
            table_name: Name of the table/dataset to read
            sample_size: Number of rows to sample (None for all rows)
            columns: Specific columns to read (None for all columns)
            filters: PyArrow-style filters for predicate pushdown
        
        Returns:
            pd.DataFrame: Data from Gold layer
        """
        return self._read_from_layer(
            layer="gold",
            table_name=table_name,
            sample_size=sample_size,
            columns=columns,
            filters=filters
        )
    
    # =========================================================================
    # VALIDATION AND QUARANTINE
    # =========================================================================
    
    def write_validated_data(
        self,
        df: DataFrameType,
        table_name: str,
        validation_result: Dict[str, Any],
        target_layer: MedallionLayer = "silver"
    ) -> Dict[str, Any]:
        """
        Write data that passed validation, return comprehensive metadata.
        
        Writes validated data to the specified layer and records validation
        metadata alongside the data. Only writes if validation passed.
        
        Args:
            df: DataFrame that passed validation
            table_name: Name of the target table
            validation_result: Dictionary containing validation results
                Expected keys: 'passed' (bool), 'score' (float), 'checks' (list)
            target_layer: Target medallion layer (default: "silver")
        
        Returns:
            Dict containing:
                - success: bool - Whether write succeeded
                - path: Path - Location of written data
                - row_count: int - Number of rows written
                - validation_score: float - DQ score
                - timestamp: str - Write timestamp
                - data_hash: str - Content hash for tracking
        
        Raises:
            ValueError: If validation_result indicates failure
        
        Example:
            >>> validation = {'passed': True, 'score': 0.98, 'checks': [...]}
            >>> result = sm.write_validated_data(df, "orders", validation)
            >>> print(f"Written {result['row_count']} rows with score {result['validation_score']}")
        """
        # Check validation status
        passed = validation_result.get("passed", False)
        score = validation_result.get("score", 0.0)
        
        if not passed:
            raise ValueError(
                f"Cannot write data that failed validation. Score: {score:.2%}. "
                "Use quarantine_data() for failed data."
            )
        
        # Convert if needed
        pdf = self._ensure_pandas(df)
        
        # Write to target layer
        output_path = self._write_to_layer(
            df=pdf,
            layer=target_layer,
            table_name=table_name,
            mode="overwrite"
        )
        
        # Prepare metadata
        metadata = {
            "success": True,
            "path": output_path,
            "row_count": len(pdf),
            "column_count": len(pdf.columns),
            "columns": list(pdf.columns),
            "validation_score": score,
            "validation_checks": validation_result.get("checks", []),
            "timestamp": _get_current_timestamp(),
            "data_hash": _compute_data_hash(pdf),
            "storage_format": self.storage_format,
            "layer": target_layer,
        }
        
        # Write metadata file
        self._write_metadata(output_path, metadata)
        
        return metadata
    
    def quarantine_data(
        self,
        df: DataFrameType,
        table_name: str,
        reason: str,
        validation_result: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Move failed data to quarantine zone for investigation.
        
        Writes data that failed validation to a quarantine directory,
        along with metadata describing the failure reason.
        
        Args:
            df: DataFrame that failed validation
            table_name: Original target table name
            reason: Human-readable reason for quarantine
            validation_result: Optional validation details
        
        Returns:
            Path: Location of quarantined data
        
        Example:
            >>> failed_rows = df[~df['valid']]
            >>> path = sm.quarantine_data(
            ...     failed_rows, 
            ...     "orders", 
            ...     "Schema validation failed: missing required fields"
            ... )
            >>> print(f"Quarantined to: {path}")
        """
        pdf = self._ensure_pandas(df)
        
        # Create quarantine path with timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        quarantine_name = f"{table_name}_{timestamp}"
        
        # Write to quarantine
        output_path = self._write_to_layer(
            df=pdf,
            layer="quarantine",
            table_name=quarantine_name,
            mode="overwrite"
        )
        
        # Write quarantine metadata
        metadata = {
            "original_table": table_name,
            "quarantine_reason": reason,
            "row_count": len(pdf),
            "columns": list(pdf.columns),
            "timestamp": _get_current_timestamp(),
            "validation_result": validation_result,
            "data_hash": _compute_data_hash(pdf),
        }
        
        metadata_path = output_path.parent / f"{quarantine_name}_metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2, default=str)
        
        return output_path
    
    # =========================================================================
    # METADATA OPERATIONS
    # =========================================================================
    
    def get_table_metadata(
        self,
        layer: MedallionLayer,
        table_name: str
    ) -> Dict[str, Any]:
        """
        Get metadata about a table (row count, schema, last modified).
        
        Retrieves comprehensive metadata about an existing table, including
        schema information, row count, file sizes, and modification times.
        
        Args:
            layer: Medallion layer ("bronze", "silver", "gold", "quarantine")
            table_name: Name of the table
        
        Returns:
            Dict containing:
                - exists: bool - Whether table exists
                - path: Path - Table location
                - row_count: int - Number of rows (may require scan)
                - schema: Dict - Column names and types
                - size_bytes: int - Total storage size
                - last_modified: str - Last modification timestamp
                - storage_format: str - "parquet" or "delta"
                - partitions: List[str] - Partition columns (if any)
        
        Raises:
            FileNotFoundError: If table doesn't exist and check_exists=True
        
        Example:
            >>> meta = sm.get_table_metadata("silver", "customers")
            >>> print(f"Rows: {meta['row_count']}, Size: {meta['size_bytes']} bytes")
        """
        table_path = self._get_table_path(layer, table_name)
        
        if not table_path.exists():
            return {
                "exists": False,
                "path": table_path,
                "message": f"Table {table_name} not found in {layer} layer"
            }
        
        metadata = {
            "exists": True,
            "path": table_path,
            "storage_format": self.storage_format,
            "layer": layer,
            "table_name": table_name,
        }
        
        try:
            if self.storage_format == "delta" and DELTA_AVAILABLE:
                metadata.update(self._get_delta_metadata(table_path))
            else:
                metadata.update(self._get_parquet_metadata(table_path))
        except Exception as e:
            metadata["error"] = str(e)
            metadata["row_count"] = None
            metadata["schema"] = None
        
        return metadata
    
    def list_tables(self, layer: MedallionLayer) -> List[str]:
        """
        List all tables in a medallion layer.
        
        Args:
            layer: Medallion layer to scan
        
        Returns:
            List[str]: Table names in the layer
        """
        layer_path = self._get_layer_path(layer)
        
        if not layer_path.exists():
            return []
        
        tables = []
        for item in layer_path.iterdir():
            if item.is_dir():
                # Check if it's a valid table
                if self.storage_format == "delta":
                    if (item / "_delta_log").exists():
                        tables.append(item.name)
                else:
                    # Check for parquet files
                    if list(item.glob("*.parquet")) or list(item.glob("**/*.parquet")):
                        tables.append(item.name)
            elif item.suffix == ".parquet":
                tables.append(item.stem)
        
        return sorted(tables)
    
    # =========================================================================
    # INTERNAL METHODS
    # =========================================================================
    
    def _get_layer_path(self, layer: MedallionLayer) -> Path:
        """Get the path for a medallion layer."""
        layer_key = f"{layer.upper()}_DIR"
        if layer_key in self.paths:
            return self.paths[layer_key]
        return self.base_dir / layer
    
    def _get_table_path(self, layer: MedallionLayer, table_name: str) -> Path:
        """Get the full path for a table."""
        layer_path = self._get_layer_path(layer)
        if self.storage_format == "delta":
            return layer_path / table_name
        else:
            # For parquet, could be directory or single file
            dir_path = layer_path / table_name
            file_path = layer_path / f"{table_name}.parquet"
            if dir_path.exists():
                return dir_path
            return file_path
    
    def _ensure_pandas(self, df: DataFrameType) -> pd.DataFrame:
        """Convert to Pandas DataFrame if needed."""
        if isinstance(df, pd.DataFrame):
            return df
        
        if PYSPARK_AVAILABLE and isinstance(df, SparkDataFrame):
            return df.toPandas()
        
        raise TypeError(f"Unsupported DataFrame type: {type(df)}")
    
    def _write_to_layer(
        self,
        df: DataFrameType,
        layer: MedallionLayer,
        table_name: str,
        partition_cols: Optional[List[str]] = None,
        mode: str = "overwrite"
    ) -> Path:
        """Internal method to write data to a medallion layer."""
        # Validate input
        if table_name is None or not table_name.strip():
            raise ValueError("table_name cannot be empty")
        
        pdf = self._ensure_pandas(df)
        
        if pdf.empty:
            raise ValueError("Cannot write empty DataFrame")
        
        # Get target path
        layer_path = self._get_layer_path(layer)
        ensure_directory(layer_path)
        
        if self.storage_format == "delta":
            return self._write_delta(pdf, layer_path, table_name, partition_cols, mode)
        else:
            return self._write_parquet(pdf, layer_path, table_name, partition_cols, mode)
    
    def _write_parquet(
        self,
        df: pd.DataFrame,
        layer_path: Path,
        table_name: str,
        partition_cols: Optional[List[str]] = None,
        mode: str = "overwrite"
    ) -> Path:
        """Write DataFrame as Parquet.
        
        Note: In overwrite mode, completely removes existing table data first.
        This ensures no residual data from previous runs (no append/delta behavior).
        Works on both local filesystem and Microsoft Fabric.
        """
        if not PYARROW_AVAILABLE:
            raise ImportError("PyArrow is required for Parquet operations")
        
        table_path = layer_path / table_name
        
        # For overwrite mode: clear existing table directory first
        # This ensures complete overwrite with no residual data
        if mode == "overwrite" and table_path.exists():
            path_str = str(table_path)
            if IS_FABRIC and (path_str.startswith("/lakehouse") or path_str.startswith("abfss://")):
                # Use mssparkutils for Fabric paths
                try:
                    from notebookutils import mssparkutils
                except ImportError:
                    import mssparkutils
                mssparkutils.fs.rm(path_str, recurse=True)
            else:
                import shutil
                shutil.rmtree(table_path)
        
        ensure_directory(table_path)
        
        # Convert to PyArrow table
        table = pa.Table.from_pandas(df, preserve_index=False)
        
        if partition_cols:
            # Partitioned write
            pq.write_to_dataset(
                table,
                root_path=str(table_path),
                partition_cols=partition_cols,
                compression=self.compression,
                existing_data_behavior="delete_matching" if mode == "overwrite" else "overwrite_or_ignore"
            )
        else:
            # Single file write
            file_path = table_path / "data.parquet"
            pq.write_table(
                table,
                str(file_path),
                compression=self.compression
            )
        
        return table_path
    
    def _write_delta(
        self,
        df: pd.DataFrame,
        layer_path: Path,
        table_name: str,
        partition_cols: Optional[List[str]] = None,
        mode: str = "overwrite"
    ) -> Path:
        """Write DataFrame as Delta Lake table."""
        if not DELTA_AVAILABLE:
            raise ImportError("deltalake package is required for Delta operations")
        
        table_path = layer_path / table_name
        
        write_deltalake(
            str(table_path),
            df,
            mode=mode,
            partition_by=partition_cols,
            schema_mode="merge" if self.enable_schema_evolution else "overwrite"
        )
        
        return table_path
    
    def _read_from_layer(
        self,
        layer: MedallionLayer,
        table_name: str,
        sample_size: Optional[int] = None,
        columns: Optional[List[str]] = None,
        filters: Optional[List[Tuple]] = None
    ) -> pd.DataFrame:
        """Internal method to read data from a medallion layer."""
        table_path = self._get_table_path(layer, table_name)
        
        if not table_path.exists():
            raise FileNotFoundError(
                f"Table '{table_name}' not found in {layer} layer at {table_path}"
            )
        
        if self.storage_format == "delta" and DELTA_AVAILABLE:
            df = self._read_delta(table_path, columns, filters)
        else:
            df = self._read_parquet(table_path, columns, filters)
        
        # Apply sampling if requested
        if sample_size is not None and len(df) > sample_size:
            df = df.sample(n=sample_size, random_state=42)
        
        return df
    
    def _read_parquet(
        self,
        table_path: Path,
        columns: Optional[List[str]] = None,
        filters: Optional[List[Tuple]] = None
    ) -> pd.DataFrame:
        """Read Parquet data."""
        if not PYARROW_AVAILABLE:
            raise ImportError("PyArrow is required for Parquet operations")
        
        if table_path.is_file():
            # Single file
            return pq.read_table(
                str(table_path),
                columns=columns,
                filters=filters
            ).to_pandas()
        else:
            # Directory (potentially partitioned)
            return pq.read_table(
                str(table_path),
                columns=columns,
                filters=filters
            ).to_pandas()
    
    def _read_delta(
        self,
        table_path: Path,
        columns: Optional[List[str]] = None,
        filters: Optional[List[Tuple]] = None
    ) -> pd.DataFrame:
        """Read Delta Lake table."""
        if not DELTA_AVAILABLE:
            raise ImportError("deltalake package is required for Delta operations")
        
        dt = DeltaTable(str(table_path))
        
        # Build query
        if columns:
            df = dt.to_pandas(columns=columns)
        else:
            df = dt.to_pandas()
        
        # Apply filters (Delta's filter pushdown is limited in Python API)
        # For complex filters, consider using the filters parameter in read
        if filters:
            for filter_expr in filters:
                col, op, val = filter_expr
                if op == "==" or op == "=":
                    df = df[df[col] == val]
                elif op == "!=":
                    df = df[df[col] != val]
                elif op == ">":
                    df = df[df[col] > val]
                elif op == ">=":
                    df = df[df[col] >= val]
                elif op == "<":
                    df = df[df[col] < val]
                elif op == "<=":
                    df = df[df[col] <= val]
                elif op == "in":
                    df = df[df[col].isin(val)]
        
        return df
    
    def _get_parquet_metadata(self, table_path: Path) -> Dict[str, Any]:
        """Get metadata for Parquet table."""
        if not PYARROW_AVAILABLE:
            return {"error": "PyArrow not available"}
        
        try:
            if table_path.is_file():
                pf = pq.ParquetFile(str(table_path))
                schema = pf.schema_arrow
                row_count = pf.metadata.num_rows
                size_bytes = table_path.stat().st_size
            else:
                # Directory - read metadata from first file
                parquet_files = list(table_path.glob("**/*.parquet"))
                if not parquet_files:
                    return {"error": "No parquet files found"}
                
                dataset = pq.ParquetDataset(str(table_path))
                schema = dataset.schema
                
                # Calculate totals
                row_count = sum(
                    pq.ParquetFile(str(f)).metadata.num_rows 
                    for f in parquet_files
                )
                size_bytes = sum(f.stat().st_size for f in parquet_files)
            
            # Get last modified
            if table_path.is_file():
                last_modified = datetime.fromtimestamp(
                    table_path.stat().st_mtime, tz=timezone.utc
                ).isoformat()
            else:
                mtimes = [f.stat().st_mtime for f in table_path.glob("**/*") if f.is_file()]
                last_modified = datetime.fromtimestamp(
                    max(mtimes) if mtimes else 0, tz=timezone.utc
                ).isoformat()
            
            return {
                "row_count": row_count,
                "schema": {field.name: str(field.type) for field in schema},
                "size_bytes": size_bytes,
                "last_modified": last_modified,
                "partitions": self._detect_partitions(table_path),
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_delta_metadata(self, table_path: Path) -> Dict[str, Any]:
        """Get metadata for Delta Lake table."""
        if not DELTA_AVAILABLE:
            return {"error": "Delta Lake not available"}
        
        try:
            dt = DeltaTable(str(table_path))
            
            # Get schema
            schema = {field.name: str(field.type) for field in dt.schema().fields}
            
            # Get metadata from history
            history = dt.history(limit=1)
            if history:
                last_modified = history[0].get("timestamp", "unknown")
            else:
                last_modified = "unknown"
            
            # Get file statistics
            files = dt.files()
            
            return {
                "row_count": dt.to_pandas().shape[0],  # This loads data - consider optimization
                "schema": schema,
                "size_bytes": sum(
                    (table_path / f).stat().st_size 
                    for f in files 
                    if (table_path / f).exists()
                ),
                "last_modified": last_modified,
                "partitions": dt.metadata().partition_columns,
                "version": dt.version(),
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _detect_partitions(self, table_path: Path) -> List[str]:
        """Detect partition columns from directory structure."""
        partitions = []
        
        if not table_path.is_dir():
            return partitions
        
        # Look for directories with "key=value" pattern
        for item in table_path.iterdir():
            if item.is_dir() and "=" in item.name:
                partition_key = item.name.split("=")[0]
                if partition_key not in partitions:
                    partitions.append(partition_key)
        
        return partitions
    
    def _write_metadata(self, table_path: Path, metadata: Dict[str, Any]) -> None:
        """Write metadata JSON file alongside data."""
        metadata_path = table_path.parent / f"{table_path.name}_metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2, default=str)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_storage_manager(
    storage_format: str = "auto",
    base_dir: Optional[Path] = None
) -> StorageManager:
    """
    Factory function to create a configured StorageManager.
    
    Args:
        storage_format: "parquet", "delta", or "auto"
        base_dir: Override base directory
    
    Returns:
        StorageManager: Configured storage manager instance
    
    Example:
        >>> sm = create_storage_manager()
        >>> print(f"Using {sm.storage_format} format")
    """
    return StorageManager(
        base_dir=base_dir,
        storage_format=storage_format
    )


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Main class
    "StorageManager",
    # Helper functions
    "get_storage_format",
    "infer_partition_columns",
    "validate_schema_compatibility",
    # Factory
    "create_storage_manager",
    # Constants
    "DELTA_AVAILABLE",
    "PYARROW_AVAILABLE",
    "PYSPARK_AVAILABLE",
    "IS_FABRIC",
]


# =============================================================================
# MODULE INFO
# =============================================================================

if __name__ == "__main__":
    # Quick module test
    print("=" * 60)
    print("AIMS Data Platform - Storage Abstraction Layer")
    print("=" * 60)
    print(f"Platform: {'Microsoft Fabric' if IS_FABRIC else 'Local Development'}")
    print(f"Storage Format: {get_storage_format()}")
    print(f"PyArrow Available: {PYARROW_AVAILABLE}")
    print(f"Delta Lake Available: {DELTA_AVAILABLE}")
    print(f"PySpark Available: {PYSPARK_AVAILABLE}")
    print("-" * 60)
    
    sm = StorageManager()
    print(f"Storage Manager initialized:")
    print(f"  Format: {sm.storage_format}")
    print(f"  Base Dir: {sm.base_dir}")
    print(f"  Compression: {sm.compression}")
    print("=" * 60)
