"""Configuration module for AIMS data platform."""
from pathlib import Path
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration settings for the data platform."""
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent
    SOURCE_DATA_PATH = Path(os.getenv(
        "SOURCE_DATA_PATH",
        BASE_DIR / "data" / "Samples_LH_Bronze_Aims_26_parquet"
    ))
    TARGET_DATA_PATH = Path(os.getenv(
        "TARGET_DATA_PATH", 
        BASE_DIR / "data"
    ))
    REPAIRED_DATA_PATH = TARGET_DATA_PATH / "repaired"
    WATERMARK_DB_PATH = Path(os.getenv(
        "WATERMARK_DB_PATH",
        BASE_DIR / "watermarks.db"
    ))
    
    # Great Expectations
    GE_ROOT_DIR = Path(os.getenv(
        "GE_ROOT_DIR",
        BASE_DIR / "great_expectations"
    ))
    
    # Parquet Settings
    PARQUET_ENGINE = os.getenv("PARQUET_ENGINE", "fastparquet")
    PARQUET_COMPRESSION = os.getenv("PARQUET_COMPRESSION", "snappy")
    
    # Incremental Load Settings
    DEFAULT_WATERMARK_COLUMN = os.getenv("DEFAULT_WATERMARK_COLUMN", "LASTUPDATED")
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10000"))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = os.getenv("LOG_FORMAT", "json")
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories."""
        cls.TARGET_DATA_PATH.mkdir(parents=True, exist_ok=True)
        cls.REPAIRED_DATA_PATH.mkdir(parents=True, exist_ok=True)
        cls.WATERMARK_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.GE_ROOT_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_config_dict(cls) -> dict:
        """Get configuration as dictionary."""
        return {
            "source_data_path": str(cls.SOURCE_DATA_PATH),
            "target_data_path": str(cls.TARGET_DATA_PATH),
            "repaired_data_path": str(cls.REPAIRED_DATA_PATH),
            "watermark_db_path": str(cls.WATERMARK_DB_PATH),
            "ge_root_dir": str(cls.GE_ROOT_DIR),
            "parquet_engine": cls.PARQUET_ENGINE,
            "default_watermark_column": cls.DEFAULT_WATERMARK_COLUMN,
            "batch_size": cls.BATCH_SIZE,
        }


# Global config instance
config = Config()
