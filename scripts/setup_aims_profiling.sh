#!/bin/bash
# ==============================================================================
# AIMS Local - Data Quality Profiling Setup
# ==============================================================================
# 
# This script sets up the fabric_data_quality framework for use with
# AIMS_LOCAL project without duplicating code.
#
# What it does:
#   1. Installs fabric_data_quality as an editable package
#   2. Creates necessary directories
#   3. Validates the installation
#   4. Provides usage instructions
#
# Usage:
#   bash setup_aims_profiling.sh
#
# ==============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo "=============================================================="
echo "AIMS Local - Data Quality Profiling Setup"
echo "=============================================================="
echo ""

# Determine project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Assuming script is in AIMS_LOCAL/scripts
AIMS_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FABRIC_DQ_DIR="$(cd "$AIMS_ROOT/../fabric_data_quality" && pwd)"

echo -e "${BLUE}📁 AIMS_LOCAL directory:${NC} $AIMS_ROOT"
echo -e "${BLUE}📁 fabric_data_quality directory:${NC} $FABRIC_DQ_DIR"
echo ""

# Check if fabric_data_quality exists
if [ ! -d "$FABRIC_DQ_DIR" ]; then
    echo -e "${RED}❌ Error: fabric_data_quality directory not found!${NC}"
    echo "Expected location: $FABRIC_DQ_DIR"
    exit 1
fi

echo -e "${GREEN}✅ Found fabric_data_quality directory${NC}"
echo ""

# Check if setup.py exists
if [ ! -f "$FABRIC_DQ_DIR/setup.py" ]; then
    echo -e "${RED}❌ Error: setup.py not found in fabric_data_quality!${NC}"
    exit 1
fi

# Step 1: Install fabric_data_quality as editable package
echo "=============================================================="
echo "Step 1: Installing fabric_data_quality (editable mode)"
echo "=============================================================="
echo ""

echo -e "${YELLOW}📦 Installing fabric_data_quality in editable mode...${NC}"
echo "This allows you to use the package without duplicating code."
echo ""

cd "$FABRIC_DQ_DIR"
pip install -e . --quiet

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ fabric_data_quality installed successfully${NC}"
else
    echo -e "${RED}❌ Installation failed${NC}"
    exit 1
fi
echo ""

# Step 2: Create necessary directories
echo "=============================================================="
echo "Step 2: Creating directory structure"
echo "=============================================================="
echo ""

cd "$AIMS_ROOT"

mkdir -p config/data_quality
mkdir -p logs
mkdir -p reports

echo -e "${GREEN}✅ Created directories:${NC}"
echo "   - config/data_quality/  (for validation configs)"
echo "   - logs/                 (for profiling logs)"
echo "   - reports/              (for validation reports)"
echo ""

# Step 3: Validate installation
echo "=============================================================="
echo "Step 3: Validating installation"
echo "=============================================================="
echo ""

python3 -c "
try:
    from dq_framework import DataProfiler
    print('✅ DataProfiler imported successfully')
    
    from dq_framework import ConfigLoader
    print('✅ ConfigLoader imported successfully')
    
    from dq_framework import FabricConnector
    print('✅ FabricConnector imported successfully')
    
    print('\n✅ All components validated!')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Validation failed${NC}"
    exit 1
fi
echo ""

# Step 4: Test with actual data
echo "=============================================================="
echo "Step 4: Testing with sample data"
echo "=============================================================="
echo ""

DATA_DIR="$AIMS_ROOT/data/Samples_LH_Bronze_Aims_26_parquet"

if [ -d "$DATA_DIR" ]; then
    FILE_COUNT=$(find "$DATA_DIR" -name "*.parquet" | wc -l)
    echo -e "${GREEN}✅ Found $FILE_COUNT parquet files in:${NC}"
    echo "   $DATA_DIR"
    echo ""
    
    # List the files
    echo "Files available for profiling:"
    find "$DATA_DIR" -name "*.parquet" -exec basename {} \; | sed 's/^/   - /'
else
    echo -e "${YELLOW}⚠️  Data directory not found:${NC} $DATA_DIR"
    echo "You can still use the profiling tools with other data."
fi
echo ""

# Success message and usage instructions
echo "=============================================================="
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "=============================================================="
echo ""
echo "🎉 You can now profile AIMS parquet files!"
echo ""
echo "Usage Examples:"
echo "----------------------------------------"
echo ""
echo "1. Profile all parquet files:"
echo "   cd $AIMS_ROOT"
echo "   python profile_aims_parquet.py"
echo ""
echo "2. Profile specific file:"
echo "   python profile_aims_parquet.py --file aims_activitydates.parquet"
echo ""
echo "3. Just view profile (no config generation):"
echo "   python profile_aims_parquet.py --profile-only"
echo ""
echo "4. Custom output directory:"
echo "   python profile_aims_parquet.py --output-dir config/custom_validations"
echo ""
echo "5. Adjust validation strictness:"
echo "   python profile_aims_parquet.py --null-tolerance 5.0 --severity high"
echo ""
echo "----------------------------------------"
echo ""
echo "📚 Documentation:"
echo "   - fabric_data_quality: $FABRIC_DQ_DIR/README.md"
echo "   - Usage examples: $FABRIC_DQ_DIR/examples/"
echo "   - Config templates: $FABRIC_DQ_DIR/config_templates/"
echo ""
echo "💡 Tips:"
echo "   - Generated configs will be in: config/data_quality/"
echo "   - Review and customize configs before production use"
echo "   - Add business-specific validation rules as needed"
echo "   - Use configs with Great Expectations for validation"
echo ""
echo "=============================================================="
