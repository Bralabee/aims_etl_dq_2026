#!/usr/bin/env python3
"""
AIMS Parquet Data Profiler
===========================

Profile all parquet files in the AIMS data directory using the
fabric_data_quality framework.

This script:
1. Discovers all .parquet files in the specified directory
2. Profiles each file using the DataProfiler
3. Generates data quality configuration files
4. Creates validation reports

Usage:
    # Profile all files in the default directory
    python profile_aims_parquet.py
    
    # Profile specific directory
    python profile_aims_parquet.py --data-dir data/Samples_LH_Bronze_Aims_26_parquet
    
    # Profile with custom output directory
    python profile_aims_parquet.py --output-dir config/aims_validations
    
    # Profile only (no config generation)
    python profile_aims_parquet.py --profile-only
"""

import argparse
import sys
from pathlib import Path
from typing import List, Dict
import pandas as pd
from datetime import datetime

try:
    # Import from the installed fabric_data_quality package
    from dq_framework import DataProfiler
    from dq_framework.loader import DataLoader
except ImportError:
    print("ERROR: The 'fabric_data_quality' package is not installed.")
    print("\nPlease install the required dependency:")
    print("  cd ../fabric_data_quality")
    print("  pip install -e .")
    print("\nOr run: bash setup_aims_profiling.sh")
    sys.exit(1)


def discover_parquet_files(data_dir: Path) -> List[Path]:
    """Discover all parquet files in the data directory."""
    parquet_files = list(data_dir.glob("*.parquet"))
    
    if not parquet_files:
        print(f"WARNING: No parquet files found in {data_dir}")
        return []
    
    print(f"Found {len(parquet_files)} parquet file(s):")
    for file in sorted(parquet_files):
        size_mb = file.stat().st_size / (1024 * 1024)
        print(f"   - {file.name} ({size_mb:.2f} MB)")
    
    return parquet_files


def profile_parquet_file(
    file_path: Path,
    output_dir: Path,
    profile_only: bool = False,
    null_tolerance: float = 10.0,
    severity: str = "medium"
) -> Dict:
    """
    Profile a single parquet file.
    
    Args:
        file_path: Path to the parquet file
        output_dir: Directory to save the config file
        profile_only: If True, only show profile without generating config
        null_tolerance: Percentage of nulls allowed
        severity: Expectation severity level
    
    Returns:
        Dictionary with profiling results
    """
    print(f"\n{'='*60}")
    print(f"Profiling: {file_path.name}")
    print(f"{'='*60}")
    
    try:
        # Load the data
        df = DataLoader.load_data(file_path)
        print(f"LOADED: {len(df):,} rows, {len(df.columns)} columns")
        
        # Initialize profiler
        profiler = DataProfiler(df)
        
        # Profile the data
        print("\n🔍 Analyzing data structure and content...")
        profile = profiler.profile()
        
        # Display profile
        profiler.print_summary()
        
        # Generate config if not profile-only mode
        if not profile_only:
            output_dir.mkdir(parents=True, exist_ok=True)
            config_path = output_dir / f"{file_path.stem}_validation.yml"
            
            config = profiler.generate_expectations(
                validation_name=f"aims_{file_path.stem}",
                description=f"Data quality validation for {file_path.name}",
                null_tolerance=null_tolerance,
                severity_threshold=severity
            )
            profiler.save_config(config, str(config_path))
            
            print(f"\nConfiguration saved to: {config_path}")
            print("\n📝 Next steps:")
            print("   1. Review and customize the generated config")
            print("   2. Add business-specific validation rules")
            print("   3. Use it with the AIMS data platform for validation")
        
        return {
            "file": file_path.name,
            "status": "success",
            "rows": len(df),
            "columns": len(df.columns),
            "profile": profile
        }
        
    except Exception as e:
        print(f"ERROR profiling {file_path.name}: {str(e)}")
        return {
            "file": file_path.name,
            "status": "error",
            "error": str(e)
        }





def main():
    parser = argparse.ArgumentParser(
        description="Profile AIMS parquet files using fabric_data_quality framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Profile all files with defaults
  python profile_aims_parquet.py
  
  # Profile specific directory
  python profile_aims_parquet.py --data-dir data/Bronze_Layer
  
  # Just view profile without generating config
  python profile_aims_parquet.py --profile-only
  
  # Custom null tolerance
  python profile_aims_parquet.py --null-tolerance 5.0 --severity high
        """
    )
    
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/Samples_LH_Bronze_Aims_26_parquet"),
        help="Directory containing parquet files (default: data/Samples_LH_Bronze_Aims_26_parquet)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("config/data_quality"),
        help="Output directory for validation configs (default: config/data_quality)"
    )
    
    parser.add_argument(
        "--profile-only",
        action="store_true",
        help="Only show data profile, don't generate config files"
    )
    
    parser.add_argument(
        "--null-tolerance",
        type=float,
        default=10.0,
        help="Percentage of null values allowed (default: 10.0)"
    )
    
    parser.add_argument(
        "--severity",
        choices=["low", "medium", "high"],
        default="medium",
        help="Severity level for expectations (default: medium)"
    )
    
    parser.add_argument(
        "--file",
        type=str,
        help="Profile only a specific file (by name)"
    )
    
    args = parser.parse_args()
    
    # Banner
    print("="*60)
    print("AIMS Parquet Data Profiler")
    print("Using fabric_data_quality framework")
    print("="*60)
    print(f"\n⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Validate data directory
    if not args.data_dir.exists():
        print(f"\n❌ Error: Data directory not found: {args.data_dir}")
        print("\nPlease check the path and try again.")
        sys.exit(1)
    
    # Discover files
    parquet_files = discover_parquet_files(args.data_dir)
    if not parquet_files:
        sys.exit(1)
    
    # Filter to specific file if requested
    if args.file:
        parquet_files = [f for f in parquet_files if f.name == args.file]
        if not parquet_files:
            print(f"\n❌ Error: File not found: {args.file}")
            sys.exit(1)
    
    # Profile each file
    results = []
    for file_path in parquet_files:
        result = profile_parquet_file(
            file_path,
            args.output_dir,
            args.profile_only,
            args.null_tolerance,
            args.severity
        )
        results.append(result)
    
    # Summary
    print("\n" + "="*60)
    print("PROFILING SUMMARY")
    print("="*60)
    
    success_count = sum(1 for r in results if r["status"] == "success")
    error_count = len(results) - success_count
    
    print(f"\n✅ Successfully profiled: {success_count}/{len(results)} files")
    if error_count > 0:
        print(f"❌ Errors: {error_count}")
        print("\nFailed files:")
        for r in results:
            if r["status"] == "error":
                print(f"   - {r['file']}: {r['error']}")
    
    if not args.profile_only and success_count > 0:
        print(f"\n📁 Configuration files saved to: {args.output_dir}")
        print("\n📚 Next steps:")
        print("   1. Review the generated YAML configurations")
        print("   2. Customize validation rules for your business logic")
        print("   3. Integrate with your AIMS data pipeline")
        print("   4. Run validations during data ingestion")
    
    print(f"\n⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)


if __name__ == "__main__":
    main()
