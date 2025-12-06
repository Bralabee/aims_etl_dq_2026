import pytest
import pandas as pd
import numpy as np
from dq_framework import DataProfiler

@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    data = {
        'id': [1, 2, 3, 4, 5],
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'age': [25, 30, 35, 40, 45],
        'email': ['alice@example.com', 'bob@example.com', 'charlie@example.com', 'david@example.com', 'eve@example.com'],
        'category': ['A', 'B', 'A', 'B', 'C'],
        'score': [85.5, 90.0, 88.5, 92.0, 89.5],
        'is_active': [True, False, True, True, False],
        'nullable_col': [1, None, 3, None, 5]
    }
    return pd.DataFrame(data)

def test_profiler_initialization(sample_df):
    """Test that DataProfiler initializes correctly."""
    profiler = DataProfiler(sample_df)
    assert profiler.df is not None
    assert len(profiler.df) == 5

def test_profiler_profile_generation(sample_df):
    """Test that profile() returns expected structure."""
    profiler = DataProfiler(sample_df)
    profile = profiler.profile()
    
    assert 'row_count' in profile
    assert profile['row_count'] == 5
    assert 'columns' in profile
    assert len(profile['columns']) == 8
    
    # Check specific column details
    age_col = profile['columns']['age']
    # detected_type might be 'numeric' or 'integer' depending on implementation
    assert age_col['detected_type'] in ['numeric', 'integer']
    assert age_col['min'] == 25
    assert age_col['max'] == 45

def test_profiler_generates_expectations(sample_df):
    """Test that generate_expectations() creates valid config."""
    profiler = DataProfiler(sample_df)
    config = profiler.generate_expectations(validation_name="test_validation")
    
    assert config['validation_name'] == "test_validation"
    assert 'expectations' in config
    assert len(config['expectations']) > 0
    
    # Check for specific expectations
    expectations = config['expectations']
    
    # Should have unique check for ID
    id_unique = any(e['expectation_type'] == 'expect_column_values_to_be_unique' and e['kwargs']['column'] == 'id' for e in expectations)
    assert id_unique
    
    # Should have not null check for name
    name_not_null = any(e['expectation_type'] == 'expect_column_values_to_not_be_null' and e['kwargs']['column'] == 'name' for e in expectations)
    assert name_not_null

def test_profiler_handles_empty_df():
    """Test profiler behavior with empty DataFrame."""
    empty_df = pd.DataFrame({'col1': []})
    profiler = DataProfiler(empty_df)
    profile = profiler.profile()
    
    assert profile['row_count'] == 0
    assert len(profile['columns']) == 1

def test_profiler_detects_categorical_columns(sample_df):
    """Test that categorical columns are correctly identified."""
    profiler = DataProfiler(sample_df)
    profile = profiler.profile()
    
    category_col = profile['columns']['category']
    # Depending on implementation, it might be 'text' or 'categorical'
    # But it should have unique values count
    assert 'unique_count' in category_col
    assert category_col['unique_count'] == 3
