# AIMS Data Platform - Microsoft Fabric Deployment Guide

**Version:** 1.3.1  
**Last Updated:** 20 January 2026  
**Fabric Runtime:** 1.3 (Spark 3.5, Delta 3.2)  
**Status:** ✅ Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Step-by-Step Deployment](#step-by-step-deployment)
4. [Configuration](#configuration)
5. [Running the Pipeline](#running-the-pipeline)
6. [Troubleshooting](#troubleshooting)
7. [Validation Checklist](#validation-checklist)

---

## Overview

### What is AIMS Data Platform?

AIMS Data Platform is a production-ready data quality and ingestion framework that:
- Validates data using Great Expectations
- Implements medallion architecture (Bronze → Silver → Gold)
- Supports dual-platform deployment (Local + MS Fabric)
- Auto-detects the runtime environment

### Data Flow Architecture

```
SFTP Server → Landing Zone → Bronze → Silver → Gold
                  ↓              ↑
            (archived)    (DQ Validation)
```

### Platform Auto-Detection

The platform automatically detects MS Fabric:
```python
IS_FABRIC = Path("/lakehouse/default/Files").exists()
```

When `IS_FABRIC=True`:
- Uses `mssparkutils.fs` for file operations
- Uses Delta format instead of Parquet
- Uses 8-16 parallel workers (vs 4 locally)
- Paths resolve to `/lakehouse/default/Files/`

---

## Prerequisites

### Required Access
- [ ] Microsoft Fabric workspace with **Contributor** or higher role
- [ ] Lakehouse access in your workspace
- [ ] Ability to create Environments (for custom libraries)

### Required Files (from your local build)

| File | Location | Description |
|------|----------|-------------|
| `aims_data_platform-1.3.1-py3-none-any.whl` | `1_AIMS_LOCAL_2026/dist/` | Core platform package |
| `fabric_data_quality-1.2.0-py3-none-any.whl` | `2_DATA_QUALITY_LIBRARY/dist/` | DQ framework |
| `notebook_settings.yaml` | `notebooks/config/` | Configuration file |
| `00_AIMS_Orchestration.ipynb` | `notebooks/` | Master orchestration |

### Build Wheel Packages (if not already built)

```bash
# Build AIMS Data Platform wheel
cd /home/sanmi/Documents/HS2/HS2_PROJECTS_2025/1_AIMS_LOCAL_2026
conda activate aims_data_platform
pip install build
python -m build --wheel

# Build DQ Framework wheel
cd /home/sanmi/Documents/HS2/HS2_PROJECTS_2025/2_DATA_QUALITY_LIBRARY
python -m build --wheel
```

---

## Step-by-Step Deployment

### Step 1: Create Fabric Environment

1. **Open your Fabric Workspace**
2. Click **+ New item** → **Environment**
3. **Name:** `aims_data_platform_env`
4. **Runtime:** Select **Runtime 1.3** (Spark 3.5, Delta 3.2)
5. Click **Create**

### Step 2: Upload Custom Libraries

1. In the Environment → **Libraries** tab
2. Click **Custom Libraries** → **Upload**
3. Upload these files:
   - `aims_data_platform-1.3.1-py3-none-any.whl`
   - `fabric_data_quality-1.2.0-py3-none-any.whl`

4. In **Public Libraries** (PyPI), add:

   | Library | Version |
   |---------|---------|
   | `great-expectations` | `0.18.22` |
   | `pyyaml` | `6.0.1` |
   | `python-dotenv` | `1.0.0` |

5. Click **Publish** → **Publish all**
6. ⏳ Wait 2-5 minutes for environment to build

### Step 3: Set as Workspace Default

1. **Workspace Settings** → **Data Engineering/Science** → **Spark settings**
2. Toggle **Set default environment** → **On**
3. Select: `aims_data_platform_env`
4. Click **Save**

### Step 4: Create Lakehouse

1. Click **+ New item** → **Lakehouse**
2. **Name:** `aims_lakehouse`

> **✅ AUTO-CREATED FOLDERS:** The pipeline **automatically creates** all required medallion layer folders (`Bronze/`, `Silver/`, `Gold/`, `landing/`, `archive/`, `state/`) on first run. You do **NOT** need to manually create these folders.

The `LandingZoneManager` initializes directories automatically:
```python
# From landing_zone_manager.py - runs on initialization
for dir_path in [self.landing_dir, self.bronze_dir, self.archive_dir]:
    self.file_ops.makedirs(dir_path)  # Uses mssparkutils.fs.mkdirs on Fabric
```

**Expected folder structure (created automatically):**
```
Files/
├── landing/              ← Auto-created, SFTP delivers files here
├── Bronze/               ← Auto-created, CAPITALIZED
├── Silver/               ← Auto-created, CAPITALIZED
├── Gold/                 ← Auto-created, CAPITALIZED
├── archive/              ← Auto-created, processed files archived here
├── config/
│   └── data_quality/     ← Auto-created during profiling phase
├── state/                ← Auto-created for watermarks
└── notebooks/
    └── config/           ← MANUAL: Upload settings YAML here (Step 5)
```

**Only manual step:** Create `notebooks/config/` folder and upload `notebook_settings.yaml` (see Step 5).

---

### 📋 **Naming Convention: CAPITALIZED Medallion Layers**

This project follows a **CAPITALIZED naming convention** for medallion layer directories:

| Layer | Directory Name | ✅ Correct | ❌ Wrong |
|-------|---------------|-----------|----------|
| Bronze | `Bronze/` | `Files/Bronze/` | `Files/bronze/` |
| Silver | `Silver/` | `Files/Silver/` | `Files/silver/` |
| Gold | `Gold/` | `Files/Gold/` | `Files/gold/` |

**Why Capitalized Names?**
- **Consistency:** Matches MS Fabric's default Lakehouse pattern
- **Visibility:** Easier to distinguish data layers in file explorers
- **Standards:** Aligns with Databricks and Azure medallion conventions
- **Code Compatibility:** The `Settings` class defaults expect capitalized names

> **⚠️ CRITICAL:** Folder names **MUST** be capitalized: `Bronze`, `Silver`, `Gold`.  
> The Settings class fallback defaults use these exact capitalized names.
> Using lowercase will cause `FileNotFoundError` or empty DataFrames.

**Local Development Note:**  
In local development, the Bronze layer may use a descriptive folder name like `Samples_LH_Bronze_Aims_26_parquet/` to identify the data source. This is configured in `notebook_settings.yaml` under `paths.bronze`.

### Step 5: Upload Configuration File

1. Download `notebooks/config/notebook_settings.yaml` from your local project
2. Upload to: `Files/notebooks/config/notebook_settings.yaml`

### Step 6: Upload Notebooks

Upload these notebooks to your lakehouse:

| Notebook | Purpose |
|----------|---------|
| `00_AIMS_Orchestration.ipynb` | Master pipeline orchestrator |
| `01_AIMS_Data_Profiling.ipynb` | Data profiling and DQ config generation |
| `02_AIMS_Data_Ingestion.ipynb` | Validation and Silver ingestion |
| `03_AIMS_Monitoring.ipynb` | DQ monitoring dashboard |

### Step 7: Configure SFTP Source (Optional)

If using SFTP for data delivery, configure your pipeline to deliver files to:
```
/lakehouse/default/Files/landing/
```

---

## Configuration

### Path Configuration

The platform auto-configures paths based on environment:

| Layer | Fabric Path |
|-------|-------------|
| Landing | `/lakehouse/default/Files/landing/` |
| Bronze | `/lakehouse/default/Files/Bronze/` |
| Silver | `/lakehouse/default/Files/Silver/` |
| Gold | `/lakehouse/default/Files/Gold/` |
| Archive | `/lakehouse/default/Files/archive/YYYY-MM-DD_run_xxx/` |
| DQ Configs | `/lakehouse/default/Files/config/data_quality/` |
| State | `/lakehouse/default/Files/state/` |

### Settings Detection Order

The Settings class loads configuration in this priority:

1. `/lakehouse/default/Files/notebooks/config/notebook_settings.yaml` (Fabric first)
2. Package location (relative to settings.py)
3. Current working directory
4. Project root
5. `importlib.resources` from wheel package
6. Hardcoded defaults with correct Fabric paths

### Data Quality Thresholds

Default thresholds from `notebook_settings.yaml`:

```yaml
data_quality:
  threshold: 85.0           # Default pass threshold
  null_tolerance: 5.0       # Max null percentage
  severity_levels:
    critical: 100.0         # Must be perfect (PKs, FKs)
    high: 95.0              # Minor issues allowed
    medium: 85.0            # Moderate issues allowed
    low: 70.0               # Significant issues allowed
```

---

## Running the Pipeline

### Option A: Full Orchestration Notebook (Recommended)

1. Open `00_AIMS_Orchestration.ipynb` in Fabric
2. Attach to your lakehouse: `aims_lakehouse`
3. Run all cells

The orchestration notebook automatically:
- Detects Fabric environment
- Moves files from landing to Bronze
- Profiles data and generates DQ configs
- Validates and promotes to Silver
- Archives processed files
- Reports metrics

### Option B: Manual Python Code

Create a new notebook and run these cells:

#### Cell 1: Setup and Imports

```python
# Disable GX analytics (required for Fabric)
import os
os.environ["GX_ANALYTICS_ENABLED"] = "False"

from pathlib import Path
from datetime import datetime
from aims_data_platform import BatchProfiler, DataQualityValidator, DataLoader
from aims_data_platform.landing_zone_manager import (
    LandingZoneManager, PlatformFileOps, IS_FABRIC
)

print(f"Running in Fabric: {IS_FABRIC}")

# Define paths
BASE_DIR = Path("/lakehouse/default/Files")
LANDING_DIR = BASE_DIR / "landing"
BRONZE_DIR = BASE_DIR / "Bronze"
SILVER_DIR = BASE_DIR / "Silver"
GOLD_DIR = BASE_DIR / "Gold"
CONFIG_DIR = BASE_DIR / "config" / "data_quality"
ARCHIVE_DIR = BASE_DIR / "archive"

# Create directories if needed
for d in [LANDING_DIR, BRONZE_DIR, SILVER_DIR, GOLD_DIR, CONFIG_DIR, ARCHIVE_DIR]:
    d.mkdir(parents=True, exist_ok=True)
    
print("✅ Directories configured")
```

#### Cell 2: Move Landing Files to Bronze

```python
# Initialize landing zone manager
lz_manager = LandingZoneManager(
    landing_dir=LANDING_DIR,
    bronze_dir=BRONZE_DIR,
    archive_dir=ARCHIVE_DIR
)

# Check for new files
landing_files = lz_manager.list_landing_files()
print(f"Found {len(landing_files)} files in landing zone")

if landing_files:
    # Move to Bronze
    run_id = lz_manager.generate_run_id()
    result = lz_manager.move_landing_to_bronze(run_id)
    print(f"✅ Moved {len(result['files_moved'])} files to Bronze")
else:
    print("⚠️ No files in landing zone - using existing Bronze data")
```

#### Cell 3: Profile Data and Generate DQ Configs

```python
# Run batch profiling
bronze_files = list(BRONZE_DIR.glob("*.parquet"))
print(f"Found {len(bronze_files)} parquet files in Bronze")

if bronze_files:
    start = datetime.now()
    
    results = BatchProfiler.run_parallel_profiling(
        input_dir=str(BRONZE_DIR),
        output_dir=str(CONFIG_DIR),
        workers=8,  # Use 8 workers in Fabric
        sample_size=100000
    )
    
    success_count = len([r for r in results if r.get('status') == 'success'])
    duration = (datetime.now() - start).total_seconds()
    
    print(f"✅ Generated {success_count} DQ configs in {duration:.1f}s")
```

#### Cell 4: Validate and Ingest to Silver

```python
DQ_THRESHOLD = 85.0
passed = 0
failed = 0

# Clear Silver for complete overwrite
file_ops = PlatformFileOps(is_fabric=True)
for existing in SILVER_DIR.glob("*.parquet"):
    file_ops.remove_file(existing)
print("Cleared Silver directory for fresh write")

for parquet_file in sorted(BRONZE_DIR.glob("*.parquet")):
    table_name = parquet_file.stem
    config_file = CONFIG_DIR / f"{table_name}_validation.yml"
    
    if not config_file.exists():
        print(f"⚠️ {table_name}: No config, skipping")
        continue
    
    try:
        # Load and validate
        df = DataLoader.load_data(str(parquet_file), sample_size=100000)
        validator = DataQualityValidator(config_path=str(config_file))
        result = validator.validate(df)
        
        pass_rate = result['statistics']['success_percent']
        
        if pass_rate >= DQ_THRESHOLD:
            # Write to Silver
            silver_path = SILVER_DIR / f"{table_name}.parquet"
            df.to_parquet(str(silver_path), index=False)
            print(f"✅ {table_name}: {pass_rate:.1f}% → Silver")
            passed += 1
        else:
            print(f"❌ {table_name}: {pass_rate:.1f}% (below {DQ_THRESHOLD}%)")
            failed += 1
            
    except Exception as e:
        print(f"💥 {table_name}: Error - {e}")
        failed += 1

print(f"\n{'='*50}")
print(f"RESULTS: {passed} passed, {failed} failed")
print(f"Pass Rate: {passed/(passed+failed)*100:.1f}%")
```

#### Cell 5: Archive Landing Files

```python
if landing_files:  # Only archive if we had new files
    archive_result = lz_manager.archive_landing_files(run_id)
    print(f"✅ Archived to: {archive_result['archive_path']}")
    
    # Verify landing is empty
    remaining = list(LANDING_DIR.glob("*.parquet"))
    if not remaining:
        print("✅ Landing zone cleared - ready for next SFTP delivery")
    else:
        print(f"⚠️ {len(remaining)} files still in landing zone")
```

### Option C: Using the Settings Class

For more control, use the Settings class:

```python
from notebooks.lib.settings import Settings

# Auto-detect environment (will detect Fabric)
settings = Settings.load()

print(f"Environment: {settings.environment}")  # fabric_dev or fabric_prod
print(f"Bronze Dir: {settings.bronze_dir}")    # /lakehouse/default/Files/Bronze
print(f"DQ Threshold: {settings.dq_threshold}") # 85.0

# Use settings-based paths
BRONZE_DIR = settings.bronze_dir
SILVER_DIR = settings.silver_dir
CONFIG_DIR = settings.config_dir
```

---

## Troubleshooting

### Common Issues

#### 1. "ModuleNotFoundError: No module named 'aims_data_platform'"

**Cause:** Environment not attached or not built.

**Solution:**
1. Ensure environment is published (check status in Environment page)
2. Attach notebook to the correct lakehouse
3. Restart the Spark session

#### 2. Wrong Paths (lowercase bronze instead of Bronze)

**Cause:** Settings not loading YAML config properly.

**Solution:**
1. Upload `notebook_settings.yaml` to `/lakehouse/default/Files/notebooks/config/`
2. Verify the `fabric_paths` section uses capitalized names:
   ```yaml
   fabric_paths:
     bronze: Bronze
     silver: Silver
     gold: Gold
   ```

#### 3. "FileNotFoundError: /lakehouse/default/Files/..."

**Cause:** Directories not created.

**Solution:**
```python
from pathlib import Path
BASE_DIR = Path("/lakehouse/default/Files")
for d in ["landing", "Bronze", "Silver", "Gold", "archive", "config/data_quality", "state"]:
    (BASE_DIR / d).mkdir(parents=True, exist_ok=True)
```

#### 4. "mssparkutils not available"

**Cause:** Running in notebook environment without mssparkutils.

**Solution:** The platform falls back to shutil operations automatically. This is normal and works correctly.

#### 5. Great Expectations Analytics Warning

**Cause:** GX tries to send analytics data.

**Solution:** Add at top of notebook:
```python
import os
os.environ["GX_ANALYTICS_ENABLED"] = "False"
```

### Debugging Commands

```python
# Check if Fabric is detected
from aims_data_platform.landing_zone_manager import IS_FABRIC
print(f"IS_FABRIC: {IS_FABRIC}")

# Check paths
from notebooks.lib.settings import Settings
settings = Settings.load()
print(settings.to_dict())

# Check mssparkutils availability
try:
    from notebookutils import mssparkutils
    print("mssparkutils available")
except ImportError:
    print("mssparkutils NOT available (using fallback)")
```

---

## Validation Checklist

Use this checklist to verify successful deployment:

### Environment Setup
- [ ] Fabric Environment created with name `aims_data_platform_env`
- [ ] Custom wheels uploaded (aims_data_platform, fabric_data_quality)
- [ ] PyPI dependencies added (great-expectations, pyyaml, python-dotenv)
- [ ] Environment published and ready
- [ ] Set as workspace default environment

### Lakehouse Structure
- [ ] Lakehouse `aims_lakehouse` created
- [ ] Folders created: `landing/`, `Bronze/`, `Silver/`, `Gold/`
- [ ] Config folder: `config/data_quality/`
- [ ] Settings file uploaded to `notebooks/config/notebook_settings.yaml`

### Notebooks
- [ ] `00_AIMS_Orchestration.ipynb` uploaded
- [ ] Notebook attached to lakehouse
- [ ] First cell runs without import errors

### Pipeline Execution
- [ ] Platform detects `IS_FABRIC = True`
- [ ] Bronze files processed successfully
- [ ] DQ configs generated (check `config/data_quality/`)
- [ ] Silver files created with validated data
- [ ] Archive created with date stamp

### Data Quality
- [ ] Validation pass rate ≥ 85%
- [ ] No critical errors in pipeline
- [ ] Results logged/saved

---

## Quick Reference

### Key Paths

| Purpose | Path |
|---------|------|
| Landing Zone | `/lakehouse/default/Files/landing/` |
| Bronze Layer | `/lakehouse/default/Files/Bronze/` |
| Silver Layer | `/lakehouse/default/Files/Silver/` |
| Gold Layer | `/lakehouse/default/Files/Gold/` |
| DQ Configs | `/lakehouse/default/Files/config/data_quality/` |
| Settings | `/lakehouse/default/Files/notebooks/config/notebook_settings.yaml` |

### Key Imports

```python
from aims_data_platform import (
    BatchProfiler, DataQualityValidator, DataLoader, ConfigLoader
)
from aims_data_platform.landing_zone_manager import (
    LandingZoneManager, PlatformFileOps, IS_FABRIC
)
from notebooks.lib.settings import Settings
```

### Quick Start Command

```python
# One-liner to test imports
import os; os.environ["GX_ANALYTICS_ENABLED"]="False"
from aims_data_platform import BatchProfiler; print("✅ AIMS ready")
```

---

## Support

For issues:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review logs in the notebook output
3. Contact the HS2 Data Team

---

*Documentation generated for AIMS Data Platform v1.3.1*  
*Last verified: 20 January 2026*
