# AIMS Data Profiling Setup - Summary

## 📝 Overview

Successfully configured AIMS_LOCAL project to use the `fabric_data_quality` framework for profiling AIMS parquet files **without duplicating code**.

## 🎯 Solution

The solution uses **editable package installation** - the `fabric_data_quality` project is installed as a Python package that can be imported and used by AIMS_LOCAL.

### Benefits:
- ✅ No code duplication
- ✅ Single source of truth
- ✅ Easy to update
- ✅ Clean integration
- ✅ Consistent across projects

## 📁 Files Created

### 1. Setup Script
**File**: `setup_aims_profiling.sh`

Automated setup script that:
- Installs `fabric_data_quality` as an editable package (`pip install -e`)
- Creates necessary directories
- Validates the installation
- Tests with actual data

**Usage**:
```bash
bash setup_aims_profiling.sh
```

### 2. CLI Profiler
**File**: `profile_aims_parquet.py`

Command-line tool for profiling AIMS parquet files:
- Discovers all .parquet files in data directory
- Profiles each file (structure, types, nulls, distributions)
- Generates validation configuration files
- Creates summary reports

**Usage**:
```bash
# Profile all files
python profile_aims_parquet.py

# Profile specific file
python profile_aims_parquet.py --file aims_activitydates.parquet

# Just view profile
python profile_aims_parquet.py --profile-only

# Custom settings
python profile_aims_parquet.py --null-tolerance 5.0 --severity high
```

### 3. Jupyter Notebook
**File**: `notebooks/03_Profile_AIMS_Data.ipynb`

Interactive notebook for data profiling:
- Step-by-step profiling workflow
- Visual data exploration
- Detailed analysis of each file
- Summary reports and statistics

**Usage**:
```bash
jupyter notebook notebooks/03_Profile_AIMS_Data.ipynb
```

### 4. Documentation

#### README_PROFILING.md
Complete documentation covering:
- Architecture overview
- Setup instructions
- Usage examples (CLI & notebook)
- Customizing validation rules
- Integration with data pipelines
- Best practices
- Troubleshooting

#### PROFILING_QUICK_START.md
Quick reference guide with:
- Common commands
- Code snippets
- Tips and tricks
- Troubleshooting shortcuts

## 🚀 Quick Start

### Step 1: Setup (One-Time)
```bash
cd /home/sanmi/Documents/HS2/HS2_PROJECTS_2025/AIMS_LOCAL
bash setup_aims_profiling.sh
```

### Step 2: Profile Your Data
```bash
# Option A: Command line
python profile_aims_parquet.py

# Option B: Jupyter notebook
jupyter notebook notebooks/03_Profile_AIMS_Data.ipynb
```

### Step 3: Review Generated Configs
Check `config/data_quality/` for generated validation configs:
- `aims_activitydates_validation.yml`
- `aims_assetattributes_validation.yml`
- `aims_assetclassattributes_validation.yml`
- `aims_assetclasschangelogs_validation.yml`

### Step 4: Customize & Use
Edit the YAML files to add business-specific rules, then use them in your data pipeline.

## 📊 What Gets Profiled

For each parquet file, the profiler analyzes:

1. **Structure**
   - Number of rows and columns
   - Memory usage
   - Column names

2. **Data Types**
   - Detected types for each column
   - Type consistency

3. **Missing Values**
   - Null counts and percentages
   - Columns with missing data

4. **Statistics** (for numeric columns)
   - Min, max, mean, median
   - Standard deviation
   - Percentiles

5. **Cardinality**
   - Unique value counts
   - Potential key columns

6. **Validation Rules**
   - Auto-generated expectations
   - Configurable thresholds
   - Severity levels

## 🔧 Integration Points

### With AIMS Data Platform

```python
# In your ingestion pipeline
from dq_framework import ConfigLoader, DataValidator
from src.cli import ingest_data

# Load validation config
config = ConfigLoader.load('config/data_quality/aims_assets_validation.yml')

# Ingest with validation
df = ingest_data('aims_assets')
validator = DataValidator(config)
results = validator.validate(df)

if results['success']:
    # Proceed with data processing
    process_data(df)
else:
    # Handle validation failures
    log_failures(results['failures'])
```

### With Great Expectations

```python
import great_expectations as gx

# Use generated config as starting point
context = gx.get_context()
# Great Expectations will automatically use the expectations
# defined in the YAML files
```

### With Microsoft Fabric

```python
from dq_framework import FabricConnector

# Connect to Fabric workspace
connector = FabricConnector(
    workspace_id="your-workspace-id",
    lakehouse_name="your-lakehouse"
)

# Validate data in Fabric
results = connector.validate_table(
    table_name="aims_activitydates",
    config_path="config/data_quality/aims_activitydates_validation.yml"
)
```

## 📈 Directory Structure

After setup, your AIMS_LOCAL project will have:

```
AIMS_LOCAL/
├── profile_aims_parquet.py           # CLI profiler
├── setup_aims_profiling.sh           # Setup script
├── README_PROFILING.md               # Full documentation
├── PROFILING_QUICK_START.md          # Quick reference
│
├── notebooks/
│   └── 03_Profile_AIMS_Data.ipynb   # Interactive profiling
│
├── config/
│   └── data_quality/                 # Generated validation configs
│       ├── aims_activitydates_validation.yml
│       ├── aims_assetattributes_validation.yml
│       └── ...
│
├── reports/                          # Profiling reports
│   └── aims_profiling_summary.csv
│
└── logs/                             # Profiling logs
```

## 🔄 Workflow

```
1. Setup                    2. Profile                  3. Customize
   ↓                           ↓                           ↓
Run setup_aims_profiling.sh  Run profiler CLI/notebook  Edit YAML configs
   ↓                           ↓                           ↓
Installs framework          Generates configs          Add business rules
   ↓                           ↓                           ↓
                                                        
4. Integrate                5. Validate                6. Monitor
   ↓                           ↓                           ↓
Add to data pipeline       Run validations            Track quality metrics
   ↓                           ↓                           ↓
Use configs in code        Check results              Continuous improvement
```

## 💡 Key Advantages

### No Code Duplication
- `fabric_data_quality` lives in one place
- AIMS_LOCAL imports it as a package
- Other projects can do the same

### Easy Updates
- Update `fabric_data_quality` once
- Changes are immediately available to all projects
- No need to sync code across projects

### Clean Separation
- Framework code: `../fabric_data_quality`
- Project-specific code: `AIMS_LOCAL/profile_aims_parquet.py`
- Generated configs: `AIMS_LOCAL/config/data_quality/`

### Reusable Across HS2 Projects
Same approach can be used by:
- `full_stack_hss`
- `ACA_COMMERCIAL`
- `fabric_data_quality` (self-testing)
- Any other HS2 project

## 🎓 Next Steps

1. **Run the Setup**
   ```bash
   bash setup_aims_profiling.sh
   ```

2. **Profile Your Data**
   ```bash
   python profile_aims_parquet.py
   ```

3. **Review Generated Configs**
   - Open `config/data_quality/*.yml` files
   - Understand the auto-generated rules

4. **Customize for Your Needs**
   - Add business-specific validation rules
   - Adjust thresholds and severity levels
   - Document your customizations

5. **Integrate with Pipeline**
   - Import `dq_framework` in your data pipeline
   - Use configs to validate data during ingestion
   - Set up automated validation checks

6. **Share with Team**
   - Commit configs to Git
   - Document validation standards
   - Train team on using the framework

## 📚 Documentation Reference

- **Quick Start**: `PROFILING_QUICK_START.md`
- **Full Guide**: `README_PROFILING.md`
- **Framework Docs**: `../fabric_data_quality/README.md`
- **Examples**: `../fabric_data_quality/examples/`

## 🤝 Support

For issues or questions:
1. Check `README_PROFILING.md` troubleshooting section
2. Review `fabric_data_quality` documentation
3. Test with the generic profiler: `../fabric_data_quality/profile_data.py`

---

**Created**: December 2025  
**Framework Version**: fabric_data_quality v1.0.0  
**Status**: Ready to use ✅
