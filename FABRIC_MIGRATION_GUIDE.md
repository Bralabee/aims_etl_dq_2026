# AIMS Project: Migration to Microsoft Fabric

This guide details the steps to migrate the AIMS Data Quality & Ingestion project from a local environment to Microsoft Fabric.

## Prerequisites

1.  **Microsoft Fabric Workspace**: You need access to a Fabric Workspace.
2.  **Lakehouse**: Create a new Lakehouse (e.g., named `AIMS_Lakehouse`).
3.  **Local Files**: Ensure you have the latest version of this repository.

---

## Step 1: Prepare OneLake Structure

We need to replicate the necessary file structure in your Fabric Lakehouse. You can do this via the Fabric UI or OneLake File Explorer.

### 1.1 Create Directories
In your Lakehouse, navigate to the **Files** section and ensure the following structure exists (or let the notebooks create the sub-folders):

```text
Files/
  ├── libs/                  <-- For the custom library
  ├── data/
  │   └── Samples_LH_Bronze_Aims_26_parquet/  <-- Upload your source data here
  └── .env                   <-- Configuration file
```

### 1.2 Upload the Library
Locate the `.whl` file in your local project:
`dq_great_expectations/dq_package_dist/fabric_data_quality-1.1.2-py3-none-any.whl`

**Action**: Upload this file to `Files/libs/` in your Lakehouse.

### 1.3 Upload Source Data
Locate your local bronze data:
`data/Samples_LH_Bronze_Aims_26_parquet/`

**Action**: Upload the `.parquet` files from this folder to `Files/data/Samples_LH_Bronze_Aims_26_parquet/` in your Lakehouse.

---

## Step 2: Configure Environment Variables

The notebooks use a `.env` file to manage paths dynamically.

**Action**: Create a file named `.env` in the root of your Lakehouse **Files** section (`Files/.env`) with the following content:

```ini
# Fabric Environment Configuration
BRONZE_PATH=data/Samples_LH_Bronze_Aims_26_parquet
SILVER_PATH=data/Silver
GOLD_PATH=data/Gold
CONFIG_DIR=dq_configs
STATE_DIR=data/state
```

*Note: The notebooks are configured to look for this file at `/lakehouse/default/Files/.env`.*

---

## Step 3: Import Notebooks

1.  Go to your Fabric Workspace.
2.  Select **Import** -> **Notebook**.
3.  Upload the following notebooks from your local `notebooks/` folder:
    *   `01_AIMS_Data_Profiling.ipynb`
    *   `02_AIMS_Data_Ingestion.ipynb`
    *   `03_AIMS_Monitoring.ipynb`

---

## Step 4: Run the Pipeline

Open each notebook and ensure it is **attached to your Lakehouse** (add the Lakehouse in the left sidebar explorer if not already attached).

### 4.1 Run Notebook 01: Data Profiling
*   **Purpose**: Scans the Bronze data and generates Data Quality (DQ) configurations.
*   **Output**: Creates YAML config files in `Files/dq_configs/`.
*   **Verification**: Check the `dq_configs` folder in the Lakehouse explorer after running.

### 4.2 Run Notebook 02: Data Ingestion
*   **Purpose**: Validates data against the configs, moves valid data to Silver, and logs results.
*   **Output**: 
    *   Valid data -> `Files/data/Silver/`
    *   Logs -> `Files/data/state/dq_logs.jsonl`
    *   Watermarks -> `Files/data/state/watermarks.json`
*   **Note**: This notebook will automatically install the library from `Files/libs/` if it's not present.

### 4.3 Run Notebook 03: Monitoring
*   **Purpose**: Visualizes the results of the ingestion.
*   **Output**: Displays charts and tables of passed/failed checks.

---

## Troubleshooting

*   **Library Not Found**: Ensure the `.whl` file is exactly at `Files/libs/fabric_data_quality-1.1.2-py3-none-any.whl`.
*   **Directories Missing**: The notebooks are designed to create `Silver`, `Gold`, `dq_configs`, and `state` directories automatically. If this fails, check your write permissions or create them manually.
*   **Path Errors**: Verify the `.env` file is in the root of `Files` and contains the correct relative paths.
