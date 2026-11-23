"""
Account service (composition service for E-04).
Requirement: FR-ACCT-001, FR-ACCT-002, FR-ACCT-003
"""
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.adapters.entitlement_sandbox_adapter import EntitlementSandboxAdapter
from app.schemas.accounts_schemas import (
    AccountItem,
    AccountOverviewResponse,
    Balance,
    CapabilityStatus,
    LoanDetails,
)
from app.services.capability_status_service import CapabilityStatusService
from app.services.read_model_service import ReadModelService


class AccountService:
    """
    Composition service for accounts overview.
    
    Composes: auth check (via middleware), entitlement check per account,
    read account_read_models, read accounts_overview capability status, shape response.
    """
    
    def __init__(
        self,
        db: Session,
        read_model_service: ReadModelService | None = None,
        capability_service: CapabilityStatusService | None = None,
        entitlement_adapter: EntitlementSandboxAdapter | None = None
    ):
        self.db = db
        self.read_model_service = read_model_service or ReadModelService(db)
        self.capability_service = capability_service or CapabilityStatusService(db)
        self.entitlement_adapter = entitlement_adapter or EntitlementSandboxAdapter(db)
    
    def get_accounts_overview(
        self,
        customer_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20
    ) -> AccountOverviewResponse:
        """
        Get account overview with entitlement checks and freshness indicators.
        
        Steps per E-04:
        1. Check entitlement (via adapter)
        2. Read account_read_models from read_model_service
        3. Read accounts_overview capability status
        4. Compute freshness_text for each account
        5. Shape response with honest balance handling
        
        Args:
            customer_id: Customer profile reference ID
            page: 1-based page number
            page_size: Items per page (1-50)
        
        Returns:
            AccountOverviewResponse with items, pagination, overview_state, capability
        
        Raises:
            HTTPException: 403 if not entitled to any in-scope account
        """
        # Validate pagination
        page = max(1, page)
        page_size = max(1, min(50, page_size))
        
        # Step 1: Check overall entitlement for accounts
        # For this working tier, we check if customer has ANY account entitlement
        # Real implementation would check per-account entitlement
        decision = self.entitlement_adapter.check_resource_access(
            customer_id=customer_id,
            resource_type="account",
            resource_reference="*"
        )
        
        if decision != "allow":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not entitled to view accounts"
            )
        
        # Step 2: Read account read models
        accounts, total = self.read_model_service.get_accounts_for_customer(
            customer_id,
            page,
            page_size
        )
        
        # Step 3: Read accounts_overview capability status
        capability_record = self.capability_service.get_capability_status("accounts_overview")
        if not capability_record:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Capability status not available"
            )
        
        # Step 4 & 5: Shape response with freshness and honest balance handling
        items: list[AccountItem] = []
        overall_state = "complete"
        
        for account in accounts:
            # Compute freshness text
            freshness_text = self._compute_freshness_text(
                account.freshness_status,
                account.as_of_timestamp
            )
            
            # Shape balance with honest handling (never show missing as zero)
            balance = self._shape_balance(
                account.balance_availability_state,
                account.balance_amount_minor,
                account.balance_currency
            )
            
            # Determine item state (available or partial)
            item_state = "available"
            if account.balance_availability_state in ("unavailable", "unknown"):
                item_state = "partial"
                overall_state = "partial"  # At least one account is partial
            
            # Payment source eligibility
            # Eligible if balance is current with known amount
            payment_source_eligible = (
                account.balance_availability_state == "current" and
                account.balance_amount_minor is not None
            )
            
            # Release 2: Include loan details if account_type is 'loan' (BR-ACCT-004)
            loan_details = None
            if account.account_type == "loan":
                loan_details = LoanDetails(
                    outstanding_balance_minor=account.loan_outstanding_balance_minor,
                    next_repayment_date=account.loan_next_repayment_date,
                    next_repayment_amount_minor=account.loan_next_repayment_amount_minor,
                    remaining_term_months=account.loan_remaining_term_months
                )
            
            items.append(AccountItem(
                account_id=str(account.id),
                account_type=account.account_type,
                display_name=account.display_name,
                masked_account_identifier=account.masked_account_identifier,
                balance=balance,
                as_of_timestamp=account.as_of_timestamp,
                freshness_status=account.freshness_status,
                freshness_text=freshness_text,
                item_state=item_state,
                payment_source_eligible=payment_source_eligible,
                loan_details=loan_details
            ))
        
        # Build capability status
        capability = CapabilityStatus(
            capability_name=capability_record.capability_name,
            status_value=capability_record.status_value,
            customer_message_code=capability_record.customer_message_code,
            customer_message=self._get_capability_message(capability_record),
            recovery_guidance=self._get_recovery_guidance(capability_record),
            effective_from=capability_record.effective_from
        )
        
        # If capability is not healthy, reflect that in overview_state
        if capability_record.status_value != "healthy":
            overall_state = "partial" if overall_state == "complete" else overall_state
        
        return AccountOverviewResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            overview_state=overall_state,
            capability=capability
        )
    
    def _compute_freshness_text(
        self,
        freshness_status: str,
        as_of_timestamp: datetime | None
    ) -> str:
        """
        Compute accessible plain-language freshness text.
        
        Args:
            freshness_status: within_target, breached, unknown
            as_of_timestamp: Source timestamp or None
        
        Returns:
            Plain-language freshness indicator
        """
        if freshness_status == "unknown" or as_of_timestamp is None:
            return "Freshness cannot be established"
        
        if freshness_status == "breached":
            return "Data may be out of date"
        
        # within_target - compute time ago
        now = datetime.now(UTC)
        # Ensure timezone-aware comparison
        as_of = as_of_timestamp
        if as_of.tzinfo is None:
            as_of = as_of.replace(tzinfo=UTC)
        
        delta = now - as_of
        seconds = int(delta.total_seconds())
        
        if seconds < 60:
            return "Updated moments ago"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"Updated {minutes} minute{'s' if minutes != 1 else ''} ago"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"Updated {hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = seconds // 86400
            return f"Updated {days} day{'s' if days != 1 else ''} ago"
    
    def _shape_balance(
        self,
        availability_state: str,
        amount_minor: int | None,
        currency: str | None
    ) -> Balance:
        """
        Shape balance with honest unavailable handling (never zero as substitute).
        
        Args:
            availability_state: current, stale, unavailable, unknown
            amount_minor: Amount in minor units or None
            currency: ISO 4217 code or None
        
        Returns:
            Balance with display_text
        """
        if availability_state == "unavailable":
            return Balance(
                availability_state=availability_state,
                amount_minor=None,
                currency=None,
                display_text="Balance unavailable"
            )
        
        if availability_state == "unknown":
            return Balance(
                availability_state=availability_state,
                amount_minor=None,
                currency=None,
                display_text="Balance cannot be shown"
            )
        
        if availability_state == "stale":
            if amount_minor is None:
                return Balance(
                    availability_state=availability_state,
                    amount_minor=None,
                    currency=currency,
                    display_text="Balance may be out of date"
                )
            # Format stale balance
            amount_str = self._format_currency(amount_minor, currency or "GBP")
            return Balance(
                availability_state=availability_state,
                amount_minor=amount_minor,
                currency=currency,
                display_text=f"{amount_str} (may be out of date)"
            )
        
        # current
        if amount_minor is None:
            # Should not happen per schema constraints, but handle gracefully
            return Balance(
                availability_state="unknown",
                amount_minor=None,
                currency=None,
                display_text="Balance cannot be shown"
            )
        
        amount_str = self._format_currency(amount_minor, currency or "GBP")
        return Balance(
            availability_state=availability_state,
            amount_minor=amount_minor,
            currency=currency,
            display_text=amount_str
        )
    
    def _format_currency(self, amount_minor: int, currency: str) -> str:
        """Format amount in minor units as currency string."""
        major = amount_minor / 100.0
        if currency == "GBP":
            return f"£{major:,.2f}"
        return f"{major:,.2f} {currency}"
    
    def _get_capability_message(self, capability_record) -> str:
        """Get plain-language capability message."""
        if capability_record.status_value == "healthy":
            return "Account overview is available"
        elif capability_record.status_value == "stale":
            return "Account data may be out of date"
        elif capability_record.status_value == "partial":
            return "Some account data is unavailable"
        elif capability_record.status_value == "unavailable":
            return "Account overview is currently unavailable"
        elif capability_record.status_value == "restricted":
            return "Account overview is restricted"
        return "Account overview status unknown"
    
    def _get_recovery_guidance(self, capability_record) -> str | None:
        """Get recovery guidance for non-healthy states."""
        if capability_record.status_value == "healthy":
            return None
        elif capability_record.status_value in ("stale", "partial"):
            return "Data will be updated automatically. Try refreshing in a few moments."
        elif capability_record.status_value == "unavailable":
            return "Please try again later. If the problem persists, contact support."
        elif capability_record.status_value == "restricted":
            return "Contact support for assistance."
        return "Please try again later."
