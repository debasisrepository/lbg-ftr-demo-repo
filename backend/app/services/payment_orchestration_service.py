"""Service for payment orchestration."""
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.repositories.payment_repository import PaymentRepository
from app.repositories.account_repository import AccountRepository
from app.repositories.payee_repository import PayeeRepository
from app.repositories.sca_repository import SCARepository
from app.models.payments import PaymentInstruction
from app.services.entitlement_service import EntitlementService
from app.services.fraud_decision_service import FraudDecisionService
from app.services.payment_status_service import PaymentStatusService
from app.services.notification_service import NotificationService
from app.services.audit_service import AuditService
from app.services.telemetry_service import TelemetryService
from app.adapters.payment_rail_adapter import PaymentRailAdapter
from app.common.enums import (
    InstructionState, ChallengeType, ChallengeMethod, ChallengeStatus,
    PaymentStatusCode, NotificationType, JourneyOutcomeCode, FraudDecisionCode
)
from app.common.errors import ValidationError, AuthorizationError
from app.common.idempotency import generate_idempotency_key
from app.common.security import generate_dynamic_link_hash


class PaymentOrchestrationService:
    """Service for orchestrating payment preparation and approval."""

    def __init__(self, db: Session, correlation_id: str):
        self.db = db
        self.correlation_id = correlation_id
        self.payment_repo = PaymentRepository(db)
        self.account_repo = AccountRepository(db)
        self.payee_repo = PayeeRepository(db)
        self.sca_repo = SCARepository(db)
        self.entitlement_service = EntitlementService(db)
        self.fraud_service = FraudDecisionService()
        self.status_service = PaymentStatusService(db)
        self.notification_service = NotificationService(db)
        self.audit_service = AuditService(db)
        self.telemetry_service = TelemetryService(db)
        self.rail_adapter = PaymentRailAdapter()

    def prepare_payment(
        self,
        profile_id: int,
        source_account_id: int,
        payee_id: int,
        amount_minor: int,
        currency: str,
        reference: str | None,
        client_idempotency_key: str | None,
        auth_session_id: int,
        user_identity_id: int
    ) -> dict:
        """
        Prepare payment with validation, fraud check, and approval challenge.
        
        Returns dict with payment_id, validation results, fraud decision, approval challenge.
        """
        # Check idempotency
        if client_idempotency_key:
            existing = self.payment_repo.get_payment_by_idempotency_key(client_idempotency_key)
            if existing:
                return self._build_prepare_response(existing)
        
        # Generate idempotency key if not provided
        if not client_idempotency_key:
            client_idempotency_key = generate_idempotency_key()

        # Check profile access
        if not self.entitlement_service.check_profile_access(profile_id, user_identity_id):
            raise AuthorizationError("Access to this profile is not permitted")

        # Get account snapshot
        account = self.account_repo.get_account_by_id(source_account_id)
        if not account or account.profile_id != profile_id:
            raise ValidationError("Invalid source account")

        # Balance validation
        available_balance = account.available_balance_minor or account.current_balance_minor
        balance_passed = amount_minor <= available_balance
        balance_check = {
            "passed": balance_passed,
            "available_balance_minor": available_balance,
            "detail": None if balance_passed else f"Amount exceeds available balance of £{available_balance / 100:.2f}"
        }

        # Limit validation (stub: £10,000 limit)
        limit_minor = 1000000  # £10,000
        limit_passed = amount_minor <= limit_minor
        limit_check = {
            "passed": limit_passed,
            "configured_limit_minor": limit_minor,
            "detail": None if limit_passed else f"Amount exceeds payment limit of £{limit_minor / 100:.2f}"
        }

        # Block if validation fails
        if not balance_passed or not limit_passed:
            self.telemetry_service.emit_enter_approve_event(
                correlation_id=self.correlation_id,
                auth_session_id=auth_session_id,
                profile_id=profile_id,
                outcome_code=JourneyOutcomeCode.FAILURE.value,
                failure_reason="validation_failed"
            )
            raise ValidationError("Payment validation failed")

        # Check entitlement for approval
        entitled_profiles = self.entitlement_service.get_entitled_profiles(user_identity_id)
        profile_entitlement = next((p for p in entitled_profiles if p["profile_id"] == profile_id), None)
        
        if not profile_entitlement or not profile_entitlement["can_approve_payment"]:
            self.telemetry_service.emit_enter_approve_event(
                correlation_id=self.correlation_id,
                auth_session_id=auth_session_id,
                profile_id=profile_id,
                outcome_code=JourneyOutcomeCode.BLOCKED.value,
                failure_reason="insufficient_entitlement"
            )
            raise AuthorizationError("You do not have permission to approve payments for this profile")

        # Get payee
        payee = self.payee_repo.get_payee_by_id(payee_id)
        if not payee or payee.profile_id != profile_id:
            raise ValidationError("Invalid payee")

        # Fraud check
        fraud_result = self.fraud_service.evaluate_payment(
            profile_id=profile_id,
            payee_id=payee_id,
            amount_minor=amount_minor,
            currency=currency
        )

        # Create payment instruction
        payment = self.payment_repo.create_payment_instruction(
            profile_id=profile_id,
            auth_session_id=auth_session_id,
            source_account_snapshot_id=source_account_id,
            payee_id=payee_id,
            amount_minor=amount_minor,
            currency=currency,
            reference_text=reference,
            client_idempotency_key=client_idempotency_key,
            instruction_state=InstructionState.PREPARED.value
        )

        # Record fraud decision
        self.payment_repo.create_fraud_decision(
            payment_instruction_id=payment.id,
            decision_code=fraud_result["decision_code"],
            warning_message=fraud_result["warning_message"],
            hold_reason=fraud_result["hold_reason"],
            provider_reference=fraud_result["provider_reference"],
            decided_at=fraud_result["decided_at"]
        )

        # Handle fraud hold
        if fraud_result["decision_code"] == FraudDecisionCode.HOLD.value:
            self.payment_repo.update_payment_state(
                payment_id=payment.id,
                state=InstructionState.HELD.value
            )
            self.audit_service.log_payment_held(
                correlation_id=self.correlation_id,
                auth_session_id=auth_session_id,
                user_identity_id=user_identity_id,
                payment_instruction_id=payment.id,
                hold_reason=fraud_result["hold_reason"]
            )
            self.telemetry_service.emit_enter_approve_event(
                correlation_id=self.correlation_id,
                auth_session_id=auth_session_id,
                profile_id=profile_id,
                outcome_code=JourneyOutcomeCode.BLOCKED.value,
                failure_reason="fraud_hold"
            )

        # Create approval challenge with dynamic linking
        challenge_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        dynamic_link_hash = generate_dynamic_link_hash(
            payee_id=payee_id,
            amount_minor=amount_minor,
            currency=currency,
            profile_id=profile_id
        )
        
        challenge = self.sca_repo.create_challenge(
            auth_session_id=auth_session_id,
            challenge_type=ChallengeType.PAYMENT_APPROVAL.value,
            method=ChallengeMethod.DYNAMIC_LINK.value,
            max_attempts=3,
            challenge_expires_at=challenge_expires_at
        )
        
        # Update challenge with dynamic link hash
        challenge.dynamic_link_hash = dynamic_link_hash
        challenge.payment_instruction_id = payment.id
        self.db.commit()

        # Log preparation
        self.audit_service.log_payment_prepared(
            correlation_id=self.correlation_id,
            auth_session_id=auth_session_id,
            user_identity_id=user_identity_id,
            payment_instruction_id=payment.id,
            amount_minor=amount_minor,
            payee_id=payee_id
        )

        # Build response
        return {
            "payment_id": payment.id,
            "payment_state": payment.instruction_state,
            "amount_minor": amount_minor,
            "currency": currency,
            "source_account_id": source_account_id,
            "payee": {
                "payee_id": payee.id,
                "display_name": payee.display_name,
                "sort_code": payee.sort_code,
                "masked_account_number": f"****{payee.account_number_last4}"
            },
            "reference": reference,
            "balance_check": balance_check,
            "limit_check": limit_check,
            "fraud_decision": {
                "decision": fraud_result["decision_code"],
                "warning_message": fraud_result["warning_message"],
                "hold_reason": fraud_result["hold_reason"]
            },
            "approval_required": True,
            "approval_challenge": {
                "challenge_id": challenge.id,
                "challenge_expires_at": challenge.challenge_expires_at,
                "dynamic_link_summary": {
                    "payee_name": payee.display_name,
                    "amount_minor": amount_minor,
                    "currency": currency
                }
            } if fraud_result["decision_code"] != FraudDecisionCode.HOLD.value else None
        }

    def approve_payment(
        self,
        payment_id: int,
        challenge_id: int,
        method: str,
        passcode: str | None,
        biometric_assertion: str | None,
        device_id: str | None,
        auth_session_id: int,
        user_identity_id: int
    ) -> dict:
        """
        Approve payment after SCA verification.
        
        Returns dict with payment status, outcome, next actions.
        """
        # Get payment
        payment = self.payment_repo.get_payment_by_id(payment_id)
        if not payment:
            raise ValidationError("Payment not found")

        # Check if already processed
        if payment.instruction_state in [InstructionState.APPROVED.value, InstructionState.SENT.value]:
            # Check for pending status - return existing status
            current_status = self.status_service.get_current_status(payment_id)
            if current_status["status_code"] == PaymentStatusCode.PENDING.value:
                payment.duplicate_submission_blocked = True
                self.db.commit()
                return self._build_approve_response(payment, current_status, duplicate_blocked=True)

        # Check if held
        if payment.instruction_state == InstructionState.HELD.value:
            fraud_decision = self.payment_repo.get_fraud_decision_by_payment(payment_id)
            raise ValidationError(f"Payment held: {fraud_decision.hold_reason if fraud_decision else 'Security review required'}")

        # Verify SCA challenge
        challenge = self.sca_repo.get_challenge_by_id(challenge_id)
        if not challenge or challenge.payment_instruction_id != payment_id:
            raise ValidationError("Invalid challenge for this payment")

        # Verify dynamic link hash (simplified check - in production would verify exact match)
        if method == ChallengeMethod.DYNAMIC_LINK.value:
            payee = self.payee_repo.get_payee_by_id(payment.payee_id)
            expected_hash = generate_dynamic_link_hash(
                payee_id=payment.payee_id,
                amount_minor=payment.amount_minor,
                currency=payment.currency,
                profile_id=payment.profile_id
            )
            if challenge.dynamic_link_hash != expected_hash:
                raise ValidationError("Dynamic link verification failed")

        # Mark challenge as verified
        self.sca_repo.mark_verified(challenge_id)

        # Generate payment reference
        timestamp = int(datetime.now(timezone.utc).timestamp())
        payment_reference = f"PAY-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{timestamp % 1000000:06d}"

        # Update payment state
        self.payment_repo.update_payment_state(
            payment_id=payment_id,
            state=InstructionState.APPROVED.value,
            payment_reference=payment_reference
        )

        # Record approval
        self.payment_repo.create_payment_approval(
            payment_instruction_id=payment_id,
            challenge_id=challenge_id,
            sca_method=method,
            dynamic_link_hash=challenge.dynamic_link_hash,
            approved_at=datetime.now(timezone.utc)
        )

        # Submit to rail
        payee = self.payee_repo.get_payee_by_id(payment.payee_id)
        rail_result = self.rail_adapter.submit_payment(
            payment_reference=payment_reference,
            payee_sort_code=payee.sort_code,
            payee_account_number=f"****{payee.account_number_last4}",  # Stub uses masked
            amount_minor=payment.amount_minor,
            currency=payment.currency,
            reference=payment.reference_text
        )

        # Record status
        self.status_service.record_status(
            payment_instruction_id=payment_id,
            status_code=rail_result["status"],
            rail_reference=rail_result.get("rail_reference"),
            reason_code=rail_result.get("reason_code"),
            reason_detail=rail_result.get("reason_detail")
        )

        # Update payment with rail outcome
        if rail_result["status"] == "sent":
            self.payment_repo.update_payment_state(
                payment_id=payment_id,
                state=InstructionState.SENT.value,
                expected_arrival_message=rail_result.get("expected_arrival")
            )
        elif rail_result["status"] == "failed":
            self.payment_repo.update_payment_state(
                payment_id=payment_id,
                state=InstructionState.FAILED.value,
                failure_reason=rail_result.get("reason_detail")
            )
        else:  # pending
            # Keep as approved, mark as pending
            pass

        # Send notification
        notification_type = NotificationType.PAYMENT_SENT.value if rail_result["status"] == "sent" else NotificationType.PAYMENT_FAILED.value
        self.notification_service.send_payment_notification(
            user_identity_id=user_identity_id,
            payment_instruction_id=payment_id,
            auth_session_id=auth_session_id,
            notification_type=notification_type,
            payload={
                "payment_reference": payment_reference,
                "amount_minor": payment.amount_minor,
                "payee_name": payee.display_name,
                "status": rail_result["status"]
            }
        )

        # Log approval
        self.audit_service.log_payment_approved(
            correlation_id=self.correlation_id,
            auth_session_id=auth_session_id,
            user_identity_id=user_identity_id,
            payment_instruction_id=payment_id,
            challenge_id=challenge_id
        )

        # Emit telemetry
        outcome_code = JourneyOutcomeCode.SUCCESS.value if rail_result["status"] == "sent" else JourneyOutcomeCode.FAILURE.value
        self.telemetry_service.emit_payment_sent_event(
            correlation_id=self.correlation_id,
            auth_session_id=auth_session_id,
            profile_id=payment.profile_id,
            outcome_code=outcome_code,
            failure_reason=rail_result.get("reason_code") if rail_result["status"] == "failed" else None
        )

        # Get current status
        current_status = self.status_service.get_current_status(payment_id)
        
        return self._build_approve_response(payment, current_status, duplicate_blocked=False)

    def get_payment_status(self, payment_id: int, user_identity_id: int) -> dict:
        """Get payment status."""
        payment = self.payment_repo.get_payment_by_id(payment_id)
        if not payment:
            raise ValidationError("Payment not found")

        # Check access
        if not self.entitlement_service.check_profile_access(payment.profile_id, user_identity_id):
            raise AuthorizationError("Access denied")

        # Get current status
        current_status = self.status_service.get_current_status(payment_id)
        
        # Get payee
        payee = self.payee_repo.get_payee_by_id(payment.payee_id)

        return {
            "payment_id": payment.id,
            "status": current_status["status_code"],
            "amount_minor": payment.amount_minor,
            "currency": payment.currency,
            "payee": {
                "payee_id": payee.id,
                "display_name": payee.display_name
            },
            "reference": payment.reference_text,
            "payment_reference": payment.payment_reference,
            "rail_reference": current_status["rail_reference"],
            "expected_arrival_message": payment.expected_arrival_message,
            "duplicate_submission_blocked": payment.duplicate_submission_blocked,
            "status_last_updated_at": current_status["effective_at"],
            "failure_reason": payment.failure_reason or current_status["reason_detail"]
        }

    def _build_prepare_response(self, payment: PaymentInstruction) -> dict:
        """Build prepare response from existing payment."""
        fraud_decision = self.payment_repo.get_fraud_decision_by_payment(payment.id)
        account = self.account_repo.get_account_by_id(payment.source_account_snapshot_id)
        payee = self.payee_repo.get_payee_by_id(payment.payee_id)
        
        available_balance = account.available_balance_minor or account.current_balance_minor
        balance_passed = payment.amount_minor <= available_balance
        
        limit_minor = 1000000  # £10,000
        limit_passed = payment.amount_minor <= limit_minor

        return {
            "payment_id": payment.id,
            "payment_state": payment.instruction_state,
            "amount_minor": payment.amount_minor,
            "currency": payment.currency,
            "source_account_id": payment.source_account_snapshot_id,
            "payee": {
                "payee_id": payee.id,
                "display_name": payee.display_name,
                "sort_code": payee.sort_code,
                "masked_account_number": f"****{payee.account_number_last4}"
            },
            "reference": payment.reference_text,
            "balance_check": {
                "passed": balance_passed,
                "available_balance_minor": available_balance,
                "detail": None if balance_passed else f"Amount exceeds available balance"
            },
            "limit_check": {
                "passed": limit_passed,
                "configured_limit_minor": limit_minor,
                "detail": None if limit_passed else f"Amount exceeds payment limit"
            },
            "fraud_decision": {
                "decision": fraud_decision.decision_code if fraud_decision else "allow",
                "warning_message": fraud_decision.warning_message if fraud_decision else None,
                "hold_reason": fraud_decision.hold_reason if fraud_decision else None
            },
            "approval_required": True,
            "approval_challenge": None  # Existing payment
        }

    def _build_approve_response(self, payment: PaymentInstruction, current_status: dict, duplicate_blocked: bool) -> dict:
        """Build approve response."""
        payee = self.payee_repo.get_payee_by_id(payment.payee_id)
        
        next_actions = []
        if current_status["status_code"] == PaymentStatusCode.SENT.value:
            next_actions = ["View payment history", "Make another payment"]
        elif current_status["status_code"] == PaymentStatusCode.PENDING.value:
            next_actions = ["Check status later", "View payment history"]
        elif current_status["status_code"] == PaymentStatusCode.FAILED.value:
            next_actions = ["Try again", "Contact support"]

        return {
            "payment_id": payment.id,
            "status": current_status["status_code"],
            "amount_minor": payment.amount_minor,
            "currency": payment.currency,
            "payee": {
                "payee_id": payee.id,
                "display_name": payee.display_name
            },
            "reference": payment.reference_text,
            "payment_reference": payment.payment_reference,
            "rail_reference": current_status["rail_reference"],
            "expected_arrival_message": payment.expected_arrival_message,
            "duplicate_submission_blocked": duplicate_blocked,
            "next_actions": next_actions
        }
