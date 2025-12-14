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

# Install fabric_data_quality from the newest available wheel
# - Prefer the highest version found across:
#   1) dq_great_expectations/dq_package_dist (bundled wheels)
#   2) ../2_DATA_QUALITY_LIBRARY/dist (freshly built wheel from shared library)
WHEEL_CANDIDATES=()
while IFS= read -r f; do WHEEL_CANDIDATES+=("$f"); done < <(find dq_great_expectations/dq_package_dist -name "fabric_data_quality-*.whl" -print 2>/dev/null || true)
while IFS= read -r f; do WHEEL_CANDIDATES+=("$f"); done < <(find ../2_DATA_QUALITY_LIBRARY/dist -name "fabric_data_quality-*.whl" -print 2>/dev/null || true)

if [ ${#WHEEL_CANDIDATES[@]} -eq 0 ]; then
    echo "Error: fabric_data_quality wheel not found. Build it in ../2_DATA_QUALITY_LIBRARY or place it in dq_great_expectations/dq_package_dist."
else
    WHEEL_PATH=$(printf '%s\n' "${WHEEL_CANDIDATES[@]}" | awk -F/ '{print $NF "\t" $0}' | sort -V | tail -n 1 | cut -f2-)
    echo "Installing fabric_data_quality from $WHEEL_PATH..."
    pip install --force-reinstall "$WHEEL_PATH"
fi

# Install local package in editable mode
echo "Installing local package in editable mode..."
pip install -e .

echo "Setup complete!"
