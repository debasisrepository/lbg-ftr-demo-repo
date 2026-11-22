"""Payee service"""
import hashlib
import uuid
from datetime import UTC, datetime

from cryptography.fernet import Fernet
from sqlalchemy.orm import Session

from app.config import settings
from app.core.errors import AuthorizationError, ResourceNotFoundError
from app.models.payee import Payee
from app.repositories.payee_repository import PayeeRepository
from app.services.cop_service import CopService


class PayeeService:
    """Service for payee operations"""

    def __init__(self):
        self.payee_repo = PayeeRepository()
        self.cop_service = CopService()

        # Initialize encryption for account numbers
        # In production, this would come from secrets management
        import base64
        # Create a proper Fernet key from secret_key
        key_bytes = settings.secret_key.encode()[:32].ljust(32, b'0')
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        self._fernet = Fernet(fernet_key)

    def get_payees_for_customer(
        self,
        db: Session,
        customer_id: uuid.UUID,
        profile_id: uuid.UUID | None = None
    ) -> list[Payee]:
        """Get payees for customer, optionally filtered by profile"""
        if profile_id:
            return self.payee_repo.get_for_profile(db, customer_id, profile_id)
        else:
            return self.payee_repo.get_for_customer(db, customer_id)

    def get_payee_by_id(
        self,
        db: Session,
        payee_id: uuid.UUID,
        customer_id: uuid.UUID
    ) -> Payee:
        """
        Get payee by ID.

        Raises:
            ResourceNotFoundError: If payee not found
            AuthorizationError: If payee doesn't belong to customer
        """
        payee = self.payee_repo.get_by_id(db, payee_id)
        if not payee:
            raise ResourceNotFoundError("Payee not found")

        if payee.customer_id != customer_id:
            raise AuthorizationError("Payee does not belong to customer")

        return payee

    def create_payee(
        self,
        db: Session,
        customer_id: uuid.UUID,
        profile_id: uuid.UUID,
        payee_name: str,
        sort_code: str,
        account_number: str,
        payee_type: str
    ):
        """
        Create new payee with CoP check.

        Returns:
            (payee, cop_check) tuple
        """
        now = datetime.now(UTC)
        payee_id = uuid.uuid4()

        # Encrypt account number
        account_number_encrypted = self._encrypt_account_number(account_number)
        account_number_masked = f"****{account_number[-4:]}"
        account_number_hash = self._hash_account_number(sort_code, account_number)

        # Create payee
        payee = Payee(
            payee_id=payee_id,
            customer_id=customer_id,
            profile_id=profile_id,
            external_payee_ref=f"payee_{payee_id.hex[:16]}",
            payee_name=payee_name,
            sort_code=sort_code,
            account_number_encrypted=account_number_encrypted,
            account_number_masked=account_number_masked,
            account_number_hash=account_number_hash,
            payee_type=payee_type,
            is_saved=False,  # Start as not saved until CoP check passes
            status="pending_verification",
            last_verified_at=None,
            created_at=now,
            updated_at=now,
        )

        self.payee_repo.create_payee(db, payee)

        # Run CoP check
        cop_check = self.cop_service.run_cop_check(
            db=db,
            payee_id=payee_id,
            payee_name=payee_name,
            sort_code=sort_code,
            account_number=account_number,
            trigger="new_payee"
        )

        # Update payee status based on CoP result
        if cop_check.outcome == "match":
            payee.status = "active"
            payee.last_verified_at = cop_check.checked_at
            payee.is_saved = True  # Mark as saved once verified
        else:
            # For non-match outcomes, save but keep pending_verification
            payee.is_saved = False

        db.flush()

        return payee, cop_check

    def update_payee(
        self,
        db: Session,
        payee_id: uuid.UUID,
        customer_id: uuid.UUID,
        payee_name: str | None = None,
        sort_code: str | None = None,
        account_number: str | None = None
    ):
        """
        Update payee. Runs CoP check if account details changed.

        Returns:
            (payee, cop_check_or_none) tuple
        """
        payee = self.get_payee_by_id(db, payee_id, customer_id)

        now = datetime.now(UTC)
        needs_cop_check = False
        cop_check = None

        # Update fields
        if payee_name:
            if payee_name != payee.payee_name:
                payee.payee_name = payee_name
                needs_cop_check = True

        if sort_code:
            if sort_code != payee.sort_code:
                payee.sort_code = sort_code
                needs_cop_check = True

        if account_number:
            # Re-encrypt and hash
            payee.account_number_encrypted = self._encrypt_account_number(account_number)
            payee.account_number_masked = f"****{account_number[-4:]}"
            payee.account_number_hash = self._hash_account_number(
                sort_code or payee.sort_code,
                account_number
            )
            needs_cop_check = True

        if needs_cop_check:
            # Run new CoP check
            cop_check = self.cop_service.run_cop_check(
                db=db,
                payee_id=payee_id,
                payee_name=payee.payee_name,
                sort_code=payee.sort_code,
                account_number=self._decrypt_account_number(payee.account_number_encrypted),
                trigger="amended_payee"
            )

            # Update payee status
            if cop_check.outcome == "match":
                payee.status = "active"
                payee.last_verified_at = cop_check.checked_at
                payee.is_saved = True
            else:
                payee.status = "pending_verification"
                payee.is_saved = False

        payee.updated_at = now
        self.payee_repo.update_payee(db, payee)

        return payee, cop_check

    def _encrypt_account_number(self, account_number: str) -> str:
        """Encrypt account number"""
        return self._fernet.encrypt(account_number.encode()).decode()

    def _decrypt_account_number(self, encrypted: str) -> str:
        """Decrypt account number"""
        return self._fernet.decrypt(encrypted.encode()).decode()

    def _hash_account_number(self, sort_code: str, account_number: str) -> str:
        """Hash account number for uniqueness checks"""
        data = f"{sort_code}:{account_number}"
        return hashlib.sha256(data.encode()).hexdigest()
