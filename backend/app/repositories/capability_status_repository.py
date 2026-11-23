"""
Capability status repository.
Requirement: FR-ACCT-001, FR-ACCT-003, FR-PAY-001, FR-PAY-011, REQ-PAY-006, REQ-PAY-007
"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.capability_status_record import CapabilityStatusRecord


class CapabilityStatusRepository:
    """Repository for capability status queries."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_current_status(self, capability_name: str) -> CapabilityStatusRecord | None:
        """
        Get current status for a capability.
        
        Args:
            capability_name: One of accounts_overview, saved_payees, payments, payment_status
        
        Returns:
            Current capability status record (effective_to IS NULL)
        """
        stmt = (
            select(CapabilityStatusRecord)
            .where(
                CapabilityStatusRecord.capability_name == capability_name,
                CapabilityStatusRecord.effective_to.is_(None)
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()
    
    def get_all_current_statuses(self) -> list[CapabilityStatusRecord]:
        """Get all current capability statuses."""
        stmt = (
            select(CapabilityStatusRecord)
            .where(CapabilityStatusRecord.effective_to.is_(None))
            .order_by(CapabilityStatusRecord.capability_name)
        )
        return list(self.db.execute(stmt).scalars().all())
    
    def update_status(
        self,
        capability_name: str,
        status_value: str,
        cause_category: str,
        customer_message: str,
        recovery_guidance: str | None,
        correlation_id: str
    ) -> CapabilityStatusRecord:
        """
        Update capability status by closing current and creating new record.
        
        Args:
            capability_name: Capability name
            status_value: New status value
            cause_category: Cause category code
            customer_message: Customer-facing message
            recovery_guidance: Recovery guidance text
            correlation_id: Correlation ID
        
        Returns:
            New capability status record
        """
        now = datetime.now(UTC)
        
        # Close existing current record if present
        current = self.get_current_status(capability_name)
        if current:
            current.effective_to = now
            current.updated_at = now
            self.db.flush()
        
        # Create new record
        new_record = CapabilityStatusRecord(
            id=uuid.uuid4(),
            capability_name=capability_name,
            status_value=status_value,
            cause_category=cause_category,
            customer_message_code=cause_category,
            customer_message=customer_message,
            recovery_guidance_code=cause_category if recovery_guidance else None,
            recovery_guidance=recovery_guidance,
            effective_from=now,
            effective_to=None,
            correlation_id=correlation_id,
            created_at=now,
            updated_at=now
        )
        self.db.add(new_record)
        self.db.flush()
        self.db.refresh(new_record)
        return new_record
