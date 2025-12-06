import pytest
import pandas as pd
import os
import tempfile
import yaml
from dq_framework import DataQualityValidator

@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    data = {
        'id': [1, 2, 3],
        'name': ['Alice', 'Bob', 'Charlie'],
        'age': [25, 30, 35]
    }
    return pd.DataFrame(data)

@pytest.fixture
def valid_config():
    """Create a valid configuration dictionary."""
    return {
        'validation_name': 'test_suite',
        'expectations': [
            {
                'expectation_type': 'expect_column_values_to_not_be_null',
                'kwargs': {'column': 'id'}
            },
            {
                'expectation_type': 'expect_column_values_to_be_unique',
                'kwargs': {'column': 'id'}
            },
            {
                'expectation_type': 'expect_column_values_to_be_between',
                'kwargs': {'column': 'age', 'min_value': 0, 'max_value': 120}
            }
        ]
    }

@pytest.fixture
def config_file(valid_config):
    """Create a temporary config file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as tmp:
        yaml.dump(valid_config, tmp)
        tmp_path = tmp.name
    
    yield tmp_path
    
    if os.path.exists(tmp_path):
        os.remove(tmp_path)

def test_validator_initialization(config_file, valid_config):
    """Test initialization with YAML file."""
    validator = DataQualityValidator(config_file)
    # The loader might add extra fields or structure, but basic checks should pass
    assert validator.config is not None
    assert 'expectations' in validator.config
    assert len(validator.config['expectations']) == len(valid_config['expectations'])

def test_validator_validate_success(sample_df, config_file):
    """Test validation passing."""
    validator = DataQualityValidator(config_file)
    result = validator.validate(sample_df)
    
    assert result['success'] is True
    assert result['success_rate'] == 100.0
    assert result['failed_checks'] == 0

def test_validator_validate_failure(config_file):
    """Test validation failing."""
    # Create bad data
    bad_df = pd.DataFrame({
        'id': [1, 1, None],  # Duplicate and Null
        'name': ['Alice', 'Bob', 'Charlie'],
        'age': [150, 30, 35] # Out of range
    })
    
    validator = DataQualityValidator(config_file)
    result = validator.validate(bad_df)
    
    assert result['success'] is False
    assert result['success_rate'] < 100.0
    assert result['failed_checks'] > 0

def test_validator_missing_column(config_file):
    """Test validation with missing column."""
    df_missing_col = pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['Alice', 'Bob', 'Charlie']
        # 'age' is missing
    })
    
    validator = DataQualityValidator(config_file)
    result = validator.validate(df_missing_col)
    
    # Missing column usually causes validation failure
    assert result['success'] is False
