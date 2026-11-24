"""Queue repository."""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.customers import CustomerAccount
from app.models.queue import PrioritizationAssessment, QueueItem
from app.models.receivables import ReceivableItem


class QueueRepository:
    """Repository for queue operations."""

    def __init__(self, db: Session):
        self.db = db

    def list_items(
        self,
        queue_state: Optional[str] = None,
        non_standard: Optional[bool] = None,
        non_standard_reason: Optional[str] = None,
        customer_id: Optional[str] = None,
        assigned_user_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[List[QueueItem], int]:
        """List queue items with filters."""
        query = (
            self.db.query(QueueItem)
            .join(ReceivableItem)
            .join(CustomerAccount)
        )

        if queue_state:
            query = query.filter(QueueItem.queue_state == queue_state)
        if non_standard is not None:
            query = query.filter(QueueItem.is_non_standard == non_standard)
        if non_standard_reason:
            query = query.filter(QueueItem.non_standard_reason == non_standard_reason)
        if customer_id:
            import uuid as uuid_module
            customer_uuid = uuid_module.UUID(customer_id) if isinstance(customer_id, str) else customer_id
            query = query.filter(CustomerAccount.customer_id == customer_uuid)
        if assigned_user_id:
            import uuid as uuid_module
            user_uuid = uuid_module.UUID(assigned_user_id) if isinstance(assigned_user_id, str) else assigned_user_id
            query = query.filter(QueueItem.assigned_user_id == user_uuid)

        total = query.count()

        items = (
            query.order_by(QueueItem.current_rank)
            .limit(limit)
            .offset(offset)
            .all()
        )

        return items, total

    def get_groups(self) -> List[dict]:
        """Get queue groups by state."""
        results = (
            self.db.query(
                QueueItem.queue_state,
                func.count(QueueItem.id).label("count"),
                func.sum(ReceivableItem.open_amount).label("total_amount"),
            )
            .join(ReceivableItem)
            .group_by(QueueItem.queue_state)
            .all()
        )

        return [
            {
                "queue_state": r.queue_state,
                "count": r.count,
                "total_amount": r.total_amount or Decimal("0"),
            }
            for r in results
        ]

    def get_data_freshness(self) -> Optional[datetime]:
        """Get latest queue refresh timestamp."""
        result = self.db.query(func.max(QueueItem.last_refreshed_at)).scalar()
        return result

    def upsert_item(self, item: QueueItem) -> QueueItem:
        """Upsert queue item."""
        existing = (
            self.db.query(QueueItem)
            .filter(QueueItem.receivable_item_id == item.receivable_item_id)
            .first()
        )

        if existing:
            for key, value in item.__dict__.items():
                if not key.startswith("_"):
                    setattr(existing, key, value)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            self.db.add(item)
            self.db.commit()
            self.db.refresh(item)
            return item

    def create_assessment(self, assessment: PrioritizationAssessment) -> PrioritizationAssessment:
        """Create prioritization assessment."""
        self.db.add(assessment)
        self.db.commit()
        self.db.refresh(assessment)
        return assessment
