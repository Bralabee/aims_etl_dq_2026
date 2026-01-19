"""
Landing Zone Manager for AIMS Data Platform

Handles:
1. Moving files from landing zone to Bronze layer
2. Archiving processed files with date stamps
3. Ensuring landing zone is empty for next SFTP fetch
4. Sending notifications via Teams webhook or email

Author: AIMS Data Platform Team
Version: 1.3.0
Created: 2026-01-19
"""

import os
import shutil
import json
import logging
import smtplib
import requests
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class RunSummary:
    """Summary of a pipeline run for notifications."""
    run_id: str
    run_timestamp: str
    environment: str
    landing_files_count: int
    files_processed: int
    files_passed_dq: int
    files_failed_dq: int
    files_errored: int
    pass_rate: float
    avg_quality_score: float
    duration_seconds: float
    archive_path: str
    status: str  # 'success', 'partial', 'failed'
    action_required: bool
    action_items: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_markdown(self) -> str:
        """Generate markdown summary for Teams/Email."""
        status_emoji = {
            'success': '✅',
            'partial': '⚠️',
            'failed': '❌'
        }.get(self.status, '❓')
        
        md = f"""
# {status_emoji} AIMS Data Pipeline Run Summary

**Run ID:** `{self.run_id}`  
**Timestamp:** {self.run_timestamp}  
**Environment:** {self.environment}  
**Duration:** {self.duration_seconds:.1f} seconds  

---

## 📊 Processing Statistics

| Metric | Value |
|--------|-------|
| Files in Landing Zone | {self.landing_files_count} |
| Files Processed | {self.files_processed} |
| ✅ Passed DQ Validation | {self.files_passed_dq} |
| ❌ Failed DQ Validation | {self.files_failed_dq} |
| 💥 Errors | {self.files_errored} |
| **Pass Rate** | **{self.pass_rate:.1f}%** |
| **Avg Quality Score** | **{self.avg_quality_score:.1f}%** |

---

## 📁 Archive Location

`{self.archive_path}`

---

"""
        if self.action_required:
            md += "## ⚡ Action Required\n\n"
            for item in self.action_items:
                md += f"- {item}\n"
        else:
            md += "## ✅ No Action Required\n\nAll files processed successfully.\n"
        
        return md


class NotificationManager:
    """Handles sending notifications via Teams webhook or email."""
    
    def __init__(
        self,
        teams_webhook_url: Optional[str] = None,
        smtp_server: Optional[str] = None,
        smtp_port: int = 587,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        email_from: Optional[str] = None,
        email_to: Optional[List[str]] = None
    ):
        self.teams_webhook_url = teams_webhook_url or os.getenv("TEAMS_WEBHOOK_URL")
        self.smtp_server = smtp_server or os.getenv("SMTP_SERVER")
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username or os.getenv("SMTP_USERNAME")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD")
        self.email_from = email_from or os.getenv("EMAIL_FROM")
        self.email_to = email_to or (os.getenv("EMAIL_TO", "").split(",") if os.getenv("EMAIL_TO") else [])
    
    def send_teams_notification(self, summary: RunSummary) -> bool:
        """Send notification to Microsoft Teams channel via webhook."""
        if not self.teams_webhook_url:
            logger.warning("Teams webhook URL not configured. Skipping Teams notification.")
            return False
        
        try:
            # Teams Adaptive Card format
            card = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": self._get_theme_color(summary.status),
                "summary": f"AIMS Pipeline Run: {summary.status.upper()}",
                "sections": [
                    {
                        "activityTitle": f"{'✅' if summary.status == 'success' else '⚠️' if summary.status == 'partial' else '❌'} AIMS Data Pipeline - {summary.status.upper()}",
                        "activitySubtitle": f"Run ID: {summary.run_id}",
                        "facts": [
                            {"name": "Timestamp", "value": summary.run_timestamp},
                            {"name": "Environment", "value": summary.environment},
                            {"name": "Duration", "value": f"{summary.duration_seconds:.1f}s"},
                            {"name": "Files Processed", "value": str(summary.files_processed)},
                            {"name": "Passed DQ", "value": str(summary.files_passed_dq)},
                            {"name": "Failed DQ", "value": str(summary.files_failed_dq)},
                            {"name": "Pass Rate", "value": f"{summary.pass_rate:.1f}%"},
                            {"name": "Avg Quality", "value": f"{summary.avg_quality_score:.1f}%"},
                            {"name": "Archive Path", "value": summary.archive_path}
                        ],
                        "markdown": True
                    }
                ]
            }
            
            # Add action items if any
            if summary.action_required:
                card["sections"].append({
                    "activityTitle": "⚡ Action Required",
                    "text": "\n".join([f"• {item}" for item in summary.action_items])
                })
            
            response = requests.post(
                self.teams_webhook_url,
                json=card,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            logger.info("Teams notification sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Teams notification: {e}")
            return False
    
    def send_email_notification(self, summary: RunSummary) -> bool:
        """Send notification via email."""
        if not all([self.smtp_server, self.email_from, self.email_to]):
            logger.warning("Email configuration incomplete. Skipping email notification.")
            return False
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[AIMS Pipeline] {summary.status.upper()} - {summary.run_id}"
            msg["From"] = self.email_from
            msg["To"] = ", ".join(self.email_to)
            
            # Plain text version
            text_content = f"""
AIMS Data Pipeline Run Summary
==============================

Run ID: {summary.run_id}
Timestamp: {summary.run_timestamp}
Status: {summary.status.upper()}
Duration: {summary.duration_seconds:.1f} seconds

Processing Statistics:
- Files in Landing Zone: {summary.landing_files_count}
- Files Processed: {summary.files_processed}
- Passed DQ Validation: {summary.files_passed_dq}
- Failed DQ Validation: {summary.files_failed_dq}
- Pass Rate: {summary.pass_rate:.1f}%
- Avg Quality Score: {summary.avg_quality_score:.1f}%

Archive Location: {summary.archive_path}
"""
            if summary.action_required:
                text_content += "\nACTION REQUIRED:\n"
                for item in summary.action_items:
                    text_content += f"  - {item}\n"
            
            # HTML version
            html_content = summary.to_markdown()
            
            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.email_from, self.email_to, msg.as_string())
            
            logger.info(f"Email notification sent to {', '.join(self.email_to)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False
    
    def _get_theme_color(self, status: str) -> str:
        """Get Teams card theme color based on status."""
        colors = {
            'success': '00FF00',  # Green
            'partial': 'FFA500',  # Orange
            'failed': 'FF0000'   # Red
        }
        return colors.get(status, '808080')


class LandingZoneManager:
    """
    Manages the landing zone lifecycle:
    1. Move files from landing to Bronze
    2. Archive processed files with date stamps
    3. Clear landing zone for next SFTP fetch
    """
    
    def __init__(
        self,
        landing_dir: Path,
        bronze_dir: Path,
        archive_dir: Path,
        notification_manager: Optional[NotificationManager] = None
    ):
        self.landing_dir = Path(landing_dir)
        self.bronze_dir = Path(bronze_dir)
        self.archive_dir = Path(archive_dir)
        self.notification_manager = notification_manager or NotificationManager()
        
        # Ensure directories exist
        for dir_path in [self.landing_dir, self.bronze_dir, self.archive_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def generate_run_id(self) -> str:
        """Generate unique run ID with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"run_{timestamp}"
    
    def get_archive_path(self, run_id: str) -> Path:
        """Get the archive path for a specific run."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        return self.archive_dir / f"{date_str}_{run_id}"
    
    def list_landing_files(self, pattern: str = "*.parquet") -> List[Path]:
        """List all files in landing zone matching pattern."""
        return list(self.landing_dir.glob(pattern))
    
    def move_landing_to_bronze(self, run_id: str) -> Dict[str, Any]:
        """
        Move files from landing zone to Bronze layer.
        
        Returns dict with:
        - files_moved: List of moved files
        - errors: List of any errors
        """
        result = {
            "files_moved": [],
            "errors": [],
            "run_id": run_id
        }
        
        landing_files = self.list_landing_files()
        logger.info(f"Found {len(landing_files)} files in landing zone")
        
        for src_file in landing_files:
            dst_file = self.bronze_dir / src_file.name
            try:
                # Copy to Bronze (keep original in landing for archival)
                shutil.copy2(src_file, dst_file)
                result["files_moved"].append(str(src_file.name))
                logger.info(f"Copied {src_file.name} to Bronze")
            except Exception as e:
                error_msg = f"Failed to copy {src_file.name}: {e}"
                result["errors"].append(error_msg)
                logger.error(error_msg)
        
        return result
    
    def archive_landing_files(self, run_id: str) -> Dict[str, Any]:
        """
        Move files from landing zone to date-stamped archive.
        
        This clears the landing zone for the next SFTP fetch.
        """
        archive_path = self.get_archive_path(run_id)
        archive_path.mkdir(parents=True, exist_ok=True)
        
        result = {
            "archive_path": str(archive_path),
            "files_archived": [],
            "errors": []
        }
        
        landing_files = self.list_landing_files()
        
        for src_file in landing_files:
            dst_file = archive_path / src_file.name
            try:
                # Move (not copy) to archive - this clears the landing zone
                shutil.move(str(src_file), str(dst_file))
                result["files_archived"].append(str(src_file.name))
                logger.info(f"Archived {src_file.name} to {archive_path}")
            except Exception as e:
                error_msg = f"Failed to archive {src_file.name}: {e}"
                result["errors"].append(error_msg)
                logger.error(error_msg)
        
        # Save run metadata
        metadata = {
            "run_id": run_id,
            "archived_at": datetime.now().isoformat(),
            "files": result["files_archived"],
            "errors": result["errors"]
        }
        metadata_file = archive_path / "_run_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return result
    
    def verify_landing_zone_empty(self) -> bool:
        """Verify the landing zone is empty and ready for next fetch."""
        remaining_files = self.list_landing_files()
        if remaining_files:
            logger.warning(f"Landing zone not empty! {len(remaining_files)} files remaining")
            return False
        logger.info("Landing zone is empty and ready for next SFTP fetch")
        return True
    
    def cleanup_old_archives(self, keep_days: int = 90) -> int:
        """Remove archives older than specified days."""
        cutoff_date = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
        removed_count = 0
        
        for archive_dir in self.archive_dir.iterdir():
            if archive_dir.is_dir():
                try:
                    # Parse date from directory name (format: YYYY-MM-DD_run_...)
                    dir_date_str = archive_dir.name.split("_")[0]
                    dir_date = datetime.strptime(dir_date_str, "%Y-%m-%d")
                    
                    if dir_date.timestamp() < cutoff_date:
                        shutil.rmtree(archive_dir)
                        removed_count += 1
                        logger.info(f"Removed old archive: {archive_dir}")
                except (ValueError, IndexError):
                    # Skip directories that don't match expected naming
                    continue
        
        return removed_count
    
    def run_full_cycle(
        self,
        pipeline_results: Dict[str, Any],
        send_notification: bool = True
    ) -> RunSummary:
        """
        Run the full landing zone management cycle:
        1. Archive processed files
        2. Verify landing zone is empty
        3. Send notification
        
        Args:
            pipeline_results: Results from the data pipeline run
            send_notification: Whether to send Teams/email notification
            
        Returns:
            RunSummary object
        """
        run_id = pipeline_results.get("run_id", self.generate_run_id())
        
        # Archive the files
        archive_result = self.archive_landing_files(run_id)
        
        # Verify landing zone is empty
        is_empty = self.verify_landing_zone_empty()
        
        # Build summary
        summary = pipeline_results.get("summary", {})
        files_processed = summary.get("total", 0)
        files_passed = summary.get("passed", 0)
        files_failed = summary.get("failed", 0)
        files_errored = summary.get("errors", 0)
        
        pass_rate = (files_passed / files_processed * 100) if files_processed > 0 else 0
        avg_quality = pipeline_results.get("avg_quality_score", 0.0)
        
        # Determine status and action items
        action_items = []
        if files_failed > 0:
            action_items.append(f"Review {files_failed} files that failed DQ validation")
        if files_errored > 0:
            action_items.append(f"Investigate {files_errored} files with processing errors")
        if not is_empty:
            action_items.append("Landing zone not empty - manual cleanup required")
        if archive_result["errors"]:
            action_items.append(f"Archive errors: {len(archive_result['errors'])} files failed to archive")
        
        if files_errored > 0 or not is_empty:
            status = "failed"
        elif files_failed > 0 or action_items:
            status = "partial"
        else:
            status = "success"
        
        run_summary = RunSummary(
            run_id=run_id,
            run_timestamp=datetime.now().isoformat(),
            environment=pipeline_results.get("environment", "unknown"),
            landing_files_count=len(archive_result["files_archived"]),
            files_processed=files_processed,
            files_passed_dq=files_passed,
            files_failed_dq=files_failed,
            files_errored=files_errored,
            pass_rate=pass_rate,
            avg_quality_score=avg_quality,
            duration_seconds=pipeline_results.get("duration_seconds", 0),
            archive_path=archive_result["archive_path"],
            status=status,
            action_required=len(action_items) > 0,
            action_items=action_items
        )
        
        # Send notifications
        if send_notification:
            self.notification_manager.send_teams_notification(run_summary)
            self.notification_manager.send_email_notification(run_summary)
        
        # Save summary to archive
        summary_file = Path(archive_result["archive_path"]) / "_run_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(run_summary.to_dict(), f, indent=2)
        
        return run_summary


# Convenience function for quick setup
def create_landing_zone_manager(
    base_dir: Optional[Path] = None,
    teams_webhook_url: Optional[str] = None,
    email_config: Optional[Dict[str, Any]] = None
) -> LandingZoneManager:
    """
    Create a LandingZoneManager with standard configuration.
    
    Args:
        base_dir: Base directory for data paths (defaults to Fabric lakehouse or local)
        teams_webhook_url: Microsoft Teams webhook URL for notifications
        email_config: Email configuration dict with smtp_server, email_from, email_to
        
    Returns:
        Configured LandingZoneManager instance
    """
    from pathlib import Path
    
    # Determine base directory
    if base_dir is None:
        if Path("/lakehouse/default/Files").exists():
            base_dir = Path("/lakehouse/default/Files")
        else:
            # Local development
            base_dir = Path(__file__).parent.parent / "data"
    
    # Setup notification manager
    notification_manager = NotificationManager(
        teams_webhook_url=teams_webhook_url,
        **(email_config or {})
    )
    
    return LandingZoneManager(
        landing_dir=base_dir / "landing",
        bronze_dir=base_dir / "Bronze",
        archive_dir=base_dir / "archive",
        notification_manager=notification_manager
    )
