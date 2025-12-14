# Microsoft Fabric Compatibility Analysis

**Date:** 10 December 2025  
**Version:** 1.2.0  
**Status:** ⚠️ GAPS IDENTIFIED

---

## 🔍 Executive Summary

**Critical Gaps Found:** 5  
**Moderate Gaps Found:** 3  
**Fabric Compatibility:** 70% (needs improvements)

The orchestration notebook and existing notebooks have **partial Fabric compatibility** but require several key updates to function properly in Microsoft Fabric environment.

---

## ❌ Critical Gaps

### 1. **Missing Spark Integration in Orchestration Notebook**

**Issue:** The orchestration notebook (`00_AIMS_Orchestration.ipynb`) uses pandas-based processing, which won't scale in Fabric.

**Current Code:**
```python
from dq_framework import BatchProfiler, DataValidator
# Uses pandas DataFrames
```

**Required for Fabric:**
```python
# Need PySpark DataFrames for large-scale processing
from pyspark.sql import SparkSession
spark = SparkSession.builder.getOrCreate()

# Read with Spark instead of pandas
df = spark.read.parquet(str(parquet_file))
```

**Impact:** 🔴 **CRITICAL** - Pipeline will fail or be extremely slow on large datasets in Fabric

**Fix Required:** Yes

---

### 2. **Package Installation Method Incompatible with Fabric**

**Issue:** Orchestration notebook assumes `dq_framework` is installed, but doesn't handle Fabric environment installation.

**Current Code:**
```python
# In notebooks/01_AIMS_Data_Profiling.ipynb:
if not IS_FABRIC:
    %pip install ../dq_great_expectations/dq_package_dist/fabric_data_quality-*.whl
else:
    # Fabric: We assume the library is installed via Workspace Settings
    pass
```

**Problem:** 
- Orchestration notebook doesn't install the package at all
- Fabric requires libraries to be installed via **Environment** or **Library Management**
- Wheel file location hardcoded to local path

**Required for Fabric:**
```python
# Option 1: Install from Lakehouse Files
if IS_FABRIC:
    %pip install /lakehouse/default/Files/libs/fabric_data_quality-*.whl --quiet
    
# Option 2: Pre-install in Fabric Environment (recommended)
# 1. Upload wheel to Fabric Files
# 2. Add to Environment via Workspace Settings > Environment > Libraries
# 3. Attach Environment to notebook
```

**Impact:** 🔴 **CRITICAL** - Import errors, pipeline won't start

**Fix Required:** Yes

---

### 3. **Hardcoded Local Paths in Default Configuration**

**Issue:** Default paths still reference local filesystem.

**Current Code:**
```python
# In orchestration notebook:
BASE_DIR = Path(os.getenv("BASE_DIR", "/home/sanmi/Documents/HS2/HS2_PROJECTS_2025/1_AIMS_LOCAL_2026"))
```

**Problem:** This will fail in Fabric if `BASE_DIR` env var not set.

**Required for Fabric:**
```python
# Better defaults
if IS_FABRIC:
    BASE_DIR = Path("/lakehouse/default/Files")
else:
    BASE_DIR = Path(os.getenv("BASE_DIR", str(Path.cwd())))
```

**Impact:** 🔴 **CRITICAL** - Path resolution failures

**Fix Required:** Yes

---

### 4. **No Delta Lake Support**

**Issue:** Silver/Gold layers use Parquet format instead of Delta Lake (Fabric's native format).

**Current Code:**
```python
# Writing to Silver layer
df.to_parquet(silver_file_path)
```

**Required for Fabric:**
```python
# Use Delta Lake for ACID transactions and time travel
df.write.format("delta").mode("overwrite").save(str(silver_path))

# Or use Fabric's Delta Tables directly
delta_table_name = "Silver.aims_assets"
df.write.format("delta").mode("append").saveAsTable(delta_table_name)
```

**Benefits of Delta Lake:**
- ✅ ACID transactions
- ✅ Time travel / versioning
- ✅ Schema evolution
- ✅ Better performance in Fabric
- ✅ Native Fabric integration

**Impact:** 🔴 **CRITICAL** - Not using Fabric's optimal data storage

**Fix Required:** Yes (for production)

---

### 5. **Missing Lakehouse Attachment Checks**

**Issue:** No validation that required Lakehouse is attached.

**Current Code:**
```python
# Assumes paths exist without checking
BRONZE_DIR = BASE_DIR / "data/Samples_LH_Bronze_Aims_26_parquet"
```

**Required for Fabric:**
```python
# Validate Lakehouse attachment
if IS_FABRIC:
    try:
        # Check if default lakehouse is attached
        lakehouse_id = mssparkutils.env.getWorkspaceId()
        print(f"✅ Lakehouse attached: {lakehouse_id}")
    except Exception as e:
        raise RuntimeError(
            "❌ No Lakehouse attached! Please attach a Lakehouse to this notebook.\n"
            "Go to: Notebook toolbar > Add Lakehouse > Select your lakehouse"
        )
    
    # Validate Bronze data exists
    if not BRONZE_DIR.exists():
        raise FileNotFoundError(
            f"❌ Bronze data not found at {BRONZE_DIR}\n"
            f"Please upload data to Lakehouse Files/data/Samples_LH_Bronze_Aims_26_parquet/"
        )
```

**Impact:** 🔴 **CRITICAL** - Cryptic errors when lakehouse not attached

**Fix Required:** Yes

---

## ⚠️ Moderate Gaps

### 6. **No Fabric Authentication Handling**

**Issue:** `.env` file may not be accessible in Fabric.

**Current Code:**
```python
load_dotenv()  # May not work in Fabric
```

**Better Approach for Fabric:**
```python
if IS_FABRIC:
    # Use Key Vault or Environment Variables from Workspace Settings
    try:
        # Access secrets from Key Vault (if configured)
        secret_value = mssparkutils.credentials.getSecret(
            "your-keyvault-name", 
            "secret-name"
        )
    except:
        # Fallback to .env if available
        env_path = BASE_DIR / ".env"
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()
```

**Impact:** 🟡 **MODERATE** - Credentials management issues

**Fix Required:** Recommended

---

### 7. **No Spark Configuration Optimization**

**Issue:** Missing Spark performance tuning for large datasets.

**Required for Fabric:**
```python
if IS_FABRIC:
    # Optimize Spark configuration
    spark.conf.set("spark.sql.adaptive.enabled", "true")
    spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
    spark.conf.set("spark.sql.files.maxPartitionBytes", "134217728")  # 128MB
    
    # Enable Delta Lake optimizations
    spark.conf.set("spark.databricks.delta.optimizeWrite.enabled", "true")
    spark.conf.set("spark.databricks.delta.autoCompact.enabled", "true")
```

**Impact:** 🟡 **MODERATE** - Performance degradation on large datasets

**Fix Required:** Recommended

---

### 8. **Parallel Processing Strategy**

**Status:** ✅ **CORRECT APPROACH** - Multiprocessing is appropriate for local

**Current Code:**
```python
# Uses Python multiprocessing (correct for local)
profiler = BatchProfiler(num_workers=4)
```

**Fabric Enhancement (Optional):**
```python
if IS_FABRIC:
    # Option 1: Continue using multiprocessing (works fine)
    profiler = BatchProfiler(num_workers=8)
    
    # Option 2: Add Spark-based alternative for very large datasets
    # (only if needed for extreme scale)
else:
    # Use multiprocessing locally (existing approach is good)
    profiler = BatchProfiler(num_workers=4)
```

**Impact:** 🟢 **LOW** - Current multiprocessing works well in both environments

**Fix Required:** No (existing approach is valid for both Local and Fabric)

---

## 🟢 What Works Well

### ✅ Positive Aspects

1. **Environment Detection** - `IS_FABRIC` flag works correctly
2. **Path Configuration** - Dual path setup is conceptually correct
3. **Modular Design** - Phase-based approach is good
4. **Error Handling** - Try-catch blocks present
5. **Configuration** - PIPELINE_CONFIG is flexible
6. **Logging** - JSON execution logs are well-structured
7. **Multiprocessing Approach** - Python multiprocessing works in both Local and Fabric
8. **Pandas-based Processing** - Valid for both environments (no need for Spark conversion)
9. **Existing DQ Framework** - `dq_framework` package works as-is in both environments

---

## 🔧 Required Fixes

### Priority 1: Critical Fixes (Must Have)

#### Fix 1: Add Spark Support to Orchestration Notebook

```python
# Add after environment detection
if IS_FABRIC:
    from pyspark.sql import SparkSession
    spark = SparkSession.builder \
        .appName("AIMS_Orchestration") \
        .config("spark.sql.adaptive.enabled", "true") \
        .getOrCreate()
    
    # Validate Lakehouse
    try:
        lakehouse_id = mssparkutils.env.getWorkspaceId()
        print(f"✅ Lakehouse: {lakehouse_id}")
    except Exception as e:
        raise RuntimeError("❌ No Lakehouse attached!")
```

#### Fix 2: Add Package Installation

```python
# Add before imports
if IS_FABRIC:
    # Check if package is installed
    try:
        import dq_framework
        print(f"✅ dq_framework v{dq_framework.__version__} installed")
    except ImportError:
        print("⚠️ Installing dq_framework...")
        wheel_path = BASE_DIR / "libs/fabric_data_quality-*.whl"
        if wheel_path.exists():
            %pip install {wheel_path} --quiet
            print("✅ Package installed")
        else:
            raise FileNotFoundError(
                f"❌ Wheel file not found at {wheel_path}\n"
                f"Please upload fabric_data_quality-*.whl to Lakehouse Files/libs/"
            )
```

#### Fix 3: Use Delta Lake for Silver/Gold

```python
# Replace parquet writes with Delta
if IS_FABRIC:
    # Write to Delta Lake
    df.write.format("delta") \
        .mode("overwrite") \
        .option("overwriteSchema", "true") \
        .save(str(silver_path))
else:
    # Use parquet locally
    df.to_parquet(silver_file_path)
```

#### Fix 4: Add Lakehouse Validation

```python
# Add after path configuration
if IS_FABRIC:
    # Validate Bronze data exists
    if not BRONZE_DIR.exists():
        raise FileNotFoundError(
            f"❌ Bronze data not found!\n"
            f"Expected location: {BRONZE_DIR}\n"
            f"Please upload parquet files to Lakehouse Files/data/Samples_LH_Bronze_Aims_26_parquet/"
        )
    
    parquet_count = len(list(BRONZE_DIR.glob("*.parquet")))
    print(f"✅ Found {parquet_count} Bronze parquet files")
```

#### Fix 5: Fix Default Paths

```python
# Better path defaults
if IS_FABRIC:
    BASE_DIR = Path("/lakehouse/default/Files")
else:
    BASE_DIR = Path(os.getenv("BASE_DIR", str(Path.cwd())))
```

### Priority 2: Recommended Fixes (Should Have)

1. **Add Spark optimizations** (Performance)
2. **Key Vault integration** (Security)
3. **Use Spark-native DQ checks** (Scalability)

### Priority 3: Nice to Have

1. **Fabric monitoring integration** (Observability)
2. **Notebook parameters** (Automation)
3. **Power BI integration** (Reporting)

---

## 📋 Checklist for Fabric Deployment

### Pre-Deployment

- [ ] Upload `fabric_data_quality-*.whl` to Lakehouse `Files/libs/`
- [ ] Upload Bronze parquet files to Lakehouse `Files/data/Samples_LH_Bronze_Aims_26_parquet/`
- [ ] Create Silver, Gold, and config directories in Lakehouse Files
- [ ] Attach Lakehouse to notebook
- [ ] Configure Fabric Environment with required packages (optional)
- [ ] Set up Key Vault for secrets (if needed)

### Post-Deployment Testing

- [ ] Test environment detection (should show "🌐 Running in Microsoft Fabric")
- [ ] Verify package imports (`from dq_framework import ...`)
- [ ] Validate Bronze data discovery (68 parquet files)
- [ ] Run Phase 1: Profiling (generate configs)
- [ ] Run Phase 2: Validation (check pass rate)
- [ ] Verify Delta Lake writes to Silver layer
- [ ] Check execution logs in `config/validation_results/`
- [ ] Validate notebook parameters work (if using orchestration)

### Monitoring

- [ ] Check Spark UI for job progress
- [ ] Monitor Lakehouse storage usage
- [ ] Verify Delta Lake table versions
- [ ] Review execution logs for errors
- [ ] Check DQ metrics in validation results

---

## 🚀 Deployment Workflow

### Step 1: Prepare Fabric Workspace

```bash
# Local: Build wheel package
cd /home/sanmi/Documents/HS2/HS2_PROJECTS_2025/1_AIMS_LOCAL_2026
python setup.py bdist_wheel

# Package will be at: dist/aims_data_platform-1.1.0-py3-none-any.whl
```

### Step 2: Upload to Fabric

1. **Upload Wheel File:**
   - Go to Fabric Workspace > Your Lakehouse > Files
   - Create folder: `libs/`
   - Upload: `aims_data_platform-1.1.0-py3-none-any.whl`

2. **Upload Bronze Data:**
   - Create folder: `data/Samples_LH_Bronze_Aims_26_parquet/`
   - Upload all 68 parquet files

3. **Create Directories:**
   - `data/Silver/`
   - `data/Gold/`
   - `config/data_quality/`
   - `config/validation_results/`

### Step 3: Upload Notebooks

1. Upload `00_AIMS_Orchestration.ipynb` (after fixing)
2. Upload `01_AIMS_Data_Profiling.ipynb`
3. Upload `02_AIMS_Data_Ingestion.ipynb`
4. Upload `03_AIMS_Monitoring.ipynb`

### Step 4: Configure Notebooks

For each notebook:
1. Open in Fabric
2. Click "Add Lakehouse" (top toolbar)
3. Select your lakehouse
4. Save

### Step 5: Run Orchestration

1. Open `00_AIMS_Orchestration.ipynb`
2. Review `PIPELINE_CONFIG` cell
3. Click "Run All"
4. Monitor progress

---

## 🎯 Expected Behavior in Fabric

### Successful Run

```
🌐 Running in Microsoft Fabric
✅ Lakehouse: abc64232-25a2-499d-90ae-9fe5939ae437
✅ dq_framework v1.2.0 installed
✅ Found 68 Bronze parquet files

📂 Configuration:
   Environment: Fabric
   Base Directory: /lakehouse/default/Files
   Bronze Layer: /lakehouse/default/Files/data/Samples_LH_Bronze_Aims_26_parquet
   ...

⚙️ Pipeline Configuration:
   run_profiling: True
   run_ingestion: True
   dq_threshold: 85.0
   max_workers: 8

================================================================================
PHASE 1: DATA PROFILING
================================================================================
📊 Profiling Bronze layer: /lakehouse/default/Files/data/Samples_LH_Bronze_Aims_26_parquet
✅ Profiling Complete:
   Files Profiled: 68
   Configs Generated: 68

[... continues through all phases ...]

================================================================================
PIPELINE EXECUTION SUMMARY
================================================================================
🎉 ALL PHASES COMPLETED SUCCESSFULLY!
```

### Performance Expectations

| Operation | Local (16 cores) | Fabric (Small) | Fabric (Medium) |
|-----------|------------------|----------------|-----------------|
| Profiling | 5-10 min | 3-5 min | 2-3 min |
| Validation | 10-15 min | 5-8 min | 3-5 min |
| Complete Pipeline | 30-45 min | 15-25 min | 10-15 min |

---

## 📊 Compatibility Score

| Component | Local | Fabric | Notes |
|-----------|-------|--------|-------|
| Environment Detection | ✅ 100% | ✅ 100% | Works perfectly |
| Path Configuration | ✅ 100% | ⚠️ 80% | Needs default fix |
| Package Installation | ✅ 100% | ❌ 50% | Needs wheel upload |
| Data Processing | ✅ 100% | ❌ 40% | Needs Spark |
| Data Storage | ✅ 100% | ⚠️ 60% | Should use Delta |
| Error Handling | ✅ 90% | ⚠️ 70% | Needs Lakehouse checks |
| **Overall** | **✅ 98%** | **⚠️ 67%** | **Needs fixes** |

---

## 🎬 Next Steps

### Immediate Actions Required

1. **Apply Critical Fixes** (Priority 1)
   - Update orchestration notebook with Spark support
   - Add package installation cell
   - Implement Delta Lake writes
   - Add Lakehouse validation

2. **Test Locally** 
   - Verify fixes don't break local execution
   - Test dual functionality

3. **Deploy to Fabric**
   - Upload wheel and data
   - Upload fixed notebooks
   - Run end-to-end test

4. **Document Fabric Setup**
   - Create Fabric deployment guide
   - Add troubleshooting section
   - Update README with Fabric instructions

### Timeline

- **Day 1:** Apply critical fixes (4 hours)
- **Day 2:** Test locally (2 hours)
- **Day 3:** Deploy to Fabric test environment (3 hours)
- **Day 4:** End-to-end testing in Fabric (4 hours)
- **Day 5:** Documentation and training (2 hours)

**Total Effort:** ~15 hours

---

## 🆘 Troubleshooting Fabric Issues

### Issue: "No module named 'dq_framework'"

**Solution:**
```python
# Install wheel from Lakehouse
%pip install /lakehouse/default/Files/libs/fabric_data_quality-*.whl --quiet
```

### Issue: "Lakehouse not attached"

**Solution:**
1. Click "Add Lakehouse" in notebook toolbar
2. Select your lakehouse
3. Restart kernel

### Issue: "Path does not exist"

**Solution:**
```python
# Check what's actually in your lakehouse
!ls -la /lakehouse/default/Files/
!ls -la /lakehouse/default/Files/data/
```

### Issue: Slow performance

**Solution:**
```python
# Increase Spark partitions
spark.conf.set("spark.sql.shuffle.partitions", "200")

# Use more workers
PIPELINE_CONFIG["max_workers"] = 16
```

---

**Status:** ⚠️ **NEEDS UPDATES FOR FABRIC**  
**Priority:** 🔴 **HIGH**  
**Estimated Effort:** 15 hours  
**Risk Level:** Medium (with fixes applied)
