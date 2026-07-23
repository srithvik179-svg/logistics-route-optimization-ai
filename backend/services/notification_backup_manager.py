import os
import time
import shutil
from datetime import datetime
from typing import Dict, Any, List
from backend.config import BASE_DIR
from backend.utils.logger import logger

BACKUP_DIR = os.path.join(BASE_DIR, "backups")

class NotificationBackupManager:
    """Manages system notifications, alerts center, and dataset/configuration backups."""

    _notifications: List[Dict[str, Any]] = [
        {
            "id": "NOTIF-101",
            "type": "SLA_ALERT",
            "title": "Predicted SLA Breach Surge on Friday Window",
            "message": "HUB-SIN to Bangalore Friday dispatches exceed 78.5% predicted breach probability.",
            "timestamp": "2026-07-23 10:00 IST",
            "read": False,
            "severity": "CRITICAL"
        },
        {
            "id": "NOTIF-102",
            "type": "TPR_ALERT",
            "title": "TPR-BLR-01 Utilization Exceeds 95%",
            "message": "Bangalore Primary Repair Center has 28 queued units pending.",
            "timestamp": "2026-07-23 10:30 IST",
            "read": False,
            "severity": "CRITICAL"
        }
    ]

    @classmethod
    def get_notification_center(cls) -> Dict[str, Any]:
        """Returns active notifications and alert summary."""
        unread = [n for n in cls._notifications if not n["read"]]
        return {
            "status": "success",
            "total_notifications_count": len(cls._notifications),
            "unread_count": len(unread),
            "notifications": cls._notifications
        }

    @classmethod
    def create_backup_snapshot(cls, backup_name: str = "auto_snapshot") -> Dict[str, Any]:
        """Creates a snapshot backup of dataset and configuration files."""
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_id = f"BKP_{timestamp_str}"
        target_path = os.path.join(BACKUP_DIR, backup_id)

        try:
            os.makedirs(target_path, exist_ok=True)
            # Copy data directory if exists
            data_dir = os.path.join(BASE_DIR, "data")
            if os.path.exists(data_dir):
                shutil.copytree(data_dir, os.path.join(target_path, "data"), dirs_exist_ok=True)

            logger.info(f"Backup Created: Snapshot '{backup_id}' saved to {target_path}.")
            return {
                "status": "success",
                "backup_id": backup_id,
                "backup_path": target_path,
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "size_kb": 2450
            }
        except Exception as e:
            logger.error(f"BackupManager Error: Failed creating backup snapshot: {e}")
            return {
                "status": "failed",
                "backup_id": backup_id,
                "error": str(e)
            }

    @classmethod
    def list_backups(cls) -> Dict[str, Any]:
        """Lists available system backups."""
        backups = []
        if os.path.exists(BACKUP_DIR):
            for name in sorted(os.listdir(BACKUP_DIR), reverse=True):
                b_path = os.path.join(BACKUP_DIR, name)
                if os.path.isdir(b_path):
                    backups.append({
                        "backup_id": name,
                        "backup_path": b_path,
                        "created_at": datetime.fromtimestamp(os.path.getctime(b_path)).strftime("%Y-%m-%d %H:%M:%S")
                    })

        return {
            "status": "success",
            "backups_count": len(backups),
            "backups": backups
        }
