# Notebook Shared Utilities Library

This directory contains shared utility modules for all AIMS Data Platform notebooks, providing centralized configuration, platform detection, storage abstraction, and logging.

## 📦 Module Overview

| Module | Purpose |
|--------|---------|
| `platform_utils.py` | Platform detection (local vs Fabric) and base directory resolution |
| `storage.py` | StorageManager class for medallion architecture writes |
| `settings.py` | Singleton Settings class for centralized configuration |
| `logging_utils.py` | Structured logging with timed operations |
| `config.py` | Configuration loading and environment management |

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

Structured logging with timing utilities.

```python
from notebooks.lib.logging_utils import setup_notebook_logger, timed_operation, log_phase

# Setup logger for a notebook
logger = setup_notebook_logger("my_notebook")
logger.info("Starting process...")

# Use timed operations
with timed_operation("Data Loading", logger):
    df = pd.read_parquet("file.parquet")
# Outputs: "⏱️ Data Loading completed in 1.23s"

# Log phase boundaries
log_phase(logger, "Phase 1", "Profiling", "Starting data profiling...")
```

## ⚙️ Configuration

Settings are loaded from `notebooks/config/notebook_settings.yaml`:

```yaml
# Environment detection
environment: auto  # auto, local, or fabric

# Data paths (relative to base_dir)
paths:
  bronze: data/Samples_LH_Bronze_Aims_26_parquet
  silver: data/Silver
  gold: data/Gold
  config: config/data_quality
  validation_results: notebooks/config/validation_results

# Performance settings
performance:
  max_workers: 4
  sample_size: 100000
  batch_size: 10

# DQ thresholds
dq_thresholds:
  critical: 100.0
  high: 95.0
  medium: 80.0
  low: 50.0

# Pipeline phases
pipeline_phases:
  profiling: true
  ingestion: true
  monitoring: true
```

## 🔄 Fallback Behavior

All modules include fallback mechanisms for when imports fail:

```python
try:
    from notebooks.config import settings
    BRONZE_DIR = settings.bronze_dir
except ImportError:
    # Fallback to inline configuration
    IS_FABRIC = Path("/lakehouse/default/Files").exists()
    if IS_FABRIC:
        BRONZE_DIR = Path("/lakehouse/default/Files/Bronze")
    else:
        BRONZE_DIR = Path.cwd().parent / "data/Bronze"
```

## 🧪 Testing Utilities

```python
# Verify all modules are working
from notebooks.lib.platform_utils import IS_FABRIC
from notebooks.lib.storage import StorageManager
from notebooks.config import settings
from notebooks.lib.logging_utils import get_logger

print(f"Platform: {'Fabric' if IS_FABRIC else 'Local'}")
print(f"Environment: {settings.environment}")
print(f"Storage format: {settings.storage_format}")
print(f"Bronze dir exists: {settings.bronze_dir.exists()}")
```

## 📁 File Structure

```
notebooks/
├── lib/
│   ├── __init__.py
│   ├── platform_utils.py    # IS_FABRIC, get_base_dir(), read_parquet_safe()
│   ├── storage.py           # StorageManager class
│   ├── settings.py          # Settings singleton
│   ├── logging_utils.py     # Logger, timed_operation(), log_phase()
│   └── config.py            # Configuration utilities
├── config/
│   ├── notebook_settings.yaml
│   └── validation_results/
└── 00_AIMS_Orchestration.ipynb  # Master orchestration notebook
```

## 📝 Version History

- **v1.3.0** (2026-01-19): Initial release with all modules
- Platform detection, storage abstraction, settings management, logging utilities
