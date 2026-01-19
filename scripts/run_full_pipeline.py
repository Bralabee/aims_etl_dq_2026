#!/usr/bin/env python
"""
AIMS Data Platform - Full Pipeline Orchestrator with Landing Zone Management

This script orchestrates the complete data pipeline on both Local and MS Fabric:
1. Move files from landing zone to Bronze
2. Run data profiling and validation
3. Ingest valid data to Silver layer
4. Archive processed files with date stamps
5. Clear landing zone for next SFTP fetch
6. Send notification via Teams/Email

Platform Support:
- Local: Uses shutil/pathlib for filesystem operations
- Fabric: Uses mssparkutils.fs for lakehouse/ABFSS operations

Usage:
    # Full pipeline with notifications
    python scripts/run_full_pipeline.py
    
    # Dry run (no archival or notifications)
    python scripts/run_full_pipeline.py --dry-run
    
    # Custom threshold
    python scripts/run_full_pipeline.py --threshold 90.0
    
    # Skip notifications
    python scripts/run_full_pipeline.py --no-notify
    
    # Force Fabric mode (for testing)
    python scripts/run_full_pipeline.py --fabric

Author: AIMS Data Platform Team
Version: 1.4.0
Created: 2026-01-19
Updated: 2026-01-19 - Added dual-platform support
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from aims_data_platform import BatchProfiler, DataQualityValidator, DataLoader, ConfigLoader
from aims_data_platform.landing_zone_manager import (
    LandingZoneManager,
    NotificationManager,
    RunSummary,
    PlatformFileOps,
    create_landing_zone_manager,
    IS_FABRIC,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def setup_paths(is_fabric: bool = False) -> dict:
    """
    Setup paths based on environment.
    
    Platform-aware path configuration:
    - Local: Uses project_root/data structure
    - Fabric: Uses /lakehouse/default/Files structure
    
    Args:
        is_fabric: Force Fabric mode (auto-detected if not specified)
        
    Returns:
        Dictionary with all required paths
    """
    # Auto-detect if not specified
    if is_fabric or IS_FABRIC:
        base_dir = Path("/lakehouse/default/Files")
        environment = "fabric"
        # Fabric paths use lakehouse structure
        bronze_path = "Bronze"  # Standard medallion architecture
        silver_path = "Silver"
        gold_path = "Gold"
    else:
        base_dir = project_root / "data"
        environment = "local"
        # Local paths - can differ from Fabric naming
        bronze_path = "Samples_LH_Bronze_Aims_26_parquet"  # Current local bronze location
        silver_path = "Silver"
        gold_path = "Gold"
    
    return {
        "base_dir": base_dir,
        "landing_dir": base_dir / "landing",
        "bronze_dir": base_dir / bronze_path,
        "silver_dir": base_dir / silver_path,
        "gold_dir": base_dir / gold_path,
        "archive_dir": base_dir / "archive",
        "config_dir": project_root / "config" / "data_quality",
        "results_dir": project_root / "config" / "validation_results",
        "environment": environment,
        "is_fabric": is_fabric or IS_FABRIC
    }


def run_profiling(bronze_dir: Path, config_dir: Path, workers: int = 4) -> dict:
    """Run data profiling phase."""
    logger.info("=" * 60)
    logger.info("PHASE 1: DATA PROFILING")
    logger.info("=" * 60)
    
    start_time = datetime.now()
    
    try:
        results = BatchProfiler.run_parallel_profiling(
            input_dir=str(bronze_dir),
            output_dir=str(config_dir),
            workers=workers,
            sample_size=100000
        )
        
        success_count = len([r for r in results if r.get('status') == 'success'])
        error_count = len([r for r in results if r.get('status') != 'success'])
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Profiling complete: {success_count} configs generated, {error_count} errors in {duration:.1f}s")
        
        return {
            "status": "success" if error_count == 0 else "partial",
            "configs_generated": success_count,
            "errors": error_count,
            "duration_seconds": duration
        }
    except Exception as e:
        logger.error(f"Profiling failed: {e}")
        return {"status": "failed", "error": str(e)}


def run_validation_and_ingestion(
    bronze_dir: Path,
    config_dir: Path,
    silver_dir: Path,
    threshold: float = 85.0,
    workers: int = 4
) -> dict:
    """Run validation and ingestion phase.
    
    Note: This function performs a COMPLETE OVERWRITE of the Silver layer.
    Raw data is archived in the landing zone, so no deltas are needed.
    """
    logger.info("=" * 60)
    logger.info("PHASE 2: VALIDATION & INGESTION")
    logger.info("=" * 60)
    
    start_time = datetime.now()
    
    # Clear Silver directory for complete overwrite (no append/delta needed)
    # Raw files are archived in landing zone with date stamps
    if silver_dir.exists():
        import shutil
        for existing_file in silver_dir.glob("*.parquet"):
            existing_file.unlink()
            logger.debug(f"Cleared existing: {existing_file.name}")
        logger.info(f"Cleared Silver directory for fresh write")
    
    parquet_files = list(bronze_dir.glob("*.parquet"))
    logger.info(f"Found {len(parquet_files)} parquet files to validate")
    
    results = {
        "total": len(parquet_files),
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "errors": 0,
        "quality_scores": []
    }
    
    for parquet_file in sorted(parquet_files):
        table_name = parquet_file.stem
        config_file = config_dir / f"{table_name}_validation.yml"
        
        if not config_file.exists():
            logger.warning(f"SKIPPED: {table_name} (no config)")
            results["skipped"] += 1
            continue
        
        try:
            validator = DataQualityValidator(config_path=str(config_file))
            df = DataLoader.load_data(str(parquet_file), sample_size=100000)
            result = validator.validate(df)
            
            success_rate = result.get('success_rate', 0)
            results["quality_scores"].append(success_rate)
            
            if result.get('success', False):
                results["passed"] += 1
                logger.info(f"✅ PASSED: {table_name} ({success_rate:.1f}%)")
                
                # Ingest to Silver
                silver_file = silver_dir / f"{table_name}.parquet"
                df.to_parquet(silver_file, index=False, engine='pyarrow')
            else:
                results["failed"] += 1
                logger.warning(f"❌ FAILED: {table_name} ({success_rate:.1f}%)")
                
        except Exception as e:
            results["errors"] += 1
            logger.error(f"💥 ERROR: {table_name} - {e}")
    
    duration = (datetime.now() - start_time).total_seconds()
    
    avg_quality = sum(results["quality_scores"]) / len(results["quality_scores"]) if results["quality_scores"] else 0
    pass_rate = (results["passed"] / results["total"] * 100) if results["total"] > 0 else 0
    
    logger.info(f"Validation complete: {results['passed']}/{results['total']} passed ({pass_rate:.1f}%)")
    logger.info(f"Average quality score: {avg_quality:.1f}%")
    
    return {
        "summary": results,
        "avg_quality_score": avg_quality,
        "pass_rate": pass_rate,
        "duration_seconds": duration
    }


def main():
    parser = argparse.ArgumentParser(description="AIMS Full Pipeline with Landing Zone Management")
    parser.add_argument("--threshold", type=float, default=85.0, help="DQ threshold percentage")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel workers")
    parser.add_argument("--dry-run", action="store_true", help="Run without archival or notifications")
    parser.add_argument("--no-notify", action="store_true", help="Skip notifications")
    parser.add_argument("--teams-webhook", type=str, help="Teams webhook URL (or set TEAMS_WEBHOOK_URL env var)")
    parser.add_argument("--skip-profiling", action="store_true", help="Skip profiling phase")
    parser.add_argument("--cleanup-days", type=int, default=90, help="Remove archives older than N days")
    parser.add_argument("--fabric", action="store_true", help="Force Fabric mode (for testing)")
    
    args = parser.parse_args()
    
    logger.info("=" * 70)
    logger.info("AIMS DATA PLATFORM - FULL PIPELINE ORCHESTRATOR")
    logger.info("=" * 70)
    
    # Setup paths (with optional Fabric override)
    paths = setup_paths(is_fabric=args.fabric)
    logger.info(f"Environment: {paths['environment']}")
    logger.info(f"Platform Detection: {'Fabric' if IS_FABRIC else 'Local'} (override: {args.fabric})")
    logger.info(f"Bronze: {paths['bronze_dir']}")
    logger.info(f"Silver: {paths['silver_dir']}")
    logger.info(f"Archive: {paths['archive_dir']}")
    
    # Initialize landing zone manager with platform awareness
    notification_manager = NotificationManager(
        teams_webhook_url=args.teams_webhook
    )
    
    landing_manager = LandingZoneManager(
        landing_dir=paths['landing_dir'],
        bronze_dir=paths['bronze_dir'],
        archive_dir=paths['archive_dir'],
        notification_manager=notification_manager,
        is_fabric=paths['is_fabric']
    )
    
    run_id = landing_manager.generate_run_id()
    pipeline_start = datetime.now()
    
    logger.info(f"Run ID: {run_id}")
    logger.info(f"Dry Run: {args.dry_run}")
    
    # Track total results
    pipeline_results = {
        "run_id": run_id,
        "environment": paths['environment'],
        "phases": []
    }
    
    # Phase 0: Move files from Landing to Bronze (if any)
    landing_files = landing_manager.list_landing_files()
    if landing_files:
        logger.info("=" * 60)
        logger.info("PHASE 0: LANDING ZONE → BRONZE")
        logger.info("=" * 60)
        logger.info(f"Found {len(landing_files)} files in landing zone")
        
        if not args.dry_run:
            move_result = landing_manager.move_landing_to_bronze(run_id)
            logger.info(f"Moved {len(move_result['files_moved'])} files to Bronze")
            if move_result['errors']:
                logger.warning(f"Move errors: {move_result['errors']}")
            pipeline_results["phases"].append(("landing_to_bronze", move_result))
        else:
            logger.info("DRY RUN: Would move files from landing to Bronze")
            for f in landing_files:
                logger.info(f"  - {f.name}")
    else:
        logger.info("No files in landing zone - using existing Bronze data")
    
    # Phase 1: Profiling (optional)
    if not args.skip_profiling:
        profiling_results = run_profiling(
            bronze_dir=paths['bronze_dir'],
            config_dir=paths['config_dir'],
            workers=args.workers
        )
        pipeline_results["phases"].append(("profiling", profiling_results))
    
    # Phase 2: Validation & Ingestion
    validation_results = run_validation_and_ingestion(
        bronze_dir=paths['bronze_dir'],
        config_dir=paths['config_dir'],
        silver_dir=paths['silver_dir'],
        threshold=args.threshold,
        workers=args.workers
    )
    pipeline_results["phases"].append(("validation", validation_results))
    pipeline_results["summary"] = validation_results["summary"]
    pipeline_results["avg_quality_score"] = validation_results["avg_quality_score"]
    
    # Calculate total duration
    pipeline_results["duration_seconds"] = (datetime.now() - pipeline_start).total_seconds()
    
    # Phase 3: Archive and Notify (unless dry-run)
    if not args.dry_run:
        logger.info("=" * 60)
        logger.info("PHASE 3: ARCHIVE & NOTIFY")
        logger.info("=" * 60)
        
        run_summary = landing_manager.run_full_cycle(
            pipeline_results=pipeline_results,
            send_notification=not args.no_notify
        )
        
        # Cleanup old archives
        if args.cleanup_days > 0:
            removed = landing_manager.cleanup_old_archives(keep_days=args.cleanup_days)
            logger.info(f"Cleaned up {removed} old archives (older than {args.cleanup_days} days)")
        
        # Verify landing zone is ready
        is_ready = landing_manager.verify_landing_zone_empty()
        
        logger.info("=" * 70)
        logger.info("PIPELINE SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Status: {run_summary.status.upper()}")
        logger.info(f"Files Processed: {run_summary.files_processed}")
        logger.info(f"Pass Rate: {run_summary.pass_rate:.1f}%")
        logger.info(f"Avg Quality: {run_summary.avg_quality_score:.1f}%")
        logger.info(f"Archive: {run_summary.archive_path}")
        logger.info(f"Landing Zone Ready: {'✅ Yes' if is_ready else '❌ No'}")
        logger.info(f"Duration: {run_summary.duration_seconds:.1f}s")
        
        if run_summary.action_required:
            logger.warning("ACTION REQUIRED:")
            for item in run_summary.action_items:
                logger.warning(f"  - {item}")
    else:
        logger.info("=" * 70)
        logger.info("DRY RUN COMPLETE - No archival or notifications sent")
        logger.info("=" * 70)
        summary = validation_results["summary"]
        logger.info(f"Files Processed: {summary['total']}")
        logger.info(f"Passed: {summary['passed']}")
        logger.info(f"Failed: {summary['failed']}")
        logger.info(f"Pass Rate: {validation_results['pass_rate']:.1f}%")
    
    return 0 if validation_results["summary"]["errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
