# AIMS Project: Migration to Microsoft Fabric

This guide details the steps to migrate the AIMS Data Quality & Ingestion project from a local environment to Microsoft Fabric, following best practices for Environments and Configuration.

## Prerequisites

1.  **Microsoft Fabric Workspace**: You need access to a Fabric Workspace.
2.  **Lakehouse**: Create a new Lakehouse (e.g., named `AIMS_Lakehouse`).
3.  **Fabric Environment**: Create a Fabric Environment artifact to manage libraries and settings.

---

## Step 1: Configure Fabric Environment (Libraries)

Instead of installing libraries inside the notebook every time, we will install them once in the Fabric Environment.

1.  **Create Environment**: In your Workspace, create a new **Environment** (e.g., `AIMS_Env`).
2.  **Upload Library**:
    *   Go to **Public Libraries** to install public packages (e.g., `great_expectations` if needed).
    *   Go to **Custom Libraries** -> **Upload**.
    *   Upload the local wheel file: `dq_great_expectations/dq_package_dist/fabric_data_quality-1.1.2-py3-none-any.whl`.
3.  **Publish**: Click **Publish** to make the environment ready.
4.  **Attach**: Go to your Workspace settings or the specific Notebook settings and attach this `AIMS_Env` environment.

---

## Step 2: Configure Environment Variables

The "Fabric way" to handle configuration (replacing `.env` files) is to use **Spark Properties** or **Environment Variables** within the Fabric Environment.

### Option A: Fabric Environment Variables (Recommended)
1.  Open your `AIMS_Env` Environment.
2.  Go to **Spark Properties** (or **Custom Configuration**).
3.  Add the following **Environment Variables** (Keys must match exactly what the notebook expects):

    | Key | Value (Example) |
    | :--- | :--- |
    | `BRONZE_PATH` | `data/Samples_LH_Bronze_Aims_26_parquet` |
    | `SILVER_PATH` | `data/Silver` |
    | `GOLD_PATH` | `data/Gold` |
    | `CONFIG_DIR` | `dq_configs` |
    | `STATE_DIR` | `data/state` |

    *Note: Use **relative paths** (e.g., `data/Silver`) because the notebook automatically prepends `/lakehouse/default/Files/`.*

### Option B: Startup Script (Robust Alternative)
1.  Create a python script named `set_env.py` locally:
    ```python
    import os
    os.environ["BRONZE_PATH"] = "data/Samples_LH_Bronze_Aims_26_parquet"
    os.environ["SILVER_PATH"] = "data/Silver"
    os.environ["GOLD_PATH"] = "data/Gold"
    os.environ["CONFIG_DIR"] = "dq_configs"
    os.environ["STATE_DIR"] = "data/state"
    ```
2.  Upload this script to your Lakehouse Files (e.g., `Files/scripts/set_env.py`).
3.  In your notebooks, add `%run /lakehouse/default/Files/scripts/set_env.py` at the top.

### Option C: The .env File (Simple & Portable)
If you prefer to keep it simple and consistent with local development:
1.  Upload your `.env` file to `Files/.env` in the Lakehouse.
2.  The notebooks are already configured to look for this file.

---

## Step 3: Prepare OneLake Structure

1.  **Upload Source Data**:
    *   Upload the `.parquet` files from `data/Samples_LH_Bronze_Aims_26_parquet/` to `Files/data/Samples_LH_Bronze_Aims_26_parquet/` in your Lakehouse.

---

## Step 4: Import & Run Notebooks

1.  **Import Notebooks**: Upload `01`, `02`, and `03` to your Workspace.
2.  **Attach Lakehouse**: Ensure each notebook is attached to `AIMS_Lakehouse`.
3.  **Attach Environment**: Ensure each notebook is using `AIMS_Env`.
4.  **Run**:
    *   **01_AIMS_Data_Profiling**: Generates configs.
    *   **02_AIMS_Data_Ingestion**: Ingests data.
    *   **03_AIMS_Monitoring**: Displays dashboard.

---

## Troubleshooting

*   **Module Not Found**: If `import fabric_data_quality` fails, ensure you **Published** the Environment and **Attached** it to the notebook.
*   **Directories**: The notebooks will automatically create `Silver`, `Gold`, etc.
