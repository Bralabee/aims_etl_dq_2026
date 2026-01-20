# AIMS Data Platform - MS Fabric Deployment Guide

> **Last Updated:** 20 January 2026 | **Fabric Runtime:** 1.3 (Spark 3.5, Delta 3.2) | **Version:** 1.3.1

---

## Data Flow

```
SFTP Server → Landing Zone → Bronze → Silver → Gold
                  ↓              ↑
            (archived)    (AIMS Pipeline)
```

---

## Step 1: Create Fabric Environment

1. In your workspace, click **+ New item** → **Environment**
2. Name: `aims_data_platform_env`
3. Select **Runtime 1.3 (Spark 3.5, Delta 3.2)**

---

## Step 2: Upload Custom Libraries

1. In Environment → **Libraries** tab → **Custom Libraries**
2. Click **Upload** and add:

   | File | Location |
   |------|----------|
   | `fabric_data_quality-1.2.0-py3-none-any.whl` | `2_DATA_QUALITY_LIBRARY/dist/` |
   | `aims_data_platform-1.3.1-py3-none-any.whl` | `1_AIMS_LOCAL_2026/dist/` |

3. In **External repositories**, add:

   | Library | Version |
   |---------|---------|
   | `great-expectations` | `0.18.22` |
   | `pyyaml` | `6.0.1` |
   | `python-dotenv` | `1.0.0` |

4. Click **Publish** → **Publish all** (wait 2-5 min)

---

## Step 3: Set as Workspace Default

1. **Workspace Settings** → **Data Engineering/Science** → **Spark settings**
2. Toggle **Set default environment** → **On**
3. Select: `aims_data_platform_env`
4. **Save**

---

## Step 4: Create Lakehouse Structure

1. Create Lakehouse: `aims_lakehouse`
2. In **Files**, create folders:

   ```
   landing/              ← SFTP delivers files here
   Bronze/               ← CAPITALIZED (required)
   Silver/               ← CAPITALIZED (required)
   Gold/                 ← CAPITALIZED (required)
   archive/              ← Processed files moved here
   config/data_quality/
   state/
   ```

> **⚠️ Important:** Folder names must be capitalized (Bronze, Silver, Gold) to match the configuration.

---

## Step 5: Configure SFTP Source

Configure your SFTP/data pipeline to deliver files to:
```
/lakehouse/default/Files/landing/
```

---

## Step 6: Run Pipeline

### Option A: Use Orchestration Notebook

Upload `notebooks/00_AIMS_Orchestration.ipynb` to Fabric and run it. It auto-detects Fabric and handles:
- Landing → Bronze ingestion
- Data profiling and config generation  
- Validation and Silver promotion
- Archive and cleanup

### Option B: Manual Notebook

```python
# Cell 1: Setup
import os
os.environ["GX_ANALYTICS_ENABLED"] = "False"

from pathlib import Path
from aims_data_platform import BatchProfiler, DataQualityValidator, DataLoader
from aims_data_platform.landing_zone_manager import LandingZoneManager

BASE_DIR = Path("/lakehouse/default/Files")
LANDING_DIR = BASE_DIR / "landing"
BRONZE_DIR = BASE_DIR / "Bronze"
SILVER_DIR = BASE_DIR / "Silver"
CONFIG_DIR = BASE_DIR / "config" / "data_quality"
ARCHIVE_DIR = BASE_DIR / "archive"
```

```python
# Cell 2: Move files from Landing to Bronze
lz_manager = LandingZoneManager(
    landing_dir=LANDING_DIR,
    bronze_dir=BRONZE_DIR,
    archive_dir=ARCHIVE_DIR
)

run_id = lz_manager.generate_run_id()
result = lz_manager.move_landing_to_bronze(run_id)
print(f"✅ Moved {len(result['files_moved'])} files to Bronze")
```

```python
# Cell 3: Profile Bronze data and generate validation configs
BatchProfiler.run_parallel_profiling(
    input_dir=str(BRONZE_DIR),
    output_dir=str(CONFIG_DIR),
    workers=8
)
print(f"✅ Generated {len(list(CONFIG_DIR.glob('*.yml')))} validation configs")
```

```python
# Cell 4: Validate and promote to Silver
DQ_THRESHOLD = 85.0

for parquet_file in sorted(BRONZE_DIR.glob("*.parquet")):
    table_name = parquet_file.stem
    config_file = CONFIG_DIR / f"{table_name}_validation.yml"
    
    if not config_file.exists():
        print(f"⚠️ {table_name}: No config, skipping")
        continue
    
    df = DataLoader.load_data(str(parquet_file))
    validator = DataQualityValidator(config_path=str(config_file))
    result = validator.validate(df)
    
    pass_rate = result['statistics']['success_percent']
    
    if pass_rate >= DQ_THRESHOLD:
        df.to_parquet(str(SILVER_DIR / f"{table_name}.parquet"), index=False)
        print(f"✅ {table_name}: {pass_rate:.1f}% → Silver")
    else:
        print(f"❌ {table_name}: {pass_rate:.1f}% (below threshold)")
```

```python
# Cell 5: Archive landing files (clears for next SFTP delivery)
archive_result = lz_manager.archive_landing_files(run_id)
print(f"✅ Archived {len(archive_result['files_archived'])} files to {archive_result['archive_path']}")

# Verify landing is empty
lz_manager.verify_landing_zone_empty()
```

---

## Path Reference

| Layer | Fabric Path |
|-------|-------------|
| Landing | `/lakehouse/default/Files/landing/` |
| Bronze | `/lakehouse/default/Files/Bronze/` |
| Silver | `/lakehouse/default/Files/Silver/` |
| Gold | `/lakehouse/default/Files/Gold/` |
| Configs | `/lakehouse/default/Files/config/data_quality/` |
| Archive | `/lakehouse/default/Files/archive/{date}_{run_id}/` |

---

## Platform Auto-Detection

The code auto-detects Fabric:
```python
IS_FABRIC = Path("/lakehouse/default/Files").exists()
```

When `IS_FABRIC=True`:
- Uses `mssparkutils.fs` for file operations
- Writes Delta format (vs Parquet locally)
- Uses 8-16 workers (vs 4 locally)
