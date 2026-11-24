"""Queue service."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.adapters.sap.configured import get_sap_receivables_reader
from app.adapters.sap.synchronizer import SapReferenceSynchronizer
from app.core.clock import Clock
from app.core.logging import get_logger
from app.models.queue import PrioritizationAssessment, QueueItem
from app.models.receivables import SapSyncRun
from app.repositories.queue_repository import QueueRepository
from app.repositories.reference_repository import ReferenceRepository
from app.repositories.sync_run_repository import SyncRunRepository

logger = get_logger(__name__)


class QueueService:
    """Service for queue operations."""

    def __init__(self, db: Session, clock: Clock):
        self.db = db
        self.clock = clock
        self.queue_repo = QueueRepository(db)
        self.sync_run_repo = SyncRunRepository(db)
        self.reference_repo = ReferenceRepository(db)

    def execute_refresh(
        self,
        scope: str,
        trigger_type: str,
        triggered_by_user_id: Optional[str],
        customer_id: Optional[str],
        correlation_id: str,
    ) -> SapSyncRun:
        """Execute queue refresh.
        
        Args:
            scope: "full" or "customer"
            trigger_type: "manual" or "scheduled"
            triggered_by_user_id: Optional user ID who triggered
            customer_id: Optional customer ID for customer scope
            correlation_id: Request correlation ID
            
        Returns:
            SapSyncRun record
        """
        now = self.clock.now()

        # Create sync run
        sync_run = SapSyncRun(
            id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
            sync_scope=scope,
            trigger_type=trigger_type,
            triggered_by_user_id=uuid.UUID(triggered_by_user_id) if triggered_by_user_id else None,
            started_at=now,
            run_status="running",
            correlation_id=correlation_id,
        )
        sync_run = self.sync_run_repo.create(sync_run)

        try:
            # Sync from SAP
            sap_reader = get_sap_receivables_reader()
            synchronizer = SapReferenceSynchronizer(self.db, sap_reader)

            company_code = "1000"  # Default company code for MVP
            customer_account_ref = None
            if scope == "customer" and customer_id:
                # Would need to resolve customer_id to account ref in real impl
                pass

            result = synchronizer.sync_open_items(company_code, customer_account_ref)

            # Rank queue items
            items_ranked, items_flagged = self._rank_queue_items(now, str(sync_run.id))

            # Update sync run
            self.sync_run_repo.update_status(
                sync_run,
                status="succeeded",
                completed_at=now,
                records_read=result["records_read"],
                records_upserted=result["records_upserted"],
            )

        except Exception as e:
            logger.exception("queue_refresh_failed", error=str(e))
            self.sync_run_repo.update_status(
                sync_run,
                status="failed",
                completed_at=now,
                error_summary=str(e),
            )

        return sync_run

    def _rank_queue_items(self, now: datetime, sync_run_id: str) -> tuple[int, int]:
        """Rank queue items deterministically.
        
        Returns:
            Tuple of (items_ranked, items_flagged_non_standard)
        """
        # Get all receivable items
        from app.models.receivables import ReceivableItem
        receivables = self.db.query(ReceivableItem).all()

        # For MVP: simple ranking by days_past_due descending, then sap_open_item_ref ascending
        ranked_items = sorted(
            receivables,
            key=lambda r: (-r.days_past_due, r.sap_open_item_ref),
        )

        items_ranked = 0
        items_flagged = 0

        for rank, receivable in enumerate(ranked_items, start=1):
            # Determine queue eligibility and non-standard status
            is_non_standard = False
            non_standard_reason = None
            queue_state = "active"

            if receivable.dispute_indicator:
                is_non_standard = True
                non_standard_reason = "disputed"
            elif receivable.unapplied_cash_indicator:
                is_non_standard = True
                non_standard_reason = "unapplied_cash"
            elif receivable.pending_evidence_indicator:
                is_non_standard = True
                non_standard_reason = "pending_evidence"

            if is_non_standard:
                items_flagged += 1

            # Calculate priority score (simple for MVP: days_past_due * open_amount)
            priority_score = Decimal(str(receivable.days_past_due)) * receivable.open_amount

            # Upsert queue item
            queue_item = QueueItem(
                id=uuid.uuid4(),
                created_at=now,
                updated_at=now,
                receivable_item_id=receivable.id,
                customer_account_id=receivable.customer_account_id,
                queue_type="collections",
                queue_state=queue_state,
                is_non_standard=is_non_standard,
                non_standard_reason=non_standard_reason,
                entered_queue_at=now,
                current_rank=rank,
                current_priority_score=priority_score,
                last_refreshed_at=now,
                last_sync_run_id=uuid.UUID(sync_run_id),
            )
            queue_item = self.queue_repo.upsert_item(queue_item)

            # Create assessment
            assessment = PrioritizationAssessment(
                id=uuid.uuid4(),
                created_at=now,
                updated_at=now,
                queue_item_id=queue_item.id,
                priority_score=priority_score,
                priority_rank=rank,
                assessment_version="v1",
                assessed_at=now,
                factor_summary_json={
                    "days_past_due": receivable.days_past_due,
                    "open_amount": float(receivable.open_amount),
                },
                actionability_status="actionable" if not is_non_standard else "non_standard",
            )
            self.queue_repo.create_assessment(assessment)

            items_ranked += 1

        return items_ranked, items_flagged
