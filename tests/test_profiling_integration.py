#!/usr/bin/env python3
"""
Test script to verify fabric_data_quality integration with AIMS_LOCAL.

This script tests:
1. Package installation
2. Imports
3. Basic profiling functionality
4. Config generation

Run after setup_aims_profiling.sh to verify everything works.
"""

import sys
from pathlib import Path

def test_imports():
    """Test that all necessary imports work."""
    print("Testing imports...")
    
    try:
        from dq_framework import DataProfiler
        print("  DataProfiler imported")
    except ImportError as e:
        print(f"  Failed to import DataProfiler: {e}")
        return False
    
    try:
        from dq_framework import ConfigLoader
        print("  ConfigLoader imported")
    except ImportError as e:
        print(f"  Failed to import ConfigLoader: {e}")
        return False
    
    try:
        from dq_framework import FabricConnector
        print("  FabricConnector imported")
    except ImportError as e:
        print(f"  Failed to import FabricConnector: {e}")
        return False
    
    try:
        import pandas as pd
        print("  pandas imported")
    except ImportError as e:
        print(f"  Failed to import pandas: {e}")
        return False
    
    return True


def test_profiler():
    """Test basic profiler functionality."""
    print("\nTesting DataProfiler...")
    
    try:
        from dq_framework import DataProfiler
        import pandas as pd
        
        # Create sample data
        df = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
            'age': [25, 30, 35, None, 45],
            'score': [85.5, 90.0, 78.5, 88.0, 92.5]
        })
        
        # Initialize profiler
        profiler = DataProfiler(
            name="test_profile",
            description="Test profiling",
            null_tolerance_pct=20.0
        )
        print("  DataProfiler initialized")
        
        # Profile the data
        profile = profiler.profile_dataframe(df)
        print("  Data profiled successfully")
        
        # Check profile structure
        if 'columns' in profile:
            print(f"  Profile contains {len(profile['columns'])} columns")
        else:
            print("  Profile missing 'columns' key")
            return False
        
        # Generate config
        config = profiler.generate_config(profile)
        print("  Config generated")
        
        # Check config structure
        if 'expectations' in config:
            print(f"  Config contains {len(config['expectations'])} expectations")
        else:
            print("  Config missing 'expectations' key")
            return False
        
        return True
        
    except Exception as e:
        print(f"  Error during profiling: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_directory():
    """Test that the AIMS data directory exists and contains parquet files."""
    print("\nTesting data directory...")
    
    data_dir = Path("data/Samples_LH_Bronze_Aims_26_parquet")
    
    if not data_dir.exists():
        print(f"  Warning: Data directory not found: {data_dir}")
        print("     This is not a critical error - you can still use the profiler")
        return True
    
    print(f"  Data directory exists: {data_dir}")
    
    parquet_files = list(data_dir.glob("*.parquet"))
    
    if not parquet_files:
        print("  Warning: No parquet files found in data directory")
        return True
    
    print(f"  Found {len(parquet_files)} parquet file(s):")
    for file in sorted(parquet_files):
        size_mb = file.stat().st_size / (1024 * 1024)
        print(f"     - {file.name} ({size_mb:.2f} MB)")
    
    return True


def test_profile_real_data():
    """Test profiling actual AIMS data if available."""
    print("\nTesting with real AIMS data...")
    
    data_dir = Path("data/Samples_LH_Bronze_Aims_26_parquet")
    
    if not data_dir.exists():
        print("  Warning: Skipping (no data directory)")
        return True
    
    parquet_files = list(data_dir.glob("*.parquet"))
    
    if not parquet_files:
        print("  Warning: Skipping (no parquet files)")
        return True
    
    try:
        from dq_framework import DataProfiler
        import pandas as pd
        
        # Test with first file
        test_file = parquet_files[0]
        print(f"  Testing with: {test_file.name}")
        
        # Load data
        df = pd.read_parquet(test_file)
        print(f"  Loaded {len(df):,} rows, {len(df.columns)} columns")
        
        # Profile
        profiler = DataProfiler(
            name=f"test_{test_file.stem}",
            description=f"Test profile for {test_file.name}"
        )
        
        profile = profiler.profile_dataframe(df)
        print(f"  Profiled successfully")
        
        # Generate config
        config = profiler.generate_config(profile)
        print(f"  Generated config with {len(config.get('expectations', []))} expectations")
        
        return True
        
    except Exception as e:
        print(f"  Error profiling real data: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_directories():
    """Test that necessary directories exist."""
    print("\nTesting directory structure...")
    
    directories = [
        "config/data_quality",
        "logs",
        "reports"
    ]
    
    all_exist = True
    for dir_path in directories:
        path = Path(dir_path)
        if path.exists():
            print(f"  {dir_path}/ exists")
        else:
            print(f"  {dir_path}/ does not exist")
            all_exist = False
    
    return all_exist


def main():
    """Run all tests."""
    print("="*60)
    print("AIMS Data Profiling - Integration Test")
    print("="*60)
    
    tests = [
        ("Package Imports", test_imports),
        ("DataProfiler Functionality", test_profiler),
        ("Directory Structure", test_directories),
        ("Data Directory", test_data_directory),
        ("Real Data Profiling", test_profile_real_data),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Test: {test_name}")
        print(f"{'='*60}")
        
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{status:12} {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\nAll tests passed! The integration is working correctly.")
        print("\nYou can now use:")
        print("  - python profile_aims_parquet.py")
        print("  - jupyter notebook notebooks/03_Profile_AIMS_Data.ipynb")
        return 0
    else:
        print("\nSome tests failed. Please check the errors above.")
        print("\nTry running the setup script again:")
        print("  bash setup_aims_profiling.sh")
        return 1


if __name__ == "__main__":
    sys.exit(main())
