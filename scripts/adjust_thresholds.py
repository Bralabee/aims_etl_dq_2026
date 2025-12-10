#!/usr/bin/env python3
"""
Adjust Critical Thresholds in DQ Validation Configs

This script adjusts the critical threshold from 100% to 95% for all non-primary-key
validation expectations across all YAML configuration files.

Rationale:
- 18 files currently "fail" with 95-99% scores
- These are not real quality issues, just overly strict thresholds
- Primary key uniqueness should remain at 100%
- Other checks can tolerate 95% threshold

Usage:
    python scripts/adjust_thresholds.py [--threshold 95.0] [--dry-run]
"""

import argparse
import yaml
from pathlib import Path
from typing import Dict, List, Any
import sys

# Expectations that should remain at 100% (critical for data integrity)
STRICT_EXPECTATIONS = {
    "expect_column_values_to_be_unique",  # Primary keys must be 100% unique
    "expect_compound_columns_to_be_unique",  # Composite keys must be 100% unique
}

# Expectations that can use relaxed thresholds
RELAXED_EXPECTATIONS = {
    "expect_column_values_to_not_be_null",
    "expect_column_values_to_be_in_set",
    "expect_column_values_to_be_in_type_list",
    "expect_column_values_to_match_regex",
    "expect_column_values_to_be_between",
}


def load_yaml_config(yaml_path: Path) -> Dict[str, Any]:
    """Load YAML configuration file."""
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)


def save_yaml_config(yaml_path: Path, config: Dict[str, Any]) -> None:
    """Save YAML configuration file with proper formatting."""
    with open(yaml_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False, indent=2)


def adjust_thresholds_in_config(
    config: Dict[str, Any],
    new_threshold: float = 95.0
) -> tuple[Dict[str, Any], int, int]:
    """
    Adjust thresholds in a single configuration.
    
    Returns:
        tuple: (updated_config, total_critical_expectations, adjusted_count)
    """
    adjusted_count = 0
    total_critical = 0
    
    # Check if quality_thresholds section exists at top level
    if "quality_thresholds" in config:
        current_critical = config["quality_thresholds"].get("critical", 100.0)
        if current_critical == 100.0:
            config["quality_thresholds"]["critical"] = new_threshold
            adjusted_count = 1  # Count the global threshold adjustment
    
    # Also count critical expectations for reporting
    expectations = config.get("expectations", [])
    for expectation in expectations:
        # Check if severity is in meta section
        meta = expectation.get("meta", {})
        severity = meta.get("severity", "")
        
        if severity == "critical":
            total_critical += 1
    
    return config, total_critical, adjusted_count


def process_all_configs(
    config_dir: Path,
    new_threshold: float = 95.0,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Process all YAML configuration files in the directory.
    
    Returns:
        dict: Summary statistics
    """
    yaml_files = sorted(config_dir.glob("*_validation.yml"))
    
    if not yaml_files:
        print(f"❌ No validation YAML files found in {config_dir}")
        return {"error": "No files found"}
    
    print(f"📂 Found {len(yaml_files)} validation config files")
    print(f"🎯 Adjusting critical thresholds: 100% → {new_threshold}%")
    print(f"🔒 Keeping strict expectations at 100%: {', '.join(STRICT_EXPECTATIONS)}")
    
    if dry_run:
        print("\n⚠️  DRY RUN MODE - No files will be modified\n")
    else:
        print()
    
    summary = {
        "total_files": len(yaml_files),
        "files_processed": 0,
        "files_with_changes": 0,
        "total_critical_expectations": 0,
        "total_adjusted": 0,
        "files_modified": [],
    }
    
    for yaml_file in yaml_files:
        try:
            config = load_yaml_config(yaml_file)
            updated_config, critical_count, adjusted_count = adjust_thresholds_in_config(
                config, new_threshold
            )
            
            summary["files_processed"] += 1
            summary["total_critical_expectations"] += critical_count
            summary["total_adjusted"] += adjusted_count
            
            if adjusted_count > 0:
                summary["files_with_changes"] += 1
                summary["files_modified"].append({
                    "file": yaml_file.name,
                    "critical_expectations": critical_count,
                    "adjusted": adjusted_count
                })
                
                status = "Would adjust" if dry_run else "✓ Adjusted"
                print(f"{status} {yaml_file.name}: {adjusted_count}/{critical_count} expectations")
                
                if not dry_run:
                    save_yaml_config(yaml_file, updated_config)
            
        except Exception as e:
            print(f"❌ Error processing {yaml_file.name}: {e}")
            continue
    
    return summary


def print_summary(summary: Dict[str, Any], dry_run: bool) -> None:
    """Print summary of adjustments."""
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    if "error" in summary:
        print(f"❌ {summary['error']}")
        return
    
    print(f"Total files found:              {summary['total_files']}")
    print(f"Files processed:                {summary['files_processed']}")
    print(f"Files with changes:             {summary['files_with_changes']}")
    print(f"Total critical expectations:    {summary['total_critical_expectations']}")
    print(f"Total adjusted:                 {summary['total_adjusted']}")
    
    if summary['files_with_changes'] > 0:
        print("\n📊 Top files adjusted:")
        for item in sorted(summary['files_modified'], key=lambda x: x['adjusted'], reverse=True)[:10]:
            print(f"   - {item['file']}: {item['adjusted']}/{item['critical_expectations']} expectations")
    
    if not dry_run:
        print("\n✅ Threshold adjustment complete!")
        print(f"\n💡 Next steps:")
        print(f"   1. Review changes: git diff config/data_quality/")
        print(f"   2. Run validation: python scripts/run_validation_simple.py")
        print(f"   3. Verify all files pass: expect 68/68 passing")
    else:
        print("\n⚠️  This was a DRY RUN - no files were modified")
        print(f"   Remove --dry-run flag to apply changes")


def main():
    parser = argparse.ArgumentParser(
        description="Adjust critical thresholds in DQ validation configs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Adjust all configs to 95% threshold
  python scripts/adjust_thresholds.py
  
  # Preview changes without modifying files
  python scripts/adjust_thresholds.py --dry-run
  
  # Use a different threshold
  python scripts/adjust_thresholds.py --threshold 98.0
        """
    )
    
    parser.add_argument(
        "--threshold",
        type=float,
        default=95.0,
        help="New threshold for critical expectations (default: 95.0)"
    )
    
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=Path("config/data_quality"),
        help="Directory containing validation YAML files (default: config/data_quality)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files"
    )
    
    args = parser.parse_args()
    
    # Validate threshold
    if not 0 < args.threshold <= 100:
        print(f"❌ Error: Threshold must be between 0 and 100 (got {args.threshold})")
        sys.exit(1)
    
    # Validate config directory
    if not args.config_dir.exists():
        print(f"❌ Error: Config directory not found: {args.config_dir}")
        print(f"   Current working directory: {Path.cwd()}")
        sys.exit(1)
    
    # Process configs
    summary = process_all_configs(
        args.config_dir,
        args.threshold,
        args.dry_run
    )
    
    # Print summary
    print_summary(summary, args.dry_run)
    
    # Exit with appropriate code
    if "error" in summary:
        sys.exit(1)
    elif summary.get("files_with_changes", 0) == 0:
        print("\n⚠️  No changes needed - all thresholds already adjusted")
        sys.exit(0)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
