"""Service for loan and business context resolution."""
from sqlalchemy.orm import Session
from app.repositories.account_repository import AccountRepository


class LoanBusinessContextService:
    """Service for providing loan and business context."""

    def __init__(self, db: Session):
        self.db = db
        self.account_repo = AccountRepository(db)

    def get_loan_context(self, account_snapshot_id: int) -> dict | None:
        """
        Get loan context for an account.
        
        Returns dict with loan repayment info or None.
        """
        loan_ctx = self.account_repo.get_loan_context_by_account(account_snapshot_id)
        
        if not loan_ctx:
            return None
        
        return {
            "next_repayment_amount_minor": loan_ctx.next_repayment_amount_minor,
            "next_repayment_due_date": loan_ctx.next_repayment_due_date,
            "source_state": loan_ctx.source_state
        }
