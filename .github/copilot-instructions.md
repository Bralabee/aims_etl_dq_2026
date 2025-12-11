# AIMS Data Platform - AI Coding Agent Instructions

## Project Overview
AIMS Data Platform is a **dual-mode (CLI + Notebooks) data quality platform** for AIMS data ingestion with Microsoft Fabric compatibility. The system validates 68 Bronze Layer Parquet tables using Great Expectations, achieving 80.9% pass rate (55/68 tables) with strict DQ rules averaging 97.3% quality score.

**Key Capabilities**: Automated profiling, parallel validation (8 workers), incremental loading, threshold management, Star Schema transformation (Bronze → Silver), and seamless Fabric/local switching.

## Critical Architectural Decisions

### 1. Split-Brain Library Pattern (MOST IMPORTANT)
```
../2_DATA_QUALITY_LIBRARY/   # Shared validation engine (pip installed)
└── dq_framework/           # DataLoader, DataQualityValidator, BatchProfiler
    ├── __init__.py
    ├── loader.py
    ├── validator.py
    ├── profiler.py
    └── batch_profiler.py

1_AIMS_LOCAL_2026/          # Application layer (thin orchestration)
└── aims_data_platform/     # AIMS-specific logic
    ├── __init__.py         # Imports from dq_framework
    ├── config.py           # Path configuration
    ├── fabric_config.py    # MS Fabric integration
    └── schema_reconciliation.py
```

**CRITICAL RULE**: 
- ✅ **DO**: Import validation logic from `dq_framework` 
- ❌ **NEVER**: Reimplement validation logic in `aims_data_platform`
- ✅ **DO**: Extend `dq_framework` classes if needed
- ❌ **NEVER**: Create duplicate DataLoader/Validator classes

**Installation**: `cd ../2_DATA_QUALITY_LIBRARY && pip install -e .`

### 2. Dual Execution Mode (Scripts + Notebooks)
```
scripts/
├── run_pipeline.py          # Headless DQ validation (CI/CD)
├── profile_aims_parquet.py  # Generate 68 YAML configs
└── adjust_thresholds.py     # Batch threshold adjustment

notebooks/
├── 00_AIMS_Orchestration.ipynb     # Mirrors run_pipeline.py
├── 01_AIMS_Data_Profiling.ipynb    # Mirrors profile_aims_parquet.py
└── 04-08_*.ipynb                    # Analysis notebooks
```

**CRITICAL SYNC RULE**: Scripts and notebooks share IDENTICAL validation logic via `dq_framework`. When modifying validation:
1. Update `dq_framework` library (if core logic changes)
2. Mirror changes in both script AND notebook
3. Test both execution paths

### 3. Environment Detection Pattern (100% Consistent)
```python
# ALWAYS use this pattern at the top of notebooks/scripts
import os
os.environ["GX_ANALYTICS_ENABLED"] = "False"  # CRITICAL: Prevents 60s+ import hangs

try:
    from notebookutils import mssparkutils
    IS_FABRIC = True
    BASE_DIR = Path("/lakehouse/default/Files")
except ImportError:
    IS_FABRIC = False
    BASE_DIR = Path("..")  # Relative to notebooks/
```

**Performance Fix**: Disabling GX analytics reduces import time from 60+ seconds to ~2.5 seconds. ALWAYS set this BEFORE importing Great Expectations.

## Developer Workflows

### Essential Commands
```bash
# Setup (one-time)
conda env create -f environment.yml
conda activate aims_data_platform
cd ../2_DATA_QUALITY_LIBRARY && pip install -e .  # Install dq_framework
cd ../1_AIMS_LOCAL_2026 && pip install -e .       # Install aims_data_platform

# Run Full Pipeline (Scripts - Recommended for CI/CD)
python scripts/run_pipeline.py --force --workers 8
python scripts/run_pipeline.py --dry-run --threshold 95.0

# Run Full Pipeline (Notebooks - Interactive)
# Open notebooks/00_AIMS_Orchestration.ipynb and run all cells

# Generate DQ Configs (One-Time Setup)
python scripts/profile_aims_parquet.py
# Output: 68 YAML files in config/data_quality/

# Adjust Thresholds Globally
python scripts/adjust_thresholds.py --threshold 95.0 --dry-run
python scripts/adjust_thresholds.py --threshold 95.0  # Apply changes

# Testing
pytest tests/ -v  # 15 tests (profiling, validation, config loading)
```

### Notebook Execution Order
1. **01_AIMS_Data_Profiling.ipynb** - Generate DQ configs (run once)
2. **00_AIMS_Orchestration.ipynb** - Full pipeline validation
3. **04_AIMS_Schema_Reconciliation.ipynb** - Schema analysis
4. **05_AIMS_Data_Insights.ipynb** - Data statistics
5. **06-08_*.ipynb** - Business intelligence analysis

**Performance Tip**: All notebooks now include `os.environ["GX_ANALYTICS_ENABLED"] = "False"` in first cell.

## Project-Specific Conventions

### 1. Data Quality Configuration (YAML)
Each table has a config in `config/data_quality/{table_name}.yaml`:
```yaml
table_name: aims_assets
expectations:
  - type: expect_column_values_to_not_be_null
    column: AssetID
    threshold: 100.0  # Pass if success_percent >= threshold
  - type: expect_column_values_to_be_in_set
    column: AssetClass
    value_set: ['Bridge', 'Tunnel', 'Track']
    threshold: 95.0
```

**Threshold Logic**: `(success_percent >= threshold) OR (element_count == 0)`

### 2. Parallel Validation Pattern
```python
from dq_framework import DataLoader, DataQualityValidator
from concurrent.futures import ThreadPoolExecutor

def validate_file(file_path, config_path):
    loader = DataLoader()
    validator = DataQualityValidator()
    df = loader.load_data(file_path)
    return validator.validate(df, config_path)

with ThreadPoolExecutor(max_workers=8) as executor:
    results = executor.map(validate_file, files, configs)
```

### 3. Import Performance Fix (ALWAYS Required)
```python
# FIRST LINE of any notebook/script using Great Expectations
import os
os.environ["GX_ANALYTICS_ENABLED"] = "False"

# Then safe to import
from dq_framework import DataQualityValidator
import great_expectations as gx
```

**Why**: GX analytics phone-home causes 60+ second hangs. This disables telemetry.

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

## Common Pitfalls & Solutions

### 1. Great Expectations Import Hangs (60+ seconds)
**Symptom**: Notebook/script freezes during import  
**Cause**: GX analytics telemetry enabled  
**Fix**: Add `os.environ["GX_ANALYTICS_ENABLED"] = "False"` BEFORE all imports

### 2. Module Not Found: dq_framework
**Symptom**: `ImportError: No module named 'dq_framework'`  
**Cause**: Shared library not installed  
**Fix**: `cd ../2_DATA_QUALITY_LIBRARY && pip install -e .`

### 3. Notebook/Script Divergence
**Symptom**: Same validation gives different results  
**Cause**: Logic duplicated instead of shared  
**Fix**: Both MUST import from `dq_framework`, never reimplement

### 4. Path Configuration Errors (FileNotFoundError)
**Symptom**: `FileNotFoundError: data/Samples_LH_Bronze_Aims_26_parquet`  
**Cause**: `.env` paths are relative or incorrect  
**Fix**: Ensure `.env` uses absolute paths:
```bash
BASE_DIR=/home/sanmi/Documents/HS2/HS2_PROJECTS_2025/1_AIMS_LOCAL_2026
DATA_PATH=data/Samples_LH_Bronze_Aims_26_parquet
```

### 5. Validation Fails with "Empty DataFrame"
**Symptom**: All tables marked as failed  
**Cause**: Configs reference wrong column names  
**Fix**: Regenerate configs: `python scripts/profile_aims_parquet.py`

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

## Key Design Decisions (The "Why")

1. **Why separate `dq_framework` library?**  
   Reusable across multiple projects; `aims_data_platform` is AIMS-specific orchestration.

2. **Why dual mode (scripts + notebooks)?**  
   Data engineers prefer interactive notebooks; DevOps/CI prefers headless scripts.

3. **Why 68 separate YAML configs?**  
   Each table has unique schema and DQ rules. Auto-generated via profiling for maintainability.

4. **Why parallel execution (8 workers)?**  
   68 tables × 2s/table = 136s sequential → 20s parallel. Time-critical for CI/CD.

5. **Why disable GX analytics?**  
   Telemetry causes 60s+ import delays. Disabling reduces to 2.5s with zero functionality loss.

6. **Why threshold-based validation?**  
   Real-world data has imperfections. Strict 100% thresholds would fail most tables unrealistically.

## Star Schema Transformation (Bronze → Silver)

### Architecture: Medallion Pattern
```
Bronze Layer (68 tables)  →  Validation  →  Silver Layer (Star Schema)
├── aims_assets.parquet                    ├── FACT_Asset_Inventory
├── aims_assetclass.parquet                ├── DIM_Route
├── aims_route.parquet                     ├── DIM_AssetClass
└── ...                                    ├── DIM_Organisation
                                          ├── DIM_Date
                                          └── DIM_Status
```

### Implementation (Notebook 07, Cell 8+)

**Critical Pattern**: Only process tables that passed DQ validation:
```python
# Step 1: Load validation results
validation_results_path = BASE_DIR / "config" / "validation_results.json"
with open(validation_results_path, 'r') as f:
    validation_data = json.load(f)

# Step 2: Filter passed tables
passed_tables = [name for name, result in validation_data.items() 
                 if result.get('success', False)]

# Step 3: Load ONLY validated Bronze tables
for table_name in passed_tables:
    df = pd.read_parquet(BRONZE_DIR / f"{table_name}.parquet")
    # Process...
```

### Star Schema Details

**FACT_Asset_Inventory** (Central table, ~100K rows):
```python
fact_columns = [
    'AssetID',           # Primary key (SK_Asset)
    'RouteID',          # FK to DIM_Route
    'AssetClassID',     # FK to DIM_AssetClass
    'OrganisationID',   # FK to DIM_Organisation
    'StatusID',         # FK to DIM_Status
    'DateKey',          # FK to DIM_Date (YYYYMMDD format)
    'Latitude',         # Geospatial
    'Longitude',        # Geospatial
    'AssetValue',       # Measure
    'LastUpdated'       # Audit column
]
```

**Dimension Tables**:
1. **DIM_Route** (33 routes): Linear referencing, start/end chainage
2. **DIM_AssetClass** (5.6K classes): Self-referencing hierarchy (ParentClassID)
3. **DIM_Organisation** (28 orgs): Parent-child relationships
4. **DIM_Date** (85K dates): Pre-calculated attributes (Quarter, FY, WeekOfYear)
5. **DIM_Status** (4 statuses): Active, Inactive, Decommissioned, Planned

**Key Relationships**:
```
FACT_Asset_Inventory.RouteID → DIM_Route.RouteID (Many-to-One)
FACT_Asset_Inventory.AssetClassID → DIM_AssetClass.ClassID (Many-to-One)
DIM_AssetClass.ParentClassID → DIM_AssetClass.ClassID (Self-referencing)
```

**Output Location**:
- Local: `data/silver_layer/*.parquet`
- Fabric: `/lakehouse/default/Tables/silver_layer/`

### Power BI Integration

**DAX Measures** (30+ implemented in Notebook 08):
```dax
Total Assets = COUNTROWS(FACT_Asset_Inventory)
Asset Value = SUM(FACT_Asset_Inventory[AssetValue])
Critical Assets = CALCULATE([Total Assets], DIM_Status[Status] = "Critical")
YoY Growth % = DIVIDE([Total Assets] - [Total Assets PY], [Total Assets PY])
```

**Semantic Model Setup**:
1. Import Silver Layer tables into Power BI
2. Create relationships (use `RouteID`, `AssetClassID`, etc. as keys)
3. Mark `DIM_Date[DateKey]` as Date table
4. Create measure groups for KPIs, Trends, and Drill-throughs
5. Configure RLS (Row-Level Security) by Organisation if needed

**Reference**: See `docs/POWERBI_SEMANTIC_MODEL_GUIDE.txt` for complete DAX formulas.

## CI/CD Integration

### GitHub Actions (`.github/workflows/ci-cd.yml`)

**Pipeline Stages**:
1. **Build DQ Library** → Install `dq_framework`, run tests, build wheel
2. **Build AIMS Platform** → Install `aims_data_platform`, run tests
3. **DQ Validation** → Execute `run_pipeline.py --dry-run`, assert 80%+ pass rate
4. **Publish Artifacts** → Upload wheels, test results, coverage reports

**Key Configuration**:
```yaml
on:
  push:
    branches: [master, develop]
    paths:
      - '1_AIMS_LOCAL_2026/**'
      - '2_DATA_QUALITY_LIBRARY/**'

jobs:
  build-dq-library:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: |
          cd 2_DATA_QUALITY_LIBRARY
          pip install -e .[dev]
          pytest tests/ --cov=dq_framework
```

**Quality Gates**:
- ✅ All tests pass (15/15)
- ✅ DQ validation ≥ 80% pass rate
- ✅ Code coverage ≥ 70%
- ✅ No critical security vulnerabilities (Bandit scan)

**Deployment Triggers**:
- **Push to `master`** → Run full pipeline + deploy to staging
- **Pull request** → Run tests only (no deployment)
- **Manual dispatch** → Run with custom parameters (e.g., `--threshold 95.0`)

### Azure DevOps (`azure-pipelines.yml`)

**Multi-stage Pipeline**:
```yaml
stages:
  - stage: Build
    jobs:
      - job: BuildDQLibrary
      - job: BuildAIMSPlatform
  
  - stage: Test
    jobs:
      - job: UnitTests
      - job: IntegrationTests
      - job: DQValidation
  
  - stage: Deploy
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/master'))
    jobs:
      - job: DeployToFabric
```

**Artifacts Published**:
- `dq_framework-1.2.0-py3-none-any.whl`
- `aims_data_platform-1.0.2-py3-none-any.whl`
- Test results (JUnit XML)
- Code coverage reports (Cobertura)
- DQ validation logs (JSON)

**Environment Variables**:
```yaml
variables:
  AZURE_CLIENT_ID: $(AZURE_CLIENT_ID_SECRET)
  AZURE_TENANT_ID: $(AZURE_TENANT_ID)
  BASE_DIR: $(Build.SourcesDirectory)/1_AIMS_LOCAL_2026
```

**Schedule**: Daily at 2 AM UTC (cron: `0 2 * * *`)

## Testing Strategy

### Test Structure (15 tests)
```
tests/
├── test_profiler.py           # Data profiling (5 tests)
│   ├── test_profile_generation
│   ├── test_yaml_output
│   └── test_threshold_defaults
├── test_validator.py          # DQ validation (7 tests)
│   ├── test_null_check
│   ├── test_type_validation
│   ├── test_threshold_logic
│   └── test_parallel_execution
└── test_profiling_integration.py  # End-to-end (3 tests)
    ├── test_full_pipeline
    ├── test_config_generation
    └── test_validation_pass_rate
```

### Running Tests

**Unit Tests** (Fast, isolated):
```bash
pytest tests/test_profiler.py -v
pytest tests/test_validator.py -v
```

**Integration Tests** (Slower, uses real data):
```bash
pytest tests/test_profiling_integration.py -v --runslow
```

**Coverage Report**:
```bash
pytest tests/ --cov=aims_data_platform --cov=dq_framework --cov-report=html
# Output: htmlcov/index.html
```

### Test Patterns

**1. Mocking External Dependencies**:
```python
@patch('dq_framework.loader.DataLoader.load_data')
def test_validation_with_mock(mock_load):
    mock_load.return_value = pd.DataFrame({'col1': [1, 2, 3]})
    validator = DataQualityValidator()
    result = validator.validate(mock_load(), config_path)
    assert result['success'] == True
```

**2. Parameterized Tests** (Multiple scenarios):
```python
@pytest.mark.parametrize("threshold,expected", [
    (100.0, False),  # Strict threshold fails
    (95.0, True),    # Relaxed threshold passes
    (0.0, True)      # Zero threshold always passes
])
def test_threshold_logic(threshold, expected):
    result = validate_with_threshold(df, threshold)
    assert result == expected
```

**3. Fixtures for Reusable Data**:
```python
@pytest.fixture
def sample_dataframe():
    return pd.DataFrame({
        'AssetID': [1, 2, 3],
        'Status': ['Active', 'Active', None]
    })

def test_null_handling(sample_dataframe):
    result = check_nulls(sample_dataframe, 'Status')
    assert result['null_count'] == 1
```

### Quality Metrics
- **Current Coverage**: 78% (aims_data_platform), 85% (dq_framework)
- **Target Coverage**: 80%+
- **Test Execution Time**: ~12s (unit), ~45s (integration)
- **CI Run Time**: ~3m (GitHub Actions), ~5m (Azure DevOps)

### Adding New Tests

**When to Add Tests**:
1. New validation expectation types
2. New data transformation logic (Star Schema)
3. Bug fixes (regression tests)
4. Performance optimizations (benchmark tests)

**Test Naming Convention**:
```python
def test_<component>_<scenario>_<expected_outcome>():
    # Example: test_validator_null_check_passes_with_threshold()
    pass
```

## Documentation Reference

- **[README.md](../README.md)** - Project overview, quick start (327 lines)
- **[QUICK_START_GUIDE.md](../QUICK_START_GUIDE.md)** - 5-minute setup
- **[docs/COMPLETE_IMPLEMENTATION_SUMMARY.md](../docs/COMPLETE_IMPLEMENTATION_SUMMARY.md)** - Full technical reference (37 pages)
- **[docs/END_TO_END_TESTING_REPORT.md](../docs/END_TO_END_TESTING_REPORT.md)** - Validation results
- **[environment.yml](../environment.yml)** - Conda environment specification

## Quick File Locator

| Component | Location |
|-----------|----------|
| Main pipeline script | `scripts/run_pipeline.py` |
| Main pipeline notebook | `notebooks/00_AIMS_Orchestration.ipynb` |
| Validation engine | `../2_DATA_QUALITY_LIBRARY/dq_framework/` |
| DQ configs (68 files) | `config/data_quality/*.yaml` |
| Environment config | `.env` |
| Test suite | `tests/` (15 tests) |
| Package metadata | `pyproject.toml` (v1.0.2) |

---

**Last Updated**: December 2025 | **Version**: 1.2.0 | **Status**: Production Ready (90%)

**Last Updated**: December 2025  
**Maintainer**: HS2 Data Team  
**Status**: Production (with identified technical debt - see CRITICAL_ANALYSIS.md)
