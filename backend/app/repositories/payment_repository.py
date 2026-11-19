"""Repository for payment-related database operations."""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.payments import (
    PaymentInstruction,
    FraudDecision,
    PaymentApproval,
    PaymentStatusHistory
)
from app.common.enums import InstructionState, PaymentStatusCode


class PaymentRepository:
    """Repository for payment persistence operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_payment_instruction(
        self,
        profile_id: int,
        auth_session_id: int,
        source_account_snapshot_id: int,
        payee_id: int,
        amount_minor: int,
        currency: str,
        reference_text: str | None,
        client_idempotency_key: str,
        instruction_state: str
    ) -> PaymentInstruction:
        """Create a new payment instruction."""
        now = datetime.now(timezone.utc)
        instruction = PaymentInstruction(
            profile_id=profile_id,
            auth_session_id=auth_session_id,
            source_account_snapshot_id=source_account_snapshot_id,
            payee_id=payee_id,
            amount_minor=amount_minor,
            currency=currency,
            reference_text=reference_text,
            client_idempotency_key=client_idempotency_key,
            payment_reference=None,
            instruction_state=instruction_state,
            duplicate_submission_blocked=False,
            expected_arrival_message=None,
            failure_reason=None,
            created_at=now,
            updated_at=now
        )
        self.db.add(instruction)
        self.db.commit()
        self.db.refresh(instruction)
        return instruction

    def get_payment_by_id(self, payment_id: int) -> PaymentInstruction | None:
        """Get payment instruction by ID."""
        return self.db.query(PaymentInstruction).filter(
            PaymentInstruction.id == payment_id
        ).first()

    def get_payment_by_idempotency_key(self, key: str) -> PaymentInstruction | None:
        """Get payment instruction by idempotency key."""
        return self.db.query(PaymentInstruction).filter(
            PaymentInstruction.client_idempotency_key == key
        ).first()

    def update_payment_state(
        self,
        payment_id: int,
        state: str,
        payment_reference: str | None = None,
        expected_arrival_message: str | None = None,
        failure_reason: str | None = None,
        duplicate_submission_blocked: bool | None = None
    ) -> None:
        """Update payment instruction state."""
        instruction = self.db.query(PaymentInstruction).filter(
            PaymentInstruction.id == payment_id
        ).first()
        if instruction:
            instruction.instruction_state = state
            instruction.updated_at = datetime.now(timezone.utc)
            if payment_reference is not None:
                instruction.payment_reference = payment_reference
            if expected_arrival_message is not None:
                instruction.expected_arrival_message = expected_arrival_message
            if failure_reason is not None:
                instruction.failure_reason = failure_reason
            if duplicate_submission_blocked is not None:
                instruction.duplicate_submission_blocked = duplicate_submission_blocked
            self.db.commit()

    def create_fraud_decision(
        self,
        payment_instruction_id: int,
        decision_code: str,
        warning_message: str | None,
        hold_reason: str | None,
        provider_reference: str | None,
        decided_at: datetime
    ) -> FraudDecision:
        """Create fraud decision record."""
        now = datetime.now(timezone.utc)
        decision = FraudDecision(
            payment_instruction_id=payment_instruction_id,
            decision_code=decision_code,
            warning_message=warning_message,
            hold_reason=hold_reason,
            provider_reference=provider_reference,
            decided_at=decided_at,
            created_at=now,
            updated_at=now
        )
        self.db.add(decision)
        self.db.commit()
        self.db.refresh(decision)
        return decision

    def get_fraud_decision_by_payment(self, payment_instruction_id: int) -> FraudDecision | None:
        """Get fraud decision for a payment."""
        return self.db.query(FraudDecision).filter(
            FraudDecision.payment_instruction_id == payment_instruction_id
        ).first()

    def create_payment_approval(
        self,
        payment_instruction_id: int,
        challenge_id: int | None,
        sca_method: str,
        dynamic_link_hash: str | None,
        approved_at: datetime
    ) -> PaymentApproval:
        """Create payment approval record."""
        now = datetime.now(timezone.utc)
        approval = PaymentApproval(
            payment_instruction_id=payment_instruction_id,
            challenge_id=challenge_id,
            sca_method=sca_method,
            dynamic_link_hash=dynamic_link_hash,
            approved_at=approved_at,
            created_at=now,
            updated_at=now
        )
        self.db.add(approval)
        self.db.commit()
        self.db.refresh(approval)
        return approval

    def create_payment_status_history(
        self,
        payment_instruction_id: int,
        status_code: str,
        rail_reference: str | None,
        reason_code: str | None,
        reason_detail: str | None,
        effective_at: datetime
    ) -> PaymentStatusHistory:
        """Create payment status history record."""
        now = datetime.now(timezone.utc)
        status = PaymentStatusHistory(
            payment_instruction_id=payment_instruction_id,
            status_code=status_code,
            rail_reference=rail_reference,
            reason_code=reason_code,
            reason_detail=reason_detail,
            effective_at=effective_at,
            created_at=now,
            updated_at=now
        )
        self.db.add(status)
        self.db.commit()
        self.db.refresh(status)
        return status

    def get_latest_payment_status(self, payment_instruction_id: int) -> PaymentStatusHistory | None:
        """Get latest status for a payment."""
        return self.db.query(PaymentStatusHistory).filter(
            PaymentStatusHistory.payment_instruction_id == payment_instruction_id
        ).order_by(PaymentStatusHistory.effective_at.desc()).first()
