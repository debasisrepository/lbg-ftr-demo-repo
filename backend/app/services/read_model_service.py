"""
Read model service for account overview queries.
Requirement: FR-ACCT-001, FR-ACCT-002, FR-ACCT-003
"""
import uuid

from sqlalchemy.orm import Session

from app.models.account_read_model import AccountReadModel
from app.repositories.read_model_repository import AccountReadModelRepository


class ReadModelService:
    """Service for read model operations."""
    
    def __init__(
        self,
        db: Session,
        read_model_repo: AccountReadModelRepository | None = None
    ):
        self.db = db
        self.read_model_repo = read_model_repo or AccountReadModelRepository(db)
    
    def get_accounts_for_customer(
        self,
        customer_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[AccountReadModel], int]:
        """
        Get paginated account list for customer.
        
        Args:
            customer_id: Customer profile reference ID
            page: 1-based page number
            page_size: Items per page
        
        Returns:
            Tuple of (accounts, total_count)
        """
        return self.read_model_repo.get_accounts_by_customer(
            customer_id,
            page,
            page_size
        )
    
    def get_account_by_id(self, account_id: uuid.UUID) -> AccountReadModel | None:
        """Get single account by ID."""
        return self.read_model_repo.get_account_by_id(account_id)
