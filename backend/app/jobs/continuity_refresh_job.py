"""Continuity refresh background job."""
import asyncio
import os
from datetime import datetime

from sqlalchemy import select

from app.core.clock import Clock
from app.database import SessionLocal
from app.models.case import Case
from app.repositories.audit_repository import AuditRepository
from app.repositories.case_repository import CaseRepository
from app.repositories.continuity_repository import ContinuityRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.ownership_repository import OwnershipRepository
from app.services.audit_service import AuditService
from app.services.continuity_service import ContinuityService


class ContinuityRefreshJob:
    """Background job to refresh pending continuity packages."""

    def __init__(self):
        self.sweep_interval_seconds = int(os.getenv("CONTINUITY_SWEEP_INTERVAL_SECONDS", "60"))
        self.running = False
        self.task = None

    async def start(self):
        """Start the background job."""
        if self.running:
            return
        
        self.running = True
        self.task = asyncio.create_task(self._run_loop())
        print(f"✓ ContinuityRefreshJob started (interval: {self.sweep_interval_seconds}s)")

    async def stop(self):
        """Stop the background job."""
        if not self.running:
            return
        
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except (asyncio.CancelledError, RuntimeError):
                # RuntimeError occurs when task is attached to different loop (test teardown)
                pass
        print("✓ ContinuityRefreshJob stopped")

    async def _run_loop(self):
        """Main loop."""
        while self.running:
            try:
                await asyncio.sleep(self.sweep_interval_seconds)
                self._process_pending_cases()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"✗ ContinuityRefreshJob error: {e}")

    def _process_pending_cases(self):
        """Process cases with refresh_pending state."""
        db = SessionLocal()
        try:
            # Find cases needing refresh
            stmt = select(Case).where(Case.continuity_state == "refresh_pending").limit(100)
            cases = list(db.scalars(stmt))
            
            if not cases:
                return
            
            print(f"✓ ContinuityRefreshJob processing {len(cases)} pending case(s)")
            
            # Create service
            clock = Clock()
            continuity_service = ContinuityService(
                continuity_repo=ContinuityRepository(db),
                case_repo=CaseRepository(db),
                ownership_repo=OwnershipRepository(db),
                history_repo=HistoryRepository(db),
                audit_repo=AuditRepository(db),
                audit_service=AuditService(AuditRepository(db), clock),
                clock=clock
            )
            
            # Process each case
            for case in cases:
                try:
                    continuity_service.refresh_if_pending(case.id)
                    db.commit()
                except Exception as e:
                    print(f"✗ Failed to refresh case {case.case_reference}: {e}")
                    db.rollback()
        
        finally:
            db.close()


# Global instance
_job_instance = None


def get_job_instance() -> ContinuityRefreshJob:
    """Get the global job instance."""
    global _job_instance
    if _job_instance is None:
        _job_instance = ContinuityRefreshJob()
    return _job_instance
