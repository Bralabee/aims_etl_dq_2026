# AIMS Data Profiling - Quick Reference

## 🚀 Setup (One-Time)

```bash
cd /home/sanmi/Documents/HS2/HS2_PROJECTS_2025/AIMS_LOCAL
bash setup_aims_profiling.sh
```

## 📊 Profile Your Data

### Command Line

```bash
# Profile all files
python profile_aims_parquet.py

# Profile specific file
python profile_aims_parquet.py --file aims_activitydates.parquet

# View profile only (no config generation)
python profile_aims_parquet.py --profile-only

# Custom settings
python profile_aims_parquet.py --null-tolerance 5.0 --severity high --output-dir config/custom
```

### Jupyter Notebook

```bash
jupyter notebook notebooks/03_Profile_AIMS_Data.ipynb
```

## 📁 Output Structure

```
AIMS_LOCAL/
├── config/data_quality/              # ← Generated validation configs
│   ├── aims_activitydates_validation.yml
│   ├── aims_assetattributes_validation.yml
│   └── ...
├── reports/                          # ← Profiling reports
│   └── aims_profiling_summary.csv
└── logs/                             # ← Profiling logs
```

## 🔧 Using Generated Configs

### In Python Scripts

```python
from dq_framework import ConfigLoader, DataValidator
import pandas as pd

# Load data
df = pd.read_parquet('data/aims_activitydates.parquet')

# Load config
config = ConfigLoader.load('config/data_quality/aims_activitydates_validation.yml')

# Validate
validator = DataValidator(config)
results = validator.validate(df)

if results['success']:
    print("✅ Validation passed")
else:
    print("❌ Validation failed:", results['failures'])
```

### In Notebooks

```python
# Load validation config
config = ConfigLoader.load('config/data_quality/aims_activitydates_validation.yml')

# Validate DataFrame
validator = DataValidator(config)
results = validator.validate(df)

# Display results
results['report'].show()
```

## 🎯 Common Tasks

### Profile New Data Directory

```bash
python profile_aims_parquet.py --data-dir data/NewDirectory --output-dir config/new_validations
```

### Re-profile After Schema Changes

```bash
# Re-run profiler (overwrites existing configs)
python profile_aims_parquet.py
```

### Customize Validation Rules

Edit the generated YAML files:

```yaml
# config/data_quality/aims_activitydates_validation.yml

expectations:
  # Add custom business rules
  - expectation_type: expect_column_values_to_be_between
    column: ActivityDate
    min_value: "2020-01-01"  # Project start date
    max_value: "2030-12-31"  # Reasonable future limit
    severity: high
```

## 💡 Tips

1. **Profile once, validate many times** - Generate configs initially, then use them for ongoing validation
2. **Version control your configs** - Track validation rule changes in Git
3. **Layer your validations** - Different rules for Bronze/Silver/Gold layers
4. **Document your rules** - Add comments to YAML files explaining business logic

## 🐛 Troubleshooting

### Import Error

```bash
# Re-run setup
bash setup_aims_profiling.sh
```

### Module Not Found

```bash
# Install manually
cd ../fabric_data_quality
pip install -e .
```

### Large Files

```python
# Profile with sampling
df = pd.read_parquet('large_file.parquet')
df_sample = df.sample(n=10000)
profiler.profile_dataframe(df_sample)
```

## 📚 Full Documentation

See [README_PROFILING.md](README_PROFILING.md) for complete documentation.

---

**Framework**: fabric_data_quality v1.0.0  
**Location**: `../fabric_data_quality`
