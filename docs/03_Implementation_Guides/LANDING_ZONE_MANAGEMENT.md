# Landing Zone Management - Architecture Guide

## Overview

This document describes the landing zone management architecture for the AIMS Data Platform, which handles:
1. Files fetched from SFTP weekly
2. Archiving processed files with date stamps
3. Ensuring landing zone is clear for next fetch
4. Notifications via Teams/Email on completion

## Directory Structure

> **✅ AUTO-CREATED:** All medallion layer folders are automatically created on first run by `LandingZoneManager`. No manual folder creation required on either Local or Fabric environments.

```
/lakehouse/default/Files/           # In Microsoft Fabric (auto-detected)
├── landing/                        # ✅ Auto-created - SFTP drops files here
│   └── *.parquet                   # Raw files from SFTP
├── archive/                        # ✅ Auto-created - Date-stamped processed files
│   ├── 2026-01-19_run_20260119_132500/
│   │   ├── aims_assets.parquet
│   │   ├── aims_attributes.parquet
│   │   ├── _run_metadata.json      # Run details
│   │   └── _run_summary.json       # Processing summary
│   └── ...
├── Bronze/                         # ✅ Auto-created - Working bronze layer
├── Silver/                         # ✅ Auto-created - Validated/cleaned data
└── Gold/                           # ✅ Auto-created - Star schema for BI
```

**Folder Auto-Creation Code:**
```python
# From LandingZoneManager.__init__()
for dir_path in [self.landing_dir, self.bronze_dir, self.archive_dir]:
    self.file_ops.makedirs(dir_path)  # Uses mssparkutils.fs.mkdirs on Fabric
```

## Data Flow

```
SFTP Server                     Landing Zone               Bronze              Silver
    │                               │                        │                   │
    │  1. Weekly fetch              │                        │                   │
    ├──────────────────────────────►│                        │                   │
    │                               │                        │                   │
    │                               │  2. Copy to Bronze     │                   │
    │                               ├───────────────────────►│                   │
    │                               │                        │                   │
    │                               │                        │  3. Validate &    │
    │                               │                        │     Profile       │
    │                               │                        │◄─────────────────►│
    │                               │                        │                   │
    │                               │                        │  4. Ingest valid  │
    │                               │                        │     records       │
    │                               │                        ├──────────────────►│
    │                               │                        │                   │
    │                               │  5. Move to Archive    │                   │
    │                               │◄──────────────────────-│                   │
    │                               │  (clears landing)      │                   │
    │                               │                        │                   │
    │                               │  6. Ready for next     │                   │
    │                               │     SFTP fetch         │                   │
    │                               │                        │                   │
```

## Usage

### Command Line

```bash
# Full pipeline with notifications
python scripts/run_full_pipeline.py

# Dry run (no archival or notifications)
python scripts/run_full_pipeline.py --dry-run

# Custom DQ threshold
python scripts/run_full_pipeline.py --threshold 90.0

# Skip profiling (use existing configs)
python scripts/run_full_pipeline.py --skip-profiling

# Skip notifications
python scripts/run_full_pipeline.py --no-notify

# Set Teams webhook
python scripts/run_full_pipeline.py --teams-webhook "https://outlook.office.com/webhook/..."

# Clean up old archives (keep 60 days)
python scripts/run_full_pipeline.py --cleanup-days 60
```

### Python API

```python
from pathlib import Path
from aims_data_platform import LandingZoneManager, NotificationManager

# Initialize managers
notification_manager = NotificationManager(
    teams_webhook_url="https://outlook.office.com/webhook/...",
    # Or configure email
    smtp_server="smtp.office365.com",
    email_from="aims-pipeline@company.com",
    email_to=["data-team@company.com"]
)

landing_manager = LandingZoneManager(
    landing_dir=Path("/lakehouse/default/Files/landing"),
    bronze_dir=Path("/lakehouse/default/Files/Bronze"),
    archive_dir=Path("/lakehouse/default/Files/archive"),
    notification_manager=notification_manager
)

# Generate run ID
run_id = landing_manager.generate_run_id()

# Move files from landing to Bronze
move_result = landing_manager.move_landing_to_bronze(run_id)
print(f"Moved {len(move_result['files_moved'])} files to Bronze")

# After processing, archive and clear landing zone
pipeline_results = {
    "run_id": run_id,
    "environment": "fabric",
    "summary": {
        "total": 68,
        "passed": 50,
        "failed": 18,
        "errors": 0
    },
    "avg_quality_score": 98.8,
    "duration_seconds": 72.5
}

# Archive files and send notification
summary = landing_manager.run_full_cycle(
    pipeline_results=pipeline_results,
    send_notification=True
)

# Verify landing zone is ready
is_ready = landing_manager.verify_landing_zone_empty()
print(f"Landing zone ready: {is_ready}")

# Cleanup old archives
removed = landing_manager.cleanup_old_archives(keep_days=90)
print(f"Removed {removed} old archives")
```

## Configuration

### Environment Variables

Set these in `.env` or as environment variables in Fabric:

```bash
# Teams webhook URL
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/YOUR/WEBHOOK/URL

# Email settings (optional)
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=your_username
SMTP_PASSWORD=your_password
EMAIL_FROM=aims-pipeline@yourcompany.com
EMAIL_TO=data-team@yourcompany.com,ops-team@yourcompany.com

# Landing zone settings
AIMS_LANDING_DIR=data/landing
AIMS_ARCHIVE_DIR=data/archive
AIMS_ARCHIVE_RETENTION_DAYS=90
```

### Configuration File

Copy `config/notification_config.yaml.example` to `config/notification_config.yaml`:

```yaml
teams:
  enabled: true
  webhook_url: "${TEAMS_WEBHOOK_URL}"
  notify_on:
    - success
    - partial
    - failed

email:
  enabled: false
  smtp_server: "smtp.office365.com"
  to_addresses:
    - "data-team@yourcompany.com"

archive:
  retention_days: 90
  directory_format: "date_run"
```

## Setting Up Teams Webhook

1. Go to your Teams channel
2. Click "..." (More options) → "Connectors"
3. Find "Incoming Webhook" and click "Configure"
4. Give it a name (e.g., "AIMS Pipeline")
5. Copy the webhook URL
6. Set as `TEAMS_WEBHOOK_URL` environment variable

## Notification Example

### Teams Card

The notification includes:
- ✅/⚠️/❌ Status indicator
- Run ID and timestamp
- Processing statistics (files processed, passed, failed)
- Pass rate and average quality score
- Archive location
- Action items (if any)

### Sample Notification

```
✅ AIMS Data Pipeline - SUCCESS

Run ID: run_20260119_132500
Timestamp: 2026-01-19T13:25:00

Processing Statistics:
- Files Processed: 68
- Passed DQ: 50
- Failed DQ: 18
- Pass Rate: 73.5%
- Avg Quality: 98.8%

Archive Path: /lakehouse/default/Files/archive/2026-01-19_run_20260119_132500

✅ No Action Required
```

## Integration with Fabric Pipelines

In Microsoft Fabric, you can trigger this as part of a Data Pipeline:

```python
# Fabric notebook cell
from aims_data_platform import create_landing_zone_manager

# Create manager with Fabric paths
manager = create_landing_zone_manager(
    base_dir=Path("/lakehouse/default/Files"),
    teams_webhook_url=spark.conf.get("spark.aims.teams_webhook")
)

# Run the full cycle
summary = manager.run_full_cycle(
    pipeline_results=pipeline_results,
    send_notification=True
)
```

## Archive Retention

By default, archives are kept for 90 days. To customize:

```bash
# Keep archives for 60 days
python scripts/run_full_pipeline.py --cleanup-days 60

# Keep archives forever (no cleanup)
python scripts/run_full_pipeline.py --cleanup-days 0
```

## Troubleshooting

### Landing Zone Not Empty After Processing

If files remain in the landing zone:
1. Check for file permission issues
2. Review `_run_metadata.json` in archive for error details
3. Manually move remaining files and investigate

### Notifications Not Sending

1. Verify webhook URL is correct
2. Check network connectivity
3. Review logs for error messages
4. Test webhook manually with curl:

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"text": "Test message"}' \
  "$TEAMS_WEBHOOK_URL"
```

### Archive Directory Growing Too Large

1. Reduce retention period: `--cleanup-days 30`
2. Enable compression in config: `archive.compress: true`
3. Run cleanup manually: `landing_manager.cleanup_old_archives(keep_days=30)`
