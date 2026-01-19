#!/usr/bin/env python3
"""
State Initialization Script
============================
Initializes watermarks and state files for both Local and Fabric environments.

Usage:
    python scripts/init_state.py [--platform local|fabric] [--force]

Options:
    --platform    Target platform: 'local' (default) or 'fabric'
    --force       Overwrite existing state files
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from aims_data_platform.config import config
from aims_data_platform.watermark_manager import WatermarkManager


def detect_platform() -> str:
    """Detect whether running on Local or Microsoft Fabric."""
    # Check for Fabric-specific paths
    fabric_paths = [
        Path("/lakehouse/default"),
        Path("/lakehouse"),
    ]
    for path in fabric_paths:
        if path.exists():
            return "fabric"
    return "local"


def get_platform_paths(platform: str) -> dict:
    """Get appropriate paths for the target platform."""
    if platform == "fabric":
        base = Path("/lakehouse/default/Files")
        return {
            "watermark_db": base / "metadata" / "watermarks.db",
            "state_dir": base / "metadata" / "state",
            "platform_name": "Microsoft Fabric"
        }
    else:
        base = Path(config.BASE_DIR)
        return {
            "watermark_db": config.WATERMARK_DB_PATH,
            "state_dir": base / "data" / "state",
            "platform_name": "Local Linux"
        }


def init_watermark_db(db_path: Path, force: bool = False) -> bool:
    """Initialize the SQLite watermark database."""
    if db_path.exists() and not force:
        print(f"  ⏭️  Skipping (exists): {db_path}")
        return False
    
    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize database through WatermarkManager
    wm = WatermarkManager(db_path)
    print(f"  ✅ Created watermark database: {db_path}")
    return True


def init_state_files(state_dir: Path, force: bool = False) -> dict:
    """Initialize state files (watermarks.json, dq_logs.jsonl)."""
    state_dir.mkdir(parents=True, exist_ok=True)
    created = []
    
    # 1. watermarks.json - File-based watermarks for run_pipeline.py
    watermarks_file = state_dir / "watermarks.json"
    if not watermarks_file.exists() or force:
        initial_watermarks = {
            "_metadata": {
                "description": "File-based watermarks for incremental processing",
                "created_at": datetime.now().isoformat(),
                "platform": detect_platform(),
                "version": "1.0"
            }
        }
        with open(watermarks_file, 'w') as f:
            json.dump(initial_watermarks, f, indent=2)
        print(f"  ✅ Created: {watermarks_file}")
        created.append("watermarks.json")
    else:
        print(f"  ⏭️  Skipping (exists): {watermarks_file}")
    
    # 2. dq_logs.jsonl - Data Quality logs
    dq_logs_file = state_dir / "dq_logs.jsonl"
    if not dq_logs_file.exists() or force:
        initial_log = {
            "timestamp": datetime.now().isoformat(),
            "event": "initialization",
            "message": "Data Quality logging initialized",
            "platform": detect_platform(),
            "version": "1.0"
        }
        with open(dq_logs_file, 'w') as f:
            f.write(json.dumps(initial_log) + "\n")
        print(f"  ✅ Created: {dq_logs_file}")
        created.append("dq_logs.jsonl")
    else:
        print(f"  ⏭️  Skipping (exists): {dq_logs_file}")
    
    return {"state_dir": state_dir, "files_created": created}


def verify_initialization(db_path: Path, state_dir: Path) -> bool:
    """Verify that initialization was successful."""
    print("\n🔍 Verification:")
    all_good = True
    
    # Check watermark database
    if db_path.exists():
        wm = WatermarkManager(db_path)
        df = wm.list_watermarks()
        print(f"  ✅ Watermark DB: {db_path} ({len(df)} watermarks)")
    else:
        print(f"  ❌ Watermark DB missing: {db_path}")
        all_good = False
    
    # Check state files
    for filename in ["watermarks.json", "dq_logs.jsonl"]:
        filepath = state_dir / filename
        if filepath.exists():
            print(f"  ✅ State file: {filepath}")
        else:
            print(f"  ❌ State file missing: {filepath}")
            all_good = False
    
    return all_good


def main():
    parser = argparse.ArgumentParser(description="Initialize AIMS state management")
    parser.add_argument(
        "--platform", 
        choices=["local", "fabric", "auto"],
        default="auto",
        help="Target platform (default: auto-detect)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing state files"
    )
    args = parser.parse_args()
    
    # Detect or use specified platform
    platform = args.platform if args.platform != "auto" else detect_platform()
    paths = get_platform_paths(platform)
    
    print("=" * 60)
    print(f"AIMS Data Platform - State Initialization")
    print("=" * 60)
    print(f"Platform: {paths['platform_name']} ({platform})")
    print(f"Force overwrite: {args.force}")
    print()
    
    # Step 1: Initialize watermark database
    print("📁 Initializing Watermark Database:")
    init_watermark_db(paths["watermark_db"], args.force)
    
    # Step 2: Initialize state files
    print("\n📄 Initializing State Files:")
    init_state_files(paths["state_dir"], args.force)
    
    # Step 3: Verify
    success = verify_initialization(paths["watermark_db"], paths["state_dir"])
    
    print()
    if success:
        print("✅ State initialization complete!")
    else:
        print("❌ Some components failed to initialize")
        sys.exit(1)


if __name__ == "__main__":
    main()
