"""Service for account overview orchestration."""
from sqlalchemy.orm import Session
from app.repositories.account_repository import AccountRepository
from app.repositories.profile_repository import ProfileRepository
from app.adapters.account_system_adapter import AccountSystemAdapter
from app.adapters.loan_context_adapter import LoanContextAdapter


class AccountOverviewService:
    """Service for aggregating account overview with partial-failure handling."""

    def __init__(self, db: Session):
        self.db = db
        self.account_repo = AccountRepository(db)
        self.profile_repo = ProfileRepository(db)
        self.account_adapter = AccountSystemAdapter()
        self.loan_adapter = LoanContextAdapter()

    def get_overview(self, profile_id: int) -> dict:
        """
        Get account overview for a profile with partial-failure handling.
        
        Returns dict with:
        - profile: profile context
        - accounts: list of account info with freshness_state
        - data_gaps: list of data gap messages
        """
        # Get profile
        profile = self.profile_repo.get_profile_by_id(profile_id)
        if not profile:
            raise ValueError("Profile not found")

        # Get entitlements to find which accounts are accessible
        entitlements = self.profile_repo.get_entitlements_by_profile(profile_id)
        external_account_ids = [e.account_external_id for e in entitlements if e.can_view_accounts]

        # Get account snapshots from local DB
        accounts = self.account_repo.get_accounts_by_profile(profile_id)
        
        data_gaps = []
        
        # Try to fetch fresh data from account system (independent call)
        try:
            account_response = self.account_adapter.fetch_accounts(profile_id, external_account_ids)
            if account_response["status"] != "success":
                # Record data gap for account system
                gap = self.account_repo.create_data_gap(
                    profile_id=profile_id,
                    source_system="account_system",
                    freshness_state="unavailable",
                    message="Account data temporarily unavailable"
                )
                data_gaps.append({
                    "source_system": gap.source_system,
                    "message": gap.message,
                    "freshness_state": gap.freshness_state
                })
        except Exception:
            # External system failure - record gap but continue
            gap = self.account_repo.create_data_gap(
                profile_id=profile_id,
                source_system="account_system",
                freshness_state="unavailable",
                message="Account data temporarily unavailable"
            )
            data_gaps.append({
                "source_system": gap.source_system,
                "message": gap.message,
                "freshness_state": gap.freshness_state
            })

        # Try to fetch loan context (independent call)
        loan_account_ids = [a.id for a in accounts if a.account_type == "loan"]
        loan_contexts = {}
        
        try:
            loan_response = self.loan_adapter.fetch_loan_context(profile_id, loan_account_ids)
            if loan_response["status"] != "success":
                # Record data gap for loan system
                gap = self.account_repo.create_data_gap(
                    profile_id=profile_id,
                    source_system="loan_system",
                    freshness_state="unavailable",
                    message="Loan data temporarily unavailable"
                )
                data_gaps.append({
                    "source_system": gap.source_system,
                    "message": gap.message,
                    "freshness_state": gap.freshness_state
                })
        except Exception:
            # External system failure - record gap but continue
            gap = self.account_repo.create_data_gap(
                profile_id=profile_id,
                source_system="loan_system",
                freshness_state="unavailable",
                message="Loan data temporarily unavailable"
            )
            data_gaps.append({
                "source_system": gap.source_system,
                "message": gap.message,
                "freshness_state": gap.freshness_state
            })
        
        # Get loan contexts from DB
        for account in accounts:
            if account.account_type == "loan":
                loan_ctx = self.account_repo.get_loan_context_by_account(account.id)
                if loan_ctx:
                    loan_contexts[account.id] = loan_ctx

        # Build account list with freshness indicators
        account_list = []
        for account in accounts:
            loan_ctx = loan_contexts.get(account.id)
            account_list.append({
                "account_id": account.id,
                "account_type": account.account_type,
                "account_name": account.account_name,
                "masked_account_number": account.masked_account_number,
                "sort_code": account.sort_code,
                "currency": account.currency,
                "current_balance_minor": account.current_balance_minor,
                "available_balance_minor": account.available_balance_minor,
                "overdraft_available_minor": account.overdraft_available_minor,
                "available_credit_minor": account.available_credit_minor,
                "next_repayment_amount_minor": loan_ctx.next_repayment_amount_minor if loan_ctx else None,
                "next_repayment_due_date": loan_ctx.next_repayment_due_date if loan_ctx else None,
                "freshness_state": account.freshness_state,
                "last_updated_at": account.last_updated_at
            })

        return {
            "profile": {
                "profile_id": profile.id,
                "profile_type": profile.profile_type,
                "display_name": profile.display_name,
                "business_name": profile.business_name
            },
            "accounts": account_list,
            "data_gaps": data_gaps
        }
