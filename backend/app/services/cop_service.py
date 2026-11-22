"""Confirmation of Payee service"""
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.adapters.cop_adapter import get_cop_adapter
from app.config import settings
from app.core.errors import ResourceNotFoundError
from app.models.payee import CopCheck
from app.repositories.cop_check_repository import CopCheckRepository

# CoP policy configuration
COP_MISMATCH_POLICY = getattr(settings, 'cop_mismatch_policy', 'warn')  # warn or block


class CopService:
    """Service for Confirmation of Payee operations"""

    def __init__(self):
        self.cop_check_repo = CopCheckRepository()
        self.cop_adapter = get_cop_adapter()

    def run_cop_check(
        self,
        db: Session,
        payee_id: uuid.UUID,
        payee_name: str,
        sort_code: str,
        account_number: str,
        trigger: str = "recheck"
    ) -> CopCheck:
        """
        Run Confirmation of Payee check.

        Args:
            trigger: One of 'new_payee', 'amended_payee', 'recheck'

        Returns:
            CopCheck record
        """
        now = datetime.now(UTC)

        # Call CoP adapter
        try:
            cop_result = self.cop_adapter.check_payee(
                payee_name=payee_name,
                sort_code=sort_code,
                account_number=account_number
            )
            outcome = cop_result.outcome
            suggested_name = cop_result.suggested_name
            provider_reference = cop_result.provider_reference
        except Exception as e:
            # CoP unavailable
            print(f"CoP check failed: {e}")
            outcome = "unavailable"
            suggested_name = None
            provider_reference = None

        # Determine policy treatment
        policy_treatment = self._determine_policy_treatment(outcome)

        # Calculate expiry (90 days from check)
        expires_at = now + timedelta(days=90) if outcome != "unavailable" else None

        # Create CoP check record
        cop_check = CopCheck(
            cop_check_id=uuid.uuid4(),
            payee_id=payee_id,
            request_reference=f"cop_{uuid.uuid4().hex[:16]}",
            check_trigger=trigger,
            checked_name=payee_name,
            checked_sort_code=sort_code,
            checked_account_number_hash=self._hash_account_details(sort_code, account_number),
            outcome=outcome,
            suggested_name=suggested_name,
            policy_treatment=policy_treatment,
            customer_acknowledged_at=None,
            provider_reference=provider_reference,
            checked_at=now,
            expires_at=expires_at,
            raw_response_digest=None,
            correlation_id=f"corr_{uuid.uuid4().hex[:16]}",
            created_at=now,
        )

        self.cop_check_repo.create_cop_check(db, cop_check)

        return cop_check

    def acknowledge_cop_result(
        self,
        db: Session,
        payee_id: uuid.UUID,
        customer_id: uuid.UUID
    ) -> CopCheck:
        """
        Record customer acknowledgement of CoP mismatch/partial match.

        Raises:
            ResourceNotFoundError: If no unacknowledged CoP check found
        """
        cop_check = self.cop_check_repo.get_latest_for_payee(db, payee_id)

        if not cop_check:
            raise ResourceNotFoundError("No CoP check found for payee")

        if cop_check.customer_acknowledged_at:
            # Already acknowledged
            return cop_check

        # Record acknowledgement
        cop_check.customer_acknowledged_at = datetime.now(UTC)
        self.cop_check_repo.update_cop_check(db, cop_check)

        return cop_check

    def _determine_policy_treatment(self, outcome: str) -> str:
        """
        Determine policy treatment based on CoP outcome.

        Returns:
            One of 'allow', 'warn', 'block'
        """
        if outcome == "match":
            return "allow"
        elif outcome in ["partial_match", "mismatch"]:
            # Use configured policy
            return COP_MISMATCH_POLICY
        elif outcome == "unavailable":
            # Policy decision when CoP unavailable
            return "warn"
        else:
            # Unknown outcome - fail safe to block
            return "block"

    def _hash_account_details(self, sort_code: str, account_number: str) -> str:
        """Hash account details for CoP check record"""
        import hashlib
        data = f"{sort_code}:{account_number}"
        return hashlib.sha256(data.encode()).hexdigest()
