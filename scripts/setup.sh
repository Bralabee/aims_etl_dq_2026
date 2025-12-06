#!/bin/bash
# Setup script for AIMS Data Platform

set -e

echo "========================================="
echo "AIMS Data Platform Setup"
echo "========================================="
echo ""

# Check if conda is available
if command -v conda &> /dev/null; then
    echo "✓ Conda found"
    
    # Create environment
    echo "Creating conda environment..."
    conda env create -f environment.yml -y
    
    echo ""
    echo "========================================="
    echo "Setup Complete!"
    echo "========================================="
    echo ""
    echo "To activate the environment, run:"
    echo "  conda activate aims_data_platform"
    echo ""
    echo "Then initialize the platform:"
    echo "  python -m aims_data_platform.cli init"
    echo ""
    
else
    echo "⚠ Conda not found. Using pip instead..."
    
    # Create virtual environment
    python3 -m venv venv
    
    # Activate and install
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    echo ""
    echo "========================================="
    echo "Setup Complete!"
    echo "========================================="
    echo ""
    echo "To activate the environment, run:"
    echo "  source venv/bin/activate"
    echo ""
    echo "Then initialize the platform:"
    echo "  python -m aims_data_platform.cli init"
    echo ""
fi

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env file from template"
    echo "  Please edit .env with your configuration"
fi

echo "Next steps:"
echo "  1. Edit .env with your paths"
echo "  2. Activate environment"
echo "  3. Run: python -m aims_data_platform.cli init"
echo "  4. Run: python -m aims_data_platform.cli repair"
echo "  5. Run: python -m aims_data_platform.cli ingest aims_assets"
