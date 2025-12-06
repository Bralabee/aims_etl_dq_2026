#!/usr/bin/env python3
"""
AIMS Data Quality Pipeline Runner
=================================

Executes the data ingestion process with Data Quality checks.
This script is designed to be run via cron or CI/CD pipelines.

Usage:
    python run_pipeline.py [--force] [--dry-run]

Options:
    --force     Ignore watermarks and re-process all files
    --dry-run   Run validation but do not update state or move files
"""

import os
import sys
import json
import time
import argparse
import logging
import requests
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv

import concurrent.futures

# Add parent directory to path to import dq_framework if needed
sys.path.append(str(Path(__file__).parent.parent))

try:
    from dq_framework import DataLoader, DataQualityValidator
except ImportError:
    print("❌ Error: dq_framework not found. Install it or run from the project root.")
    sys.exit(1)

# --- Configuration ---
load_dotenv()

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("pipeline.log")
    ]
)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(os.getenv("BASE_DIR", "/home/sanmi/Documents/HS2/HS2_PROJECTS_2025/AIMS_LOCAL"))
DATA_PATH = BASE_DIR / os.getenv("DATA_PATH", "data/Samples_LH_Bronze_Aims_26_parquet")
CONFIG_DIR = BASE_DIR / os.getenv("CONFIG_DIR", "dq_great_expectations/generated_configs")
STATE_DIR = BASE_DIR / os.getenv("STATE_DIR", "data/state")

# Ensure state dir exists
STATE_DIR.mkdir(exist_ok=True, parents=True)

WATERMARK_FILE = STATE_DIR / "watermarks.json"
DQ_LOG_FILE = STATE_DIR / "dq_logs.jsonl"
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL")

# --- Helper Functions ---

def send_teams_alert(message, severity="info"):
    """Send notification to Microsoft Teams."""
    if not TEAMS_WEBHOOK_URL:
        return

    # Map severity to theme colors
    colors = {
        "info": "00FF00",    # Green
        "warning": "FFFF00", # Yellow
        "error": "FF0000"    # Red
    }
    
    # Simple card format
    payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": colors.get(severity, "0076D7"),
        "summary": "AIMS DQ Alert",
        "sections": [{
            "activityTitle": "AIMS Data Quality Pipeline",
            "activitySubtitle": f"Severity: {severity.upper()}",
            "text": message,
            "markdown": True
        }]
    }

    try:
        response = requests.post(TEAMS_WEBHOOK_URL, json=payload, timeout=5)
        if response.status_code != 200:
            logger.error(f"Failed to send Teams alert: {response.text}")
    except Exception as e:
        logger.error(f"Error sending Teams alert: {e}")

def send_slack_alert(message, severity="info"):
    """Send notification to Slack."""
    if not SLACK_WEBHOOK_URL:
        return

    colors = {
        "info": "#36a64f",    # Green
        "warning": "#ffcc00", # Yellow
        "error": "#ff0000"    # Red
    }
    
    payload = {
        "attachments": [
            {
                "color": colors.get(severity, "#cccccc"),
                "text": message,
                "footer": "AIMS DQ Pipeline",
                "ts": int(datetime.now().timestamp())
            }
        ]
    }
    
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=5)
        if response.status_code != 200:
            logger.error(f"Failed to send Slack alert: {response.text}")
    except Exception as e:
        logger.error(f"Error sending Slack alert: {e}")

def load_watermarks():
    if WATERMARK_FILE.exists():
        with open(WATERMARK_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_watermark(file_name):
    watermarks = load_watermarks()
    watermarks[file_name] = datetime.now().isoformat()
    with open(WATERMARK_FILE, 'w') as f:
        json.dump(watermarks, f, indent=2)

def is_processed(file_name):
    watermarks = load_watermarks()
    return file_name in watermarks

def log_dq_result(file_name, status, score, details=None, lineage=None):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "file": file_name,
        "status": status,
        "score": score,
        "details": details or {},
        "lineage": lineage or {}
    }
    with open(DQ_LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def process_single_file(file_path_str, config_dir_str):
    """
    Process a single file.
    Returns a dict with results.
    """
    file_path = Path(file_path_str)
    file_name = file_path.name
    config_dir = Path(config_dir_str)
    
    MAX_RETRIES = 3
    RETRY_DELAY = 5
    
    last_error = None
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # 1. DQ Check
            config_name = file_name.replace('.parquet', '_validation.yml')
            config_path = config_dir / config_name
            
            if not config_path.exists():
                return {
                    "file_name": file_name,
                    "status": "SKIPPED_NO_CONFIG",
                    "score": 0.0,
                    "failures": [],
                    "lineage": {}
                }
            
            validator = DataQualityValidator(config_path=str(config_path))
            df_batch = DataLoader.load_data(str(file_path), sample_size=100000)
            result = validator.validate(df_batch)
            
            validation_passed = result['success']
            score = result['success_rate']
            failures = result.get('failed_expectations', [])
            
            lineage = {
                "source_path": str(file_path),
                "config_path": str(config_path),
                "file_size_bytes": file_path.stat().st_size,
                "validation_timestamp": datetime.now().isoformat(),
                "host": os.uname().nodename
            }
            
            return {
                "file_name": file_name,
                "status": "PASSED" if validation_passed else "FAILED",
                "score": score,
                "failures": failures,
                "lineage": lineage
            }

        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES:
                logger.warning(f"⚠️ Attempt {attempt}/{MAX_RETRIES} failed for {file_name}: {e}. Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"❌ All {MAX_RETRIES} attempts failed for {file_name}.")

    return {
        "file_name": file_name,
        "status": "ERROR",
        "score": 0.0,
        "error": str(last_error),
        "lineage": {}
    }

# --- Main Pipeline ---

def run_pipeline(force=False, dry_run=False, max_workers=4):
    logger.info(f"🚀 Starting AIMS Data Quality Pipeline (Workers: {max_workers})")
    
    if not DATA_PATH.exists():
        logger.error(f"Data directory not found: {DATA_PATH}")
        return

    source_files = list(DATA_PATH.glob("*.parquet"))
    logger.info(f"Found {len(source_files)} files in {DATA_PATH}")

    stats = {
        "processed": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "errors": 0
    }
    
    # Filter files to process
    files_to_process = []
    watermarks = load_watermarks()
    
    for file_path in source_files:
        file_name = file_path.name
        if not force and file_name in watermarks:
            logger.debug(f"Skipping {file_name} (Already Processed)")
            stats["skipped"] += 1
        else:
            files_to_process.append(file_path)
            
    logger.info(f"Files to process: {len(files_to_process)}")

    # Process in parallel
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(process_single_file, str(fp), str(CONFIG_DIR)): fp 
            for fp in files_to_process
        }
        
        for future in tqdm(concurrent.futures.as_completed(future_to_file), total=len(files_to_process), desc="Processing"):
            file_path = future_to_file[future]
            file_name = file_path.name
            
            try:
                result = future.result()
                status = result["status"]
                score = result.get("score", 0.0)
                
                lineage = result.get("lineage", {})

                if status == "SKIPPED_NO_CONFIG":
                    logger.warning(f"No config found for {file_name}. Skipping DQ.")
                    # Treat as passed but with warning? Or skipped?
                    # Original logic treated as passed with 0 score but empty failures
                    # Let's count as passed for now to match original behavior logic roughly
                    # Or maybe skipped is better.
                    # Original: validation_passed = True, score = 0.0
                    if not dry_run:
                        log_dq_result(file_name, "PASSED", 0.0, {"note": "No config found"}, lineage)
                        save_watermark(file_name)
                    stats["passed"] += 1
                    stats["processed"] += 1
                    
                elif status == "PASSED":
                    logger.info(f"✅ DQ Passed: {file_name} (Score: {score:.1f}%)")
                    if not dry_run:
                        log_dq_result(file_name, "PASSED", score, {"failed_count": 0}, lineage)
                        save_watermark(file_name)
                    else:
                        logger.info(f"[DRY RUN] Lineage for {file_name}: {lineage}")
                    stats["passed"] += 1
                    stats["processed"] += 1
                    
                elif status == "FAILED":
                    failures = result.get("failures", [])
                    logger.warning(f"❌ DQ Failed: {file_name} (Score: {score:.1f}%) - {len(failures)} failures")
                    if not dry_run:
                        log_dq_result(
                            file_name, 
                            "FAILED", 
                            score, 
                            {"failed_count": len(failures), "failures": failures[:5]},
                            lineage
                        )
                        alert_msg = f"❌ DQ Failed: *{file_name}*\nScore: {score:.1f}%\nFailures: {len(failures)}"
                        # send_teams_alert(alert_msg) # Optional
                    else:
                        logger.info(f"[DRY RUN] Lineage for {file_name}: {lineage}")
                    stats["failed"] += 1
                    stats["processed"] += 1
                    
                elif status == "ERROR":
                    error_msg = result.get("error", "Unknown error")
                    logger.error(f"💥 Error processing {file_name}: {error_msg}")
                    if not dry_run:
                        log_dq_result(file_name, "ERROR", 0.0, {"error": error_msg}, lineage)
                        alert_msg = f"💥 Pipeline Error: {file_name}\n{error_msg}"
                        send_slack_alert(alert_msg, severity="error")
                        send_teams_alert(alert_msg, severity="error")
                    stats["errors"] += 1
                    stats["processed"] += 1

            except Exception as e:
                logger.error(f"💥 Critical Error processing future for {file_name}: {e}")
                stats["errors"] += 1

    # Summary
    summary_msg = (
        f"🏁 Pipeline Complete\n"
        f"Total: {len(source_files)} | Processed: {stats['processed']} | "
        f"Passed: {stats['passed']} | Failed: {stats['failed']} | "
        f"Skipped: {stats['skipped']} | Errors: {stats['errors']}"
    )
    logger.info(summary_msg)
    
    if stats["failed"] > 0 or stats["errors"] > 0:
        send_slack_alert(summary_msg, severity="warning")
        send_teams_alert(summary_msg, severity="warning")
    else:
        # Only send success alert if we actually did something
        if stats["processed"] > 0:
            send_slack_alert(summary_msg, severity="info")
            send_teams_alert(summary_msg, severity="info")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AIMS DQ Pipeline Runner")
    parser.add_argument("--force", action="store_true", help="Ignore watermarks")
    parser.add_argument("--dry-run", action="store_true", help="Simulate run")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel workers")
    
    args = parser.parse_args()
    
    run_pipeline(force=args.force, dry_run=args.dry_run, max_workers=args.workers)
