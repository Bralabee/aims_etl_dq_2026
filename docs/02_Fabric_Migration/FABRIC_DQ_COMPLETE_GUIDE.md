# 📚 Complete Understanding: fabric_data_quality Framework

## 🎯 Executive Summary

`fabric_data_quality` is a **universal, reusable data quality framework** built on Great Expectations. It follows a **"profile once, validate forever"** philosophy.

**Key Principle**: Profile your data ONCE to understand it, then use the generated validation config for ALL future data batches.

---

## 🏗️ Architecture & Components

### Core Modules

#### 1. **DataProfiler** (`dq_framework/data_profiler.py`)
**Purpose**: Automatically analyze data and generate validation rules

**What it does**:
- Loads data from any source (CSV, Parquet, Excel, JSON)
- Analyzes each column:
  - Data type (int, float, string, datetime)
  - Semantic type (ID, date, categorical, monetary, code, text)
  - Null percentage
  - Uniqueness (% of unique values)
  - Statistics (min, max, mean, median, std for numerics)
  - String lengths (min, max, avg for strings)
  - Sample values
- Calculates overall data quality score (0-100)
- **Auto-generates validation expectations** based on patterns found

**Smart Detection**:
```python
# It automatically detects:
- IDs: High uniqueness + "id" in column name
- Dates: datetime type or parseable dates
- Codes: "code" or "nr" in name, alphanumeric
- Monetary: "amount", "value", "price" in name
- Categorical: Low uniqueness (< 5%)
- Text: Strings with avg length > 50 chars
```

**Generated Expectations**:
- Structural: Table not empty, column count stable, columns exist
- Completeness: Not null (if currently < tolerance)
- Validity:
  - IDs must be unique
  - Numeric values within observed range
  - Categorical values in known set
  - String lengths within observed range

#### 2. **DataQualityValidator** (`dq_framework/validator.py`)
**Purpose**: Execute validation checks using Great Expectations

**What it does**:
- Loads YAML configuration files
- Creates Great Expectations context (ephemeral, in-memory)
- Builds expectation suite from config
- Runs validation against DataFrame
- Returns detailed results:
  - `success`: bool (all checks passed?)
  - `evaluated_checks`: int (total checks run)
  - `failed_checks`: int (how many failed)
  - `success_rate`: float (percentage)
  - `details`: list (failure details)
  - `timestamp`: str (when validated)

#### 3. **ConfigLoader** (`dq_framework/config_loader.py`)
**Purpose**: Parse and load YAML validation configs

**YAML Structure**:
```yaml
validation_name: my_validation
description: Data quality checks
expectations:
  - expectation_type: expect_column_to_exist
    kwargs:
      column: customer_id
    meta:
      severity: critical
      description: Customer ID column must exist
```

#### 4. **FabricDataQualityRunner** (`dq_framework/fabric_connector.py`)
**Purpose**: Microsoft Fabric integration

**What it does**:
- Validates Delta tables in Fabric lakehouses
- Works with Spark DataFrames
- Integrates with Fabric notebooks

#### 5. **profile_data.py** (CLI Tool)
**Purpose**: Universal command-line data profiler

**Supported Formats**:
- ✅ CSV (auto-detects encoding: utf-8, latin-1, iso-8859-1, cp1252)
- ✅ Parquet
- ✅ Excel (.xlsx, .xls)
- ✅ JSON

**Usage**:
```bash
python profile_data.py <file> [options]

Options:
  --output PATH               # Where to save validation config
  --name NAME                 # Validation name
  --description DESC          # Description
  --null-tolerance FLOAT      # % of nulls to allow (default: 5.0)
  --severity LEVEL            # critical|high|medium|low (default: medium)
  --sample INT                # Sample size for large files
  --profile-only              # Just show profile, don't generate config
  --encoding ENCODING         # CSV encoding
```

---

## 🔄 How It Works: The Workflow

### Phase 1: Profiling (ONE-TIME)

```
Input Data → DataProfiler
              ↓
         Analyze Structure:
         - Column types
         - Null percentages  
         - Uniqueness
         - Value ranges
         - Patterns
              ↓
         Detect Semantic Types:
         - IDs, dates, categories
         - Monetary, codes, text
              ↓
         Generate Expectations:
         - Structural checks
         - Completeness checks
         - Validity checks
              ↓
         Save YAML Config
```

### Phase 2: Customization (ONE-TIME)

```
Generated YAML Config
       ↓
   Review & Enhance:
   - Add business rules
   - Adjust thresholds
   - Set severity levels
   - Add descriptions
       ↓
   Save to Project Config
```

### Phase 3: Validation (REPEATED - Every Data Load)

```
New Data Batch
       ↓
Load Same YAML Config  ← (No re-profiling!)
       ↓
DataQualityValidator
       ↓
Run Great Expectations
       ↓
Get Results:
- Pass/Fail
- Failure details
- Success rate
       ↓
Handle Failures:
- Log issues
- Send alerts
- Reject batch
- Continue with warnings
```

---

## 📊 What Gets Detected & Generated

### Column Analysis

For each column, the profiler determines:

| Aspect | Description | Used For |
|--------|-------------|----------|
| **Data Type** | pandas dtype (int64, float64, object, datetime64) | Type validation |
| **Semantic Type** | Detected purpose (ID, date, categorical, etc.) | Smart expectations |
| **Null %** | Percentage of missing values | Completeness checks |
| **Uniqueness** | % unique values vs total rows | ID detection, cardinality |
| **Statistics** | min, max, mean, median, std | Range validation |
| **Lengths** | String length stats | Length validation |
| **Samples** | Example values | Category validation |

### Semantic Type Detection Logic

```python
ID: 
  - > 90% unique values
  - Column name contains "id" or "uniqid"
  → Generates: expect_column_values_to_be_unique

Date:
  - datetime64 type OR parseable as dates
  → Generates: Date range expectations

Code:
  - Column name contains "code" or "nr"
  - Alphanumeric, limited length
  → Generates: Length and pattern expectations

Monetary:
  - Numeric type
  - Column name contains "amount", "value", "price"
  → Generates: Numeric range expectations

Categorical:
  - < 5% unique values
  → Generates: expect_column_values_to_be_in_set

Text:
  - String type with avg length > 50 chars
  → Generates: Length expectations
```

### Auto-Generated Expectations

#### Structural (Table-Level)
```yaml
- expectation_type: expect_table_row_count_to_be_between
  kwargs: {min_value: 1, max_value: null}
  meta: {severity: critical, description: 'Table should not be empty'}

- expectation_type: expect_table_column_count_to_equal
  kwargs: {value: 42}
  meta: {severity: high, description: 'Detect schema drift'}
```

#### Completeness (Column-Level)
```yaml
- expectation_type: expect_column_to_exist
  kwargs: {column: customer_id}
  meta: {severity: critical, description: 'Column must exist'}

- expectation_type: expect_column_values_to_not_be_null
  kwargs: {column: customer_id}
  meta: {severity: high, description: 'Minimal nulls (currently 2.3%)'}
```

#### Validity (Data Quality)
```yaml
# For ID columns
- expectation_type: expect_column_values_to_be_unique
  kwargs: {column: transaction_id}
  meta: {severity: critical}

# For numeric columns
- expectation_type: expect_column_values_to_be_between
  kwargs: {column: amount, min_value: 0.0, max_value: 999999.99}
  meta: {severity: medium}

# For categorical columns
- expectation_type: expect_column_values_to_be_in_set
  kwargs: {column: status, value_set: ['active', 'pending', 'closed']}
  meta: {severity: medium}

# For string columns
- expectation_type: expect_column_value_lengths_to_be_between
  kwargs: {column: product_code, min_value: 8, max_value: 12}
  meta: {severity: low}
```

---

## 💡 Key Features

### 1. Universal Format Support
Works with any data source that pandas can read:
- CSV (with auto-encoding detection)
- Parquet
- Excel
- JSON
- SQL databases (via pandas)
- Spark DataFrames (via Fabric integration)

### 2. Smart Profiling
- **Sampling**: Can sample large datasets for performance
- **Type Detection**: Automatically detects semantic types beyond pandas dtypes
- **Quality Score**: Calculates 0-100 score based on nulls and cardinality

### 3. Configurable Generation
Control what expectations get generated:
```python
profiler.generate_expectations(
    include_structural=True,      # Table-level checks
    include_completeness=True,    # Null checks
    include_validity=True,        # Range/pattern checks
    null_tolerance=10.0,          # Allow up to 10% nulls
    severity_threshold='medium'   # Default severity
)
```

### 4. Great Expectations Integration
Leverages the full power of Great Expectations:
- 50+ built-in expectation types
- Extensible with custom expectations
- Detailed validation reports
- Integration with data docs

### 5. Microsoft Fabric Ready
- Direct Delta table validation
- Spark DataFrame support
- Lakehouse integration
- Fabric notebook compatibility

---

## 🎯 Direct Usage for AIMS Parquet Files

### Method 1: CLI (Simplest)

```bash
cd /home/sanmi/Documents/HS2/HS2_PROJECTS_2025/fabric_data_quality

# Profile one file
python profile_data.py \
    /home/sanmi/Documents/HS2/HS2_PROJECTS_2025/AIMS_LOCAL/data/Samples_LH_Bronze_Aims_26_parquet/aims_activitydates.parquet \
    --output /home/sanmi/Documents/HS2/HS2_PROJECTS_2025/AIMS_LOCAL/config/data_quality/aims_activitydates_validation.yml \
    --null-tolerance 10.0 \
    --severity medium
```

### Method 2: Batch Script (Profile All Files)

```bash
cd /home/sanmi/Documents/HS2/HS2_PROJECTS_2025/AIMS_LOCAL
bash profile_with_fabric_dq.sh
```

This will profile all 4 parquet files and generate validation configs.

### Method 3: Python Script (Most Flexible)

```bash
cd /home/sanmi/Documents/HS2/HS2_PROJECTS_2025/AIMS_LOCAL
python use_fabric_dq_directly.py
```

This provides:
- Automated profiling of all files
- Detailed progress output
- Example validation run
- Summary reports

### Method 4: Interactive Python

```python
import sys
from pathlib import Path
import pandas as pd

# Add fabric_data_quality to path
sys.path.insert(0, '/home/sanmi/Documents/HS2/HS2_PROJECTS_2025/fabric_data_quality')

from dq_framework import DataProfiler

# Load your parquet file
df = pd.read_parquet('data/Samples_LH_Bronze_Aims_26_parquet/aims_activitydates.parquet')

# Profile it
profiler = DataProfiler(df)
profile = profiler.profile()

# Show summary
profiler.print_summary()

# Generate config
config = profiler.generate_expectations(
    validation_name='aims_activitydates',
    null_tolerance=10.0,
    severity_threshold='medium'
)

# Save config
profiler.save_config(config, 'config/data_quality/aims_activitydates_validation.yml')
```

---

## 📁 Output Structure

After profiling, you'll have:

```
AIMS_LOCAL/
└── config/
    └── data_quality/
        ├── aims_activitydates_validation.yml
        ├── aims_assetattributes_validation.yml
        ├── aims_assetclassattributes_validation.yml
        └── aims_assetclasschangelogs_validation.yml
```

Each YAML file contains:
- Validation metadata (name, description, timestamp)
- Data source info (rows, columns profiled)
- List of expectations (20-50 per file typically)

---

## 🔧 Using Generated Configs

### In Python Scripts

```python
import sys
sys.path.insert(0, '/home/sanmi/Documents/HS2/HS2_PROJECTS_2025/fabric_data_quality')

from dq_framework import DataQualityValidator, ConfigLoader
import pandas as pd

# Load new data batch
df = pd.read_parquet('data/new_batch/aims_activitydates.parquet')

# Load validation config (created once)
config = ConfigLoader().load('config/data_quality/aims_activitydates_validation.yml')

# Validate
validator = DataQualityValidator(config_dict=config)
results = validator.validate(df)

# Check results
if results['success']:
    print(f"✅ All {results['evaluated_checks']} checks passed")
    # Proceed with data processing
    process_data(df)
else:
    print(f"❌ {results['failed_checks']} checks failed")
    # Handle failures
    for detail in results['details']:
        print(f"  - {detail}")
    # Reject batch or log errors
```

### In Notebooks

```python
# Cell 1: Setup
import sys
sys.path.insert(0, '/home/sanmi/Documents/HS2/HS2_PROJECTS_2025/fabric_data_quality')
from dq_framework import DataQualityValidator, ConfigLoader
import pandas as pd

# Cell 2: Load and validate
df = pd.read_parquet('data/aims_activitydates.parquet')
config = ConfigLoader().load('config/data_quality/aims_activitydates_validation.yml')
validator = DataQualityValidator(config_dict=config)
results = validator.validate(df)

# Cell 3: Display results
print(f"Success: {results['success']}")
print(f"Success Rate: {results['success_rate']:.1f}%")
if not results['success']:
    display(pd.DataFrame(results['details']))
```

---

## 🎓 Best Practices

### 1. Profile Once Per Schema
- Profile when you first receive a dataset
- Re-profile only when schema changes
- Use same config for all future batches with same schema

### 2. Customize Thoughtfully
- Review auto-generated expectations
- Add business-specific rules
- Adjust severity levels appropriately
- Document your customizations

### 3. Layer Your Validations
```yaml
Bronze Layer (Raw):
  - Structural checks (columns exist, not empty)
  - Basic completeness (critical fields not null)
  - Severity: medium

Silver Layer (Cleaned):
  - Referential integrity
  - Format consistency
  - Value ranges
  - Severity: high

Gold Layer (Business):
  - Business rules
  - KPIs and metrics
  - Aggregation logic
  - Severity: critical
```

### 4. Version Control Configs
```bash
git add config/data_quality/*.yml
git commit -m "Add AIMS data validation configs"
```

### 5. Monitor Quality Scores
Track the `data_quality_score` over time to detect degradation.

---

## 🚀 Quick Start Commands

```bash
# Navigate to AIMS_LOCAL
cd /home/sanmi/Documents/HS2/HS2_PROJECTS_2025/AIMS_LOCAL

# Option 1: Use the batch script (easiest)
bash profile_with_fabric_dq.sh

# Option 2: Use the Python script (most detailed)
python use_fabric_dq_directly.py

# Option 3: Profile one file manually
cd ../fabric_data_quality
python profile_data.py \
    ../AIMS_LOCAL/data/Samples_LH_Bronze_Aims_26_parquet/aims_activitydates.parquet \
    --output ../AIMS_LOCAL/config/data_quality/aims_activitydates_validation.yml
```

---

## ✅ Summary

**What fabric_data_quality does**:
1. Analyzes your data automatically
2. Detects patterns and types
3. Generates validation rules
4. Saves reusable YAML configs
5. Validates future data batches

**Why it's powerful**:
- No manual rule writing
- Smart pattern detection
- Reusable across projects
- Built on Great Expectations
- Works with any data format

**How to use it for AIMS**:
1. Run `bash profile_with_fabric_dq.sh` (one-time)
2. Review generated YAML files
3. Customize with business rules
4. Use configs in your pipeline forever

**No code duplication needed** - just reference the framework directly!

---

**Ready to use!** Run `bash profile_with_fabric_dq.sh` to get started.
