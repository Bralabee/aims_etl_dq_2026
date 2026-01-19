# AIMS Data Platform - File Structure

```
AIMS_LOCAL/
│
├── 📋 Configuration Files
│   ├── environment.yml              # Conda environment with Python 3.10
│   ├── requirements.txt             # All Python dependencies
│   ├── .env.example                 # Template for environment variables
│   ├── Makefile                     # Convenient command shortcuts
│   └── setup.sh                     # Automated setup script (executable)
│
├── 📚 Documentation
│   ├── README.md                    # Main usage guide
│   ├── IMPLEMENTATION_GUIDE.md      # Detailed implementation guide
│   └── FILE_STRUCTURE.md            # This file
│
├── 🐍 Python Package (src/)
│   ├── __init__.py                  # Package initialization
│   ├── config.py                    # Configuration & environment variables
│   ├── watermark_manager.py        # SQLite watermark tracking
│   ├── ingestion.py                 # Data ingestion & parquet repair
│   ├── data_quality.py              # Great Expectations integration
│   └── cli.py                       # Rich CLI interface (Typer)
│
├── 📊 Data Directories (created on init)
│   ├── data/                        # Target directory for ingested data
│   │   └── repaired/                # Repaired parquet files
│   └── great_expectations/          # GE configuration and results
│
├── 🗄️ Database (created on init)
│   └── watermarks.db                # SQLite: watermarks + load history
│
└── 📓 Notebooks (existing)
    ├── aims_data_simple.ipynb       # Simple standalone notebook
    ├── aims_data_exploration.ipynb  # Data exploration notebook
    └── testing_aims_parquet_files.ipynb  # Testing notebook
```

## File Descriptions

### Configuration Layer

**environment.yml**
- Conda environment specification
- Python 3.10 base
- References requirements.txt for pip packages
- Includes conda-forge channel

**requirements.txt**
- Core: pandas, pyarrow, fastparquet
- Quality: great-expectations
- Database: sqlalchemy
- Azure: azure-identity, azure-storage-*
- CLI: typer, rich, click
- Utils: python-dotenv, pyyaml, structlog

**.env.example**
- Template for configuration
- Source/target paths
- Parquet engine settings
- Watermark column defaults
- Logging configuration
- Azure/Fabric credentials (optional)

**Makefile**
- `make setup` - Run setup.sh
- `make init` - Initialize platform
- `make repair` - Fix corrupted files
- `make ingest-all` - Ingest all sources
- `make watermarks` - Show current watermarks
- `make history` - Show load history
- `make clean` - Remove generated files

**setup.sh**
- Automated environment setup
- Detects conda vs pip
- Creates .env from template
- Shows next steps

### Python Package (src/)

**config.py** (Config Management)
```python
- Config class with all settings
- Environment variable loading
- Path management
- Directory creation
- Configuration as dictionary
```

**watermark_manager.py** (Watermark Tracking)
```python
- WatermarkManager class
- SQLite database operations
- get_watermark(source_name)
- update_watermark(source, value, count)
- start_load(source) / complete_load(load_id)
- list_watermarks() → DataFrame
- get_load_history() → DataFrame
```

**ingestion.py** (Data Ingestion)
```python
- DataIngester class
- repair_parquet_file(source, output)
- repair_directory(source_dir, output_dir)
- ingest_incremental(...) → results dict
- validate_source_files(dir) → validation results
- Multi-engine support (fastparquet/pyarrow)
- Watermark filtering
- Error handling & logging
```

**data_quality.py** (Quality Validation)
```python
- DataQualityValidator class
- initialize_context() - GE setup
- create_datasource(name, base_dir)
- create_expectation_suite(name, schema)
- validate_dataframe(df, suite) → results
- validate_file(path, suite) → results
- generate_data_profile(df) → profile dict
- Basic validations without full GE
```

**cli.py** (Command-Line Interface)
```python
Commands:
- init - Initialize platform
- repair - Fix corrupted parquet files
- validate-source - Validate source files
- ingest - Incremental data ingestion
- list-watermarks - Show all watermarks
- load-history - Show load history

Features:
- Rich terminal output
- Tables and formatting
- Error handling
- Help system
```

### Data Flow

```
1. Source Files (corrupted)
   ↓
2. repair → Repaired Files (data/repaired/)
   ↓
3. ingest → Incremental Load → Target Files (data/)
   ↓
4. validate → Quality Check → Results
   ↓
5. watermark → Update Tracking → watermarks.db
```

### Database Schema

**watermarks table:**
```sql
- source_name (TEXT, PRIMARY KEY)
- watermark_value (TEXT)
- watermark_type (TEXT)
- last_updated (TIMESTAMP)
- records_processed (INTEGER)
- metadata (TEXT)
```

**load_history table:**
```sql
- id (INTEGER, PRIMARY KEY)
- source_name (TEXT)
- load_start (TIMESTAMP)
- load_end (TIMESTAMP)
- records_processed (INTEGER)
- status (TEXT)
- error_message (TEXT)
- watermark_value (TEXT)
```

## Usage Patterns

### Pattern 1: First-Time Setup
```bash
./setup.sh
conda activate aims_data_platform
make init
make repair
make ingest-all
```

### Pattern 2: Incremental Updates
```bash
conda activate aims_data_platform
make ingest-all
make watermarks
```

### Pattern 3: Monitoring
```bash
make watermarks    # Check current state
make history       # Review past loads
```

### Pattern 4: Python API
```python
from src import WatermarkManager, DataIngester
watermark_mgr = WatermarkManager("watermarks.db")
ingester = DataIngester(watermark_mgr)
# ... use API
```

## Dependencies Overview

**Core Data:**
- pandas: DataFrame operations
- pyarrow: Modern parquet engine
- fastparquet: Legacy parquet compatibility

**Quality:**
- great-expectations: Data validation framework

**Storage:**
- sqlalchemy: Database abstraction
- sqlite3: Built-in (no install needed)

**Azure (Optional):**
- azure-identity: Authentication
- azure-storage-blob: Blob storage
- azure-storage-file-datalake: Data Lake Gen2

**CLI:**
- typer: CLI framework
- rich: Terminal formatting
- click: Command parsing

**Utils:**
- python-dotenv: Environment variables
- pyyaml: YAML parsing
- structlog: Structured logging

## Extension Points

1. **Add New Data Sources**: Update CLI and add to Makefile
2. **Custom Validations**: Extend data_quality.py
3. **New Storage Backends**: Extend ingestion.py
4. **Fabric Integration**: Implement in separate module
5. **Scheduling**: Use cron/Airflow with CLI commands

---

## Notebook Architecture Layer

**Version 1.3.0** introduces a unified notebook utilities layer that provides consistent behavior across local and Fabric environments.

### Notebook Utilities (`notebooks/lib/`)

```
notebooks/lib/
├── __init__.py                  # Package initialization
├── platform_utils.py            # Platform detection & cross-platform I/O
├── storage.py                   # StorageManager (Bronze/Silver/Gold)
├── settings.py                  # Settings singleton with YAML config
├── logging_utils.py             # Logging setup & progress tracking
└── config.py                    # Additional config helpers
```

#### Module Descriptions

**platform_utils.py** (Platform Detection)
```python
- IS_FABRIC constant (bool)
- _detect_fabric_environment()
- safe_import_mssparkutils()
- get_data_paths() → Dict[str, Path]
- copy_file(src, dst) - platform-aware copy
- list_files(path) → List[Path]
- Cross-platform path resolution
```

**storage.py** (Storage Abstraction)
```python
- StorageManager class
- read_from_bronze(table, sample_size) → DataFrame
- read_from_silver(table) → DataFrame
- write_to_silver(df, table, partition_cols) → Path
- write_to_gold(df, table) → Path
- write_validated_data(df, table, validation_result) → Path
- quarantine_data(df, table, reason) → Path
- get_storage_format() → "parquet" | "delta"
- Schema evolution support
- Partition inference
```

**settings.py** (Configuration Management)
```python
- Settings dataclass (singleton)
- Settings.load(environment) → Settings
- Auto-detection: local | fabric_dev | fabric_prod
- YAML config loading from notebook_settings.yaml
- Environment variable overrides
- Type-safe path accessors:
  - bronze_dir, silver_dir, gold_dir
  - config_dir, state_dir, reports_dir
- Data quality accessors:
  - dq_threshold, null_tolerance
  - get_dq_threshold(severity) → float
```

**logging_utils.py** (Logging & Progress)
```python
- setup_notebook_logger(name, level) → Logger
- @log_phase_start(phase_name) decorator
- ProgressTracker context manager
- Consistent JSON/text formatting
- File rotation support
```

### Notebook Configuration (`notebooks/config/`)

```
notebooks/config/
├── notebook_settings.yaml       # Main configuration file
├── data_quality/                # Per-table DQ configs
└── validation_results/          # Validation output storage
```

**notebook_settings.yaml** Structure:
```yaml
environments:           # Environment-specific settings
  local: {...}
  fabric_dev: {...}
  fabric_prod: {...}

data_quality:           # DQ thresholds and tolerances
  threshold: 85.0
  severity_levels: {...}

paths:                  # Medallion architecture paths
  bronze: data/...
  silver: data/Silver
  gold: data/Gold

pipeline:               # Pipeline behavior settings
  phases: {...}
  continue_on_error: false

storage:                # Storage format settings
  parquet_engine: pyarrow
  compression: snappy

table_overrides: {}     # Per-table customization
```

### Configuration Priority

```
┌─────────────────────────────────────┐
│ 1. Environment Variables (highest)  │
│    AIMS_DQ_THRESHOLD=90.0           │
├─────────────────────────────────────┤
│ 2. .env File Values                 │
│    LOCAL_OVERRIDE=value             │
├─────────────────────────────────────┤
│ 3. YAML Configuration               │
│    notebook_settings.yaml           │
├─────────────────────────────────────┤
│ 4. Built-in Defaults (lowest)       │
│    Hardcoded fallbacks              │
└─────────────────────────────────────┘
```

### Data Flow with Notebook Utilities

```
┌──────────────────────────────────────────────────────────────────┐
│                     Notebook Layer                                │
├──────────────────────────────────────────────────────────────────┤
│  00_Orchestration → 01_Profiling → 02_Ingestion → 03_Monitoring  │
│                           ↓                                       │
│  04_Schema_Recon → 05_Insights → 06_BI → 07_DQ_Matrix → 08_BI    │
└──────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   lib/ Utilities   │
                    ├───────────────────┤
                    │ • platform_utils  │ ← Platform Detection
                    │ • storage         │ ← StorageManager
                    │ • settings        │ ← Settings Singleton
                    │ • logging_utils   │ ← Logging Setup
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │  config/ Settings  │
                    ├───────────────────┤
                    │ notebook_settings │
                    │      .yaml        │
                    └─────────┬─────────┘
                              │
           ┌──────────────────┼──────────────────┐
           ▼                  ▼                  ▼
     ┌──────────┐      ┌──────────┐       ┌──────────┐
     │  Local   │      │  Fabric  │       │  Fabric  │
     │   Dev    │      │   Dev    │       │   Prod   │
     ├──────────┤      ├──────────┤       ├──────────┤
     │ Parquet  │      │  Delta   │       │  Delta   │
     │ 4 workers│      │ 8 workers│       │16 workers│
     │  DEBUG   │      │   INFO   │       │ WARNING  │
     └──────────┘      └──────────┘       └──────────┘
```

---

**Total Files Created**: 11 + 5 (notebook utilities)
**Lines of Code**: ~4,500+
**Test Coverage**: Ready for pytest integration
**Production Ready**: Yes (with proper .env configuration)
