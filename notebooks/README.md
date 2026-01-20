# AIMS Data Platform - Notebooks

**Version:** 1.3.1  
**Last Updated:** 2026-01-20

## Overview

This directory contains Jupyter notebooks for the AIMS Data Quality pipeline. All notebooks are designed to run both locally (development/testing) and in Microsoft Fabric (production).

## ⚠️ Fabric Deployment

**Wheel Package:** `aims_data_platform-1.3.1-py3-none-any.whl`

Upload to Fabric Environment → Libraries → Custom libraries, then Publish.

**Key Fix in 1.3.1:** Configuration loading now works correctly from wheel packages in Fabric. Settings properly resolves to capitalized Fabric paths (`/lakehouse/default/Files/Bronze`).

## Notebook Index

| # | Notebook | Purpose | Dependencies |
|---|----------|---------|--------------|
| 00 | `00_AIMS_Orchestration.ipynb` | Master pipeline orchestrator | All below |
| 01 | `01_AIMS_Data_Profiling.ipynb` | Generate DQ configs from data | BatchProfiler |
| 02 | `02_AIMS_Data_Ingestion.ipynb` | Bronze layer data ingestion | WatermarkManager |
| 03 | `03_AIMS_Monitoring.ipynb` | Pipeline monitoring and alerting | logging_utils |
| 04 | `04_AIMS_Schema_Reconciliation.ipynb` | Schema drift detection | storage |
| 05 | `05_AIMS_Data_Insights.ipynb` | Data exploration and analysis | pandas, plotly |
| 06 | `06_AIMS_Business_Intelligence.ipynb` | BI metrics and KPIs | Silver layer |
| 07 | `07_AIMS_DQ_Matrix_and_Modeling.ipynb` | DQ matrix dashboard and modeling | DQ configs |
| 08 | `08_AIMS_Business_Intelligence.ipynb` | Advanced BI analytics | Gold layer |

## Shared Utilities

All notebooks use shared utilities from `lib/`:

| Module | Description | Key Features |
|--------|-------------|--------------|
| `platform_utils` | Platform detection | `IS_FABRIC` flag, path management, cross-platform file operations |
| `storage` | StorageManager for I/O | Read/write Bronze/Silver/Gold, Parquet/Delta support, schema validation |
| `settings` | Centralized configuration | YAML config loading, environment detection, type-safe accessors |
| `logging_utils` | Consistent logging | `setup_notebook_logger()`, progress tracking, phase decorators |

### Import Pattern

```python
# Standard imports for all notebooks
from notebooks.lib.platform_utils import IS_FABRIC, get_data_paths, copy_file
from notebooks.lib.storage import StorageManager
from notebooks.lib.settings import Settings
from notebooks.lib.logging_utils import setup_notebook_logger, ProgressTracker

# Initialize
settings = Settings.load()
logger = setup_notebook_logger(__name__)
storage = StorageManager()
```

## Configuration

### `config/notebook_settings.yaml`

Centralized YAML configuration with environment-specific settings:

```yaml
environments:
  local:
    base_dir: null  # Auto-detected
    storage_format: parquet
    max_workers: 4
    log_level: DEBUG
  
  fabric_dev:
    base_dir: /lakehouse/default/Files
    storage_format: delta
    max_workers: 8
    log_level: INFO
  
  fabric_prod:
    base_dir: /lakehouse/default/Files
    storage_format: delta
    max_workers: 16
    log_level: WARNING

data_quality:
  threshold: 85.0
  null_tolerance: 5.0
  duplicate_tolerance: 1.0
```

### Configuration Priority

Settings are resolved in the following order (highest to lowest priority):

1. **Environment variables** - e.g., `AIMS_DQ_THRESHOLD=90.0`
2. **`.env` file values** - Local overrides
3. **YAML configuration** - `notebook_settings.yaml`
4. **Built-in defaults** - Fallback values

## Running Notebooks

### Local Environment

```bash
# 1. Activate environment
conda activate aims_data_platform

# 2. Start Jupyter Lab
jupyter lab

# 3. Open notebooks from the file browser
# Navigate to: notebooks/00_AIMS_Orchestration.ipynb
```

### Microsoft Fabric

1. **Upload notebooks** to your Fabric workspace:
   - Navigate to your Lakehouse
   - Click "Import notebook"
   - Select notebooks from this directory

2. **Upload shared utilities**:
   - Create folder: `/lakehouse/default/Files/notebooks/lib/`
   - Upload all files from `lib/` directory
   - Create folder: `/lakehouse/default/Files/notebooks/config/`
   - Upload `notebook_settings.yaml`

3. **Verify environment**:
   ```python
   from notebooks.lib.platform_utils import IS_FABRIC
   print(f"Running in Fabric: {IS_FABRIC}")  # Should print: True
   ```

4. **Configure production settings** (optional):
   - Set workspace environment variable: `AIMS_ENVIRONMENT=fabric_prod`
   - Or let auto-detection handle it

## Directory Structure

```
notebooks/
├── README.md                          # This file
├── 00_AIMS_Orchestration.ipynb        # Master pipeline
├── 01_AIMS_Data_Profiling.ipynb       # Data profiling
├── 02_AIMS_Data_Ingestion.ipynb       # Data ingestion
├── 03_AIMS_Monitoring.ipynb           # Monitoring
├── 04_AIMS_Schema_Reconciliation.ipynb # Schema reconciliation
├── 05_AIMS_Data_Insights.ipynb        # Data insights
├── 06_AIMS_Business_Intelligence.ipynb # BI metrics
├── 07_AIMS_DQ_Matrix_and_Modeling.ipynb # DQ matrix
├── 08_AIMS_Business_Intelligence.ipynb # Advanced BI
├── archive/                           # Archived notebooks
├── config/
│   ├── notebook_settings.yaml         # Main configuration
│   ├── data_quality/                  # DQ configs per table
│   └── validation_results/            # Validation output
├── data/                              # Notebook-specific data
├── lib/
│   ├── __init__.py
│   ├── platform_utils.py              # Platform detection
│   ├── storage.py                     # Storage abstraction
│   ├── settings.py                    # Settings manager
│   ├── logging_utils.py               # Logging utilities
│   └── config.py                      # Additional config helpers
└── utils/                             # Legacy utilities (deprecated)
```

## Best Practices

### 1. Always Use Shared Utilities

```python
# ✅ Good - uses platform-aware storage
from notebooks.lib.storage import StorageManager
storage = StorageManager()
df = storage.read_from_bronze("aims_assets")

# ❌ Bad - hardcoded paths
df = pd.read_parquet("/home/user/data/aims_assets.parquet")
```

### 2. Respect Configuration Hierarchy

```python
# ✅ Good - uses Settings singleton
from notebooks.lib.settings import Settings
settings = Settings.load()
threshold = settings.dq_threshold

# ❌ Bad - hardcoded values
threshold = 85.0
```

### 3. Use Consistent Logging

```python
# ✅ Good - structured logging
from notebooks.lib.logging_utils import setup_notebook_logger
logger = setup_notebook_logger(__name__)
logger.info("Processing started", extra={"table": "aims_assets"})

# ❌ Bad - print statements
print("Processing started")
```

### 4. Handle Platform Differences

```python
# ✅ Good - platform-aware code
from notebooks.lib.platform_utils import IS_FABRIC, copy_file
if IS_FABRIC:
    # Use mssparkutils for Fabric-specific operations
    pass
else:
    # Use standard file operations
    pass
```

## Troubleshooting

### Import Errors

```bash
# Ensure you're in the correct directory
cd /path/to/1_AIMS_LOCAL_2026

# Verify environment is activated
conda activate aims_data_platform

# Check PYTHONPATH includes project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Configuration Not Loading

```python
# Force reload settings
from notebooks.lib.settings import Settings
settings = Settings.load(force_reload=True)

# Check detected environment
print(f"Environment: {settings.environment}")
print(f"Base dir: {settings.base_dir}")
```

### Storage Manager Issues

```python
# Verify storage format
from notebooks.lib.storage import get_storage_format
print(f"Storage format: {get_storage_format()}")

# Check paths
from notebooks.lib.settings import Settings
settings = Settings.load()
print(f"Bronze path: {settings.bronze_dir}")
```

## Related Documentation

- [Main README](../README.md) - Project overview
- [Architecture Guide](../docs/01_Architecture_and_Design/) - System architecture
- [Fabric Migration Guide](../docs/02_Fabric_Migration/) - Deploy to Microsoft Fabric
- [Implementation Guides](../docs/03_Implementation_Guides/) - Detailed procedures
