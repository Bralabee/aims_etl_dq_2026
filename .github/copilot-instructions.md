# AIMS Data Platform - AI Coding Instructions

## 🧠 Architecture & Core Patterns
- **Hybrid Runtime:** System runs on **Microsoft Fabric** (Spark) and **Local Linux** (Python).
  - **Detection:** MUST use `if Path("/lakehouse/default/Files").exists():` to detect Fabric. **DO NOT** rely on `import notebookutils` failing, as it hangs indefinitely on local Linux.
  - **Paths:** Use `pathlib.Path`. Fabric Root: `/lakehouse/default/Files`. Local Root: Project dir.
- **Split-Library Pattern:**
  - `dq_framework` (in `../2_DATA_QUALITY_LIBRARY`): Core validation engine (Generic).
  - `aims_data_platform` (in `.`): Project logic (Specific).
  - **Rule:** Import from `aims_data_platform` which wraps `dq_framework`. Do not duplicate logic.

## 🛡️ Data Quality (Great Expectations)
- **Performance:** ALWAYS set `os.environ["GX_ANALYTICS_ENABLED"] = "False"` before importing GX to prevent 60s+ hangs.
- **Validation Results:** The installed `dq_framework` returns a flat dictionary for stats.
  - **Use:** `result.get('evaluated_checks')` and `result.get('successful_checks')`.
  - **Avoid:** `result.get('statistics').get(...)` (Old schema, causes KeyErrors).
- **Configuration:** YAML files in `config/data_quality/{table}.yml`.

## 📓 Notebooks & Orchestration
- **Orchestrator:** `00_AIMS_Orchestration.ipynb` is the master pipeline.
- **Config Injection:** Use `PIPELINE_CONFIG` dict at the top of notebooks to control phases (`run_profiling`, `run_ingestion`).
- **Error Handling:** Explicitly `raise` in `try/except` blocks if `continue_on_error` is False.

## 🛠️ Developer Workflow
- **Sync:** Logic in `scripts/run_pipeline.py` MUST match `notebooks/00_AIMS_Orchestration.ipynb`.
- **Testing:** `pytest tests/` for library code.
- **Dependencies:** `environment.yml` (Conda).
