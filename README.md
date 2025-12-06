# AIMS Data Platform

![CI Status](https://github.com/Bralabee/HSS/actions/workflows/aims_dq_ci.yml/badge.svg)

Federated, governed data ingestion platform with incremental loading, data quality validation using Great Expectations, and Microsoft Fabric compatibility.

## Features

- ✅ **Incremental Loading** - Watermark-based incremental data ingestion
- ✅ **Data Quality** - Great Expectations integration for validation
- ✅ **Data Profiling** - Automated profiling using fabric_data_quality framework
- ✅ **Parquet Repair** - Handle corrupted/legacy parquet files
- ✅ **Governance** - Load history and watermark tracking
- ✅ **CLI Interface** - Easy-to-use command-line interface
- ✅ **MS Fabric Ready** - Compatible with Microsoft Fabric/OneLake

## 📊 Data Profiling (NEW!)

Profile your AIMS parquet files to understand data quality and generate validation configs:

```bash
# Setup (one-time)
bash setup_aims_profiling.sh

# Profile all parquet files
python profile_aims_parquet.py

# Or use Jupyter notebook for interactive profiling
jupyter notebook notebooks/03_Profile_AIMS_Data.ipynb
```

**📖 See [README_PROFILING.md](README_PROFILING.md) for complete documentation.**

## 🚀 Pipeline Runner (NEW!)

Run the end-to-end data quality pipeline with configurable thresholds:

```bash
# Run pipeline with default settings (dry-run)
python scripts/run_pipeline.py --dry-run

# Run with a global 90% success threshold
python scripts/run_pipeline.py --dry-run --threshold 90.0

# Force re-processing of all files
python scripts/run_pipeline.py --force --threshold 95.0
```

The `--threshold` flag sets a global baseline. Files with specific configurations (in `dq_great_expectations/generated_configs/`) will use their specific thresholds if defined, otherwise they default to this global value.

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
