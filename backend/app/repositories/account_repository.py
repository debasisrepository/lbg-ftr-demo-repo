"""Repository for account-related database operations."""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.accounts import AccountSnapshot, AccountDataGap, LoanContextSnapshot


class AccountRepository:
    """Repository for account operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_accounts_by_profile(self, profile_id: int) -> list[AccountSnapshot]:
        """Get all account snapshots for a profile."""
        return self.db.query(AccountSnapshot).filter(
            AccountSnapshot.profile_id == profile_id
        ).all()

    def get_account_by_id(self, account_id: int) -> AccountSnapshot | None:
        """Get account snapshot by ID."""
        return self.db.query(AccountSnapshot).filter(
            AccountSnapshot.id == account_id
        ).first()

    def get_loan_context_by_account(self, account_snapshot_id: int) -> LoanContextSnapshot | None:
        """Get loan context for an account."""
        return self.db.query(LoanContextSnapshot).filter(
            LoanContextSnapshot.account_snapshot_id == account_snapshot_id
        ).first()

    def create_data_gap(
        self,
        profile_id: int,
        source_system: str,
        freshness_state: str,
        message: str
    ) -> AccountDataGap:
        """Create an account data gap record."""
        now = datetime.now(timezone.utc)
        gap = AccountDataGap(
            profile_id=profile_id,
            source_system=source_system,
            freshness_state=freshness_state,
            message=message,
            detected_at=now,
            cleared_at=None,
            created_at=now,
            updated_at=now
        )
        self.db.add(gap)
        self.db.commit()
        self.db.refresh(gap)
        return gap
