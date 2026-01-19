# AIMS Data Platform

![CI Status](https://github.com/Bralabee/aims_etl_dq_2026/actions/workflows/ci-cd.yml/badge.svg)
![Azure DevOps](https://dev.azure.com/{org}/AIMS-Data-Platform/_apis/build/status/aims-pipeline)
![Test Coverage](https://img.shields.io/badge/tests-15%2F15%20passing-brightgreen)
![DQ Pass Rate](https://img.shields.io/badge/DQ%20validation-73.5%25-yellow)
![Production Ready](https://img.shields.io/badge/production%20ready-70%25-yellow)

# AIMS Data Platform - Local Development Environment

**Version:** 1.3.0
**Status:** Stable - All Notebooks Validated
**Last Updated:** 2026-01-19

A comprehensive, governed data ingestion platform designed for incremental loading, data quality validation via Great Expectations, dual CLI/Notebook functionality, and seamless integration with Microsoft Fabric.

## 📊 Quick Stats

| Metric | Value |
|--------|-------|
| **Bronze Tables** | 68 |
| **DQ Configs Generated** | 68 |
| **Validation Pass Rate** | 73.5% (50/68) |
| **Average Quality Score** | 97.3% |
| **Test Suite** | 15/15 passing (100%) |
| **Notebooks Validated** | 8/8 passing (100%) |
| **Documentation** | 170+ pages |
| **CI/CD Pipelines** | Azure DevOps + GitHub Actions |

## Key Features

- ✅ **Dual Functionality** - Complete CLI scripts AND interactive Jupyter notebooks for all operations
- ✅ **Incremental Loading** - Implements watermark-based incremental data ingestion
- ✅ **Data Quality** - Integrates Great Expectations for robust data validation (68 configs, 97.3% avg score)
- ✅ **Automated Profiling** - Generates DQ configs automatically using `fabric_data_quality` framework
- ✅ **Silver Layer Transformation** - Converts Bronze Parquet files into Star Schema for BI reporting
- ✅ **DQ Matrix Dashboard** - Visual heat map of data quality rule coverage across all tables
- ✅ **Threshold Management** - Automated script to adjust validation thresholds (100% → 95%)
- ✅ **CI/CD Integration** - Complete Azure DevOps and GitHub Actions workflows
- ✅ **Governance** - Maintains detailed load history and watermark tracking for auditability
- ✅ **CLI + Notebook Interface** - Choose your preferred workflow: command-line or interactive
- ✅ **MS Fabric Ready** - Fully compatible with Microsoft Fabric and OneLake architectures
- ✅ **Production Ready** - 70% ready for deployment with comprehensive testing and documentation

## Data Profiling Capabilities

Analyze AIMS Parquet files to assess data quality and generate validation configurations automatically.

```bash
# Initial Setup (one-time)
bash setup.sh

# Execute profiling for all Parquet files
python scripts/profile_aims_parquet.py

# Interactive profiling via Jupyter Notebook
jupyter notebook notebooks/01_AIMS_Data_Profiling.ipynb
```

**📖 Refer to [docs/README_PROFILING.md](docs/README_PROFILING.md) for comprehensive documentation.**

## 🚀 Pipeline Execution

Execute the end-to-end data quality pipeline with configurable success thresholds.

```bash
# Execute pipeline with default settings (dry-run mode)
python scripts/run_pipeline.py --dry-run

# Execute with a global 90% success threshold
python scripts/run_pipeline.py --dry-run --threshold 90.0

# Force re-processing of all files with increased parallelism
python scripts/run_pipeline.py --force --threshold 95.0 --workers 8
```

The `--threshold` parameter establishes a global baseline. Files with specific configurations (located in `dq_great_expectations/generated_configs/`) utilize their defined thresholds; otherwise, the global default is applied.
The `--workers` parameter controls the level of parallelism (default: 4).

## 🚀 Quick Start (5 Minutes)

```bash
# 1. Navigate to project
cd /home/sanmi/Documents/HS2/HS2_PROJECTS_2025/1_AIMS_LOCAL_2026

# 2. Activate environment
conda activate aims_data_platform

# 3. Run validation
python scripts/run_validation_simple.py

# Expected: ✅ 50/68 passing (73.5%)
```

**See [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) for detailed instructions.**

## 📚 Documentation (170+ Pages)

### 🎯 Start Here
- **[QUICK_START_GUIDE.md](QUICK_START_GUIDE.md)** - Get started in 5 minutes
- **[COMPLETE_IMPLEMENTATION_SUMMARY.md](docs/COMPLETE_IMPLEMENTATION_SUMMARY.md)** - Full project overview (37 pages)
- **[END_TO_END_TESTING_REPORT.md](docs/END_TO_END_TESTING_REPORT.md)** - Testing results and validation (NEW)

### 🔧 Implementation Guides
- **[PHASES_2_3_EXECUTION_REPORT.md](docs/PHASES_2_3_EXECUTION_REPORT.md)** - Phase 2 & 3 detailed execution (30 pages)
- **[THRESHOLD_ADJUSTMENT_REPORT.md](docs/THRESHOLD_ADJUSTMENT_REPORT.md)** - DQ threshold analysis (20 pages)
- **[CI_CD_SETUP_GUIDE.md](docs/CI_CD_SETUP_GUIDE.md)** - Complete CI/CD configuration (40 pages)

### 📖 Reference Documentation
- **[PROJECT_STATE_ANALYSIS.md](docs/PROJECT_STATE_ANALYSIS.md)** - Current system state
- **[COMPREHENSIVE_FIX_REPORT.md](docs/COMPREHENSIVE_FIX_REPORT.md)** - Phase 1 fixes (26 pages)
- **[README_PROFILING.md](docs/README_PROFILING.md)** - Profiling documentation
- **[Silver Layer Guide](docs/SILVER_LAYER_GUIDE.md)** - Star Schema modeling
- **[Fabric Migration Guide](docs/FABRIC_MIGRATION_GUIDE.md)** - Deploy to Microsoft Fabric

## Quick Start

### 1. Setup Environment

```bash
# Create conda environment
conda env create -f environment.yml

# Activate environment
conda activate aims_data_platform

# Or using pip directly
pip install -r requirements.txt
```

### 2. Configure

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your paths
nano .env
```

### 3. Initialize

```bash
# Initialize the platform
python -m aims_data_platform.cli init
```

### 4. Repair Corrupted Files (if needed)

```bash
# Repair parquet files
python -m aims_data_platform.cli repair

# Or specify custom paths
python -m aims_data_platform.cli repair --source-dir /path/to/source --output-dir /path/to/output
```

### 5. Validate Source Files

```bash
# Validate source files
python -m aims_data_platform.cli validate-source

# Or with custom path
python -m aims_data_platform.cli validate-source --source-dir /path/to/data
```

### 6. Ingest Data

```bash
# Ingest aims_assets data
python -m aims_data_platform.cli ingest aims_assets --watermark-column LASTUPDATED

# Ingest aims_attributes data
python -m aims_data_platform.cli ingest aims_attributes --watermark-column LASTUPDATED

# Skip validation
python -m aims_data_platform.cli ingest aims_assets --no-validate
```

### 7. Monitor

```bash
# View watermarks
python -m aims_data_platform.cli list-watermarks

# View load history
python -m aims_data_platform.cli load-history

# View history for specific source
python -m aims_data_platform.cli load-history --source-name aims_assets --limit 20
```

## Python API Usage

```python
from aims_data_platform import config, WatermarkManager, DataIngester, DataQualityValidator
from pathlib import Path

# Initialize
config.ensure_directories()
watermark_mgr = WatermarkManager(config.WATERMARK_DB_PATH)
ingester = DataIngester(watermark_mgr, engine="fastparquet")

# Repair files
results = ingester.repair_directory(
    source_dir=config.SOURCE_DATA_PATH,
    output_dir=config.REPAIRED_DATA_PATH
)

# Ingest data
source_files = list(config.REPAIRED_DATA_PATH.glob("aims_assets*.parquet"))
result = ingester.ingest_incremental(
    source_name="aims_assets",
    source_files=source_files,
    target_path=config.TARGET_DATA_PATH,
    watermark_column="LASTUPDATED"
)

# Validate quality
validator = DataQualityValidator()
import pandas as pd
df = pd.read_parquet(result["target_file"])
validation_results = validator.validate_dataframe(df, suite_name="aims_assets")
```

## Project Structure

```
AIMS_LOCAL/
├── aims_data_platform/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── watermark_manager.py   # Watermark tracking
│   ├── ingestion.py           # Data ingestion logic
│   ├── data_quality.py        # Great Expectations integration
│   └── cli.py                 # Command-line interface
├── notebooks/                 # Interactive Jupyter notebooks
│   ├── 00-08_*.ipynb          # Pipeline notebooks (see Notebook Index)
│   ├── lib/                   # Shared notebook utilities
│   │   ├── platform_utils.py  # Platform detection (local vs Fabric)
│   │   ├── storage.py         # StorageManager for I/O operations
│   │   ├── settings.py        # Centralized configuration
│   │   └── logging_utils.py   # Consistent logging setup
│   └── config/                # Notebook configuration
│       └── notebook_settings.yaml  # Environment-specific settings
├── data/                      # Target data directory
│   └── repaired/              # Repaired parquet files
├── great_expectations/        # GE configuration
├── dq_great_expectations/     # Generated DQ configs
├── environment.yml            # Conda environment
├── requirements.txt           # Python dependencies
├── .env.example               # Example environment variables
├── watermarks.db             # Watermark database
└── README.md                 # This file
```

## Configuration

### Environment Variables (`.env`)

Edit `.env` file to configure core settings:

- **SOURCE_DATA_PATH**: Source parquet files location
- **TARGET_DATA_PATH**: Target directory for processed data
- **DEFAULT_WATERMARK_COLUMN**: Default column for incremental loading
- **PARQUET_ENGINE**: Engine to use (fastparquet or pyarrow)
- **AIMS_ENVIRONMENT**: Environment selection (`local`, `fabric_dev`, `fabric_prod`)
- **AIMS_DQ_THRESHOLD**: Data quality pass threshold (default: 85%)
- **AIMS_MAX_WORKERS**: Parallel processing workers

### Notebook Configuration (`notebooks/config/notebook_settings.yaml`)

Centralized YAML configuration for all notebooks with:
- **Environment-specific settings**: Automatic detection or explicit override
- **Data quality thresholds**: Customizable per environment and severity level
- **Path templates**: Medallion architecture paths (Bronze/Silver/Gold)
- **Pipeline configuration**: Phase enable/disable and behavior settings
- **Table-specific overrides**: Per-table DQ threshold customization

```yaml
# Example: Access settings in notebooks
from notebooks.lib.settings import Settings
settings = Settings.load()
print(f"Environment: {settings.environment}")
print(f"DQ Threshold: {settings.dq_threshold}")
```

## Environment Configuration

### Local Development

```bash
# 1. Set up environment
conda activate aims_data_platform

# 2. Configure paths (optional - defaults work for most cases)
cp .env.example .env
nano .env  # Edit paths if needed

# 3. Run notebooks
jupyter lab notebooks/
```

### Microsoft Fabric

1. Upload notebooks to Fabric workspace
2. Configuration auto-detects Fabric environment (`/lakehouse/default/Files`)
3. Override settings via Fabric environment variables if needed:
   - `AIMS_ENVIRONMENT=fabric_prod`
   - `AIMS_IS_PRODUCTION=true`

See [Fabric Migration Guide](docs/02_Fabric_Migration/) for detailed instructions.

## Notebook Utilities

The `notebooks/lib/` directory provides shared utilities for consistent notebook behavior:

| Module | Purpose |
|--------|---------|
| `platform_utils` | Platform detection (local vs Fabric), path management, cross-platform file operations |
| `storage` | StorageManager for reading/writing Bronze/Silver/Gold layers (Parquet/Delta) |
| `settings` | Singleton settings manager with YAML config and environment override support |
| `logging_utils` | Consistent logging setup with progress tracking and phase decorators |

### Usage Example

```python
# In any notebook
from notebooks.lib.platform_utils import IS_FABRIC, get_data_paths
from notebooks.lib.storage import StorageManager
from notebooks.lib.settings import Settings
from notebooks.lib.logging_utils import setup_notebook_logger

# Auto-detect environment
settings = Settings.load()
logger = setup_notebook_logger(__name__)
storage = StorageManager()

# Platform-aware operations
logger.info(f"Running in {'Fabric' if IS_FABRIC else 'Local'} environment")
df = storage.read_from_bronze("aims_assets")
```

See [notebooks/README.md](notebooks/README.md) for complete notebook documentation.

## Data Quality Validation

The platform includes automated data quality checks:

1. **Row count validation** - Ensures data exists
2. **Null value checks** - Validates required fields
3. **Duplicate detection** - Identifies duplicate records
4. **Data type validation** - Ensures correct types
5. **Date validation** - Validates timestamp columns

## Incremental Loading

The platform uses watermark-based incremental loading:

1. **First Load**: Loads all data
2. **Subsequent Loads**: Only loads data where watermark column > last watermark
3. **Tracking**: All loads tracked in load_history table
4. **Recovery**: Automatic retry on failure

## Microsoft Fabric Integration

To sync with Microsoft Fabric:

1. Configure Azure credentials in `.env`
2. Use OneLake-compatible paths
3. Data is stored in Delta-compatible parquet format
4. Partitioning supported for optimal performance

## Troubleshooting

### Corrupted Parquet Files

If you encounter "Repetition level histogram size mismatch" errors:

```bash
python -m aims_data_platform.cli repair
```

### Import Errors

Ensure environment is activated:

```bash
conda activate aims_data_platform
```

### Permission Errors

Ensure you have write access to:
- Target data directory
- Watermark database path
- Great Expectations directory

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black aims_data_platform/
ruff check aims_data_platform/
```

## License

Proprietary - HS2

## Support

For issues or questions, contact the HS2 Data Team.
