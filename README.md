# AIMS Data Platform

![CI Status](https://github.com/Bralabee/aims_etl_dq_2026/actions/workflows/ci-cd.yml/badge.svg)
![Azure DevOps](https://dev.azure.com/{org}/AIMS-Data-Platform/_apis/build/status/aims-pipeline)
![Test Coverage](https://img.shields.io/badge/tests-15%2F15%20passing-brightgreen)
![DQ Pass Rate](https://img.shields.io/badge/DQ%20validation-80.9%25-yellow)
![Production Ready](https://img.shields.io/badge/production%20ready-90%25-green)

# AIMS Data Platform - Local Development Environment

**Version:** 1.2.2
**Status:** Stable - All Notebooks Validated
**Last Updated:** 2025-02-24

A comprehensive, governed data ingestion platform designed for incremental loading, data quality validation via Great Expectations, dual CLI/Notebook functionality, and seamless integration with Microsoft Fabric.

## 📊 Quick Stats

| Metric | Value |
|--------|-------|
| **Bronze Tables** | 68 |
| **DQ Configs Generated** | 68 |
| **Validation Pass Rate** | 80.9% (55/68) |
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
- ✅ **Production Ready** - 90% ready for deployment with comprehensive testing and documentation

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

# Expected: ✅ 55/68 passing (80.9%)
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
python -m src.cli init
```

### 4. Repair Corrupted Files (if needed)

```bash
# Repair parquet files
python -m src.cli repair

# Or specify custom paths
python -m src.cli repair --source-dir /path/to/source --output-dir /path/to/output
```

### 5. Validate Source Files

```bash
# Validate source files
python -m src.cli validate-source

# Or with custom path
python -m src.cli validate-source --source-dir /path/to/data
```

### 6. Ingest Data

```bash
# Ingest aims_assets data
python -m src.cli ingest aims_assets --watermark-column LASTUPDATED

# Ingest aims_attributes data
python -m src.cli ingest aims_attributes --watermark-column LASTUPDATED

# Skip validation
python -m src.cli ingest aims_assets --no-validate
```

### 7. Monitor

```bash
# View watermarks
python -m src.cli list-watermarks

# View load history
python -m src.cli load-history

# View history for specific source
python -m src.cli load-history --source-name aims_assets --limit 20
```

## Python API Usage

```python
from src import config, WatermarkManager, DataIngester, DataQualityValidator
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
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── watermark_manager.py   # Watermark tracking
│   ├── ingestion.py           # Data ingestion logic
│   ├── data_quality.py        # Great Expectations integration
│   └── cli.py                 # Command-line interface
├── data/                      # Target data directory
│   └── repaired/              # Repaired parquet files
├── great_expectations/        # GE configuration
├── environment.yml            # Conda environment
├── requirements.txt           # Python dependencies
├── .env.example               # Example environment variables
├── watermarks.db             # Watermark database
└── README.md                 # This file
```

## Configuration

Edit `.env` file to configure:

- **SOURCE_DATA_PATH**: Source parquet files location
- **TARGET_DATA_PATH**: Target directory for processed data
- **DEFAULT_WATERMARK_COLUMN**: Default column for incremental loading
- **PARQUET_ENGINE**: Engine to use (fastparquet or pyarrow)

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
python -m src.cli repair
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
black src/
ruff check src/
```

## License

Proprietary - HS2

## Support

For issues or questions, contact the HS2 Data Team.
