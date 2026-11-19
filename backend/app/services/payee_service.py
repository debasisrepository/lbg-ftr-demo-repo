"""Service for payee operations with CoP integration."""
import hashlib
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.repositories.payee_repository import PayeeRepository
from app.repositories.sca_repository import SCARepository
from app.adapters.cop_adapter import CoPAdapter
from app.common.enums import ChallengeStatus, CoPDecisionState
from app.common.errors import AuthorizationError, ValidationError


class PayeeService:
    """Service for payee management with CoP checks."""

    def __init__(self, db: Session, correlation_id: str):
        self.db = db
        self.correlation_id = correlation_id
        self.payee_repo = PayeeRepository(db)
        self.sca_repo = SCARepository(db)
        self.cop_adapter = CoPAdapter()

    def get_payees(self, profile_id: int) -> list[dict]:
        """
        Get all payees for a profile.
        
        Returns list of payee info with latest CoP result.
        """
        payees = self.payee_repo.get_payees_by_profile(profile_id)
        result = []
        
        for payee in payees:
            cop_result = self.payee_repo.get_latest_cop_result(payee.id)
            
            result.append({
                "payee_id": payee.id,
                "display_name": payee.display_name,
                "sort_code": payee.sort_code,
                "masked_account_number": f"****{payee.account_number_last4}",
                "nickname": payee.nickname,
                "can_proceed": payee.can_proceed,
                "latest_cop_result": cop_result.result_code if cop_result else None,
                "latest_cop_checked_at": cop_result.checked_at if cop_result else None
            })
        
        return result

    def create_payee(
        self,
        profile_id: int,
        display_name: str,
        nickname: str | None,
        sort_code: str,
        account_number: str,
        payee_action_challenge_id: int,
        payee_action_assertion: str
    ) -> dict:
        """
        Create a new payee with fresh payee-action SCA verification and CoP check.
        
        Returns dict with payee info, CoP result, and override_required flag.
        Raises AuthorizationError if SCA not verified.
        """
        # Verify fresh payee-action SCA
        challenge = self.sca_repo.get_challenge_by_id(payee_action_challenge_id)
        if not challenge:
            raise ValidationError("Challenge not found")
        
        if challenge.status != ChallengeStatus.VERIFIED.value:
            raise AuthorizationError("Fresh SCA verification required before creating payee")
        
        # Hash account number for storage
        account_hash = hashlib.sha256(f"{sort_code}{account_number}".encode()).hexdigest()
        account_number_last4 = account_number[-4:]
        
        # Perform CoP check
        cop_response = self.cop_adapter.check_payee(display_name, sort_code, account_number)
        
        # Determine can_proceed based on CoP result
        can_proceed = cop_response["result_code"] == "match"
        override_required = cop_response["result_code"] in ["close_match", "no_match", "unavailable"]
        
        # Determine decision state
        if cop_response["result_code"] == "match":
            decision_state = CoPDecisionState.CONFIRMED.value
        else:
            decision_state = CoPDecisionState.PENDING.value
        
        # Create payee
        payee = self.payee_repo.create_payee(
            profile_id=profile_id,
            display_name=display_name,
            nickname=nickname,
            sort_code=sort_code,
            account_number_last4=account_number_last4,
            account_number_hash=account_hash,
            can_proceed=can_proceed,
            created_in_journey=True,
            payee_action_sca_verified_at=challenge.verified_at
        )
        
        # Create CoP result record
        cop_result = self.payee_repo.create_cop_result(
            payee_id=payee.id,
            result_code=cop_response["result_code"],
            decision_state=decision_state,
            provider_reference=cop_response["provider_reference"],
            returned_name=cop_response["returned_name"],
            warning_message=cop_response["warning_message"],
            checked_at=datetime.now(timezone.utc)
        )
        
        return {
            "payee_id": payee.id,
            "display_name": payee.display_name,
            "sort_code": payee.sort_code,
            "masked_account_number": f"****{payee.account_number_last4}",
            "cop_result": cop_result.result_code,
            "warning_message": cop_result.warning_message,
            "can_proceed": payee.can_proceed,
            "override_required": override_required
        }

    def confirm_cop_warning(self, payee_id: int, override_reason: str) -> dict:
        """
        Confirm CoP warning and allow proceeding with payee.
        
        Returns dict with updated payee info.
        """
        payee = self.payee_repo.get_payee_by_id(payee_id)
        if not payee:
            raise ValidationError("Payee not found")
        
        # Get latest CoP result
        cop_result = self.payee_repo.get_latest_cop_result(payee_id)
        if not cop_result:
            raise ValidationError("No CoP result found for payee")
        
        # Update CoP result with override confirmation
        self.payee_repo.update_cop_override(cop_result.id)
        
        # Update payee to allow proceeding
        self.payee_repo.update_payee_can_proceed(payee_id, True)
        
        # Refresh payee
        self.db.refresh(payee)
        
        return {
            "payee_id": payee.id,
            "can_proceed": payee.can_proceed,
            "cop_result": cop_result.result_code
        }
