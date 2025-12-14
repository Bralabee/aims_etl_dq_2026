# AIMS Data Quality Pipeline - Orchestration Guide

This guide details how to orchestrate, run, and monitor the AIMS Data Quality Pipeline. It covers both manual execution via Jupyter Notebooks and automated execution via the CLI.

## 💻 CLI Operations

The pipeline can be run from the command line using `scripts/run_pipeline.py`. This provides a robust way to execute the pipeline in production environments or CI/CD systems.

### Basic Usage

```bash
# Run the full pipeline (Profile -> Ingest -> Monitor)
python scripts/run_pipeline.py run-all

# Run specific steps
python scripts/run_pipeline.py profile
python scripts/run_pipeline.py ingest
python scripts/run_pipeline.py monitor
```

### Advanced Options

The CLI supports several arguments to control execution behavior:

| Argument | Description | Default | Example |
|----------|-------------|---------|---------|
| `--force` | Ignore watermarks and reprocess all files | `False` | `python scripts/run_pipeline.py ingest --force` |
| `--dry-run` | Simulate execution without updating state or moving files | `False` | `python scripts/run_pipeline.py ingest --dry-run` |
| `--workers` | Number of parallel workers for processing | `4` | `python scripts/run_pipeline.py profile --workers 8` |
| `--threshold` | Override the global quality score threshold (0-100) | `None` | `python scripts/run_pipeline.py ingest --threshold 95.0` |

### Examples

**1. Reprocess all files with higher parallelism:**
```bash
python scripts/run_pipeline.py ingest --force --workers 8
```

**2. Test a new threshold without changing state:**
```bash
python scripts/run_pipeline.py ingest --dry-run --threshold 98.5
```

**3. Run the full pipeline with strict quality gates:**
```bash
python scripts/run_pipeline.py run-all --threshold 99.0
```

---

## 📓 Notebooks Summary

The pipeline consists of 3 sequential notebooks that work together to profile, validate, and monitor data quality.

### 📊 Notebook 01: Data Profiling
**Path:** `notebooks/01_AIMS_Data_Profiling.ipynb`

**Purpose:** Generate validation rules from your data
- Analyzes all parquet files in `data/Samples_LH_Bronze_Aims_26_parquet/`
- Creates YAML validation configs in `dq_great_expectations/generated_configs/`
- Uses parallel processing (4 workers) for efficiency
- Samples 100k rows per file for memory safety

**When to Run:** 
- First time setup
- When data structure changes
- When you want to update validation rules

**Output:** 68 YAML files (one per data file)

---

### 🔄 Notebook 02: Data Ingestion with DQ Gatekeeping
**Path:** `notebooks/02_AIMS_Data_Ingestion.ipynb`

**Purpose:** Production ETL pipeline with quality gates
- Discovers files in source directory
- Validates each file against its YAML config
- **If PASSED (100% score):** Marks as processed, ready for Silver layer
- **If FAILED (<100% score):** Quarantines file, logs failure
- Tracks processed files using watermarks

**State Files:**
- `data/state/watermarks.json` - Tracks which files have been processed
- `data/state/dq_logs.jsonl` - Logs every validation result

**When to Run:** 
- Every time you have new data to process
- Daily/hourly in production

**Behavior:**
- Skips files already processed (idempotent)
- Logs all validation results for monitoring

---

### 📈 Notebook 03: Interactive Monitoring Dashboard
**Path:** `notebooks/03_AIMS_Monitoring.ipynb`

**Purpose:** Comprehensive observability with interactive visualizations
- Reads watermarks to show processed files
- Reads DQ logs to analyze quality trends
- Displays 15 analysis sections with interactive Plotly dashboards
- Generates alert payloads for failures
- Exports summary reports

**15 Analysis Sections:**

**Basic Monitoring (Steps 1-5):**
1. Import Libraries
2. Configuration
3. Watermark Status
4. DQ Dashboard (summary stats + trend chart)
5. Alerting System

**Advanced Analytics (Steps 6-10):**
6. Failure Analysis (root cause breakdown)
7. Performance Metrics (processing speed, score distribution)
8. Historical Comparison (daily trends)
9. Freshness Check (staleness alerts)
10. Export Report (JSON summaries)

**Interactive Dashboards (Steps 11-15):** ⭐ NEW!
11. Main Dashboard (KPI gauges, pie charts, trend lines, bar charts)
12. File Explorer (sunburst chart with drill-down)
13. Failure Heatmap (visual root cause analysis)
14. Processing Timeline (scatter plot with annotations)
15. Performance Analytics (4-panel cumulative metrics)

**Interactive Features:**
- 🖱️ Hover for details
- 🔍 Zoom and pan
- 📊 Drill-down exploration
- 🎨 Color-coded visualizations

**When to Run:** 
- After ingestion to review results
- Daily for monitoring
- When investigating quality issues
- For stakeholder presentations

---

## 🛠️ Manual Orchestration (Current Setup)

### 🎯 First Time Setup

1. **Run Notebook 01 (Profiling)**
   ```
   Open: notebooks/01_AIMS_Data_Profiling.ipynb
   Run All Cells
   Result: 68 YAML configs created
   Time: ~5-10 minutes
   ```

2. **Run Notebook 02 (Ingestion)**
   ```
   Open: notebooks/02_AIMS_Data_Ingestion.ipynb
   Run All Cells
   Result: Files validated, watermarks created, logs generated
   Time: ~2-5 minutes (depends on data)
   ```

3. **Run Notebook 03 (Monitoring)**
   ```
   Open: notebooks/03_AIMS_Monitoring.ipynb
   Run All Cells (18 cells total)
   Result: 15 analysis sections + 5 interactive Plotly dashboards
   Time: ~30 seconds
   
   Note: First run will install plotly/ipywidgets (~30 sec extra)
   ```

### 🔁 Daily Operations

For regular data processing:

1. **Skip Notebook 01** (configs already exist)
2. **Run Notebook 02** (process new files)
3. **Run Notebook 03** (review results)

---

## 🧪 Testing the Pipeline

### Quick Test Run

1. **Clear previous state** (optional, to test from scratch):
   ```bash
   rm data/state/watermarks.json
   rm data/state/dq_logs.jsonl
   ```

2. **Run all 3 notebooks in sequence**

3. **Verify outputs:**
   - [ ] Notebook 01: Check `dq_great_expectations/generated_configs/` has 68 YAML files
   - [ ] Notebook 02: Check `data/state/watermarks.json` exists with file timestamps
   - [ ] Notebook 02: Check `data/state/dq_logs.jsonl` contains validation logs (68 entries)
   - [ ] Notebook 03: All 15 sections execute successfully
   - [ ] Notebook 03: 5 interactive Plotly dashboards display correctly
   - [ ] Notebook 03: Summary report exported to `data/state/dq_report_*.json`

4. **Test idempotency:**
   - Run Notebook 02 again
   - Should skip all files (already processed)
   - Should complete instantly

---

## 🤖 Automation Options (Future)

Once manual testing is complete, consider:

### Option A: Python Script
Create `scripts/run_pipeline.py` to execute all notebooks programmatically

### Option B: Azure Data Factory
Schedule pipeline:
- Trigger: Time-based (daily)
- Activity 1: Run Notebook 02 (Ingestion)
- Activity 2: Run Notebook 03 (Monitoring)
- Activity 3: Send email if failures detected

### Option C: Airflow DAG
Use existing Airflow setup in `/Airflow/project_horrace_one/`
```python
dag = DAG('aims_dq_pipeline')
task1 = PythonOperator(task_id='ingest', ...)
task2 = PythonOperator(task_id='monitor', ...)
task1 >> task2
```

### Option D: Azure Synapse Pipelines
Native integration with notebooks and scheduling

---

## ❓ Troubleshooting

### Issue: "No validation config found"
**Cause:** Notebook 01 not run or configs deleted
**Fix:** Run Notebook 01 first

### Issue: "File already processed" (all files skipped)
**Cause:** Watermarks exist from previous run
**Fix:** 
- Expected behavior if data hasn't changed
- To reprocess: Delete `data/state/watermarks.json`
- Or use CLI with `--force`

### Issue: "DQ log file not found"
**Cause:** Notebook 02 not run yet
**Fix:** Run Notebook 02 first

### Issue: Import errors (dq_framework not found)
**Cause:** Package not installed in environment
**Fix:** Ensure `fabric-dq` conda environment is active

---

## 📂 Key Files & Directories

```
AIMS_LOCAL/
├── notebooks/
│   ├── 01_AIMS_Data_Profiling.ipynb      # Generate YAML configs
│   ├── 02_AIMS_Data_Ingestion.ipynb      # ETL + DQ gatekeeping
│   └── 03_AIMS_Monitoring.ipynb          # Dashboard + alerts
├── scripts/
│   └── run_pipeline.py                   # CLI entry point
├── data/
│   ├── Samples_LH_Bronze_Aims_26_parquet/  # 68 source files
│   └── state/
│       ├── watermarks.json                  # Processed files tracker
│       └── dq_logs.jsonl                    # Validation results log
├── dq_great_expectations/
│   └── generated_configs/                   # 68 YAML validation configs
└── ORCHESTRATION_GUIDE.md                   # This file
```

---

## ✅ Success Criteria

**Pipeline is working correctly when:**
1. Notebook 01 generates 68 YAML files
2. Notebook 02 validates all files and creates state files
3. Notebook 03 displays dashboard with metrics and charts
4. Subsequent runs of Notebook 02 skip already-processed files
5. All notebooks run without errors in the `fabric-dq` environment
