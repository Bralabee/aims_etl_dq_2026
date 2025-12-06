"""
Direct Usage of fabric_data_quality for AIMS Parquet Files
===========================================================

This script demonstrates how to use the fabric_data_quality framework
DIRECTLY without any installation, to profile and validate AIMS parquet files.

Usage:
    python use_fabric_dq_directly.py
"""

import sys
from pathlib import Path
import pandas as pd

# Add fabric_data_quality to Python path
FABRIC_DQ_PATH = Path("/home/sanmi/Documents/HS2/HS2_PROJECTS_2025/fabric_data_quality")
sys.path.insert(0, str(FABRIC_DQ_PATH))

# Now import from dq_framework
from dq_framework import DataProfiler, DataQualityValidator, ConfigLoader

# Paths
AIMS_DATA_DIR = Path("/home/sanmi/Documents/HS2/HS2_PROJECTS_2025/AIMS_LOCAL/data/Samples_LH_Bronze_Aims_26_parquet")
OUTPUT_DIR = Path("/home/sanmi/Documents/HS2/HS2_PROJECTS_2025/AIMS_LOCAL/config/data_quality")

# Create output directory
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def profile_parquet_file(file_path: Path, output_dir: Path):
    """
    Profile a single parquet file and generate validation config.
    
    Args:
        file_path: Path to parquet file
        output_dir: Directory to save validation config
    """
    print(f"\n{'='*70}")
    print(f"Profiling: {file_path.name}")
    print(f"{'='*70}")
    
    # Load data
    print("📥 Loading data...")
    df = pd.read_parquet(file_path)
    print(f"   ✓ Loaded {len(df):,} rows, {len(df.columns)} columns")
    
    # Profile data
    print("\n🔍 Analyzing data structure...")
    profiler = DataProfiler(df)
    profile = profiler.profile()
    
    print(f"   ✓ Analysis complete")
    print(f"   ✓ Data Quality Score: {profile['data_quality_score']:.1f}/100")
    
    # Show summary
    print("\n" + "="*70)
    profiler.print_summary()
    
    # Generate validation config
    print(f"\n⚙️  Generating validation configuration...")
    validation_name = f"{file_path.stem}_validation"
    
    config = profiler.generate_expectations(
        validation_name=validation_name,
        description=f"Auto-generated validation for {file_path.name}",
        severity_threshold='medium',
        include_structural=True,
        include_completeness=True,
        include_validity=True,
        null_tolerance=10.0
    )
    
    print(f"   ✓ Generated {len(config['expectations'])} expectations")
    
    # Save config
    output_file = output_dir / f"{validation_name}.yml"
    profiler.save_config(config, str(output_file))
    
    print(f"\n✅ Validation config saved: {output_file}")
    
    return profile, config


def validate_with_config(file_path: Path, config_path: Path):
    """
    Validate a parquet file using a previously generated config.
    
    Args:
        file_path: Path to parquet file to validate
        config_path: Path to YAML validation config
    """
    print(f"\n{'='*70}")
    print(f"Validating: {file_path.name}")
    print(f"Using config: {config_path.name}")
    print(f"{'='*70}")
    
    # Load data
    df = pd.read_parquet(file_path)
    print(f"📥 Loaded {len(df):,} rows")
    
    # Load config
    config = ConfigLoader().load(str(config_path))
    print(f"⚙️  Loaded {len(config['expectations'])} expectations")
    
    # Validate
    print("\n🔍 Running validation...")
    validator = DataQualityValidator(config_dict=config)
    results = validator.validate(df)
    
    # Display results
    print("\n" + "="*70)
    print("VALIDATION RESULTS")
    print("="*70)
    
    if results['success']:
        print(f"✅ PASSED - All {results['evaluated_checks']} checks passed")
    else:
        print(f"❌ FAILED - {results['failed_checks']} of {results['evaluated_checks']} checks failed")
        print(f"\nSuccess Rate: {results['success_rate']:.1f}%")
        
        if results.get('details'):
            print("\nFailed Checks:")
            for detail in results['details'][:5]:  # Show first 5 failures
                print(f"  - {detail}")
    
    return results


def main():
    """Main workflow: Profile all AIMS parquet files."""
    
    print("="*70)
    print("AIMS Data Profiling with fabric_data_quality")
    print("="*70)
    print()
    print(f"📁 Data directory: {AIMS_DATA_DIR}")
    print(f"📁 Output directory: {OUTPUT_DIR}")
    print()
    
    # Discover parquet files
    parquet_files = sorted(AIMS_DATA_DIR.glob("*.parquet"))
    
    if not parquet_files:
        print(f"❌ No parquet files found in {AIMS_DATA_DIR}")
        return 1
    
    print(f"Found {len(parquet_files)} parquet file(s):")
    for file in parquet_files:
        size_mb = file.stat().st_size / (1024 * 1024)
        print(f"  - {file.name} ({size_mb:.2f} MB)")
    print()
    
    # Profile each file
    print("="*70)
    print("STEP 1: PROFILING (ONE-TIME SETUP)")
    print("="*70)
    
    profiles = {}
    configs = {}
    
    for file_path in parquet_files:
        try:
            profile, config = profile_parquet_file(file_path, OUTPUT_DIR)
            profiles[file_path.stem] = profile
            configs[file_path.stem] = config
        except Exception as e:
            print(f"\n❌ Error profiling {file_path.name}: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "="*70)
    print("PROFILING SUMMARY")
    print("="*70)
    print(f"\n✅ Successfully profiled {len(profiles)}/{len(parquet_files)} files")
    print(f"\n📁 Validation configs saved to: {OUTPUT_DIR}")
    print("\nGenerated files:")
    for yml_file in sorted(OUTPUT_DIR.glob("*.yml")):
        print(f"  - {yml_file.name}")
    
    # Example validation (optional)
    print("\n" + "="*70)
    print("STEP 2: VALIDATION EXAMPLE (OPTIONAL)")
    print("="*70)
    print("\nDemonstrating how to use generated configs for validation...")
    
    if parquet_files:
        first_file = parquet_files[0]
        config_file = OUTPUT_DIR / f"{first_file.stem}_validation.yml"
        
        if config_file.exists():
            try:
                validate_with_config(first_file, config_file)
            except Exception as e:
                print(f"\n❌ Validation error: {e}")
    
    # Next steps
    print("\n" + "="*70)
    print("NEXT STEPS")
    print("="*70)
    print("""
1. Review Generated Configs
   cd config/data_quality
   cat aims_activitydates_validation.yml

2. Customize with Business Rules
   Edit the YAML files to add project-specific validation rules

3. Use in Your Pipeline
   from dq_framework import DataQualityValidator, ConfigLoader
   
   df = pd.read_parquet('data/new_batch.parquet')
   config = ConfigLoader().load('config/data_quality/aims_activitydates_validation.yml')
   validator = DataQualityValidator(config_dict=config)
   results = validator.validate(df)
   
   if not results['success']:
       # Handle validation failures
       log_errors(results['details'])

4. No Need to Re-Profile!
   Use the same configs for all future data batches
    """)
    
    print("="*70)
    print("✅ DONE!")
    print("="*70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
