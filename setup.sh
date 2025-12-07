#!/bin/bash
set -e

echo "Setting up AIMS Data Platform environment..."

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 could not be found"
    exit 1
fi

# Check if we are in a conda environment
if [ -z "$CONDA_DEFAULT_ENV" ]; then
    echo "Warning: No Conda environment detected."
    echo "Please ensure you have activated the 'fabric-dq' environment before running this script."
else
    echo "Detected Conda environment: $CONDA_DEFAULT_ENV"
fi

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
if [ -f "requirements.txt" ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt
fi

# Install fabric_data_quality from local wheel
# Find the latest wheel in the project's distribution folder
WHEEL_PATH=$(find dq_great_expectations/dq_package_dist -name "fabric_data_quality-*.whl" | sort -V | tail -n 1)

if [ -z "$WHEEL_PATH" ]; then
    echo "Warning: fabric_data_quality wheel not found in dq_great_expectations/dq_package_dist."
    echo "Checking parent directory..."
    WHEEL_PATH=$(find ../2_DATA_QUALITY_LIBRARY/dist -name "fabric_data_quality-*.whl" | sort -V | tail -n 1)
fi

if [ -z "$WHEEL_PATH" ]; then
    echo "Error: fabric_data_quality wheel not found. Please build it in 2_DATA_QUALITY_LIBRARY."
else
    echo "Installing fabric_data_quality from $WHEEL_PATH..."
    pip install --force-reinstall "$WHEEL_PATH"
fi

# Install local package in editable mode
echo "Installing local package in editable mode..."
pip install -e .

echo "Setup complete!"
