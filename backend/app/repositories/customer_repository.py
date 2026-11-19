"""Customer repository for identity lookups"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.customer import Customer


class CustomerRepository:
    """Customer data access"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, customer_id: uuid.UUID) -> Customer | None:
        """Get customer by ID"""
        return self.db.get(Customer, customer_id)

    def get_by_external_identity_ref(self, external_identity_ref: str) -> Customer | None:
        """Get customer by external identity reference (username/email)"""
        stmt = select(Customer).where(Customer.external_identity_ref == external_identity_ref)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def get_active_customer(self, external_identity_ref: str) -> Customer | None:
        """Get active customer by external identity reference"""
        stmt = select(Customer).where(
            Customer.external_identity_ref == external_identity_ref,
            Customer.status == 'active'
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
