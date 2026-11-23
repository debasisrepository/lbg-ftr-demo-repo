"""
Read model repository for account overview projection.
Requirement: FR-ACCT-001, FR-ACCT-002, FR-ACCT-003
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account_read_model import AccountReadModel


class AccountReadModelRepository:
    """Repository for account read model queries."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_accounts_by_customer(
        self,
        customer_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[AccountReadModel], int]:
        """
        Get paginated accounts for a customer.
        
        Args:
            customer_id: Customer profile reference ID
            page: 1-based page number
            page_size: Items per page (1-50)
        
        Returns:
            Tuple of (account list, total count)
        """
        # Count total
        count_stmt = select(AccountReadModel).where(
            AccountReadModel.customer_profile_ref_id == customer_id
        )
        total = len(self.db.execute(count_stmt).scalars().all())
        
        # Get paginated results
        offset = (page - 1) * page_size
        stmt = (
            select(AccountReadModel)
            .where(AccountReadModel.customer_profile_ref_id == customer_id)
            .order_by(AccountReadModel.created_at)
            .offset(offset)
            .limit(page_size)
        )
        accounts = self.db.execute(stmt).scalars().all()
        
        return list(accounts), total
    
    def get_account_by_id(self, account_id: uuid.UUID) -> AccountReadModel | None:
        """Get single account by ID."""
        return self.db.get(AccountReadModel, account_id)
