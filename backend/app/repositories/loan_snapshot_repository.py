"""Loan snapshot repository"""
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import LoanSnapshot


class LoanSnapshotRepository:
    """Repository for LoanSnapshot operations"""

    def get_by_id(self, db: Session, loan_snapshot_id: uuid.UUID) -> Optional[LoanSnapshot]:
        """Get loan snapshot by ID"""
        return db.get(LoanSnapshot, loan_snapshot_id)

    def get_for_profile(self, db: Session, profile_id: uuid.UUID) -> list[LoanSnapshot]:
        """Get all loan snapshots for a profile"""
        stmt = (
            select(LoanSnapshot)
            .where(LoanSnapshot.profile_id == profile_id)
            .order_by(LoanSnapshot.loan_name)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def upsert_loan(self, db: Session, loan: LoanSnapshot) -> LoanSnapshot:
        """Insert or update loan snapshot"""
        existing = db.get(LoanSnapshot, loan.loan_snapshot_id)
        if existing:
            for key, value in loan.__dict__.items():
                if not key.startswith('_'):
                    setattr(existing, key, value)
            return existing
        else:
            db.add(loan)
            return loan
