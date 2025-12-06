"""Data ingestion module for AIMS parquet files."""
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
import logging

from .config import config
from .watermark_manager import WatermarkManager

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataIngester:
    """Handles incremental data ingestion from parquet files."""
    
    def __init__(
        self,
        watermark_manager: WatermarkManager,
        engine: str = "fastparquet"
    ):
        """
        Initialize data ingester.
        
        Args:
            watermark_manager: WatermarkManager instance
            engine: Parquet engine to use ('fastparquet' or 'pyarrow')
        """
        self.watermark_manager = watermark_manager
        self.engine = engine
        logger.info(f"Initialized DataIngester with engine: {engine}")
    
    def repair_parquet_file(
        self,
        source_file: Path,
        output_file: Path
    ) -> bool:
        """
        Repair a corrupted parquet file by reading with fastparquet 
        and writing with pyarrow.
        
        Args:
            source_file: Path to source parquet file
            output_file: Path to output repaired file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Repairing parquet file: {source_file.name}")
            
            # Read with fastparquet
            df = pd.read_parquet(source_file, engine='fastparquet')
            
            # Write with pyarrow in modern format
            output_file.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(
                output_file,
                engine='pyarrow',
                compression=config.PARQUET_COMPRESSION,
                index=False
            )
            
            logger.info(
                f"Successfully repaired {source_file.name} -> {output_file.name} "
                f"({len(df):,} rows)"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to repair {source_file.name}: {str(e)}")
            return False
    
    def repair_directory(
        self,
        source_dir: Path,
        output_dir: Path
    ) -> Dict[str, Any]:
        """
        Repair all parquet files in a directory.
        
        Args:
            source_dir: Source directory containing parquet files
            output_dir: Output directory for repaired files
            
        Returns:
            Dictionary with repair statistics
        """
        source_files = list(source_dir.glob("*.parquet"))
        logger.info(f"Found {len(source_files)} parquet files to repair")
        
        results = {
            "total_files": len(source_files),
            "successful": 0,
            "failed": 0,
            "repaired_files": []
        }
        
        for source_file in source_files:
            output_file = output_dir / f"{source_file.stem}_repaired.parquet"
            
            if self.repair_parquet_file(source_file, output_file):
                results["successful"] += 1
                results["repaired_files"].append(str(output_file))
            else:
                results["failed"] += 1
        
        logger.info(
            f"Repair complete: {results['successful']} successful, "
            f"{results['failed']} failed"
        )
        return results
    
    def ingest_incremental(
        self,
        source_name: str,
        source_files: List[Path],
        target_path: Path,
        watermark_column: str,
        partition_columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Ingest data incrementally based on watermark.
        
        Args:
            source_name: Name of the data source
            source_files: List of source parquet files
            target_path: Path to target directory
            watermark_column: Column to use for incremental loading
            partition_columns: Optional columns to partition by
            
        Returns:
            Dictionary with ingestion results
        """
        load_id = self.watermark_manager.start_load(source_name)
        
        try:
            logger.info(f"Starting incremental load for: {source_name}")
            
            # Get last watermark
            last_watermark = self.watermark_manager.get_watermark(source_name)
            logger.info(
                f"Last watermark: {last_watermark or 'None (first load)'}"
            )
            
            # Read all source files
            dfs = []
            for file in source_files:
                try:
                    df = pd.read_parquet(file, engine=self.engine)
                    dfs.append(df)
                    logger.info(f"Read {file.name}: {len(df):,} rows")
                except Exception as e:
                    logger.warning(
                        f"Failed to read {file.name} with {self.engine}, "
                        f"trying alternative engine"
                    )
                    alt_engine = (
                        'pyarrow' if self.engine == 'fastparquet' 
                        else 'fastparquet'
                    )
                    try:
                        df = pd.read_parquet(file, engine=alt_engine)
                        dfs.append(df)
                        logger.info(
                            f"Read {file.name} with {alt_engine}: {len(df):,} rows"
                        )
                    except Exception as e2:
                        logger.error(f"Failed to read {file.name}: {str(e2)}")
                        continue
            
            if not dfs:
                raise ValueError("No files could be read")
            
            # Concatenate all dataframes
            df_all = pd.concat(dfs, ignore_index=True)
            logger.info(f"Total source records: {len(df_all):,}")
            
            # Filter based on watermark
            if last_watermark and watermark_column in df_all.columns:
                # Convert to datetime if needed
                if df_all[watermark_column].dtype == 'object':
                    df_all[watermark_column] = pd.to_datetime(
                        df_all[watermark_column],
                        errors='coerce'
                    )
                
                last_watermark_dt = pd.to_datetime(last_watermark)
                df_new = df_all[df_all[watermark_column] > last_watermark_dt]
            else:
                df_new = df_all
            
            logger.info(f"New records to process: {len(df_new):,}")
            
            if len(df_new) == 0:
                self.watermark_manager.complete_load(load_id, 0)
                return {
                    "status": "no_new_data",
                    "records_processed": 0,
                    "source_name": source_name
                }
            
            # Get new watermark
            if watermark_column in df_new.columns:
                new_watermark = df_new[watermark_column].max()
            else:
                new_watermark = datetime.now().isoformat()
            
            # Save to target
            target_file = (
                target_path / 
                f"{source_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
            )
            target_path.mkdir(parents=True, exist_ok=True)
            
            df_new.to_parquet(
                target_file,
                engine='pyarrow',
                compression=config.PARQUET_COMPRESSION,
                index=False
            )
            logger.info(f"Saved to: {target_file.name}")
            
            # Update watermark
            self.watermark_manager.update_watermark(
                source_name,
                str(new_watermark),
                len(df_new)
            )
            
            # Complete load
            self.watermark_manager.complete_load(load_id, len(df_new))
            
            return {
                "status": "success",
                "records_processed": len(df_new),
                "old_watermark": last_watermark,
                "new_watermark": str(new_watermark),
                "target_file": str(target_file),
                "source_name": source_name
            }
            
        except Exception as e:
            logger.error(f"Ingestion failed: {str(e)}", exc_info=True)
            self.watermark_manager.complete_load(
                load_id,
                0,
                success=False,
                error_message=str(e)
            )
            raise
    
    def validate_source_files(self, source_dir: Path) -> Dict[str, Any]:
        """
        Validate source parquet files.
        
        Args:
            source_dir: Directory containing source files
            
        Returns:
            Dictionary with validation results
        """
        files = list(source_dir.glob("*.parquet"))
        logger.info(f"Validating {len(files)} parquet files")
        
        results = {
            "total_files": len(files),
            "valid": 0,
            "corrupted": 0,
            "file_info": []
        }
        
        for file in files:
            try:
                df = pd.read_parquet(file, engine=self.engine)
                results["valid"] += 1
                results["file_info"].append({
                    "file": file.name,
                    "status": "valid",
                    "rows": len(df),
                    "columns": len(df.columns),
                    "size_mb": file.stat().st_size / (1024 * 1024)
                })
                logger.info(f"✓ {file.name}: {len(df):,} rows")
            except Exception as e:
                results["corrupted"] += 1
                results["file_info"].append({
                    "file": file.name,
                    "status": "corrupted",
                    "error": str(e)[:100],
                    "size_mb": file.stat().st_size / (1024 * 1024)
                })
                logger.warning(f"✗ {file.name}: {str(e)[:100]}")
        
        return results
