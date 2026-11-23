"""
PaymentRepository - database operations for payment intents.
Requirement: REQ-PAY-002, REQ-PAY-003, REQ-PAY-004, REQ-PAY-005
"""
import uuid

from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import Session

from app.models.account_read_model import AccountReadModel
from app.models.payee import Payee
from app.models.payment_intent import PaymentIntent


class PaymentRepository:
    """Repository for payment intent persistence."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, payment: PaymentIntent) -> PaymentIntent:
        """
        Create a new payment intent.
        
        Args:
            payment: PaymentIntent to persist
        
        Returns:
            Created PaymentIntent
        """
        self.db.add(payment)
        self.db.flush()
        self.db.refresh(payment)
        return payment
    
    def get_by_id(
        self,
        payment_id: uuid.UUID,
        customer_id: uuid.UUID
    ) -> PaymentIntent | None:
        """
        Get payment intent by ID, scoped to customer.
        
        Args:
            payment_id: Payment intent ID
            customer_id: Customer profile reference ID
        
        Returns:
            PaymentIntent or None
        """
        stmt = select(PaymentIntent).where(
            and_(
                PaymentIntent.id == payment_id,
                PaymentIntent.customer_profile_ref_id == customer_id
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()
    
    def update(self, payment: PaymentIntent) -> PaymentIntent:
        """
        Update existing payment intent.
        
        Args:
            payment: PaymentIntent with changes
        
        Returns:
            Updated PaymentIntent
        """
        self.db.flush()
        self.db.refresh(payment)
        return payment
    
    def get_account_by_id(
        self,
        account_id: uuid.UUID,
        customer_id: uuid.UUID
    ) -> AccountReadModel | None:
        """
        Get account by ID, scoped to customer.
        
        Args:
            account_id: Account read model ID
            customer_id: Customer profile reference ID
        
        Returns:
            AccountReadModel or None
        """
        stmt = select(AccountReadModel).where(
            and_(
                AccountReadModel.id == account_id,
                AccountReadModel.customer_profile_ref_id == customer_id
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()
    
    def get_payee_by_id(
        self,
        payee_id: uuid.UUID,
        customer_id: uuid.UUID
    ) -> Payee | None:
        """
        Get payee by ID, scoped to customer.
        
        Args:
            payee_id: Payee ID
            customer_id: Customer profile reference ID
        
        Returns:
            Payee or None
        """
        stmt = select(Payee).where(
            and_(
                Payee.id == payee_id,
                Payee.customer_profile_ref_id == customer_id
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()
    
    def list_by_customer(
        self,
        customer_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20
    ) -> list[PaymentIntent]:
        """
        List payment intents for customer, newest first.
        
        Args:
            customer_id: Customer profile reference ID
            page: Page number (1-based)
            page_size: Items per page
        
        Returns:
            List of PaymentIntent
        """
        offset = (page - 1) * page_size
        stmt = select(PaymentIntent).where(
            PaymentIntent.customer_profile_ref_id == customer_id
        ).order_by(desc(PaymentIntent.created_at)).limit(page_size).offset(offset)
        
        return list(self.db.execute(stmt).scalars())
    
    def count_by_customer(self, customer_id: uuid.UUID) -> int:
        """
        Count payment intents for customer.
        
        Args:
            customer_id: Customer profile reference ID
        
        Returns:
            Count of payment intents
        """
        stmt = select(func.count()).select_from(PaymentIntent).where(
            PaymentIntent.customer_profile_ref_id == customer_id
        )
        return self.db.execute(stmt).scalar() or 0
