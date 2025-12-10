#!/usr/bin/env python
"""
Script to reconcile the AIMS Data Model with actual Parquet files.
This script is a wrapper around the aims_data_platform library.
"""
import sys
import argparse
from pathlib import Path

# Add project root to path to ensure we can import the library
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from aims_data_platform.schema_reconciliation import (
    parse_data_model,
    analyze_comparison,
    analyze_extra_files,
    generate_model,
    DEFAULT_DATA_MODEL_FILE,
    DEFAULT_PARQUET_DIR,
    DEFAULT_GENERATED_MODEL_FILE
)

def main():
    parser = argparse.ArgumentParser(description="Reconcile AIMS Data Model with Parquet files.")
    parser.add_argument("--model", type=Path, default=DEFAULT_DATA_MODEL_FILE, help="Path to AIMS Data Model file")
    parser.add_argument("--data", type=Path, default=DEFAULT_PARQUET_DIR, help="Path to Parquet data directory")
    parser.add_argument("--generate", action="store_true", help="Generate a new data model file based on actual data")
    parser.add_argument("--output", type=Path, default=DEFAULT_GENERATED_MODEL_FILE, help="Output path for generated model")
    
    args = parser.parse_args()
    
    print(f"Using Data Model: {args.model}")
    print(f"Using Data Dir:   {args.data}")
    
    if not args.model.exists():
        print(f"Error: Model file not found at {args.model}")
        return
    
    if not args.data.exists():
        print(f"Error: Data directory not found at {args.data}")
        return

    # 1. Parse Model
    print("Parsing Data Model...")
    tables = parse_data_model(args.model)
    print(f"Found {len(tables)} tables in model definition.")

    # 2. Analyze
    print("Analyzing Parquet Files...")
    df_results, modeled_files = analyze_comparison(tables, args.data)
    
    # Print Summary
    total_tables = len(df_results)
    matches = len(df_results[df_results['Status'].str.contains('MATCH')])
    mismatches = len(df_results[df_results['Status'] == 'MISMATCH'])
    missing_files = len(df_results[df_results['Status'] == 'MISSING FILE'])
    
    print(f"\nSummary (Model vs Files):")
    print(f"Total Tables Defined in Model: {total_tables}")
    print(f"[MATCHED] Fully Matched:              {matches}")
    print(f"[WARNING] Schema Mismatches:          {mismatches}")
    print(f"[ERROR] Missing Files:              {missing_files}")
    
    # 3. Extra Files
    df_extra = analyze_extra_files(modeled_files, args.data)
    print(f"\nExtra Files Analysis:")
    print(f"Total Parquet Files Found:     {len(list(args.data.glob('*.parquet')))}")
    print(f"Files accounted for in Model:  {len(modeled_files)}")
    print(f"❓ Unmodeled Files (Extra):    {len(df_extra)}")

    # 4. Generate New Model
    if args.generate:
        print(f"\nGenerating new data model at {args.output}...")
        generate_model(tables, args.data, output_file=args.output)
        print("Done.")

if __name__ == "__main__":
    main()
