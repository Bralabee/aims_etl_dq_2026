"""Cloud-aware configuration for MS Fabric deployment."""
from pathlib import Path
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class FabricConfig:
    """Configuration for MS Fabric environment with dependency injection."""
    
    def __init__(
        self,
        source_path: Optional[str] = None,
        target_path: Optional[str] = None,
        watermark_db_path: Optional[str] = None,
        environment: str = "local",
        **kwargs
    ):
        """
        Initialize configuration.
        
        Args:
            source_path: Source data path (ABFSS or local)
            target_path: Target output path
            watermark_db_path: Watermark database path
            environment: 'local' or 'fabric'
            **kwargs: Additional configuration options
        """
        self.environment = environment
        
        # Service Principal Credentials
        self.client_id = os.getenv("AZURE_CLIENT_ID")
        self.client_secret = os.getenv("AZURE_CLIENT_SECRET")
        self.tenant_id = os.getenv("AZURE_TENANT_ID")
        self.subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
        
        # Determine paths based on environment
        if environment == "fabric":
            # MS Fabric paths
            self.source_path = source_path or self._get_fabric_source_path()
            self.target_path = target_path or os.getenv("TARGET_DATA_PATH", "/lakehouse/default/Files/processed")
            self.watermark_db_path = watermark_db_path or os.getenv("WATERMARK_DB_PATH", "/lakehouse/default/Files/metadata/watermarks.db")
            self.gx_context_root = kwargs.get("gx_context_root", os.getenv("GE_ROOT_DIR", "/lakehouse/default/Files/gx"))
        else:
            # Local paths
            base_dir = Path(__file__).parent.parent
            self.source_path = source_path or self._get_fabric_source_path() or str(base_dir / "data" / "source")
            self.target_path = target_path or os.getenv("TARGET_DATA_PATH", str(base_dir / "data" / "processed"))
            self.watermark_db_path = watermark_db_path or os.getenv("WATERMARK_DB_PATH", str(base_dir / "watermarks.db"))
            self.gx_context_root = kwargs.get("gx_context_root", os.getenv("GE_ROOT_DIR", str(base_dir / "data" / "gx")))
        
        # Parse additional settings
        self.parquet_engine = kwargs.get("parquet_engine", os.getenv("PARQUET_ENGINE", "pyarrow"))
        self.compression = kwargs.get("compression", os.getenv("PARQUET_COMPRESSION", "snappy"))
        self.watermark_column = kwargs.get("watermark_column", os.getenv("DEFAULT_WATERMARK_COLUMN", "LASTUPDATED"))
        self.batch_size = int(kwargs.get("batch_size", os.getenv("BATCH_SIZE", 10000)))
        self.log_level = kwargs.get("log_level", os.getenv("LOG_LEVEL", "INFO"))
    
    @staticmethod
    def _get_fabric_source_path() -> str:
        """Get default Fabric source path."""
        # Prefer environment variable, fallback to hardcoded for backward compatibility if needed
        return os.getenv(
            "SOURCE_DATA_PATH",
            "abfss://COE_F_EUC_P2@onelake.dfs.fabric.microsoft.com/LH_Bronze_Aims_26.Lakehouse/Files/13-11-2025"
        )
    
    @classmethod
    def for_fabric(cls, source_path: Optional[str] = None, **kwargs) -> "FabricConfig":
        """Create config for Fabric environment."""
        return cls(
            source_path=source_path,
            environment="fabric",
            **kwargs
        )
    
    @classmethod
    def for_local(cls, source_path: Optional[str] = None, **kwargs) -> "FabricConfig":
        """Create config for local environment."""
        return cls(
            source_path=source_path,
            environment="local",
            **kwargs
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Export config as dictionary."""
        return {
            "environment": self.environment,
            "source_path": self.source_path,
            "target_path": self.target_path,
            "watermark_db_path": self.watermark_db_path,
            "parquet_engine": self.parquet_engine,
            "compression": self.compression,
            "watermark_column": self.watermark_column,
            "batch_size": self.batch_size,
            "log_level": self.log_level,
        }
    
    def __repr__(self) -> str:
        return f"FabricConfig(environment={self.environment}, source_path={self.source_path})"
