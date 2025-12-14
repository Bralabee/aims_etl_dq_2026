# AIMS Data Profiling with fabric_data_quality

This document explains how to use the `fabric_data_quality` framework to profile AIMS parquet files without duplicating code.

## 🎯 Overview

The `fabric_data_quality` framework is installed as a **reusable package** that can be used across all HS2 projects. This approach:

- ✅ **No Code Duplication**: Single source of truth in `../fabric_data_quality`
- ✅ **Easy Updates**: Changes to the framework are immediately available
- ✅ **Clean Integration**: Simple imports in scripts and notebooks
- ✅ **Consistent Validation**: Same validation rules across all projects

## 📦 Architecture

```
HS2_PROJECTS_2025/
│
├── fabric_data_quality/          # ← Framework (installed as package)
│   ├── dq_framework/             # Core library
│   ├── profile_data.py           # Generic profiler CLI
│   ├── setup.py                  # Package installer
│   └── ...
│
└── AIMS_LOCAL/                   # ← Your project
    ├── scripts/
    │   ├── profile_aims_parquet.py   # AIMS-specific profiler
    │   └── setup_aims_profiling.sh   # Setup script
    ├── notebooks/
    │   └── 01_AIMS_Data_Profiling.ipynb  # Interactive profiling
    ├── config/
    │   └── data_quality/         # Generated validation configs
    └── data/
        └── Samples_LH_Bronze_Aims_26_parquet/  # Your data
```

## 🚀 Quick Start

### Step 1: Run Setup Script

This installs `fabric_data_quality` in editable mode:

```bash
cd /home/sanmi/Documents/HS2/HS2_PROJECTS_2025/AIMS_LOCAL
bash scripts/setup_aims_profiling.sh
```

**What it does:**
1. Installs `fabric_data_quality` as an editable Python package
2. Creates necessary directories (`config/data_quality/`, `logs/`, `reports/`)
3. Validates the installation
4. Tests with your actual data

### Step 2: Profile Your Data

#### Option A: Command Line (Quick)

```bash
# Profile all parquet files
python profile_aims_parquet.py

# Profile specific file
python profile_aims_parquet.py --file aims_activitydates.parquet

# Just view profile (no config generation)
python profile_aims_parquet.py --profile-only

# Custom settings
python profile_aims_parquet.py --null-tolerance 5.0 --severity high
```

#### Option B: Jupyter Notebook (Interactive)

```bash
jupyter notebook notebooks/03_Profile_AIMS_Data.ipynb
```

The notebook provides:
- Interactive data exploration
- Visual summaries
- Step-by-step profiling
- Detailed analysis of each file

## 📊 What Gets Generated

After profiling, you'll have:

```
config/data_quality/
├── aims_activitydates_validation.yml
├── aims_assetattributes_validation.yml
├── aims_assetclassattributes_validation.yml
└── aims_assetclasschangelogs_validation.yml
```

Each YAML file contains:
- Column names and data types
- Null value checks
- Data type validations
- Statistical expectations (for numeric columns)
- Unique value expectations (for ID columns)

## 🔧 Using the Generated Configs

### In Your Data Pipeline

```python
from dq_framework import ConfigLoader, DataValidator
import pandas as pd

# Load data
df = pd.read_parquet('data/aims_activitydates.parquet')

# Load validation config
config = ConfigLoader.load('config/data_quality/aims_activitydates_validation.yml')

# Validate
validator = DataValidator(config)
results = validator.validate(df)

# Check results
if results['success']:
    print("✅ Data quality checks passed")
    # Proceed with data processing
else:
    print("❌ Data quality issues found:")
    for failure in results['failures']:
        print(f"  - {failure}")
    # Handle validation failures
```

### In Great Expectations

```python
import great_expectations as gx

# Initialize context
context = gx.get_context()

# Add your data
datasource = context.sources.add_pandas("aims_data")
data_asset = datasource.add_dataframe_asset(name="activity_dates")

# Use the generated config as a starting point
# Great Expectations will automatically use the expectations
batch = data_asset.add_batch_definition_whole_dataframe("batch1")
```

## 📝 Customizing Validation Rules

The generated YAML files are **starting points**. Customize them with business logic:

```yaml
# config/data_quality/aims_activitydates_validation.yml

name: aims_activitydates
description: Activity dates validation with business rules

expectations:
  - expectation_type: expect_column_values_to_be_unique
    column: ActivityID
    severity: high  # ← Custom severity
    
  - expectation_type: expect_column_values_to_be_between
    column: ActivityDate
    min_value: "2020-01-01"  # ← Business rule: no dates before project start
    max_value: "2030-12-31"  # ← Business rule: reasonable future limit
    severity: high
    
  - expectation_type: expect_column_values_to_match_regex
    column: ActivityType
    regex: "^(PLANNED|ACTUAL|FORECAST)$"  # ← Allowed values
    severity: high
```

## 🔄 Workflow

```
1. Profile Data              2. Review & Customize       3. Integrate
   ↓                             ↓                           ↓
[profile_aims_parquet.py]   [Edit YAML files]        [Use in pipeline]
   ↓                             ↓                           ↓
Generates configs        Add business rules         Validate data loads
   ↓                             ↓                           ↓
Initial expectations     Custom expectations        Production ready
```

## 💡 Best Practices

### 1. Profile Once, Validate Many Times

- Profile your data initially to understand structure
- Generate baseline validation configs
- Use those configs for ongoing validation
- Re-profile only when schema changes

### 2. Layer Your Validations

```yaml
# Bronze Layer (Raw Data)
- Check: columns exist, data types correct, no completely null columns
- Severity: medium

# Silver Layer (Cleaned Data)
- Check: referential integrity, format consistency, value ranges
- Severity: high

# Gold Layer (Business Data)
- Check: business rules, KPIs, aggregation logic
- Severity: high
```

### 3. Version Control Your Configs

```bash
git add config/data_quality/*.yml
git commit -m "Add AIMS data quality validations"
```

### 4. Document Validation Rules

Add comments to your YAML files:

```yaml
expectations:
  # Rule: ActivityID must be unique across all records
  # Rationale: Primary key constraint
  # Owner: Data Engineering Team
  - expectation_type: expect_column_values_to_be_unique
    column: ActivityID
```

## 🛠 Advanced Usage

### Profile Multiple Directories

```python
# profile_all_aims_data.py
from pathlib import Path
from dq_framework import DataProfiler
import pandas as pd

data_dirs = [
    "data/Bronze_Layer",
    "data/Silver_Layer",
    "data/Gold_Layer"
]

for data_dir in data_dirs:
    for parquet_file in Path(data_dir).glob("*.parquet"):
        df = pd.read_parquet(parquet_file)
        profiler = DataProfiler(name=f"{data_dir.split('/')[-1]}_{parquet_file.stem}")
        profile = profiler.profile_dataframe(df)
        config = profiler.generate_config(profile)
        profiler.save_config(config, f"config/data_quality/{parquet_file.stem}.yml")
```

### Integrate with Airflow

```python
# dags/aims_data_validation.py
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from dq_framework import ConfigLoader, DataValidator
import pandas as pd

def validate_aims_data(**context):
    df = pd.read_parquet(context['params']['file_path'])
    config = ConfigLoader.load(context['params']['config_path'])
    validator = DataValidator(config)
    results = validator.validate(df)
    
    if not results['success']:
        raise ValueError(f"Validation failed: {results['failures']}")

dag = DAG('aims_validation', schedule_interval='@daily')

validate_task = PythonOperator(
    task_id='validate_activity_dates',
    python_callable=validate_aims_data,
    params={
        'file_path': 'data/aims_activitydates.parquet',
        'config_path': 'config/data_quality/aims_activitydates_validation.yml'
    },
    dag=dag
)
```

## 🐛 Troubleshooting

### Import Error: `dq_framework` not found

```bash
# Re-run setup
bash setup_aims_profiling.sh

# Or manually install
cd ../fabric_data_quality
pip install -e .
```

### Validation Config Not Loading

```python
from dq_framework import ConfigLoader

# Check if file exists
config_path = "config/data_quality/aims_activitydates_validation.yml"
print(f"Exists: {Path(config_path).exists()}")

# Try loading with error details
try:
    config = ConfigLoader.load(config_path)
except Exception as e:
    print(f"Error: {e}")
```

### Profiler Fails on Large Files

```python
# Profile with sampling
df = pd.read_parquet('large_file.parquet')
df_sample = df.sample(n=10000)  # Sample 10k rows
profiler.profile_dataframe(df_sample)
```

## 📚 Additional Resources

- **Framework Documentation**: `../fabric_data_quality/README.md`
- **Config Templates**: `../fabric_data_quality/config_templates/`
- **Usage Examples**: `../fabric_data_quality/examples/`
- **Great Expectations Docs**: https://docs.greatexpectations.io/

## 🤝 Support

For issues or questions:
1. Check the `fabric_data_quality` documentation
2. Review example configs in `../fabric_data_quality/examples/`
3. Test with the generic profiler: `python ../fabric_data_quality/profile_data.py`

---

**Last Updated**: December 2025  
**Framework Version**: 1.0.0  
**Maintained By**: HS2 Data Engineering Team
