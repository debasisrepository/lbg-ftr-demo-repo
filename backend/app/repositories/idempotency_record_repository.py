"""IdempotencyRecord repository"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.payment import IdempotencyRecord


class IdempotencyRecordRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, record: IdempotencyRecord) -> IdempotencyRecord:
        self.db.add(record)
        self.db.flush()
        return record

    def get_by_key(self, idempotency_key: str) -> IdempotencyRecord | None:
        result = self.db.execute(
            select(IdempotencyRecord).where(IdempotencyRecord.idempotency_key == idempotency_key)
        )
        return result.scalar_one_or_none()
