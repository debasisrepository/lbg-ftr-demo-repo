"""
Payee repository for data access.
Requirement: FR-PAY-001
"""
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.payee import Payee


class PayeeRepository:
    """Repository for payee data access."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_saved_active_payees_for_customer(
        self, 
        customer_profile_ref_id: UUID,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[Payee], int]:
        """
        Get saved_active payees for a customer with pagination.
        
        Args:
            customer_profile_ref_id: Customer UUID
            page: Page number (1-based)
            page_size: Number of items per page
            
        Returns:
            Tuple of (list of Payee objects, total count)
        """
        # Get total count
        count_stmt = (
            select(func.count(Payee.id))
            .where(Payee.customer_profile_ref_id == customer_profile_ref_id)
            .where(Payee.payee_status == "saved_active")
        )
        total = self.db.execute(count_stmt).scalar() or 0
        
        # Get paginated results
        offset = (page - 1) * page_size
        stmt = (
            select(Payee)
            .where(Payee.customer_profile_ref_id == customer_profile_ref_id)
            .where(Payee.payee_status == "saved_active")
            .order_by(Payee.payee_name)
            .offset(offset)
            .limit(page_size)
        )
        payees = list(self.db.execute(stmt).scalars().all())
        
        return payees, total
