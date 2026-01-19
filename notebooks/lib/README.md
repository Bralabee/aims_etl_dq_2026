# Notebook Shared Utilities Library

**Version:** 1.4.0  
**Last Updated:** 2026-01-19

This directory contains shared utility modules for all AIMS Data Platform notebooks, providing centralized configuration, platform detection, storage abstraction, and logging.

## 📦 Module Overview

| Module | Purpose | v1.4.0 Updates |
|--------|---------|----------------|
| `platform_utils.py` | Platform detection (local vs Fabric) and base directory resolution | Cross-platform file ops |
| `storage.py` | StorageManager class for medallion architecture writes | `clear_layer()` method added |
| `settings.py` | Singleton Settings class for centralized configuration | Landing zone paths |
| `logging_utils.py` | Structured logging with timed operations | - |
| `config.py` | Configuration loading and environment management | Archive config |

## 🆕 v1.4.0 Features

### Complete Overwrite Strategy
- `StorageManager.clear_layer()` clears existing data before writes
- `_write_parquet()` removes existing table directories
- No delta/append behavior - fresh data each pipeline run

### Platform-Aware Operations
- `PlatformFileOps` class for cross-platform file operations
- Uses `mssparkutils.fs.rm()` on Fabric, `shutil.rmtree()` locally
- Auto-detects platform via `IS_FABRIC` flag

## 🚀 Quick Start

```python
# Standard notebook import pattern
import sys
from pathlib import Path

# Add project root to path
project_root = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import utilities
from notebooks.lib import platform_utils, logging_utils
from notebooks.lib.storage import StorageManager
from notebooks.config import settings
```

## 📖 Module Documentation

### `platform_utils.py`

Handles platform detection and cross-platform file operations.

```python
from notebooks.lib.platform_utils import IS_FABRIC, get_base_dir, read_parquet_safe

# Check if running in Microsoft Fabric
if IS_FABRIC:
    print("Running in Fabric environment")
else:
    print("Running locally")

# Get base directory
base_dir = get_base_dir()  # Returns Path object

# Safely read parquet with error handling
df = read_parquet_safe("/path/to/file.parquet", sample_size=10000)
```

### `storage.py`

Platform-aware storage abstraction for medallion architecture.

```python
from notebooks.lib.storage import StorageManager

# Initialize storage manager
storage = StorageManager()

# Or with custom base directory
storage = StorageManager(base_dir=Path("/custom/path"))

# Write to Silver layer (auto-detects parquet vs delta)
storage.write_to_silver(df, "table_name")

# Access storage format
print(storage.storage_format)  # 'parquet' or 'delta'

# 🆕 v1.4.0: Clear a layer before writing
storage.clear_layer("Silver")  # Platform-aware clearing
```

#### Clear Layer Method (v1.4.0)

The `clear_layer()` method provides platform-aware directory clearing:

```python
def clear_layer(self, layer: str) -> None:
    """
    Clear all data from a medallion layer.
    
    Platform-aware:
    - Fabric: Uses mssparkutils.fs.rm(path, recurse=True)
    - Local: Uses shutil.rmtree()
    
    Args:
        layer: One of 'bronze', 'silver', 'gold'
    """
```

### `settings.py`

Centralized configuration management via singleton pattern.

```python
from notebooks.config import settings

# Access paths
bronze_dir = settings.bronze_dir
silver_dir = settings.silver_dir
gold_dir = settings.gold_dir
config_dir = settings.config_dir
validation_results_dir = settings.validation_results_dir

# 🆕 v1.4.0: Landing zone paths
landing_dir = settings.landing_dir
archive_dir = settings.archive_dir

# Access settings
max_workers = settings.max_workers
sample_size = settings.sample_size
storage_format = settings.storage_format
environment = settings.environment  # 'local' or 'fabric'

# Get DQ threshold
threshold = settings.get_dq_threshold("medium")  # Returns 80.0

# Access pipeline phases
if settings.pipeline_phases.get("profiling", True):
    # Run profiling...
```

### `logging_utils.py`

Structured logging with timing support.

```python
from notebooks.lib.logging_utils import get_logger, timed_operation

logger = get_logger(__name__)

# Timed operation context manager
with timed_operation(logger, "Processing files"):
    # Your code here
    pass
# Outputs: "Processing files completed in 1.23s"
```

## 🌐 Platform Support

### Auto-Detection

| Environment | Detection | API Used |
|-------------|-----------|----------|
| **Local** | Default | `pathlib`, `shutil` |
| **MS Fabric** | `/lakehouse/default/Files` exists | `mssparkutils.fs.*` |

### Fabric API Compatibility (v1.4.0)

```python
# File operations are automatically platform-aware
from aims_data_platform import PlatformFileOps

ops = PlatformFileOps()
ops.copy_file(src, dst)        # fs.cp() on Fabric
ops.move_file(src, dst)        # fs.mv() on Fabric (no recurse param)
ops.remove_directory(path)     # fs.rm(path, recurse=True) on Fabric
ops.list_files(path)           # fs.ls() with isDir handling on Fabric
```

## 📁 Directory Structure

```
notebooks/lib/
├── __init__.py           # Package exports
├── platform_utils.py     # Platform detection + file ops
├── storage.py            # StorageManager + medallion writes
├── settings.py           # Singleton config
├── logging_utils.py      # Logging utilities
├── config.py             # Config loading
└── README.md             # This file
```

## 🔗 Related Documentation

- [Main README](../../README.md)
- [Landing Zone Guide](../../docs/03_Implementation_Guides/LANDING_ZONE_MANAGEMENT.md)
- [Fabric Deployment](../../docs/02_Fabric_Migration/FABRIC_DEPLOYMENT_GUIDE.md)
- [Pipeline Flow](../../docs/pipeline_flow.md)
