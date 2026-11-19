"""Accounts overview service with parallel adapter calls"""
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.adapters.core_banking_adapter import get_core_banking_adapter
from app.adapters.loan_adapter import get_loan_adapter
from app.core.parallel import run_parallel
from app.models.customer import BankAccount, LoanSnapshot, ProfileAccountVisibility
from app.repositories.bank_account_repository import BankAccountRepository
from app.repositories.loan_snapshot_repository import LoanSnapshotRepository
from app.repositories.profile_account_visibility_repository import ProfileAccountVisibilityRepository

STALE_MAX_SECONDS = 900  # 15 minutes


class AccountsOverviewService:
    """Service for accounts and loans aggregation"""

    def __init__(self):
        self.bank_account_repo = BankAccountRepository()
        self.loan_repo = LoanSnapshotRepository()
        self.visibility_repo = ProfileAccountVisibilityRepository()
        self.core_banking_adapter = get_core_banking_adapter()
        self.loan_adapter = get_loan_adapter()

    def get_accounts_overview(
        self,
        db: Session,
        customer_id: uuid.UUID,
        profile_id: uuid.UUID
    ) -> tuple[list[tuple[BankAccount, bool]], list[LoanSnapshot]]:
        """
        Get accounts and loans overview for profile.
        
        Calls Core Banking and Loan adapters in parallel.
        Uses stale snapshots if fresh data unavailable.
        
        Returns:
            (accounts_with_permission, loans) where accounts_with_permission
            is list of (BankAccount, payment_permission) tuples
        """
        # Fetch fresh data from adapters in parallel
        try:
            account_data_list, loan_data_list = run_parallel(
                lambda: self.core_banking_adapter.get_accounts(customer_id),
                lambda: self.loan_adapter.get_loans(customer_id),
                timeout=3.0
            )

            # Update snapshots with fresh data
            self._update_account_snapshots(db, customer_id, profile_id, account_data_list)
            self._update_loan_snapshots(db, profile_id, loan_data_list)

        except Exception as e:
            # Adapters failed, will use stale snapshots
            print(f"Adapter calls failed, using stale snapshots: {e}")

        # Get visible accounts for profile
        accounts_with_perm = self.bank_account_repo.get_visible_for_profile(db, profile_id)

        # Get loans for profile
        loans = self.loan_repo.get_for_profile(db, profile_id)

        return accounts_with_perm, loans

    def _update_account_snapshots(
        self,
        db: Session,
        customer_id: uuid.UUID,
        profile_id: uuid.UUID,
        account_data_list: list
    ) -> None:
        """Update account snapshots with fresh data"""
        now = datetime.now(UTC)

        for account_data in account_data_list:
            # Generate deterministic account ID based on external ref
            account_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"account:{account_data.external_account_ref}")

            account = BankAccount(
                bank_account_id=account_id,
                external_account_ref=account_data.external_account_ref,
                account_type=account_data.account_type,
                account_name=account_data.account_name,
                sort_code_masked=account_data.sort_code_masked,
                account_number_masked=account_data.account_number_masked,
                currency_code=account_data.currency_code,
                account_holder_name=account_data.account_holder_name,
                current_balance_minor=account_data.current_balance_minor,
                available_balance_minor=account_data.available_balance_minor,
                overdraft_limit_minor=account_data.overdraft_limit_minor,
                freshness_at=now,
                source_status=account_data.source_status,
                created_at=now,
                updated_at=now,
            )

            self.bank_account_repo.upsert_account(db, account)

            # Ensure visibility mapping exists
            visibility = self.visibility_repo.get_by_profile_and_account(db, profile_id, account_id)
            if not visibility:
                visibility = ProfileAccountVisibility(
                    profile_account_visibility_id=uuid.uuid4(),
                    profile_id=profile_id,
                    bank_account_id=account_id,
                    visibility_reason="profile_owned",
                    payment_permission=True,
                    visible_from=now,
                    visible_to=None,
                    created_at=now,
                    updated_at=now,
                )
                self.visibility_repo.create_visibility(db, visibility)

    def _update_loan_snapshots(
        self,
        db: Session,
        profile_id: uuid.UUID,
        loan_data_list: list
    ) -> None:
        """Update loan snapshots with fresh data"""
        now = datetime.now(UTC)

        for loan_data in loan_data_list:
            # Generate deterministic loan ID based on external ref
            loan_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"loan:{loan_data.external_loan_ref}")

            loan = LoanSnapshot(
                loan_snapshot_id=loan_id,
                profile_id=profile_id,
                external_loan_ref=loan_data.external_loan_ref,
                loan_name=loan_data.loan_name,
                outstanding_balance_minor=loan_data.outstanding_balance_minor,
                next_repayment_minor=loan_data.next_repayment_minor,
                next_repayment_date=loan_data.next_repayment_date,
                currency_code=loan_data.currency_code,
                freshness_at=now,
                source_status=loan_data.source_status,
                created_at=now,
                updated_at=now,
            )

            self.loan_repo.upsert_loan(db, loan)
