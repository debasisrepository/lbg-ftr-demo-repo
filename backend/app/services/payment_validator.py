"""Payment validation service"""
import uuid

from sqlalchemy.orm import Session

from ..core.errors import ValidationError
from ..models.customer import BankAccount
from ..models.payee import Payee
from ..repositories.bank_account_repository import BankAccountRepository
from ..repositories.entitlement_repository import EntitlementRepository
from ..repositories.payee_repository import PayeeRepository


class PaymentValidator:
    """Validates payment requests against business rules"""

    def __init__(self, db: Session):
        self.db = db
        self.bank_account_repo = BankAccountRepository()
        self.payee_repo = PayeeRepository()
        self.entitlement_repo = EntitlementRepository()

    def validate_payment_request(
        self,
        customer_id: uuid.UUID,
        profile_id: uuid.UUID,
        source_account_id: uuid.UUID,
        payee_id: uuid.UUID,
        amount_minor: int
    ) -> tuple[BankAccount, Payee]:
        """Validate payment request and return account and payee"""

        # Validate source account exists and is available
        account = self.bank_account_repo.get_by_id(self.db, source_account_id)
        if not account:
            raise ValidationError("Source account not found")

        if account.source_status != "available":
            raise ValidationError("Source account is not available")

        # Validate payee exists and is active
        payee = self.payee_repo.get_by_id(self.db, payee_id)
        if not payee:
            raise ValidationError("Payee not found")

        if payee.customer_id != customer_id:
            raise ValidationError("Payee does not belong to customer")

        if payee.status != "active":
            raise ValidationError("Payee is not active")

        # Validate amount
        if amount_minor <= 0:
            raise ValidationError("Payment amount must be positive")

        if amount_minor > 100000000:  # £1M limit
            raise ValidationError("Payment amount exceeds maximum allowed")

        # Validate entitlements
        entitlements = self.entitlement_repo.get_active_for_profile(self.db, profile_id)
        if not entitlements:
            raise ValidationError("No active entitlements for profile")

        has_payment_entitlement = any(
            e.can_initiate_payments for e in entitlements
        )

        if not has_payment_entitlement:
            raise ValidationError("Profile does not have payment initiation entitlement")

        return account, payee
