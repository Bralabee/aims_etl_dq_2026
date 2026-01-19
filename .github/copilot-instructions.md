# AIMS Data Platform - AI Coding Instructions

> **Version:** 1.3.0 | **Updated:** January 2026

## 🧠 Architecture & Core Patterns

### Dual-Platform Runtime
- **Microsoft Fabric** (Spark notebooks) + **Local Linux** (Python scripts)
- **Detection Pattern:**
  ```python
  from pathlib import Path
  IS_FABRIC = Path("/lakehouse/default/Files").exists()
  ```
- **CRITICAL:** NEVER use `import notebookutils` at top level—it hangs indefinitely on local Linux!

### Split-Library Pattern
| Library | Location | Purpose |
|---------|----------|---------|
| `dq_framework` | `../2_DATA_QUALITY_LIBRARY` | Generic data quality engine (source of truth) |
| `aims_data_platform` | `.` (this project) | AIMS-specific wrappers and orchestration |

**Import Rule:** Always import from `aims_data_platform`, which wraps `dq_framework`:
```python
# ✅ Correct
from aims_data_platform import DataIngester, DataValidator
from aims_data_platform.watermark_manager import WatermarkManager

# ❌ Wrong - don't import directly from dq_framework in AIMS code
from dq_framework import DataIngester
```

### Module Structure
```
aims_data_platform/
├── __init__.py          # Re-exports from dq_framework
├── config.py            # Configuration management
├── data_quality.py      # DQ validation wrappers
├── fabric_config.py     # Fabric-specific settings
├── ingestion.py         # DataIngester with watermark support
├── schema_reconciliation.py
└── watermark_manager.py # Incremental load tracking
```

## 📁 File Locations

### Configuration
- **DQ Configs:** `config/data_quality/*.yml` (65+ validation configs)
- **Main Config:** `config/` directory

### State & Persistence
- **Watermarks (JSON):** `data/state/watermarks.json`
- **DQ Logs:** `data/state/dq_logs.jsonl`
- **Watermarks (SQLite):** `watermarks.db` (root directory)

### Data Layers
- **Bronze (Raw):** `data/Samples_LH_Bronze_Aims_26_parquet/`
- **Silver (Cleaned):** `data/silver_layer/`

## 🛡️ Data Quality (Great Expectations)

### Performance Critical
```python
import os
os.environ["GX_ANALYTICS_ENABLED"] = "False"  # MUST be before GX imports!

import great_expectations as gx  # Now safe to import
```

### Validation Result Schema (Flat Dictionary)
```python
# ✅ Current schema (v1.2.0)
result.get('evaluated_checks')   # Total checks run
result.get('successful_checks')  # Passed checks
result.get('success_percent')    # Pass rate

# ❌ Old schema - DO NOT USE
result.get('statistics').get('evaluated_expectations')  # KeyError!
```

### Configuration Files
- Pattern: `config/data_quality/aims_{tablename}_validation.yml`
- Example: `aims_assets_validation.yml`, `aims_workorders_validation.yml`

## 📓 Notebooks & Orchestration

- **Master Orchestrator:** `notebooks/00_AIMS_Orchestration.ipynb`
- **Pipeline Control:**
  ```python
  PIPELINE_CONFIG = {
      "run_profiling": True,
      "run_ingestion": True,
      "run_validation": True,
      "continue_on_error": False
  }
  ```
- **Error Handling:** Explicitly `raise` in `try/except` if `continue_on_error=False`

## 🛠️ Developer Workflow

### Testing
```bash
conda activate aims_data_platform
pytest tests/ -v

# Verify imports work before committing
python -c "from aims_data_platform import DataIngester, DataValidator; print('OK')"
```

### Path Handling (Dynamic, Not Hardcoded)
```python
# ✅ Correct - dynamic BASE_DIR
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent

# ❌ Wrong - hardcoded user path
BASE_DIR = Path("/home/sanmi/Documents/...")
```

### Sync Requirements
- `scripts/run_pipeline.py` logic MUST match `notebooks/00_AIMS_Orchestration.ipynb`
- Dependencies: `environment.yml` (Conda) + `requirements.txt` (pip)

## ⚠️ Common Pitfalls

| Pitfall | Wrong | Correct |
|---------|-------|---------|
| Fabric detection | `try: import notebookutils` | `Path("/lakehouse/default/Files").exists()` |
| GX import | Import GX directly | Set `GX_ANALYTICS_ENABLED=False` first |
| Result schema | `result['statistics']['...']` | `result.get('evaluated_checks')` |
| Paths | `/home/sanmi/...` | `BASE_DIR = Path(__file__).parent.parent` |
| Imports | `from dq_framework import X` | `from aims_data_platform import X` |

## 🔄 Incremental Load (Watermarks)

```python
from aims_data_platform.watermark_manager import WatermarkManager
from aims_data_platform import DataIngester

# Initialize with watermark tracking
wm = WatermarkManager(db_path="watermarks.db")
ingester = DataIngester(watermark_manager=wm)

# Watermarks stored in:
# - watermarks.db (SQLite, primary)
# - data/state/watermarks.json (JSON backup)
```

## 📓 Notebook Utilities (NEW in v1.3.0)

When working with notebooks, ALWAYS use the shared utilities:

### Configuration
```python
# ✅ CORRECT - Use centralized settings
from notebooks.config import settings
BASE_DIR = settings.base_dir
BRONZE_DIR = settings.bronze_dir

# ❌ INCORRECT - Don't hardcode paths
BASE_DIR = Path("/home/sanmi/...")  # NO!
```

### Storage Operations
```python
# ✅ CORRECT - Use StorageManager
from notebooks.lib.storage import StorageManager
sm = StorageManager()
sm.write_to_silver(df, "table_name")

# ❌ INCORRECT - Don't use shutil directly
import shutil
shutil.copy2(src, dest)  # NO! Won't work in Fabric
```

### Platform Detection
```python
# ✅ CORRECT - Use platform_utils
from notebooks.lib import platform_utils
if platform_utils.IS_FABRIC:
    ...

# ❌ INCORRECT - Don't reinvent detection
IS_FABRIC = Path("/lakehouse/...").exists()  # NO! Use platform_utils
```

### Data Loading
```python
# ✅ CORRECT - Use data_loaders
from notebooks.lib.data_loaders import load_bronze_table
df = load_bronze_table("assets")

# ❌ INCORRECT - Don't manually build paths
df = pd.read_parquet(f"{base}/Bronze/assets")  # NO!
```

## 📁 File Structure (Updated v1.3.0)

```
notebooks/
├── config/                     # Notebook configuration (NEW)
│   ├── __init__.py            # Settings loader
│   └── notebook_settings.yaml # Centralized paths & params
├── lib/                       # Shared utilities (NEW)
│   ├── __init__.py
│   ├── data_loaders.py        # Bronze/Silver loading
│   ├── platform_utils.py      # Platform detection
│   └── storage.py             # StorageManager class
├── 00_AIMS_Orchestration.ipynb
└── ...
```

## 🧪 Pre-Commit Checklist

- [ ] Imports work: `python -c "from aims_data_platform import ..."`
- [ ] Tests pass: `pytest tests/`
- [ ] No hardcoded paths (grep for `/home/`)
- [ ] GX analytics disabled before GX imports
- [ ] Using flat result schema, not nested `statistics`
