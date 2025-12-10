#!/usr/bin/env python3
"""
Simple DQ Validation Runner (No Multiprocessing)
=================================================

Run data quality validation on all parquet files sequentially.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dq_framework import DataLoader, DataQualityValidator

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "Samples_LH_Bronze_Aims_26_parquet"
CONFIG_DIR = PROJECT_ROOT / "config" / "data_quality"
OUTPUT_DIR = PROJECT_ROOT / "config" / "validation_results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

THRESHOLD = 85.0

def main():
    print("="*70)
    print("AIMS Data Quality Validation")
    print("="*70)
    print(f"Data Directory: {DATA_DIR}")
    print(f"Config Directory: {CONFIG_DIR}")
    print(f"Threshold: {THRESHOLD}%")
    print()
    
    # Discover parquet files
    parquet_files = sorted(DATA_DIR.glob("*.parquet"))
    print(f"Found {len(parquet_files)} parquet files\n")
    
    # Results storage
    results = {
        "timestamp": datetime.now().isoformat(),
        "threshold": THRESHOLD,
        "files": [],
        "summary": {
            "total": len(parquet_files),
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0
        }
    }
    
    # Process each file
    for file_path in tqdm(parquet_files, desc="Validating"):
        file_name = file_path.name
        config_name = file_name.replace('.parquet', '_validation.yml')
        config_path = CONFIG_DIR / config_name
        
        file_result = {
            "file": file_name,
            "config": str(config_path),
            "status": "unknown",
            "score": 0.0,
            "failures": [],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Check config exists
            if not config_path.exists():
                print(f"⚠️  No config: {file_name}")
                file_result["status"] = "SKIPPED_NO_CONFIG"
                results["summary"]["skipped"] += 1
                results["files"].append(file_result)
                continue
            
            # Load data (sample for large files)
            df = DataLoader.load_data(str(file_path), sample_size=100000)
            
            # Validate
            validator = DataQualityValidator(config_path=str(config_path))
            validation_result = validator.validate(df, threshold=THRESHOLD)
            
            file_result["score"] = validation_result["success_rate"]
            file_result["failures"] = validation_result.get("failed_expectations", [])
            file_result["threshold_failures"] = validation_result.get("threshold_failures", [])
            
            if validation_result["success"]:
                file_result["status"] = "PASSED"
                results["summary"]["passed"] += 1
                print(f"✅ PASSED: {file_name} ({file_result['score']:.1f}%)")
            else:
                file_result["status"] = "FAILED"
                results["summary"]["failed"] += 1
                failures_count = len(file_result["failures"])
                threshold_failures = file_result.get("threshold_failures", [])
                print(f"❌ FAILED: {file_name} ({file_result['score']:.1f}%) - {failures_count} failures")
                if threshold_failures:
                    print(f"   Thresholds missed: {', '.join(threshold_failures)}")
            
            results["files"].append(file_result)
            
        except Exception as e:
            file_result["status"] = "ERROR"
            file_result["error"] = str(e)
            results["summary"]["errors"] += 1
            results["files"].append(file_result)
            print(f"💥 ERROR: {file_name} - {str(e)}")
    
    # Save results
    output_file = OUTPUT_DIR / "validation_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    print(f"Total Files:  {results['summary']['total']}")
    print(f"✅ Passed:     {results['summary']['passed']}")
    print(f"❌ Failed:     {results['summary']['failed']}")
    print(f"⚠️  Skipped:    {results['summary']['skipped']}")
    print(f"💥 Errors:     {results['summary']['errors']}")
    print()
    print(f"Results saved to: {output_file}")
    print("="*70)
    
    # Return exit code
    if results['summary']['errors'] > 0:
        return 2
    elif results['summary']['failed'] > 0:
        return 1
    else:
        return 0

if __name__ == "__main__":
    sys.exit(main())
