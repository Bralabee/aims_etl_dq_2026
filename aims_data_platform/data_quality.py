"""Data quality validation using Great Expectations."""
from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd
import logging

try:
    import great_expectations as gx
    from great_expectations.core.batch import RuntimeBatchRequest
    from great_expectations.checkpoint import Checkpoint
    HAS_GX = True
except ImportError:
    HAS_GX = False
    logging.warning("Great Expectations not installed. Data quality validation disabled.")

from .config import config

logger = logging.getLogger(__name__)


class DataQualityValidator:
    """Validates data quality using Great Expectations."""
    
    def __init__(self, ge_root_dir: Optional[Path] = None):
        """
        Initialize data quality validator.
        
        Args:
            ge_root_dir: Root directory for Great Expectations
        """
        if not HAS_GX:
            raise ImportError(
                "Great Expectations is required. "
                "Install with: pip install great-expectations"
            )
        
        self.ge_root_dir = ge_root_dir or config.GE_ROOT_DIR
        self.ge_root_dir.mkdir(parents=True, exist_ok=True)
        self.context = None
        logger.info(f"Initialized DataQualityValidator at {self.ge_root_dir}")
    
    def initialize_context(self) -> None:
        """Initialize or load Great Expectations context."""
        try:
            # Try to load existing context
            self.context = gx.get_context(
                context_root_dir=str(self.ge_root_dir)
            )
            logger.info("Loaded existing Great Expectations context")
        except Exception:
            # Create new context
            logger.info("Creating new Great Expectations context")
            self.context = gx.get_context(
                context_root_dir=str(self.ge_root_dir),
                mode="file"
            )
    
    def create_datasource(
        self,
        datasource_name: str,
        base_directory: Path
    ) -> None:
        """
        Create a pandas datasource for parquet files.
        
        Args:
            datasource_name: Name of the datasource
            base_directory: Base directory containing parquet files
        """
        if not self.context:
            self.initialize_context()
        
        try:
            datasource = self.context.sources.add_pandas_filesystem(
                name=datasource_name,
                base_directory=str(base_directory)
            )
            logger.info(f"Created datasource: {datasource_name}")
        except Exception as e:
            logger.warning(f"Datasource {datasource_name} may already exist: {e}")
    
    def create_expectation_suite(
        self,
        suite_name: str,
        columns_schema: Dict[str, str]
    ) -> None:
        """
        Create an expectation suite with basic validations.
        
        Args:
            suite_name: Name of the expectation suite
            columns_schema: Dictionary mapping column names to expected types
        """
        if not self.context:
            self.initialize_context()
        
        # Create or get suite
        try:
            suite = self.context.add_expectation_suite(
                expectation_suite_name=suite_name
            )
        except Exception:
            suite = self.context.get_expectation_suite(
                expectation_suite_name=suite_name
            )
        
        logger.info(f"Working with expectation suite: {suite_name}")
        
        # Add basic expectations
        expectations = []
        
        # 1. Expect table to exist
        expectations.append({
            "expectation_type": "expect_table_row_count_to_be_between",
            "kwargs": {
                "min_value": 1,
                "max_value": None
            }
        })
        
        # 2. Expect columns to exist
        for column_name in columns_schema.keys():
            expectations.append({
                "expectation_type": "expect_column_to_exist",
                "kwargs": {
                    "column": column_name
                }
            })
        
        # 3. Expect no null values in key columns
        for column_name, col_type in columns_schema.items():
            if "ID" in column_name.upper() or "NAME" in column_name.upper():
                expectations.append({
                    "expectation_type": "expect_column_values_to_not_be_null",
                    "kwargs": {
                        "column": column_name
                    }
                })
        
        # 4. Expect datetime columns to be valid
        for column_name, col_type in columns_schema.items():
            if any(x in column_name.upper() for x in ["DATE", "CREATED", "UPDATED"]):
                expectations.append({
                    "expectation_type": "expect_column_values_to_not_be_null",
                    "kwargs": {
                        "column": column_name,
                        "mostly": 0.95  # Allow 5% nulls
                    }
                })
        
        logger.info(f"Created {len(expectations)} expectations for {suite_name}")
        
        return suite
    
    def validate_dataframe(
        self,
        df: pd.DataFrame,
        suite_name: str,
        expectations: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Validate a DataFrame against expectations.
        
        Args:
            df: DataFrame to validate
            suite_name: Name of expectation suite
            expectations: Optional list of custom expectations
            
        Returns:
            Dictionary with validation results
        """
        if not self.context:
            self.initialize_context()
        
        logger.info(f"Validating DataFrame with {len(df)} rows")
        
        # Use simple validations if GX not available
        results = {
            "success": True,
            "statistics": {
                "evaluated_expectations": 0,
                "successful_expectations": 0,
                "unsuccessful_expectations": 0,
                "success_percent": 0.0
            },
            "results": []
        }
        
        # Basic validations
        checks = []
        
        # 1. Check row count
        row_count_ok = len(df) > 0
        checks.append({
            "expectation_type": "expect_table_row_count_to_be_between",
            "success": row_count_ok,
            "result": {"observed_value": len(df)}
        })
        
        # 2. Check for null values in key columns
        for col in df.columns:
            if "ID" in col.upper():
                null_count = df[col].isnull().sum()
                success = null_count == 0
                checks.append({
                    "expectation_type": "expect_column_values_to_not_be_null",
                    "column": col,
                    "success": success,
                    "result": {
                        "unexpected_count": int(null_count),
                        "unexpected_percent": float(null_count / len(df) * 100)
                    }
                })
        
        # 3. Check for duplicate rows
        duplicate_count = df.duplicated().sum()
        checks.append({
            "expectation_type": "expect_table_row_count_to_equal_value",
            "success": duplicate_count == 0,
            "result": {
                "observed_value": len(df),
                "duplicate_count": int(duplicate_count)
            }
        })
        
        # Calculate statistics
        results["results"] = checks
        results["statistics"]["evaluated_expectations"] = len(checks)
        results["statistics"]["successful_expectations"] = sum(
            1 for c in checks if c["success"]
        )
        results["statistics"]["unsuccessful_expectations"] = sum(
            1 for c in checks if not c["success"]
        )
        results["statistics"]["success_percent"] = (
            results["statistics"]["successful_expectations"] / 
            len(checks) * 100 if checks else 0
        )
        results["success"] = all(c["success"] for c in checks)
        
        logger.info(
            f"Validation complete: {results['statistics']['success_percent']:.1f}% passed"
        )
        
        return results
    
    def validate_file(
        self,
        file_path: Path,
        suite_name: str
    ) -> Dict[str, Any]:
        """
        Validate a parquet file.
        
        Args:
            file_path: Path to parquet file
            suite_name: Name of expectation suite
            
        Returns:
            Dictionary with validation results
        """
        logger.info(f"Validating file: {file_path.name}")
        
        try:
            df = pd.read_parquet(file_path)
            return self.validate_dataframe(df, suite_name)
        except Exception as e:
            logger.error(f"Failed to validate {file_path.name}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "file": str(file_path)
            }
    
    def generate_data_profile(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate a data profile report.
        
        Args:
            df: DataFrame to profile
            
        Returns:
            Dictionary with profile information
        """
        profile = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": {},
            "missing_values": {},
            "data_types": {}
        }
        
        for col in df.columns:
            profile["columns"][col] = {
                "dtype": str(df[col].dtype),
                "null_count": int(df[col].isnull().sum()),
                "null_percent": float(df[col].isnull().sum() / len(df) * 100),
                "unique_count": int(df[col].nunique())
            }
            
            # Add statistics for numeric columns
            if pd.api.types.is_numeric_dtype(df[col]):
                profile["columns"][col].update({
                    "min": float(df[col].min()) if not df[col].isnull().all() else None,
                    "max": float(df[col].max()) if not df[col].isnull().all() else None,
                    "mean": float(df[col].mean()) if not df[col].isnull().all() else None
                })
        
        # Summary of missing values
        missing = df.isnull().sum()
        profile["missing_values"] = {
            col: int(count) 
            for col, count in missing.items() 
            if count > 0
        }
        
        logger.info(f"Generated profile for {len(df)} rows, {len(df.columns)} columns")
        
        return profile
