# AIMS Data Platform - AI Coding Agent Instructions

## Project Overview
AIMS Data Platform is a **Bronze-to-Silver data transformation pipeline** for HS2's asset management system, featuring:
- **Incremental loading** with watermark-based state tracking
- **Data Quality validation** using Great Expectations
- **Star Schema modeling** for BI reporting (1 FACT + 5 DIM tables)
- **Dual-environment support**: Local development + Microsoft Fabric production

**Architecture Pattern**: Medallion (Bronze → Silver), with validation quarantine layer.

## Critical Architectural Decisions

### 1. Dual-Library System
```
aims_data_platform/          # Core ETL library (installed package)
├── config.py               # Environment-aware config (local vs Fabric)
├── ingestion.py            # Parquet repair + incremental loading
├── watermark_manager.py    # SQLite-based state tracking
└── cli.py                  # Typer CLI interface

dq_great_expectations/      # Separate DQ validation configs
└── generated_configs/      # YAML validation rules per table
```

**Why Separated**: DQ validation library (`fabric_data_quality`) is deployed independently as a wheel (`dq_package_dist/`) to support both local and Fabric environments without conflicting dependencies.

### 2. Environment Detection Pattern
ALL notebooks and scripts use this standard pattern:
```python
try:
    import notebookutils
    IS_FABRIC = True
    BASE_DIR = Path("/lakehouse/default/Files")
except ImportError:
    IS_FABRIC = False
    project_root = Path.cwd().parent.resolve()
    sys.path.insert(0, str(project_root))
    BASE_DIR = project_root
```
**Critical**: Never hardcode paths. Always use `BASE_DIR` for portability.

### 3. Star Schema Design (Silver Layer)
Located in `data/silver_layer/`, consists of:
- `FACT_Asset_Inventory.parquet` (100K rows, 15 columns)
- `DIM_Route.parquet` (33 routes)
- `DIM_AssetClass.parquet` (5.6K classes, self-referencing hierarchy)
- `DIM_Organisation.parquet` (28 orgs, parent-child)
- `DIM_Date.parquet` (85K dates, pre-calculated attributes)
- `DIM_Status.parquet` (4 statuses)

**Schema Documentation**: See `docs/SILVER_LAYER_STAR_SCHEMA.txt` and `docs/POWERBI_SEMANTIC_MODEL_GUIDE.txt`.

## Developer Workflows

### Essential Commands
```bash
# Setup (one-time)
conda env create -f environment.yml && conda activate aims_data_platform
pip install -e .  # Installs aims_data_platform in editable mode

# Data Operations
make repair              # Fix corrupted parquet files (Repetition level errors)
make validate            # Run GE validation on Bronze layer
python scripts/run_pipeline.py --dry-run --threshold 90.0  # Full DQ pipeline

# CLI Usage
python -m aims_data_platform.cli init               # Initialize directories
python -m aims_data_platform.cli list-watermarks    # View incremental state
python -m aims_data_platform.cli ingest aims_assets --watermark-column LASTUPDATED
```

### Notebook Execution Order
1. **01_AIMS_Data_Profiling.ipynb** - Profile Bronze parquet, generate DQ configs
2. **07_AIMS_DQ_Matrix_and_Modeling.ipynb** - Run DQ validation, build Silver layer (Star Schema)
3. **08_AIMS_Business_Intelligence.ipynb** - BI analytics on Silver layer (14 analysis sections)

**Key**: Notebook 07 ONLY processes tables that passed validation (reads `config/validation_results.json`).

### Testing & Quality
```bash
pytest tests/                    # No existing tests - TODO priority
make format                      # Black + Ruff formatting
python scripts/profile_aims_parquet.py  # Data profiling
```

## Project-Specific Conventions

### 1. Data Quality Filtering
**Pattern**: Always check validation results before Silver Layer processing:
```python
validation_results_path = BASE_DIR / "config" / "validation_results.json"
if validation_results_path.exists():
    with open(validation_results_path, 'r') as f:
        validation_data = json.load(f)
    passed_tables = [name for name, result in validation_data.items() 
                     if result.get('success', False)]
```

### 2. Parquet Loading with Memory Safety
```python
def load_parquet(name, limit=100000):
    """Always use pyarrow with batch reading for large files."""
    file_path = DATA_DIR / f"aims_{name}.parquet"
    table = pq.read_table(file_path, use_threads=True)
    return table.to_pandas() if len(table) <= limit else table.slice(0, limit).to_pandas()
```

### 3. Formal Language Standards
- **NO emojis** in code or outputs (replaced with `[MATCH]`, `[ERROR]`, `[WARNING]`)
- Use formal, instructive language (not conversational)
- Examples:
  - ❌ "Let's load the data..."
  - ✅ "Load data from Bronze layer"
  - ❌ "Oops, validation failed!"
  - ✅ "Validation check failed - quarantine table"

### 4. Error Handling Pattern
```python
# Standard pattern for all data operations
try:
    result = operation()
    logger.info(f"[SUCCESS] Operation completed: {result}")
except ValidationError as e:
    logger.error(f"[VALIDATION_ERROR] {str(e)}")
    # Quarantine data, do not halt pipeline
except Exception as e:
    logger.error(f"[ERROR] Unexpected failure: {str(e)}")
    raise  # Re-raise for pipeline orchestration
```

## Integration Points

### Microsoft Fabric Deployment
- **Notebook uploads**: All notebooks have Fabric-compatible paths (`/lakehouse/default/Files`)
- **Authentication**: Uses `notebookutils` for Fabric, Azure Identity for local
- **Scheduling**: Configure via Fabric Workspace → Schedule Refresh (daily recommended)
- **Semantic Model**: Follow `docs/POWERBI_SEMANTIC_MODEL_GUIDE.txt` for 30+ DAX measures

### Data Quality Framework
- **Validation Configs**: Auto-generated in `dq_great_expectations/generated_configs/`
- **Threshold System**: Global default (90%) overridable per table
- **Expectation Suite**: Uses `fabric_data_quality` library (NOT standard GE)
- **Quarantine Logic**: Tables failing validation excluded from Silver layer

### External Dependencies
- **PyArrow**: Required for parquet repair (handles schema mismatches)
- **FastParquet**: Alternative engine, use `PARQUET_ENGINE=fastparquet` in `.env`
- **Great Expectations**: v0.18+ (compatibility issue with v1.x)
- **Typer + Rich**: CLI framework with colored output

## Known Issues & Workarounds

1. **"Repetition level histogram size mismatch" error**
   - **Cause**: Legacy parquet files with schema drift
   - **Fix**: `python -m aims_data_platform.cli repair`

2. **Missing `dq_framework` import**
   - **Cause**: `fabric_data_quality` wheel not installed
   - **Fix**: `pip install dq_great_expectations/dq_package_dist/fabric_data_quality-1.1.0-py3-none-any.whl`

3. **Watermark database locked**
   - **Cause**: Concurrent pipeline runs
   - **Fix**: Single-instance execution, use `--workers 1` flag

4. **Hardcoded paths in old notebooks**
   - **Legacy Issue**: Some notebooks pre-date BASE_DIR pattern
   - **Action**: Always refactor to use `BASE_DIR` when editing

## Documentation References

- **Start Here**: `docs/START_HERE.md` - Quickstart guide
- **Architecture**: `docs/CRITICAL_ANALYSIS.md` - Technical debt inventory
- **Silver Layer**: `docs/SILVER_LAYER_GUIDE.md` - Star schema details
- **Power BI**: `docs/POWERBI_SEMANTIC_MODEL_GUIDE.txt` - DAX formulas + relationships
- **Fabric Migration**: `docs/FABRIC_MIGRATION_GUIDE.md` - Deployment checklist
- **Enhancements**: `docs/ENHANCEMENT_SUMMARY_DEC2025.md` - Recent changes (emoji removal, DQ filtering, 5 new BI sections)

## Code Generation Guidelines

1. **Always** use the environment detection pattern for new notebooks
2. **Always** implement validation filtering before Silver layer processing
3. **Always** use formal language in print statements and logs
4. **Always** handle parquet errors with repair logic
5. **Never** use absolute paths - leverage `BASE_DIR`
6. **Never** skip data quality checks - validate then transform
7. **Prefer** pyarrow for large file operations (memory-safe batch reading)
8. **Document** all DAX measures with business context (see Notebook 08 examples)

## Quick Context Lookup

- **Main entry point**: `aims_data_platform/cli.py` (Typer CLI)
- **Configuration**: `aims_data_platform/config.py` + `.env` file
- **Incremental loading**: `aims_data_platform/watermark_manager.py` (SQLite state)
- **Data validation**: `scripts/run_pipeline.py` (orchestrator)
- **Star schema generation**: `notebooks/07_AIMS_DQ_Matrix_and_Modeling.ipynb` (Cell 8+)
- **BI analytics**: `notebooks/08_AIMS_Business_Intelligence.ipynb` (14 sections)
- **Package metadata**: `setup.py` + `pyproject.toml` (version 1.1.0)

---

**Last Updated**: December 2025  
**Maintainer**: HS2 Data Team  
**Status**: Production (with identified technical debt - see CRITICAL_ANALYSIS.md)
