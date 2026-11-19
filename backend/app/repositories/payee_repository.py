"""Payee repository"""
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.payee import Payee


class PayeeRepository:
    """Repository for Payee operations"""

    def get_by_id(self, db: Session, payee_id: uuid.UUID) -> Optional[Payee]:
        """Get payee by ID with latest CoP check"""
        stmt = (
            select(Payee)
            .where(Payee.payee_id == payee_id)
            .options(joinedload(Payee.cop_checks))
        )
        result = db.execute(stmt)
        return result.unique().scalar_one_or_none()

    def get_for_customer(self, db: Session, customer_id: uuid.UUID) -> list[Payee]:
        """Get all payees for a customer"""
        stmt = (
            select(Payee)
            .where(Payee.customer_id == customer_id)
            .where(Payee.status.in_(["active", "pending_verification"]))
            .where(Payee.is_saved.is_(True))
            .options(joinedload(Payee.cop_checks))
            .order_by(Payee.payee_name)
        )
        result = db.execute(stmt)
        return list(result.scalars().unique().all())

    def get_for_profile(self, db: Session, customer_id: uuid.UUID, profile_id: uuid.UUID) -> list[Payee]:
        """Get payees for a specific profile"""
        stmt = (
            select(Payee)
            .where(Payee.customer_id == customer_id)
            .where(
                (Payee.profile_id == profile_id) | (Payee.profile_id.is_(None))
            )
            .where(Payee.status.in_(["active", "pending_verification"]))
            .where(Payee.is_saved == True)
            .options(joinedload(Payee.cop_checks))
            .order_by(Payee.payee_name)
        )
        result = db.execute(stmt)
        return list(result.scalars().unique().all())

    def create_payee(self, db: Session, payee: Payee) -> Payee:
        """Create new payee"""
        db.add(payee)
        db.flush()
        return payee

    def update_payee(self, db: Session, payee: Payee) -> Payee:
        """Update existing payee"""
        db.flush()
        return payee

    def belongs_to_customer(self, db: Session, payee_id: uuid.UUID, customer_id: uuid.UUID) -> bool:
        """Check if payee belongs to customer"""
        stmt = select(Payee).where(
            Payee.payee_id == payee_id,
            Payee.customer_id == customer_id
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None
