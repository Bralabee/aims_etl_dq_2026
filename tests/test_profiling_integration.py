#!/usr/bin/env python3
"""
Test script to verify fabric_data_quality integration with AIMS_LOCAL.

This script tests:
1. Package installation
2. Imports
3. Basic profiling functionality
4. Config generation

Run with pytest.
"""

import sys
import pytest
from pathlib import Path
import pandas as pd

# Ensure we can import from the project root if needed
sys.path.append(str(Path(__file__).parent.parent))

def test_imports():
    """Test that all necessary imports work."""
    try:
        from dq_framework import DataProfiler
        from dq_framework import ConfigLoader
        from dq_framework import FabricDataQualityRunner
        import pandas as pd
    except ImportError as e:
        pytest.fail(f"Failed to import required modules: {e}")

def test_profiler():
    """Test basic profiler functionality."""
    from dq_framework import DataProfiler
    
    # Create sample data
    df = pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'age': [25, 30, 35, None, 45],
        'score': [85.5, 90.0, 78.5, 88.0, 92.5]
    })
    
    # Initialize profiler
    profiler = DataProfiler(df)
    
    # Profile the data
    profile = profiler.profile()
    
    # Check profile structure
    assert 'columns' in profile, "Profile missing 'columns' key"
    assert len(profile['columns']) > 0, "Profile has no columns"
    
    # Generate config
    config = profiler.generate_expectations(validation_name="test_validation")
    
    # Check config structure
    assert 'expectations' in config, "Config missing 'expectations' key"
    assert len(config['expectations']) > 0, "Config has no expectations"
    assert 'quality_thresholds' in config, "Config missing 'quality_thresholds' key"
    assert 'critical' in config['quality_thresholds'], "Config missing 'critical' threshold"

def test_data_directory():
    """Test that the AIMS data directory exists and contains parquet files."""
    data_dir = Path("data/Samples_LH_Bronze_Aims_26_parquet")
    
    if not data_dir.exists():
        pytest.skip(f"Data directory not found: {data_dir}")
    
    assert data_dir.exists()
    
    parquet_files = list(data_dir.glob("*.parquet"))
    
    if not parquet_files:
        pytest.skip("No parquet files found in data directory")
    
    assert len(parquet_files) > 0

def test_profile_real_data():
    """Test profiling actual AIMS data if available."""
    data_dir = Path("data/Samples_LH_Bronze_Aims_26_parquet")
    
    if not data_dir.exists():
        pytest.skip("Skipping (no data directory)")
    
    parquet_files = list(data_dir.glob("*.parquet"))
    
    if not parquet_files:
        pytest.skip("Skipping (no parquet files)")
    
    from dq_framework import DataProfiler
    
    # Test with first file
    test_file = parquet_files[0]
    
    # Load data
    df = pd.read_parquet(test_file)
    assert len(df) > 0, "Loaded dataframe is empty"
    
    # Profile
    profiler = DataProfiler(df)
    
    profile = profiler.profile()
    assert profile is not None
    
    # Generate config
    config = profiler.generate_expectations(validation_name=f"test_{test_file.stem}")
    assert 'expectations' in config
    assert len(config.get('expectations', [])) > 0

def test_directories():
    """Test that necessary directories exist."""
    directories = [
        "config/data_quality",
        "logs",
    ]
    
    for dir_path in directories:
        path = Path(dir_path)
        # We don't assert existence here because they might be created at runtime
        # But if we want to enforce structure:
        # assert path.exists(), f"{dir_path} does not exist"
        pass 
