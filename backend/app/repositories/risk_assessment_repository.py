"""RiskAssessment repository"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.payment import RiskAssessment


class RiskAssessmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, assessment: RiskAssessment) -> RiskAssessment:
        self.db.add(assessment)
        self.db.flush()
        return assessment

    def get_by_payment_order(self, payment_order_id: uuid.UUID) -> RiskAssessment | None:
        result = self.db.execute(
            select(RiskAssessment)
            .where(RiskAssessment.payment_order_id == payment_order_id)
            .order_by(RiskAssessment.assessed_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
