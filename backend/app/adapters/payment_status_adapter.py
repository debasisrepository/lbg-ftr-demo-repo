"""Adapter for payment status tracking integration."""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.payments import PaymentInstruction
from app.repositories.payment_repository import PaymentRepository


class PaymentStatusAdapter:
    """Adapter for payment status retrieval from external tracking system."""

    def __init__(self, db: Session):
        """Initialize adapter with database session."""
        self.db = db
        self.payment_repo = PaymentRepository(db)

    def get_payment_status(self, payment_reference: str) -> dict | None:
        """
        Retrieve payment status from status tracking system.
        
        Returns status data or None if not found.
        
        This implementation queries the local payment status store.
        In production, this would query an external payment tracking system.
        """
        # Query payment instruction by reference
        instruction = self.db.query(PaymentInstruction).filter(
            PaymentInstruction.payment_reference == payment_reference
        ).first()
        
        if not instruction:
            return None
        
        # Get latest status from history
        status_history = self.payment_repo.get_latest_payment_status(instruction.id)
        
        if not status_history:
            return None
        
        return {
            "payment_instruction_id": instruction.id,
            "payment_reference": payment_reference,
            "status_code": status_history.status_code,
            "rail_reference": status_history.rail_reference,
            "reason_code": status_history.reason_code,
            "reason_detail": status_history.reason_detail,
            "effective_at": status_history.effective_at.isoformat()
        }
    
    def poll_status_update(self, payment_reference: str) -> dict | None:
        """
        Poll for status updates on pending payments.
        
        Returns updated status if available, None otherwise.
        
        This implementation checks the local store for status changes.
        In production, this would poll an external payment rail or status tracking API.
        """
        # Retrieve current status
        current_status = self.get_payment_status(payment_reference)
        
        if not current_status:
            return None
        
        # In this implementation, status updates come from the payment rail responses
        # which are already recorded in the database
        # Return the current status if it exists
        return current_status
