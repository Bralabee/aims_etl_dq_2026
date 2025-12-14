# 🚀 Quick Start: Profile AIMS Parquet Files

## TL;DR

```bash
cd /home/sanmi/Documents/HS2/HS2_PROJECTS_2025/AIMS_LOCAL
bash profile_with_fabric_dq.sh
```

That's it! This will profile all 4 AIMS parquet files and generate validation configs.

---

## What You Have

1. **`fabric_data_quality/`** - The framework (already exists, no changes needed)
2. **AIMS parquet files** - Your data in `data/Samples_LH_Bronze_Aims_26_parquet/`:
   - aims_activitydates.parquet
   - aims_assetattributes.parquet
   - aims_assetclassattributes.parquet
   - aims_assetclasschangelogs.parquet

## What You Need

**Profile the data** to generate validation configs (one-time setup).

---

## Three Ways to Do It

### Option 1: Bash Script (Easiest) ⭐

```bash
cd /home/sanmi/Documents/HS2/HS2_PROJECTS_2025/AIMS_LOCAL
bash profile_with_fabric_dq.sh
```

**What it does**:
- Profiles all 4 parquet files
- Generates 4 YAML validation configs
- Saves to `config/data_quality/`

**Time**: ~2-5 minutes

---

### Option 2: Python Script (Most Detailed)

```bash
cd /home/sanmi/Documents/HS2/HS2_PROJECTS_2025/AIMS_LOCAL
python use_fabric_dq_directly.py
```

**What it does**:
- Same as Option 1
- Plus: Shows detailed analysis for each file
- Plus: Demonstrates validation example
- Plus: Provides next steps

**Time**: ~2-5 minutes

---

### Option 3: Manual CLI (One File at a Time)

```bash
cd /home/sanmi/Documents/HS2/HS2_PROJECTS_2025/fabric_data_quality

python profile_data.py \
    ../AIMS_LOCAL/data/Samples_LH_Bronze_Aims_26_parquet/aims_activitydates.parquet \
    --output ../AIMS_LOCAL/config/data_quality/aims_activitydates_validation.yml \
    --null-tolerance 10.0 \
    --severity medium
```

Repeat for each file.

**Time**: ~1 minute per file

---

## What You Get

After running any option, you'll have:

```
AIMS_LOCAL/
└── config/
    └── data_quality/
        ├── aims_activitydates_validation.yml          ← Generated!
        ├── aims_assetattributes_validation.yml        ← Generated!
        ├── aims_assetclassattributes_validation.yml   ← Generated!
        └── aims_assetclasschangelogs_validation.yml   ← Generated!
```

Each YAML file contains:
- 20-50 auto-generated validation rules
- Column type checks
- Null value checks
- Range validations
- Uniqueness checks

---

## How to Use the Configs

### In Your Python Code

```python
import sys
sys.path.insert(0, '/home/sanmi/Documents/HS2/HS2_PROJECTS_2025/fabric_data_quality')

from dq_framework import DataQualityValidator, ConfigLoader
import pandas as pd

# Load new data
df = pd.read_parquet('data/new_batch/aims_activitydates.parquet')

# Validate using config you created once
config = ConfigLoader().load('config/data_quality/aims_activitydates_validation.yml')
validator = DataQualityValidator(config_dict=config)
results = validator.validate(df)

# Check results
if results['success']:
    print("✅ Data quality passed!")
else:
    print(f"❌ Failed: {results['failed_checks']} issues")
```

### In Notebooks

```python
# Add to first cell
import sys
sys.path.insert(0, '/home/sanmi/Documents/HS2/HS2_PROJECTS_2025/fabric_data_quality')

# Then use normally
from dq_framework import DataQualityValidator, ConfigLoader
# ... rest of your code
```

---

## Next Steps After Profiling

1. **Review the YAML files**
   ```bash
   cd config/data_quality
   cat aims_activitydates_validation.yml
   ```

2. **Customize (optional)**
   - Add business-specific rules
   - Adjust thresholds
   - Change severity levels

3. **Use in your pipeline**
   - Import dq_framework
   - Load config
   - Validate data
   - Handle failures

4. **Done!**
   - No need to re-profile
   - Use same configs forever
   - Update only when schema changes

---

## Troubleshooting

### "Module not found: dq_framework"

The scripts already handle this by adding fabric_data_quality to Python path:
```python
sys.path.insert(0, '/home/sanmi/Documents/HS2/HS2_PROJECTS_2025/fabric_data_quality')
```

### "File not found"

Check paths:
- Data dir: `data/Samples_LH_Bronze_Aims_26_parquet/`
- Fabric DQ: `../fabric_data_quality/`

### "Great Expectations error"

Make sure pandas and great-expectations are installed:
```bash
pip install pandas great-expectations pyarrow
```

---

## Full Documentation

See `FABRIC_DQ_COMPLETE_GUIDE.md` for complete understanding of how it all works.

---

## Ready?

```bash
cd /home/sanmi/Documents/HS2/HS2_PROJECTS_2025/AIMS_LOCAL
bash profile_with_fabric_dq.sh
```

**That's it!** 🎉
