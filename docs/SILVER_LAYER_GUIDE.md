# Silver Layer Transformation

## Overview

The Silver Layer transformation module converts Bronze layer Parquet files into a structured **Star Schema** optimized for business intelligence and reporting.

## Star Schema Design

### Fact Table
- **FACT_Asset_Inventory**: Central fact table containing asset inventory with foreign keys to all dimensions

### Dimension Tables
1. **DIM_Route**: Route reference data (33 routes)
2. **DIM_AssetClass**: Asset classification hierarchy (5,644 classes)
3. **DIM_Organisation**: Organizational entities and ownership (28 organizations)
4. **DIM_Date**: Calendar dimension for time-based analysis
5. **DIM_Status**: Asset status codes and descriptions

## Usage

### From Notebook
Run `notebooks/07_AIMS_DQ_Matrix_and_Modeling.ipynb` to:
1. Generate the Data Quality Matrix
2. Create Silver Layer tables interactively
3. Visualize the DQ coverage

### From Command Line

```bash
# Using the installed CLI tool
aims-silver-transform \
    --bronze-dir data/Samples_LH_Bronze_Aims_26_parquet \
    --silver-dir data/silver_layer \
    --row-limit 100000

# Or as a Python module
python -m aims_data_platform.silver_layer_transform \
    --bronze-dir data/Samples_LH_Bronze_Aims_26_parquet \
    --silver-dir data/silver_layer
```

### Programmatic Usage

```python
from aims_data_platform.silver_layer_transform import SilverLayerTransformer
from pathlib import Path

transformer = SilverLayerTransformer(
    bronze_dir=Path("data/bronze"),
    silver_dir=Path("data/silver"),
    row_limit=100000
)

results = transformer.run()

# Access individual tables
fact_table = results['FACT_Asset_Inventory']
dim_route = results['DIM_Route']
```

## Output Files

All tables are saved as Parquet files in the specified `silver_dir`:

```
silver_layer/
├── FACT_Asset_Inventory.parquet    # ~100k rows (sampled)
├── DIM_Route.parquet                # 33 rows
├── DIM_AssetClass.parquet           # 5,644 rows
├── DIM_Organisation.parquet         # 28 rows
├── DIM_Date.parquet                 # Variable (based on date range)
└── DIM_Status.parquet               # Variable (unique statuses)
```

## BI Tool Integration

### PowerBI / Tableau Setup

1. **Connect to Data Source**: Point to the `silver_layer/` directory
2. **Configure Relationships**:
   - `FACT_Asset_Inventory.Route_Key` → `DIM_Route.Route_Key`
   - `FACT_Asset_Inventory.Class_Key` → `DIM_AssetClass.Class_Key`
   - `FACT_Asset_Inventory.Owner_Key` → `DIM_Organisation.Owner_Key`
   - `FACT_Asset_Inventory.Asset_Status` → `DIM_Status.Status_Key`

3. **Build Reports** using measures like:
   - Asset Count by Route
   - Asset Distribution by Class
   - Status Trends over Time (using DIM_Date)
   - Organizational Ownership Analysis

## Automation

### Daily Pipeline Integration

Add to your ETL pipeline (Airflow, Fabric, etc.):

```python
# Airflow DAG example
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG('aims_silver_layer', start_date=datetime(2025, 1, 1), schedule_interval='@daily') as dag:
    
    transform_task = BashOperator(
        task_id='silver_transform',
        bash_command='aims-silver-transform --bronze-dir /data/bronze --silver-dir /data/silver'
    )
```

### Microsoft Fabric Notebook

Schedule `notebooks/07_AIMS_DQ_Matrix_and_Modeling.ipynb` as a Fabric pipeline activity.

## Data Quality Matrix

The DQ Matrix provides a comprehensive view of validation rule coverage across all AIMS tables:

### Dimensions Tracked
- **Completeness**: Null checks (highest priority)
- **Validity**: Schema and type validation
- **Uniqueness**: Primary key and duplicate detection
- **Consistency**: Row/column count checks
- **Accuracy**: Custom business rules

### Key Insights
- Tables with 35+ total rules are considered **high-risk**
- `noncompliances` has the highest coverage (185 rules)
- The matrix can be used to prioritize data remediation efforts

## Version History

- **v1.1.0** (2025-12-08): Added Silver Layer transformation and DQ Matrix
- **v1.0.2**: Initial Bronze layer profiling and reconciliation
