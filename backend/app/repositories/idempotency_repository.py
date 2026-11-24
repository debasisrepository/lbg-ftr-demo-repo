"""Repository for idempotency records."""
import uuid
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.models.promises import IdempotencyRecord


class IdempotencyRepository:
    """Repository for idempotency records."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, record: IdempotencyRecord) -> IdempotencyRecord:
        """Create idempotency record."""
        self.db.add(record)
        self.db.flush()
        self.db.refresh(record)
        return record

    def get_by_key(
        self, user_id: uuid.UUID, operation: str, idempotency_key: str
    ) -> Optional[IdempotencyRecord]:
        """Get idempotency record by key."""
        stmt = select(IdempotencyRecord).where(
            and_(
                IdempotencyRecord.user_id == user_id,
                IdempotencyRecord.operation == operation,
                IdempotencyRecord.idempotency_key == idempotency_key,
            )
        )
        return self.db.scalar(stmt)
