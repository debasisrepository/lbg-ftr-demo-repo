"""Customer repository."""
import uuid
from typing import Optional
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.customers import Customer, CustomerAccount
from app.models.receivables import ReceivableItem


class CustomerRepository:
    """Repository for customer operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_account_count(self, customer_id: uuid.UUID) -> int:
        """Get count of accounts for a customer."""
        count = self.db.scalar(
            select(func.count()).where(CustomerAccount.customer_id == customer_id)
        ) or 0
        return count

    def get_by_id(self, customer_id: uuid.UUID) -> Optional[Customer]:
        """Get customer by ID."""
        return self.db.scalar(
            select(Customer).where(Customer.id == customer_id)
        )

    def get_account_open_balance(self, account_id: uuid.UUID) -> Decimal:
        """Get open balance for an account."""
        balance = self.db.scalar(
            select(func.sum(ReceivableItem.open_amount)).where(
                ReceivableItem.customer_account_id == account_id
            )
        ) or 0
        return balance

    def get_account_by_id(self, account_id: uuid.UUID) -> Optional[CustomerAccount]:
        """Get customer account by ID."""
        return self.db.scalar(
            select(CustomerAccount).where(CustomerAccount.id == account_id)
        )
