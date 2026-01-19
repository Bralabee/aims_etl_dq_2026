"""AIMS Data Ingestion Module.

This module provides an AIMS-specific wrapper around dq_framework's DataIngester,
adding watermark management and project-specific functionality.

Architecture Pattern:
    - dq_framework.DataIngester = Generic reusable base (source of truth)
    - aims_data_platform.DataIngester = AIMS-specific wrapper (adds watermark, repair, etc.)
"""
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import pandas as pd
import logging
import shutil

# Re-export base class from dq_framework (DO NOT duplicate logic)
from dq_framework import DataIngester as BaseDataIngester

from .config import config

logger = logging.getLogger(__name__)


class DataIngester(BaseDataIngester):
    """AIMS-specific data ingester with watermark management.
    
    Extends dq_framework.DataIngester with:
        - Watermark-based incremental ingestion
        - File repair capabilities
        - Source validation
        - AIMS configuration integration
    
    Attributes:
        watermark_manager: Optional watermark manager for incremental loads
        engine: Parquet engine ('fastparquet' or 'pyarrow')
    """
    
    def __init__(
        self,
        watermark_manager=None,
        engine: str = "fastparquet"
    ):
        """Initialize AIMS DataIngester.
        
        Args:
            watermark_manager: WatermarkManager instance for tracking incremental loads.
                             If None, runs without watermark tracking.
            engine: Parquet engine to use. Options: 'fastparquet', 'pyarrow'.
        """
        super().__init__(engine=engine)
        self.watermark_manager = watermark_manager
        logger.info(
            f"Initialized AIMS DataIngester (engine={engine}, "
            f"watermark={'enabled' if watermark_manager else 'disabled'})"
        )
    
    def repair_directory(
        self,
        source_dir: Path,
        output_dir: Path,
        file_pattern: str = "*.parquet"
    ) -> Dict[str, Any]:
        """Repair corrupted parquet files in a directory.
        
        Reads each parquet file and re-writes it with a clean schema.
        Useful for fixing files with schema drift or corruption.
        
        Args:
            source_dir: Directory containing source parquet files
            output_dir: Directory to write repaired files
            file_pattern: Glob pattern for files to process
            
        Returns:
            Dictionary with repair statistics:
                - total_files: Number of files found
                - successful: Number successfully repaired
                - failed: Number that failed repair
                - errors: List of error details
        """
        source_dir = Path(source_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        files = list(source_dir.glob(file_pattern))
        results = {
            "total_files": len(files),
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        for file_path in files:
            try:
                # Read and re-write to repair schema issues
                df = pd.read_parquet(file_path, engine=self.engine)
                target_path = output_dir / file_path.name
                df.to_parquet(target_path, engine=self.engine, index=False)
                results["successful"] += 1
                logger.info(f"Repaired: {file_path.name}")
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "file": file_path.name,
                    "error": str(e)
                })
                logger.error(f"Failed to repair {file_path.name}: {e}")
        
        return results
    
    def validate_source_files(
        self,
        source_dir: Path,
        file_pattern: str = "*.parquet"
    ) -> Dict[str, Any]:
        """Validate parquet files in a directory.
        
        Checks each file for:
            - Readability (not corrupted)
            - Row count
            - File size
        
        Args:
            source_dir: Directory containing parquet files
            file_pattern: Glob pattern for files to validate
            
        Returns:
            Dictionary with validation results:
                - valid: Count of valid files
                - corrupted: Count of corrupted files
                - file_info: List of file details
        """
        source_dir = Path(source_dir)
        files = list(source_dir.glob(file_pattern))
        
        results = {
            "valid": 0,
            "corrupted": 0,
            "file_info": []
        }
        
        for file_path in files:
            file_info = {
                "file": file_path.name,
                "size_mb": file_path.stat().st_size / (1024 * 1024)
            }
            
            try:
                df = pd.read_parquet(file_path, engine=self.engine)
                file_info["status"] = "valid"
                file_info["rows"] = len(df)
                file_info["columns"] = list(df.columns)
                results["valid"] += 1
            except Exception as e:
                file_info["status"] = "corrupted"
                file_info["error"] = str(e)
                results["corrupted"] += 1
                logger.warning(f"Corrupted file: {file_path.name} - {e}")
            
            results["file_info"].append(file_info)
        
        return results
    
    def ingest_incremental(
        self,
        source_name: str,
        source_files: List[Path],
        target_path: Path,
        watermark_column: str,
        is_fabric: bool = False
    ) -> Dict[str, Any]:
        """Perform incremental ingestion based on watermark.
        
        Only ingests data newer than the last recorded watermark.
        Updates the watermark after successful ingestion.
        
        Args:
            source_name: Logical name of the data source (for watermark tracking)
            source_files: List of source file paths
            target_path: Target directory for ingested files
            watermark_column: Column to use for watermark comparison
            is_fabric: Whether running in MS Fabric environment
            
        Returns:
            Dictionary with ingestion results:
                - status: 'success', 'skipped', or 'partial'
                - rows_ingested: Total rows ingested
                - files_processed: Number of files processed
                - new_watermark: Updated watermark value
                - target_file: Path to output file
        """
        target_path = Path(target_path)
        target_path.mkdir(parents=True, exist_ok=True)
        
        # Get current watermark
        current_watermark = None
        if self.watermark_manager:
            current_watermark = self.watermark_manager.get_watermark(source_name)
            logger.info(f"Current watermark for {source_name}: {current_watermark}")
        
        # Read and filter data
        all_dfs = []
        for file_path in source_files:
            try:
                df = pd.read_parquet(file_path, engine=self.engine)
                
                # Apply watermark filter if applicable
                if current_watermark and watermark_column in df.columns:
                    df = df[df[watermark_column] > current_watermark]
                
                if len(df) > 0:
                    all_dfs.append(df)
                    logger.info(f"Read {len(df)} rows from {file_path.name}")
                    
            except Exception as e:
                logger.error(f"Failed to read {file_path}: {e}")
        
        if not all_dfs:
            return {
                "status": "skipped",
                "reason": "No new data found after watermark filter",
                "rows_ingested": 0,
                "files_processed": 0
            }
        
        # Combine and write
        combined_df = pd.concat(all_dfs, ignore_index=True)
        
        # Determine new watermark
        new_watermark = None
        if watermark_column in combined_df.columns:
            new_watermark = combined_df[watermark_column].max()
        
        # Write to target
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_file = target_path / f"{source_name}_{timestamp}.parquet"
        
        # Use base class method for hybrid write (local vs Fabric)
        if is_fabric:
            combined_df.to_parquet(target_file, index=False, engine=self.engine)
        else:
            combined_df.to_parquet(target_file, index=False, engine=self.engine)
        
        # Update watermark
        if self.watermark_manager and new_watermark is not None:
            self.watermark_manager.update_watermark(
                source_name=source_name,
                watermark_value=new_watermark,
                rows_processed=len(combined_df),
                file_path=str(target_file)
            )
        
        return {
            "status": "success",
            "rows_ingested": len(combined_df),
            "files_processed": len(all_dfs),
            "new_watermark": new_watermark,
            "target_file": str(target_file)
        }


# Re-export for backwards compatibility
__all__ = ["DataIngester", "BaseDataIngester"]
