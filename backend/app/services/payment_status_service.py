"""Service for payment status tracking."""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.repositories.payment_repository import PaymentRepository
from app.adapters.payment_status_adapter import PaymentStatusAdapter
from app.common.enums import PaymentStatusCode


class PaymentStatusService:
    """Service for tracking payment outcomes."""

    def __init__(self, db: Session):
        self.db = db
        self.payment_repo = PaymentRepository(db)
        self.status_adapter = PaymentStatusAdapter(db)

    def record_status(
        self,
        payment_instruction_id: int,
        status_code: str,
        rail_reference: str | None = None,
        reason_code: str | None = None,
        reason_detail: str | None = None
    ) -> None:
        """Record payment status in history."""
        self.payment_repo.create_payment_status_history(
            payment_instruction_id=payment_instruction_id,
            status_code=status_code,
            rail_reference=rail_reference,
            reason_code=reason_code,
            reason_detail=reason_detail,
            effective_at=datetime.now(timezone.utc)
        )

    def get_current_status(self, payment_instruction_id: int) -> dict:
        """
        Get current payment status.
        
        Returns dict with status_code, rail_reference, reason_code, reason_detail, effective_at.
        """
        status_history = self.payment_repo.get_latest_payment_status(payment_instruction_id)
        
        if not status_history:
            return {
                "status_code": PaymentStatusCode.PENDING.value,
                "rail_reference": None,
                "reason_code": None,
                "reason_detail": None,
                "effective_at": datetime.now(timezone.utc)
            }
        
        return {
            "status_code": status_history.status_code,
            "rail_reference": status_history.rail_reference,
            "reason_code": status_history.reason_code,
            "reason_detail": status_history.reason_detail,
            "effective_at": status_history.effective_at
        }

    def is_pending(self, payment_instruction_id: int) -> bool:
        """Check if payment is in pending state."""
        status = self.get_current_status(payment_instruction_id)
        return status["status_code"] == PaymentStatusCode.PENDING.value
