"""Repository for interaction log entries."""
import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.queue import InteractionLogEntry


class InteractionRepository:
    """Repository for interaction log entries."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, entry: InteractionLogEntry) -> InteractionLogEntry:
        """Create interaction log entry."""
        self.db.add(entry)
        self.db.flush()
        self.db.refresh(entry)
        return entry

    def get_by_id(self, interaction_id: uuid.UUID) -> Optional[InteractionLogEntry]:
        """Get interaction by ID."""
        stmt = select(InteractionLogEntry).where(InteractionLogEntry.id == interaction_id)
        return self.db.scalar(stmt)

    def get_for_customer_account(
        self, customer_account_id: uuid.UUID, limit: int = 100
    ) -> List[InteractionLogEntry]:
        """Get interactions for customer account."""
        stmt = (
            select(InteractionLogEntry)
            .where(InteractionLogEntry.customer_account_id == customer_account_id)
            .order_by(InteractionLogEntry.occurred_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())
