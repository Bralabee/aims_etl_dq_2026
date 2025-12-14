# AIMS Data Platform - Orchestration Guide

**Version:** 1.2.0  
**Date:** 10 December 2025  
**Status:** Production Ready

## 📋 Overview

This guide explains how to orchestrate the AIMS Data Quality and ETL platform using three approaches:

1. **Orchestration Notebook** - Single notebook execution (`00_AIMS_Orchestration.ipynb`)
2. **Makefile Automation** - Command-line automation targets
3. **Manual Notebook Execution** - Run individual notebooks as needed

---

## 🚀 Quick Start

### Option 1: Run Complete Pipeline (Makefile)

```bash
# Complete end-to-end pipeline (DQ + Data)
make pipeline

# Or run specific pipelines
make dq-pipeline      # Data Quality only
make data-pipeline    # ETL only
```

### Option 2: Run Orchestration Notebook

```bash
# Execute orchestration notebook
make run-orchestration

# Or manually
jupyter nbconvert --execute --to notebook --inplace notebooks/00_AIMS_Orchestration.ipynb
```

### Option 3: Run Individual Operations

```bash
# Data Quality operations
make profile                # Generate DQ configs
make adjust-thresholds      # Adjust thresholds to 95%
make validate-dq           # Run validation

# Data operations
make repair                 # Repair parquet files
make validate              # Validate sources
make ingest-all            # Ingest Bronze → Silver
```

---

## 📓 Orchestration Notebook

### Overview

**File:** `notebooks/00_AIMS_Orchestration.ipynb`

The orchestration notebook provides a **single-click solution** to run the entire AIMS pipeline with:

- ✅ **Environment detection** (Fabric vs Local)
- ✅ **Configurable pipeline** (enable/disable phases)
- ✅ **Progress tracking** (real-time status updates)
- ✅ **Error handling** (continue on error option)
- ✅ **Execution logging** (JSON logs with metrics)
- ✅ **Summary reporting** (success rates, timing)

### Configuration

Modify the `PIPELINE_CONFIG` cell to customize execution:

```python
PIPELINE_CONFIG = {
    "run_profiling": True,          # Phase 1: Generate DQ configs
    "run_ingestion": True,          # Phase 2: Bronze → Silver
    "run_monitoring": True,         # Phase 3: DQ monitoring
    "run_dq_modeling": True,        # Phase 4: Advanced modeling
    "run_bi_analytics": True,       # Phase 5: BI analytics
    "force_reprocess": False,       # Force reprocessing
    "dq_threshold": 85.0,          # Global DQ threshold
    "max_workers": 4,              # Parallel workers
}
```

### Execution Phases

| Phase | Notebook | Description | Duration |
|-------|----------|-------------|----------|
| 1 | `01_AIMS_Data_Profiling.ipynb` | Profile 68 Bronze tables, generate DQ configs | ~5-10 min |
| 2 | `02_AIMS_Data_Ingestion.ipynb` | Validate Bronze, ingest to Silver layer | ~10-15 min |
| 3 | `03_AIMS_Monitoring.ipynb` | Generate DQ dashboards and reports | ~2-5 min |
| 4 | `07_AIMS_DQ_Matrix_and_Modeling.ipynb` | Advanced DQ modeling (optional) | ~5-10 min |
| 5 | `08_AIMS_Business_Intelligence.ipynb` | BI analytics (optional) | ~5-10 min |

### Output

The orchestration notebook generates:

- **Execution logs:** `config/validation_results/orchestration_log_YYYYMMDD_HHMMSS.json`
- **Validation results:** `config/validation_results/validation_results.json`
- **DQ configs:** `config/data_quality/*.yml` (68 files)
- **Console output:** Real-time progress and summaries

---

## 🛠️ Makefile Commands

### Complete Reference

#### Setup & Installation
```bash
make setup          # Setup conda environment and dependencies
make init           # Initialize the data platform
```

#### Data Quality Operations
```bash
make profile                # Profile Bronze layer & generate DQ configs
make adjust-thresholds      # Adjust DQ thresholds to 95%
make validate-dq           # Run DQ validation pipeline
make dq-pipeline           # Full DQ pipeline (profile → adjust → validate)
```

#### Data Operations
```bash
make repair          # Repair corrupted parquet files
make validate        # Validate source files (schema check)
make ingest-all      # Ingest all data sources
make ingest-assets   # Ingest aims_assets only
make ingest-attrs    # Ingest aims_attributes only
make data-pipeline   # Full data pipeline (init → repair → validate → ingest)
```

#### Notebook Operations
```bash
make run-orchestration   # Run orchestration notebook (00_AIMS_Orchestration)
make run-notebooks       # Run all AIMS notebooks sequentially (01-08)
```

#### Monitoring
```bash
make watermarks      # List all watermarks
make history         # Show load history (last 20 loads)
```

#### Pipelines
```bash
make pipeline        # Complete end-to-end (DQ + Data)
```

#### Maintenance
```bash
make clean           # Clean generated files
make test            # Run pytest tests
make format          # Format code (black + ruff)
```

### Pipeline Workflows

#### Workflow 1: Fresh Start (Complete Pipeline)
```bash
# Step 1: Setup environment
make setup

# Step 2: Initialize platform
make init

# Step 3: Run complete pipeline
make pipeline
```

#### Workflow 2: DQ Updates Only
```bash
# Re-profile Bronze layer
make profile

# Adjust thresholds
make adjust-thresholds

# Re-validate
make validate-dq
```

#### Workflow 3: Data Ingestion Only
```bash
# Validate and ingest
make validate
make ingest-all
```

#### Workflow 4: Notebook Execution
```bash
# Run orchestration notebook
make run-orchestration

# Or run all notebooks individually
make run-notebooks
```

---

## 📊 Individual Notebooks

### Manual Execution

To run individual notebooks manually in Jupyter:

1. **01_AIMS_Data_Profiling.ipynb**
   - Purpose: Profile Bronze tables and generate DQ configs
   - Runtime: ~5-10 minutes
   - Output: 68 YAML configs in `config/data_quality/`

2. **02_AIMS_Data_Ingestion.ipynb**
   - Purpose: Validate Bronze and ingest to Silver
   - Runtime: ~10-15 minutes
   - Output: Silver parquet files with DQ filtering

3. **03_AIMS_Monitoring.ipynb**
   - Purpose: Generate DQ dashboards
   - Runtime: ~2-5 minutes
   - Output: Interactive plotly visualizations

4. **04_AIMS_Schema_Reconciliation.ipynb**
   - Purpose: Schema drift detection
   - Runtime: ~5 minutes
   - Output: Schema comparison reports

5. **05_AIMS_Silver_Data_Enhancement.ipynb**
   - Purpose: Silver → Gold transformations
   - Runtime: ~10 minutes
   - Output: Enhanced Gold layer

6. **06_AIMS_Data_Quality_Insights.ipynb**
   - Purpose: DQ analysis and insights
   - Runtime: ~5 minutes
   - Output: Quality trend analysis

7. **07_AIMS_DQ_Matrix_and_Modeling.ipynb**
   - Purpose: Advanced DQ modeling
   - Runtime: ~5-10 minutes
   - Output: DQ matrices and predictions

8. **08_AIMS_Business_Intelligence.ipynb**
   - Purpose: BI analytics and reporting
   - Runtime: ~5-10 minutes
   - Output: Business insights and KPIs

### Notebook Features

All notebooks include:
- ✅ **Dual functionality** - Works in both Fabric and Local environments
- ✅ **Environment detection** - Automatic path configuration
- ✅ **Error handling** - Graceful error recovery
- ✅ **Progress indicators** - Real-time status updates
- ✅ **Output validation** - Verify results at each step

---

## 🔧 CLI Alternative

### Using Python Scripts Directly

```bash
# Profiling
python scripts/profile_aims_parquet.py

# Threshold adjustment
python scripts/adjust_thresholds.py --threshold 95

# Validation
python scripts/run_validation_simple.py

# CLI commands
python -m aims_data_platform.cli init
python -m aims_data_platform.cli repair
python -m aims_data_platform.cli validate-source
python -m aims_data_platform.cli ingest aims_assets
python -m aims_data_platform.cli ingest aims_attributes
```

### Script Locations

| Script | Purpose | Location |
|--------|---------|----------|
| `profile_aims_parquet.py` | Generate DQ configs | `scripts/` |
| `adjust_thresholds.py` | Adjust thresholds | `scripts/` |
| `run_validation_simple.py` | Run validation | `scripts/` |
| `use_fabric_dq_directly.py` | Test DQ framework | Root |

---

## 📈 Monitoring & Results

### Validation Results

**Location:** `config/validation_results/validation_results.json`

```json
{
  "timestamp": "2025-12-10T10:30:00",
  "threshold": 95.0,
  "summary": {
    "total": 68,
    "passed": 55,
    "failed": 13,
    "skipped": 0,
    "errors": 0
  },
  "files": {
    "table_name": {
      "overall_success": true,
      "success_percentage": 96.5,
      "statistics": {...}
    }
  }
}
```

### Orchestration Logs

**Location:** `config/validation_results/orchestration_log_YYYYMMDD_HHMMSS.json`

```json
{
  "start_time": "2025-12-10T10:00:00",
  "end_time": "2025-12-10T10:45:00",
  "total_duration_seconds": 2700,
  "environment": "Local",
  "phases": [
    {
      "phase": "profiling",
      "status": "success",
      "duration_seconds": 600,
      "files_profiled": 68,
      "configs_generated": 68
    },
    {
      "phase": "validation_ingestion",
      "status": "success",
      "duration_seconds": 900,
      "validation_summary": {...}
    }
  ]
}
```

### DQ Metrics

Key metrics tracked:

- **Quality Score:** Average percentage of passed expectations
- **Pass Rate:** Percentage of tables passing threshold
- **Completeness:** Null value percentage
- **Validity:** Data type and format compliance
- **Consistency:** Cross-table relationship integrity

---

## 🎯 Best Practices

### 1. Environment Setup

```bash
# Always activate environment first
conda activate aims_data_platform

# Verify environment
which python
python --version  # Should be 3.11.14
```

### 2. Sequential Execution

Follow the recommended execution order:

1. **Profile** → 2. **Adjust** → 3. **Validate** → 4. **Ingest**

```bash
# Correct order
make profile
make adjust-thresholds
make validate-dq
make ingest-all

# Or use pipeline shortcut
make pipeline
```

### 3. Threshold Management

- **Initial profiling:** Use 100% threshold (strict)
- **Production:** Adjust to 95% threshold (practical)
- **Re-profiling:** Run after significant data changes

```bash
# Adjust to 95%
make adjust-thresholds

# Adjust to custom threshold
python scripts/adjust_thresholds.py --threshold 90
```

### 4. Error Handling

```python
# In orchestration notebook, enable continue_on_error
PIPELINE_CONFIG["continue_on_error"] = True

# In CLI, capture errors
python scripts/run_validation_simple.py 2>&1 | tee validation.log
```

### 5. Performance Optimization

```python
# Increase parallel workers for large datasets
PIPELINE_CONFIG["max_workers"] = 8  # Default is 4

# Use sampling for profiling
SAMPLE_SIZE = 10000  # Profile only first 10k rows
```

---

## 🐛 Troubleshooting

### Common Issues

#### Issue 1: Notebook Cell Hanging

**Symptom:** Cell execution doesn't complete

**Solution:**
```bash
# Use CLI alternative
make validate-dq

# Or run via papermill
papermill notebooks/01_AIMS_Data_Profiling.ipynb output.ipynb
```

#### Issue 2: Import Errors

**Symptom:** `ModuleNotFoundError: No module named 'dq_framework'`

**Solution:**
```bash
# Reinstall package
pip install -e .

# Or add to path
export PYTHONPATH="${PYTHONPATH}:/home/sanmi/Documents/HS2/HS2_PROJECTS_2025/1_AIMS_LOCAL_2026"
```

#### Issue 3: Parquet File Corruption

**Symptom:** `pyarrow.lib.ArrowInvalid`

**Solution:**
```bash
# Repair corrupted files
make repair

# Or manually
python -m aims_data_platform.cli repair
```

#### Issue 4: Threshold Too Strict

**Symptom:** Most tables failing validation (100% threshold)

**Solution:**
```bash
# Adjust to 95%
make adjust-thresholds

# Re-validate
make validate-dq
```

#### Issue 5: Memory Issues

**Symptom:** `MemoryError` during profiling

**Solution:**
```python
# Reduce sample size in profiling notebook
SAMPLE_SIZE = 5000  # Smaller sample

# Or reduce workers
PIPELINE_CONFIG["max_workers"] = 2
```

---

## 📚 Additional Resources

### Documentation

- **QUICK_START_GUIDE.md** - Getting started (15 pages)
- **TESTING_DOCUMENTATION.md** - Testing guide (30 pages)
- **CI_CD_DOCUMENTATION.md** - CI/CD setup (25 pages)
- **COMPREHENSIVE_PROJECT_DOCUMENTATION.md** - Complete reference (45 pages)
- **README.md** - Project overview with badges

### Scripts

- **scripts/profile_aims_parquet.py** - DQ profiling
- **scripts/adjust_thresholds.py** - Threshold management
- **scripts/run_validation_simple.py** - Validation execution
- **scripts/generate_documentation.py** - Docs generation

### Configuration Files

- **.azure/plan.copilot.md** - Deployment plan
- **azure-pipelines.yml** - Azure DevOps CI/CD
- **.github/workflows/ci-cd.yml** - GitHub Actions
- **config/data_quality/*.yml** - 68 DQ validation configs

---

## 📊 Performance Benchmarks

### Typical Execution Times

| Operation | Local (16 cores) | Fabric |
|-----------|------------------|--------|
| Profiling (68 tables) | 5-10 min | 3-5 min |
| Validation | 10-15 min | 5-8 min |
| Ingestion (Bronze → Silver) | 15-20 min | 8-12 min |
| Monitoring | 2-5 min | 1-3 min |
| **Complete Pipeline** | **30-45 min** | **15-25 min** |

### Optimization Tips

1. **Increase parallelization:** `max_workers = 8` (for 16+ core systems)
2. **Use sampling:** Profile subset of data for large tables
3. **Skip optional phases:** Disable DQ modeling and BI if not needed
4. **Batch ingestion:** Ingest specific tables only (`make ingest-assets`)

---

## 🎉 Success Criteria

### Pipeline Success

✅ **Profiling Complete**
- 68 YAML configs generated
- All Bronze tables profiled
- No errors in profiling log

✅ **Validation Passing**
- Pass rate > 80% (55/68 tables)
- Quality score > 85%
- validation_results.json generated

✅ **Ingestion Complete**
- Silver parquet files created
- Quarantine files for failed records
- Load history updated

✅ **Monitoring Active**
- Dashboards generated
- Metrics calculated
- Trends visualized

### Quality Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Pass Rate | > 80% | 80.9% ✅ |
| Quality Score | > 85% | 87.3% ✅ |
| Completeness | > 95% | 96.8% ✅ |
| Configs Generated | 68 | 68 ✅ |
| Tables Ingested | 55+ | 55 ✅ |

---

## 📞 Support

For issues or questions:

1. Check **Troubleshooting** section above
2. Review **COMPREHENSIVE_PROJECT_DOCUMENTATION.md**
3. Check execution logs in `config/validation_results/`
4. Run diagnostics: `make test`

---

**Last Updated:** 10 December 2025  
**Version:** 1.2.0  
**Status:** ✅ Production Ready
