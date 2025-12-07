# MS Fabric Deployment Guide - AIMS Data Platform

**Complete Step-by-Step Guide to Deploy AIMS as a Wheel Package in Microsoft Fabric**

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Phase 1: Local Package Preparation](#phase-1-local-package-preparation)
3. [Phase 2: Build Wheel Package](#phase-2-build-wheel-package)
4. [Phase 3: Upload to Fabric](#phase-3-upload-to-fabric)
5. [Phase 4: Fabric Notebook Setup](#phase-4-fabric-notebook-setup)
6. [Phase 5: Testing & Validation](#phase-5-testing--validation)
7. [Phase 6: Production Deployment](#phase-6-production-deployment)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### ✅ What You Need

- [ ] Microsoft Fabric workspace with Lakehouse access
- [ ] Python 3.10 or higher locally
- [ ] Access to ABFSS path: `abfss://DPT_F_DE_AIMSAssurance@onelake.dfs.fabric.microsoft.com/LH_AIMSExtract_Bronze.Lakehouse/Files/`
- [ ] Local AIMS project at: `/home/sanmi/Documents/HS2/HS2_PROJECTS_2025/AIMS_LOCAL`
- [ ] ~80 parquet files in source location

### ✅ Required Tools

```bash
# Install build tools
pip install build setuptools wheel twine
```

---

## Phase 1: Local Package Preparation

### Step 1.1: Refactor Config for Cloud Compatibility

**Problem**: Current config uses hardcoded paths that won't work in Fabric.

**Solution**: Create cloud-aware configuration with dependency injection.

Create `src/fabric_config.py`:

```python
"""Cloud-aware configuration for MS Fabric deployment."""
from pathlib import Path
from typing import Optional, Dict, Any
import os


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
        
        # Determine paths based on environment
        if environment == "fabric":
            # MS Fabric paths
            self.source_path = source_path or self._get_fabric_source_path()
            self.target_path = target_path or "/lakehouse/default/Files/processed"
            self.watermark_db_path = watermark_db_path or "/lakehouse/default/Files/metadata/watermarks.db"
        else:
            # Local paths
            base_dir = Path(__file__).parent.parent
            self.source_path = source_path or str(base_dir / "data" / "source")
            self.target_path = target_path or str(base_dir / "data" / "processed")
            self.watermark_db_path = watermark_db_path or str(base_dir / "watermarks.db")
        
        # Parse additional settings
        self.parquet_engine = kwargs.get("parquet_engine", "pyarrow")
        self.compression = kwargs.get("compression", "snappy")
        self.watermark_column = kwargs.get("watermark_column", "LASTUPDATED")
        self.batch_size = kwargs.get("batch_size", 1.0.2)
        self.log_level = kwargs.get("log_level", "INFO")
    
    @staticmethod
    def _get_fabric_source_path() -> str:
        """Get default Fabric source path."""
        return (
            "abfss://DPT_F_DE_AIMSAssurance@onelake.dfs.fabric.microsoft.com/"
            "LH_AIMSExtract_Bronze.Lakehouse/Files/Parquet files from Datb/13-11-2025"
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
```

### Step 1.2: Create Proper Package Structure

Create `setup.py` for wheel building:

```python
"""Setup configuration for AIMS Data Platform package."""
from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="aims-data-platform",
    version="1.0.2",
    description="AIMS data ingestion platform with incremental loading and data quality",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="HS2 Data Team",
    author_email="data-team@hs2.org.uk",
    url="https://github.com/hs2/aims-data-platform",
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.10",
    install_requires=[
        "pandas>=2.0.0",
        "pyarrow>=14.0.0",
        "numpy>=1.24.0",
        "great-expectations>=0.18.0",
        "sqlalchemy>=2.0.0",
        "pyyaml>=6.0",
        "typer>=0.9.0",
        "rich>=13.0.0",
    ],
    extras_require={
        "azure": [
            "azure-identity>=1.15.0",
            "azure-storage-blob>=12.19.0",
            "azure-storage-file-datalake>=12.14.0",
        ],
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "aims-data=src.cli:app",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    include_package_data=True,
    zip_safe=False,
)
```

### Step 1.3: Create `pyproject.toml` (Modern Python Standard)

```toml
[build-system]
requires = ["setuptools>=65.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "aims-data-platform"
version = "1.0.2"
description = "AIMS data ingestion platform for MS Fabric"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "Proprietary"}
authors = [
    {name = "HS2 Data Team", email = "data-team@hs2.org.uk"}
]
keywords = ["data", "etl", "fabric", "aims", "data-quality"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]

dependencies = [
    "pandas>=2.0.0",
    "pyarrow>=14.0.0",
    "numpy>=1.24.0",
    "great-expectations>=0.18.0",
    "sqlalchemy>=2.0.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
azure = [
    "azure-identity>=1.15.0",
    "azure-storage-blob>=12.19.0",
]
dev = [
    "pytest>=7.4.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]

[project.scripts]
aims-data = "src.cli:app"

[tool.setuptools.packages.find]
where = ["."]
include = ["src*"]
exclude = ["tests*"]

[tool.black]
line-length = 100
target-version = ['py310']

[tool.ruff]
line-length = 100
select = ["E", "F", "W", "I", "N"]
```

### Step 1.4: Update Package `__init__.py`

Update `src/__init__.py` to export properly:

```python
"""AIMS Data Platform - Cloud-ready data ingestion with data quality."""

__version__ = "1.0.2"

# Export main classes for easy import
from .fabric_config import FabricConfig
from .watermark_manager import WatermarkManager
from .ingestion import DataIngester
from .data_quality import DataQualityValidator

__all__ = [
    "FabricConfig",
    "WatermarkManager",
    "DataIngester",
    "DataQualityValidator",
]
```

### Step 1.5: Create MANIFEST.in

```text
include README.md
include LICENSE
include requirements.txt
recursive-include src *.py
recursive-exclude tests *
recursive-exclude * __pycache__
recursive-exclude * *.pyc
recursive-exclude * *.pyo
```

---

## Phase 2: Build Wheel Package

### Step 2.1: Clean Previous Builds

```bash
cd /home/sanmi/Documents/HS2/HS2_PROJECTS_2025/AIMS_LOCAL

# Remove old build artifacts
rm -rf build/ dist/ *.egg-info/
find . -type d -name __pycache__ -exec rm -rf {} +
```

### Step 2.2: Build the Wheel

```bash
# Build wheel package
python -m build

# This creates:
# - dist/aims_data_platform-1.0.2-py3-none-any.whl
# - dist/aims-data-platform-1.0.2.tar.gz
```

### Step 2.3: Verify the Wheel

```bash
# List contents of wheel
unzip -l dist/aims_data_platform-1.0.2-py3-none-any.whl

# Test local installation
pip install dist/aims_data_platform-1.0.2-py3-none-any.whl

# Test import
python -c "from src import FabricConfig, DataIngester; print('✅ Import successful')"
```

---

## Phase 3: Upload to Fabric

### Step 3.1: Upload Wheel to Fabric Lakehouse

**Option A: Via Fabric UI**

1. Open your Fabric workspace
2. Navigate to your Lakehouse: `LH_AIMSExtract_Bronze`
3. Go to **Files** section
4. Create folder structure: `Files/wheels/`
5. Upload `aims_data_platform-1.0.2-py3-none-any.whl`

**Option B: Via Azure CLI (if you have access)**

```bash
# Install Azure CLI
pip install azure-cli

# Login
az login

# Upload wheel
az storage blob upload \
    --account-name onelake \
    --container-name "DPT_F_DE_AIMSAssurance" \
    --name "LH_AIMSExtract_Bronze.Lakehouse/Files/wheels/aims_data_platform-1.0.2-py3-none-any.whl" \
    --file dist/aims_data_platform-1.0.2-py3-none-any.whl
```

**Final Path in Fabric:**
```
/lakehouse/default/Files/wheels/aims_data_platform-1.0.2-py3-none-any.whl
```

### Step 3.2: Upload Source Data (if not already there)

Verify your parquet files are at:
```
abfss://DPT_F_DE_AIMSAssurance@onelake.dfs.fabric.microsoft.com/LH_AIMSExtract_Bronze.Lakehouse/Files/Parquet files from Datb/13-11-2025/
```

---

## Phase 4: Fabric Notebook Setup

### Step 4.1: Create Installation Notebook

Create notebook: `01_Install_AIMS_Package`

**Cell 1: Install the wheel**
```python
# Install AIMS Data Platform package
%pip install /lakehouse/default/Files/wheels/aims_data_platform-1.0.2-py3-none-any.whl --force-reinstall

# Verify installation
import sys
print(f"Python version: {sys.version}")

from src import FabricConfig, DataIngester, WatermarkManager
print("✅ AIMS Data Platform installed successfully!")
```

**Cell 2: Test import**
```python
# Test configuration
config = FabricConfig.for_fabric()
print("Configuration loaded:")
print(f"  Environment: {config.environment}")
print(f"  Source: {config.source_path}")
print(f"  Target: {config.target_path}")
```

### Step 4.2: Create Main Processing Notebook

Create notebook: `02_AIMS_Data_Ingestion`

**Cell 1: Setup**
```python
# Import AIMS package
from src import FabricConfig, DataIngester, WatermarkManager
from pathlib import Path
import pandas as pd
from notebookutils import mssparkutils

# Configure for Fabric environment
config = FabricConfig.for_fabric(
    source_path="abfss://DPT_F_DE_AIMSAssurance@onelake.dfs.fabric.microsoft.com/LH_AIMSExtract_Bronze.Lakehouse/Files/Parquet files from Datb/13-11-2025",
    watermark_column="LASTUPDATED",
    batch_size=1.0.2
)

print("🔧 Configuration:")
for key, value in config.to_dict().items():
    print(f"  {key}: {value}")
```

**Cell 2: List source files**
```python
# List available parquet files
source_path = config.source_path

try:
    # Use mssparkutils to list files
    files = mssparkutils.fs.ls(source_path)
    parquet_files = [f for f in files if f.name.endswith('.parquet')]
    
    print(f"📁 Found {len(parquet_files)} parquet files:")
    for f in parquet_files[:10]:  # Show first 10
        size_mb = f.size / (1024 * 1024)
        print(f"  • {f.name} ({size_mb:.2f} MB)")
    
    if len(parquet_files) > 10:
        print(f"  ... and {len(parquet_files) - 10} more files")
        
except Exception as e:
    print(f"❌ Error listing files: {e}")
    print("Note: You may need to adjust the path or use Spark to read ABFSS")
```

**Cell 3: Initialize components**
```python
# Initialize watermark manager
watermark_mgr = WatermarkManager(config.watermark_db_path)
print("✅ Watermark manager initialized")

# Initialize data ingester
ingester = DataIngester(
    watermark_manager=watermark_mgr,
    engine=config.parquet_engine
)
print("✅ Data ingester initialized")
```

**Cell 4: Read data using Spark (Fabric-native approach)**
```python
# Use Spark to read from ABFSS (more efficient in Fabric)
source_path_spark = (
    "abfss://DPT_F_DE_AIMSAssurance@onelake.dfs.fabric.microsoft.com/"
    "LH_AIMSExtract_Bronze.Lakehouse/Files/Parquet files from Datb/13-11-2025"
)

# Read all parquet files
df_spark = spark.read.parquet(source_path_spark)

print(f"📊 Data loaded:")
print(f"  Rows: {df_spark.count():,}")
print(f"  Columns: {len(df_spark.columns)}")
print(f"\n🔍 Schema:")
df_spark.printSchema()
```

**Cell 5: Convert to Pandas for processing**
```python
# Get sample or full data
sample_size = 1.0.20  # Adjust based on your needs

if df_spark.count() > sample_size:
    df_pd = df_spark.limit(sample_size).toPandas()
    print(f"⚠️  Using sample of {sample_size:,} rows")
else:
    df_pd = df_spark.toPandas()
    print(f"✅ Using full dataset: {len(df_pd):,} rows")

print(f"\n📋 Columns: {list(df_pd.columns)}")
print(f"\n🔢 Shape: {df_pd.shape}")
```

**Cell 6: Incremental load with watermark**
```python
# Get last watermark
source_name = "aims_assets"
last_watermark = watermark_mgr.get_watermark(source_name)

print(f"⏱️  Last watermark: {last_watermark or 'None (first load)'}")

# Filter new records
watermark_col = config.watermark_column

if watermark_col in df_pd.columns:
    # Ensure datetime type
    if df_pd[watermark_col].dtype == 'object':
        df_pd[watermark_col] = pd.to_datetime(df_pd[watermark_col], errors='coerce')
    
    # Filter based on watermark
    if last_watermark:
        last_watermark_dt = pd.to_datetime(last_watermark)
        df_new = df_pd[df_pd[watermark_col] > last_watermark_dt]
    else:
        df_new = df_pd  # First load - take all
    
    print(f"🆕 New records: {len(df_new):,}")
    
    if len(df_new) > 0:
        new_watermark = df_new[watermark_col].max()
        print(f"📅 New watermark: {new_watermark}")
    else:
        print("✅ No new records to process")
        new_watermark = None
else:
    print(f"⚠️  Watermark column '{watermark_col}' not found in data")
    df_new = df_pd
    new_watermark = None
```

**Cell 7: Save to Delta table**
```python
# Save processed data to Delta table
if len(df_new) > 0:
    # Convert back to Spark DataFrame
    df_spark_new = spark.createDataFrame(df_new)
    
    # Save as Delta table
    table_name = f"aims_assets_processed"
    
    # Write to Delta (append mode for incremental)
    df_spark_new.write.format("delta") \
        .mode("append") \
        .option("mergeSchema", "true") \
        .saveAsTable(table_name)
    
    print(f"✅ Saved {len(df_new):,} rows to table: {table_name}")
    
    # Update watermark
    if new_watermark:
        watermark_mgr.update_watermark(
            source_name=source_name,
            watermark_value=str(new_watermark),
            records_processed=len(df_new)
        )
        print(f"✅ Watermark updated: {new_watermark}")
else:
    print("ℹ️  No records to save")
```

**Cell 8: Validation summary**
```python
# Show processing summary
print("=" * 60)
print("PROCESSING SUMMARY")
print("=" * 60)
print(f"Source: {source_name}")
print(f"Total source records: {len(df_pd):,}")
print(f"New records processed: {len(df_new):,}")
print(f"Old watermark: {last_watermark}")
print(f"New watermark: {new_watermark}")
print(f"Target table: {table_name}")
print("=" * 60)

# Query the table to verify
result_count = spark.sql(f"SELECT COUNT(*) as count FROM {table_name}").collect()[0]['count']
print(f"\n✅ Verification: Table contains {result_count:,} total records")
```

### Step 4.3: Create Monitoring Notebook

Create notebook: `03_AIMS_Monitoring`

**Cell 1: View watermarks**
```python
from src import WatermarkManager

watermark_mgr = WatermarkManager("/lakehouse/default/Files/metadata/watermarks.db")

# Get all watermarks
watermarks = watermark_mgr.get_all_watermarks()

print("📊 Current Watermarks:")
print("-" * 80)
for wm in watermarks:
    print(f"Source: {wm['source_name']}")
    print(f"  Watermark: {wm['watermark_value']}")
    print(f"  Last Updated: {wm['last_updated']}")
    print(f"  Records Processed: {wm['records_processed']:,}")
    print()
```

**Cell 2: View load history**
```python
# Get load history
history = watermark_mgr.get_load_history(limit=20)

import pandas as pd
df_history = pd.DataFrame(history)

if not df_history.empty:
    print("📈 Recent Load History:")
    print(df_history.to_string(index=False))
else:
    print("ℹ️  No load history found")
```

**Cell 3: Query processed tables**
```python
# Query all AIMS tables
tables = spark.sql("SHOW TABLES").toPandas()
aims_tables = tables[tables['tableName'].str.contains('aims', case=False)]

print("📋 AIMS Tables in Lakehouse:")
for _, table in aims_tables.iterrows():
    table_name = table['tableName']
    count = spark.sql(f"SELECT COUNT(*) as count FROM {table_name}").collect()[0]['count']
    print(f"  • {table_name}: {count:,} rows")
```

---

## Phase 5: Testing & Validation

### Step 5.1: Test Local Installation

Before deploying to Fabric, test locally:

```bash
cd /home/sanmi/Documents/HS2/HS2_PROJECTS_2025/AIMS_LOCAL

# Install in editable mode
pip install -e .

# Test imports
python -c "
from src import FabricConfig, DataIngester, WatermarkManager
config = FabricConfig.for_local()
print('Local config:', config)
print('✅ All imports successful')
"

# Run CLI
aims-data --help
```

### Step 5.2: Test in Fabric

1. Run `01_Install_AIMS_Package` notebook
2. Verify no errors
3. Check imports work
4. Run `02_AIMS_Data_Ingestion` with small sample first

### Step 5.3: Validation Checklist

- [ ] Wheel installs without errors
- [ ] All imports work
- [ ] Can read from ABFSS path
- [ ] Watermark database created
- [ ] Data written to Delta tables
- [ ] Incremental load works (run twice)
- [ ] Monitoring queries work

---

## Phase 6: Production Deployment

### Step 6.1: Create Data Pipeline

Create a Fabric Data Pipeline:

1. **Activity 1**: Install Package
   - Notebook: `01_Install_AIMS_Package`
   
2. **Activity 2**: List Sources
   - Notebook: Custom notebook to discover all source files
   
3. **Activity 3**: Process Each Source
   - Notebook: `02_AIMS_Data_Ingestion`
   - Parameters: `source_name`, `source_path`
   - Run in loop for each source file
   
4. **Activity 4**: Validation
   - Notebook: `03_AIMS_Monitoring`
   - Check all loads succeeded

### Step 6.2: Schedule Pipeline

1. Go to your pipeline
2. Click "Schedule"
3. Set frequency (e.g., daily at 2 AM)
4. Configure alerts for failures

### Step 6.3: Set Up Monitoring

Create monitoring dashboard:

```python
# Create monitoring view
spark.sql("""
CREATE OR REPLACE VIEW v_aims_load_monitoring AS
SELECT 
    source_name,
    MAX(watermark_value) as latest_watermark,
    MAX(last_updated) as last_load_time,
    SUM(records_processed) as total_records,
    COUNT(*) as load_count
FROM watermark_metadata
GROUP BY source_name
""")
```

---

## Troubleshooting

### Issue 1: Import Errors

**Problem**: `ModuleNotFoundError: No module named 'src'`

**Solution**:
```python
# Reinstall package
%pip install /lakehouse/default/Files/wheels/aims_data_platform-1.0.2-py3-none-any.whl --force-reinstall --no-deps
```

### Issue 2: ABFSS Access Denied

**Problem**: `403 Forbidden` or access denied errors

**Solution**:
- Verify workspace permissions
- Check lakehouse is attached to notebook
- Use `mssparkutils.fs.ls()` to verify path

### Issue 3: Watermark Database Lock

**Problem**: `database is locked` error

**Solution**:
```python
# Use different path or ensure single writer
config = FabricConfig.for_fabric(
    watermark_db_path="/lakehouse/default/Files/metadata/watermarks_{source_name}.db"
)
```

### Issue 4: Memory Errors with Large Files

**Problem**: Out of memory when processing

**Solution**:
```python
# Process in batches
batch_size = 50000
for batch in pd.read_parquet(file, chunksize=batch_size):
    process_batch(batch)
```

### Issue 5: Wheel Not Found

**Problem**: Wheel file not accessible

**Solution**:
```bash
# Verify file exists
mssparkutils.fs.ls("/lakehouse/default/Files/wheels/")

# Use absolute path
%pip install /lakehouse/default/Files/wheels/aims_data_platform-1.0.2-py3-none-any.whl
```

---

## Advanced Topics

### Using with PySpark Throughout

For large datasets, stay in Spark:

```python
from pyspark.sql import functions as F

# Read data
df = spark.read.parquet(source_path)

# Get watermark
watermark_value = spark.sql(
    f"SELECT MAX({watermark_col}) FROM watermark_table WHERE source = '{source_name}'"
).collect()[0][0]

# Filter new records
df_new = df.filter(F.col(watermark_col) > watermark_value)

# Save to Delta
df_new.write.format("delta").mode("append").saveAsTable("target_table")
```

### Version Management

Update version in multiple places when releasing new version:

1. `setup.py`: `version="1.1.0"`
2. `pyproject.toml`: `version = "1.1.0"`
3. `src/__init__.py`: `__version__ = "1.1.0"`
4. Rebuild wheel: `python -m build`
5. Upload new wheel to Fabric

### CI/CD Integration

Automate wheel building:

```yaml
# .github/workflows/build-wheel.yml
name: Build Wheel
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install build
      - run: python -m build
      - uses: actions/upload-artifact@v2
        with:
          name: wheel
          path: dist/*.whl
```

---

## Summary Checklist

### Pre-Deployment
- [ ] Create `fabric_config.py` with cloud-aware config
- [ ] Create `setup.py` and `pyproject.toml`
- [ ] Update `src/__init__.py` exports
- [ ] Create `MANIFEST.in`

### Build
- [ ] Clean old builds: `rm -rf build dist *.egg-info`
- [ ] Build wheel: `python -m build`
- [ ] Test locally: `pip install dist/*.whl`

### Upload
- [ ] Upload wheel to Fabric: `Files/wheels/`
- [ ] Verify source data accessible
- [ ] Create metadata directories

### Fabric Setup
- [ ] Create install notebook
- [ ] Create processing notebook
- [ ] Create monitoring notebook
- [ ] Test with small sample

### Production
- [ ] Create data pipeline
- [ ] Schedule pipeline
- [ ] Set up monitoring dashboard
- [ ] Configure alerts
- [ ] Document for team

---

## Quick Reference Commands

```bash
# Build wheel
python -m build

# Install locally
pip install dist/aims_data_platform-1.0.2-py3-none-any.whl

# Test import
python -c "from src import FabricConfig; print('OK')"

# In Fabric notebook:
%pip install /lakehouse/default/Files/wheels/aims_data_platform-1.0.2-py3-none-any.whl
```

---

**🎉 You're ready to deploy! Follow the steps sequentially and check off each item as you complete it.**

For questions or issues, refer to the troubleshooting section or check the AIMS team documentation.
