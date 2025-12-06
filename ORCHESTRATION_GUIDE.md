# AIMS Data Quality Pipeline - Orchestration Guide






































































































































































































































































































































































































































































































































**Overall Status:** ✅ Excellent - Ready for production with minor enhancements recommended**Pipeline Version:** 2.0  **Assessment Date:** December 6, 2025  ---- Enterprise-grade reliability- ML-enhanced quality detection- Integrated with monitoring/alerting systems- Fully automated, scheduled execution**Long-Term Vision (Quarter 1):**4. Set up CI/CD3. Build test suite2. Create CLI interface1. Add alerting integration**Strategic Actions (Month 1):**4. Consolidate documentation3. Make thresholds configurable2. Add progress indicators1. Add .env support**Immediate Actions (Week 1):**- Solid state management- Comprehensive documentation- Beautiful visualizations- Complete functionality**Strengths:****Current Assessment:** ✅ Production-ready for manual execution## ✅ Conclusion---**Gap to Close:** ~40 hours of development```Configuration: Environment-based (.env)Deployment: Scheduled (ADF/Airflow)Testing: Automated test suite + CI/CDAlerting: Integrated (Slack/Teams/Email)Monitoring: Interactive dashboards + automated alertsPipeline: Automated CLI/orchestrator```### Future State (v3.0) - Recommended Target```Deployment: Local/ad-hocTesting: Manual validationAlerting: Manual reviewMonitoring: Interactive dashboardsPipeline: Manual notebook execution```### Current State (v2.0)## 📊 Current vs. Future State---- Does the team have expertise?- Will this require ongoing support?**Maintenance:**- Can it be done incrementally?- Does this block other work?**Dependencies:**- Risk reduction vs maintenance burden?- Time saved vs development effort?**ROI:**- Have stakeholders requested this?- Is this solving a real pain point?**User Need:**Ask these questions:### When to Implement?## 💡 Decision Criteria---- ⚠️ Data lineage (adds complexity)- ⚠️ Real-time streaming (architectural change)- ⚠️ ML anomaly detection (may generate false positives)### High Risk Improvements (Prototype First)- ⚠️ Parallel validation (thread safety)- ⚠️ CLI interface (test with papermill)- ⚠️ Alerting integration (test webhooks)### Medium Risk Improvements (Test Thoroughly)- ✅ Documentation consolidation- ✅ Configurable thresholds- ✅ Progress indicators  - ✅ Environment variables### Low Risk Improvements (Do First)## 🎯 Risk Assessment---**Impact:** Next-level capabilities**Estimated Effort:** 80 hours  - [ ] Real-time streaming support- [ ] ML anomaly detection (P3.3)- [ ] Power BI dashboard template- [ ] Data lineage tracking (P3.2)### Month 2-3: Advanced Features---**Impact:** Enterprise-grade reliability**Estimated Effort:** 24 hours  - [ ] Parallel validation (P2.3)- [ ] CI/CD pipeline (GitHub Actions)- [ ] Integration tests- [ ] Unit test suite (P3.1)### Week 3-4: Testing & Hardening---**Impact:** Production-ready automation**Estimated Effort:** 12 hours  - [ ] Fix test_profiling_integration.py- [ ] CLI interface (P2.2)- [ ] Slack/Teams alerting (P2.1)### Week 2: Automation---**Impact:** Immediate improvement in usability**Estimated Effort:** 4 hours  - [ ] Update documentation (consolidate READMEs)- [ ] Configurable thresholds (P1.3)- [ ] Add progress indicators (P1.2)- [ ] Add .env support (P1.1)### Week 1: Quick Wins## 📋 Implementation Roadmap---**Tools:** Prophet, scikit-learn, Azure ML- Auto-tune validation thresholds- Predict quality degradation- Detect statistical anomalies- Learn normal data patterns**Features:****Impact:** Medium - Proactive quality monitoring**Effort:** 40 hours  #### 3.3 ML-Based Anomaly Detection---**Tools:** OpenLineage, Apache Atlas- Generate lineage diagrams- Monitor downstream consumers- Record transformation history- Track upstream data sources**Features:****Impact:** Low - Advanced governance feature**Effort:** 20 hours  #### 3.2 Data Lineage Tracking---**Target:** 60% code coverage```def test_alert_generation()def test_dashboard_generation()def test_log_parsing()# tests/test_monitoring.pydef test_idempotency()def test_dq_validation()def test_watermark_tracking()# tests/test_ingestion.pydef test_sample_validation()def test_yaml_config_generation()def test_data_profiler_initialization()# tests/test_profiling.py```python**Test Coverage:****Impact:** Medium - Safer deployments**Effort:** 16 hours  #### 3.1 Automated Testing Suite### Priority 3: Medium Impact, High Effort---- Only worth it if processing >500 files- Current dataset (68 files) processes in ~3 min**Consideration:** ```    results = pool.map(validate_file, unprocessed_files)with Pool(NUM_WORKERS) as pool:    return result    # validation logicdef validate_file(file_path):from multiprocessing import Pool```python**Impact:** Medium - Faster processing for large datasets**Effort:** 4 hours  #### 2.3 Parallel Validation in Notebook 02---- `click` (CLI framework)- `papermill` (notebook execution)**Dependencies:**```python scripts/run_pipeline.py monitorpython scripts/run_pipeline.py ingestpython scripts/run_pipeline.py run-all```bash**Usage:**```    cli()if __name__ == '__main__':    monitor()    ingest()    profile()    """Run complete pipeline"""def run_all():@cli.command()    pm.execute_notebook('notebooks/03_AIMS_Monitoring.ipynb', ...)    """Generate monitoring dashboard"""def monitor():@cli.command()    pm.execute_notebook('notebooks/02_AIMS_Data_Ingestion.ipynb', ...)    """Run data ingestion with DQ"""def ingest():@cli.command()    pm.execute_notebook('notebooks/01_AIMS_Data_Profiling.ipynb', ...)    """Run data profiling"""def profile():@cli.command()    passdef cli():@click.group()import papermill as pmimport click# Create scripts/run_pipeline.py```python**Impact:** High - Easier automation**Effort:** 6 hours  #### 2.2 CLI Interface---- Create `utils/alerting.py` helper- Notebook 03 (alerting section)**Files to Update:**- Azure Monitor integration- Email via SendGrid- Teams webhook- Slack webhook (easiest)**Options:**```        send_slack_alert(alert)    for alert in alerts:if os.getenv('ENABLE_ALERTS') == 'true':# In Notebook 03, after generating alerts:    requests.post(webhook_url, json=alert_payload)    webhook_url = os.getenv('SLACK_WEBHOOK_URL')    import requestsdef send_slack_alert(alert_payload):```python**Implementation:****Impact:** High - Automated monitoring**Effort:** 4 hours  #### 2.1 Alerting Integration### Priority 2: High Impact, Medium Effort---- Notebook 02 (validation logic)**Files to Update:**```    status = "FAILED"else:    status = "WARNING"elif score >= WARNING_THRESHOLD:    status = "PASSED"if score >= PASS_THRESHOLD:WARNING_THRESHOLD = 90  # Warning levelPASS_THRESHOLD = 95  # Allow 5% tolerance# Add configuration```python**Impact:** Medium - More flexible gatekeeping**Effort:** 1 hour  #### 1.3 Configurable Quality Thresholds---- Notebook 02 (validation loop)- Notebook 01 (profiling loop)**Files to Update:**```    # validatefor file in tqdm(files, desc="Processing files"):from tqdm import tqdm```python**Impact:** Medium - Better UX for long operations**Effort:** 30 minutes  #### 1.2 Progress Indicators---- Create `.env.example` template- All 3 notebooks**Files to Update:**```BASE_DIR = Path(os.getenv('BASE_DIR'))load_dotenv()from dotenv import load_dotenv# Update notebooksSAMPLE_SIZE=100000NUM_WORKERS=4BASE_DIR=/path/to/AIMS_LOCAL# Create .env file```python**Impact:** High - Portable across environments**Effort:** 1 hour  #### 1.1 Environment Variables (.env support)### Priority 1: High Impact, Low Effort## 🚀 Recommended Improvements---**Impact:** Low - Just created README_COMPLETE.md to consolidate- Redundant content- No single source of truth- Inconsistent information across docs**Gap:** - README_COMPLETE.md (new comprehensive guide)- CRITICAL_ANALYSIS.md- ORCHESTRATION_GUIDE.md- README.md (original)**Files:****Current:** Multiple README files with overlapping content### 8. Documentation Versioning---**Impact:** Medium - Risky for production changes- test_profiling_integration.py exists but has API mismatches- No CI/CD pipeline- No integration tests for pipeline- No unit tests for helper functions**Gap:****Current:** No automated tests### 7. Testing & Validation---**Impact:** Low - Nice-to-have for advanced governance- No data provenance metadata- No downstream consumption tracking- No upstream source tracking**Gap:****Current:** Only tracks processed/unprocessed status### 6. Data Lineage---**Impact:** Low - Current dataset is small (68 files, ~3 min)- No early termination on critical failures- No progress indicators for long-running operations- No parallel validation**Gap:****Current:** Sequential file processing in Notebook 02### 5. Performance Optimization---**Impact:** High - Manual monitoring required- Azure Monitor- PagerDuty- Slack/Teams webhooks- Email (SMTP/SendGrid)**Gap:** No actual integration with:```print(json.dumps(alert_payload))  # Just printed}    # ...    "alert_type": "DataQualityFailure",alert_payload = {```python**Current:** Alert payloads generated but not sent### 4. Alerting Integration---**Impact:** Low - Works but inflexible- All failures treated equally- No severity levels (warning vs critical)- No configurable tolerance**Gap:**```    status = "FAILED"else:    status = "PASSED"if validation_score == 100:```python**Current:** Hardcoded 100% pass threshold### 3. Quality Thresholds---**Impact:** Medium - Production runs could fail unnecessarily- Errors stop execution- No graceful degradation- No retry logic for transient failures**Gap:** ```    print("Path not found")else:    # processif os.path.exists(DATA_PATH):```python**Current:** Basic error handling in notebooks### 2. Error Handling---**Impact:** Medium - Requires manual editing for each environment**Gap:** Difficult to run on different environments```BASE_DIR = Path("/home/sanmi/Documents/HS2/HS2_PROJECTS_2025/AIMS_LOCAL")# In each notebook:```python**Current:** Hardcoded paths in notebooks### 1. Configuration Management## 🔍 Identified Gaps---- ✅ Complete audit trail in dq_logs.jsonl- ✅ Watermarks tracking 44 processed files- ✅ 98.8% average quality score- ✅ 68 files validated (44 passed, 24 failed)- ✅ 68 YAML configs generated### Metrics (Current Run)7. **Professional Quality** - Production-ready code and documentation6. **State Management** - Watermarks and logs for full traceability5. **Comprehensive Monitoring** - 15 analysis sections covering all aspects4. **Local Execution** - Fully testable without external dependencies3. **Idempotent** - Safe to rerun, tracks processed files2. **Interactive Dashboards** - 5 Plotly visualizations with drill-down capability1. **Complete Pipeline** - End-to-end profiling → validation → monitoring### Strengths## ✅ Current State (What Works)## Overview
The AIMS DQ pipeline consists of 3 sequential notebooks that work together to profile, validate, and monitor data quality.

## Notebooks Summary

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

## Manual Orchestration (Current Setup)

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

## Testing the Pipeline

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

## Automation Options (Future)

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

## Troubleshooting

### Issue: "No validation config found"
**Cause:** Notebook 01 not run or configs deleted
**Fix:** Run Notebook 01 first

### Issue: "File already processed" (all files skipped)
**Cause:** Watermarks exist from previous run
**Fix:** 
- Expected behavior if data hasn't changed
- To reprocess: Delete `data/state/watermarks.json`

### Issue: "DQ log file not found"
**Cause:** Notebook 02 not run yet
**Fix:** Run Notebook 02 first

### Issue: Import errors (dq_framework not found)
**Cause:** Package not installed in environment
**Fix:** Ensure `fabric-dq` conda environment is active

---

## Key Files & Directories

```
AIMS_LOCAL/
├── notebooks/
│   ├── 01_AIMS_Data_Profiling.ipynb      # Generate YAML configs
│   ├── 02_AIMS_Data_Ingestion.ipynb      # ETL + DQ gatekeeping
│   └── 03_AIMS_Monitoring.ipynb          # Dashboard + alerts
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

## Success Criteria

✅ **Pipeline is working correctly when:**
1. Notebook 01 generates 68 YAML files
2. Notebook 02 validates all files and creates state files
3. Notebook 03 displays dashboard with metrics and charts
4. Subsequent runs of Notebook 02 skip already-processed files
5. All notebooks run without errors in the `fabric-dq` environment

---

## Next Steps

1. **Test manually** → Run notebooks 01, 02, 03 in sequence
2. **Review results** → Check dashboard in Notebook 03
3. **Validate behavior** → Ensure gatekeeping works (files with DQ issues are quarantined)
4. **Choose automation** → Pick orchestration approach for production
5. **Integrate alerting** → Connect alerts to Teams/Slack/Email

For questions or issues, refer to `CRITICAL_ANALYSIS.md` for technical details.
