"""ScaApproval repository"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.payment import ScaApproval


class ScaApprovalRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, approval: ScaApproval) -> ScaApproval:
        self.db.add(approval)
        self.db.flush()
        return approval

    def get_by_payment_order(self, payment_order_id: uuid.UUID) -> list[ScaApproval]:
        result = self.db.execute(
            select(ScaApproval)
            .where(ScaApproval.payment_order_id == payment_order_id)
            .order_by(ScaApproval.created_at.desc())
        )
        return list(result.scalars().all())
