"""Sync run repository."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.receivables import SapSyncRun


class SyncRunRepository:
    """Repository for SAP sync run operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, sync_run: SapSyncRun) -> SapSyncRun:
        """Create sync run."""
        self.db.add(sync_run)
        self.db.commit()
        self.db.refresh(sync_run)
        return sync_run

    def get_by_id(self, run_id: str) -> Optional[SapSyncRun]:
        """Get sync run by ID."""
        try:
            run_uuid = uuid.UUID(run_id)
        except (ValueError, AttributeError):
            return None
        return self.db.query(SapSyncRun).filter(SapSyncRun.id == run_uuid).first()

    def update_status(
        self,
        sync_run: SapSyncRun,
        status: str,
        completed_at: "datetime",
        records_read: int = 0,
        records_upserted: int = 0,
        error_summary: Optional[str] = None,
    ) -> None:
        """Update sync run status."""
        sync_run.run_status = status
        sync_run.completed_at = completed_at
        sync_run.records_read = records_read
        sync_run.records_upserted = records_upserted
        sync_run.error_summary = error_summary
        self.db.commit()
