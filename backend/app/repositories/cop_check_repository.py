"""CoP check repository"""
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.payee import CopCheck


class CopCheckRepository:
    """Repository for CopCheck operations"""

    def get_by_id(self, db: Session, cop_check_id: uuid.UUID) -> Optional[CopCheck]:
        """Get CoP check by ID"""
        return db.get(CopCheck, cop_check_id)

    def get_latest_for_payee(self, db: Session, payee_id: uuid.UUID) -> Optional[CopCheck]:
        """Get latest CoP check for a payee"""
        stmt = (
            select(CopCheck)
            .where(CopCheck.payee_id == payee_id)
            .order_by(CopCheck.checked_at.desc())
            .limit(1)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def create_cop_check(self, db: Session, cop_check: CopCheck) -> CopCheck:
        """Create new CoP check"""
        db.add(cop_check)
        db.flush()
        return cop_check

    def update_cop_check(self, db: Session, cop_check: CopCheck) -> CopCheck:
        """Update existing CoP check"""
        db.flush()
        return cop_check
