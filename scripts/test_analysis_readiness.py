#!/usr/bin/env python3
"""
Test Analysis Notebooks Readiness
==================================
Verifies that all prerequisites for notebooks 06, 07, 08 are in place.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Disable GX analytics
os.environ["GX_ANALYTICS_ENABLED"] = "False"

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

load_dotenv()

def main():
    print("=" * 70)
    print("AIMS Analysis Notebooks - Prerequisites Check")
    print("=" * 70)
    
    # Check 1: Environment Configuration
    print("\n[1/5] Checking Environment Configuration...")
    BASE_DIR = Path(os.getenv("BASE_DIR", str(project_root)))
    DATA_PATH = BASE_DIR / os.getenv("DATA_PATH", "data/Samples_LH_Bronze_Aims_26_parquet")
    CONFIG_DIR = BASE_DIR / os.getenv("CONFIG_DIR", "config/data_quality")
    
    print(f"  ✓ BASE_DIR: {BASE_DIR}")
    print(f"  ✓ DATA_PATH: {DATA_PATH}")
    print(f"  ✓ CONFIG_DIR: {CONFIG_DIR}")
    
    # Check 2: Data Directory
    print("\n[2/5] Checking Data Directory...")
    if not DATA_PATH.exists():
        print(f"  ✗ ERROR: Data directory not found: {DATA_PATH}")
        return False
    
    parquet_files = list(DATA_PATH.glob("*.parquet"))
    print(f"  ✓ Found {len(parquet_files)} parquet files")
    
    if len(parquet_files) == 0:
        print("  ✗ ERROR: No parquet files found")
        return False
    
    # Check 3: Key Tables for Analysis
    print("\n[3/5] Checking Key Tables...")
    required_tables = [
        "aims_assets",
        "aims_assetclass",
        "aims_route",
        "aims_organisation"
    ]
    
    missing_tables = []
    for table in required_tables:
        table_path = DATA_PATH / f"{table}.parquet"
        if table_path.exists():
            print(f"  ✓ {table}.parquet")
        else:
            print(f"  ✗ {table}.parquet (MISSING)")
            missing_tables.append(table)
    
    if missing_tables:
        print(f"  WARNING: {len(missing_tables)} required tables missing")
    
    # Check 4: DQ Configs
    print("\n[4/5] Checking DQ Configuration...")
    if not CONFIG_DIR.exists():
        print(f"  ✗ ERROR: Config directory not found: {CONFIG_DIR}")
        return False
    
    config_files = list(CONFIG_DIR.glob("*.yaml"))
    print(f"  ✓ Found {len(config_files)} DQ config files")
    
    # Check 5: Library Imports
    print("\n[5/5] Checking Library Imports...")
    try:
        import pandas as pd
        print(f"  ✓ pandas {pd.__version__}")
    except ImportError as e:
        print(f"  ✗ pandas: {e}")
        return False
    
    try:
        import pyarrow as pa
        print(f"  ✓ pyarrow {pa.__version__}")
    except ImportError as e:
        print(f"  ✗ pyarrow: {e}")
        return False
    
    try:
        import matplotlib
        print(f"  ✓ matplotlib {matplotlib.__version__}")
    except ImportError as e:
        print(f"  ✗ matplotlib: {e}")
        return False
    
    try:
        import seaborn
        print(f"  ✓ seaborn {seaborn.__version__}")
    except ImportError as e:
        print(f"  ✗ seaborn: {e}")
        return False
    
    try:
        from dq_framework import DataLoader
        print(f"  ✓ dq_framework.DataLoader")
    except ImportError as e:
        print(f"  ✗ dq_framework: {e}")
        print(f"     Fix: cd ../2_DATA_QUALITY_LIBRARY && pip install -e .")
        return False
    
    # Summary
    print("\n" + "=" * 70)
    print("✓ ALL CHECKS PASSED - Analysis notebooks are ready!")
    print("=" * 70)
    print("\nYou can now run:")
    print("  - notebooks/06_AIMS_Business_Intelligence.ipynb")
    print("  - notebooks/07_AIMS_DQ_Matrix_and_Modeling.ipynb")
    print("  - notebooks/08_AIMS_Business_Intelligence.ipynb")
    print()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
