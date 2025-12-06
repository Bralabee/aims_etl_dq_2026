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
3.  Add the following **Environment Variables**.
    *   **Important**: Use **Relative Paths** (folder names only). The notebook automatically maps these to your Lakehouse structure (`/lakehouse/default/Files/...`).

    | Key | Value (Your Specific Setup) | Description |
    | :--- | :--- | :--- |
    | `BRONZE_PATH` | `13-11-2025` | The folder containing your raw parquet files. |
    | `SILVER_PATH` | `Silver` | Where validated data will be saved. |
    | `GOLD_PATH` | `Gold` | Where aggregated data will be saved. |
    | `CONFIG_DIR` | `dq_configs` | Where validation rules are stored. |
    | `STATE_DIR` | `state` | Where logs and watermarks are stored. |

    *Resulting Path*: `BRONZE_PATH` will resolve to `abfss://.../Files/13-11-2025`.

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

---

## Step 5: Orchestration (Triggers)

To ensure the pipeline only runs when **new data exists**, use a **Fabric Pipeline with a Storage Event Trigger**.

### 5.1 Create the Pipeline
1.  In your Fabric Workspace, create a new **Data Pipeline**.
2.  Add a **Notebook Activity** for each notebook (01, 02, 03) and chain them together:
    *    -> On Success ->  -> On Success -> 

### 5.2 Add the Event Trigger
1.  In the Pipeline editor, click the **Trigger** button (top menu) -> **OneLake events**.
2.  **Scope**: Select your Workspace and Lakehouse.
3.  **Event**: Select **File Created**.
4.  **Blob path begins with**: Enter the folder path where data lands (e.g., `Files/13-11-2025/` or just `Files/`).
    *   *Tip: Be specific to avoid triggering on temp files.*
5.  **Concurrency**: Set **Concurrency Control** to `1` in the Pipeline settings.
    *   *Why?* If 50 files arrive at once, you don't want 50 pipelines running. You want one pipeline to pick up all available files.

### 5.3 Alternative: Scheduled "Short-Circuit"
If you prefer a schedule (e.g., every hour) but want to avoid empty runs:
1.  The notebooks already contain logic to skip processed files.
2.  If no new files are found, the notebook finishes quickly (seconds), costing very little.

---

## Step 5: Orchestration (Triggers)

To ensure the pipeline only runs when **new data exists**, use a **Fabric Pipeline with a Storage Event Trigger**.

### 5.1 Create the Pipeline
1.  In your Fabric Workspace, create a new **Data Pipeline**.
2.  Add a **Notebook Activity** for each notebook (01, 02, 03) and chain them together:
    *   `Notebook 01` -> On Success -> `Notebook 02` -> On Success -> `Notebook 03`

### 5.2 Add the Event Trigger
1.  In the Pipeline editor, click the **Trigger** button (top menu) -> **OneLake events**.
2.  **Scope**: Select your Workspace and Lakehouse.
3.  **Event**: Select **File Created**.
4.  **Blob path begins with**: Enter the folder path where data lands (e.g., `Files/13-11-2025/` or just `Files/`).
    *   *Tip: Be specific to avoid triggering on temp files.*
5.  **Concurrency**: Set **Concurrency Control** to `1` in the Pipeline settings.
    *   *Why?* If 50 files arrive at once, you don't want 50 pipelines running. You want one pipeline to pick up all available files.

### 5.3 Alternative: Scheduled "Short-Circuit"
If you prefer a schedule (e.g., every hour) but want to avoid empty runs:
1.  The notebooks already contain logic to skip processed files.
2.  If no new files are found, the notebook finishes quickly (seconds), costing very little.

---

## Step 6: Notifications (Teams Alert)

To receive a notification when the pipeline completes successfully:

### 6.1 Add Teams Activity
1.  Open your Pipeline editor.
2.  In the **Activities** pane, search for **Teams**.
3.  Drag the **Teams** activity onto the canvas.
4.  Connect the **Success** output (green arrow) of `Notebook 03` to this Teams activity.

### 6.2 Configure the Message
1.  Select the Teams activity and go to the **Settings** tab.
2.  **Login**: You may need to sign in to authorize the connection.
3.  **Post in**: Select **Channel** or **Group Chat**.
4.  **Team/Channel**: Select the specific Team and Channel (e.g., "Data Engineering" > "Alerts").
5.  **Message**: Enter a message like:
    > ✅ **AIMS Pipeline Success**
    >
    > The Data Quality and Ingestion pipeline has completed successfully.
    > Check the [Monitoring Dashboard] for details.
    
    *Tip: You can use dynamic content to include the Run ID or time.*
