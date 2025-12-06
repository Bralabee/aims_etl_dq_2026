#!/bin/bash
# Direct Usage of fabric_data_quality for AIMS Parquet Files
# ===========================================================

set -e

echo "======================================================================"
echo "Using fabric_data_quality to Profile AIMS Parquet Files"
echo "======================================================================"
echo ""

# Paths
FABRIC_DQ_DIR="/home/sanmi/Documents/HS2/HS2_PROJECTS_2025/fabric_data_quality"
AIMS_DATA_DIR="/home/sanmi/Documents/HS2/HS2_PROJECTS_2025/AIMS_LOCAL/data/Samples_LH_Bronze_Aims_26_parquet"
OUTPUT_DIR="/home/sanmi/Documents/HS2/HS2_PROJECTS_2025/AIMS_LOCAL/config/data_quality"

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "📁 Input:  $AIMS_DATA_DIR"
echo "📁 Output: $OUTPUT_DIR"
echo ""

# Change to fabric_data_quality directory
cd "$FABRIC_DQ_DIR"

echo "======================================================================"
echo "Step 1: Profile Each Parquet File"
echo "======================================================================"
echo ""

# Profile aims_activitydates.parquet
echo "1️⃣  Profiling aims_activitydates.parquet..."
python profile_data.py \
    "$AIMS_DATA_DIR/aims_activitydates.parquet" \
    --output "$OUTPUT_DIR/aims_activitydates_validation.yml" \
    --name "aims_activitydates_validation" \
    --description "AIMS Activity Dates data quality validation" \
    --null-tolerance 10.0 \
    --severity medium

echo ""
echo "✅ aims_activitydates.parquet profiled"
echo ""

# Profile aims_assetattributes.parquet
echo "2️⃣  Profiling aims_assetattributes.parquet..."
python profile_data.py \
    "$AIMS_DATA_DIR/aims_assetattributes.parquet" \
    --output "$OUTPUT_DIR/aims_assetattributes_validation.yml" \
    --name "aims_assetattributes_validation" \
    --description "AIMS Asset Attributes data quality validation" \
    --null-tolerance 10.0 \
    --severity medium

echo ""
echo "✅ aims_assetattributes.parquet profiled"
echo ""

# Profile aims_assetclassattributes.parquet
echo "3️⃣  Profiling aims_assetclassattributes.parquet..."
python profile_data.py \
    "$AIMS_DATA_DIR/aims_assetclassattributes.parquet" \
    --output "$OUTPUT_DIR/aims_assetclassattributes_validation.yml" \
    --name "aims_assetclassattributes_validation" \
    --description "AIMS Asset Class Attributes data quality validation" \
    --null-tolerance 10.0 \
    --severity medium

echo ""
echo "✅ aims_assetclassattributes.parquet profiled"
echo ""

# Profile aims_assetclasschangelogs.parquet
echo "4️⃣  Profiling aims_assetclasschangelogs.parquet..."
python profile_data.py \
    "$AIMS_DATA_DIR/aims_assetclasschangelogs.parquet" \
    --output "$OUTPUT_DIR/aims_assetclasschangelogs_validation.yml" \
    --name "aims_assetclasschangelogs_validation" \
    --description "AIMS Asset Class Change Logs data quality validation" \
    --null-tolerance 10.0 \
    --severity medium

echo ""
echo "✅ aims_assetclasschangelogs.parquet profiled"
echo ""

echo "======================================================================"
echo "✅ ALL FILES PROFILED SUCCESSFULLY!"
echo "======================================================================"
echo ""
echo "📁 Generated validation configs in:"
echo "   $OUTPUT_DIR/"
echo ""
echo "📋 Files created:"
ls -lh "$OUTPUT_DIR"/*.yml 2>/dev/null || echo "   (checking...)"
echo ""
echo "======================================================================"
echo "Next Steps:"
echo "======================================================================"
echo ""
echo "1. Review the generated YAML files"
echo "   cd $OUTPUT_DIR"
echo "   cat aims_activitydates_validation.yml"
echo ""
echo "2. Customize with business rules (optional)"
echo "   vim $OUTPUT_DIR/aims_activitydates_validation.yml"
echo ""
echo "3. Use in Python code:"
echo "   from dq_framework import DataQualityValidator, ConfigLoader"
echo "   import pandas as pd"
echo ""
echo "   df = pd.read_parquet('data/aims_activitydates.parquet')"
echo "   config = ConfigLoader().load('config/data_quality/aims_activitydates_validation.yml')"
echo "   validator = DataQualityValidator(config_dict=config)"
echo "   results = validator.validate(df)"
echo ""
echo "======================================================================"
