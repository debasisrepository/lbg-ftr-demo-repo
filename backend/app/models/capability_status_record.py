"""
Capability status records model (table 4.20).
Requirement: FR-ACCT-001, FR-ACCT-003, FR-PAY-001, FR-PAY-011
Release 2: BR-ACCT-004 (loan_view capability)
"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, Column, DateTime, String, Uuid

from app.database import Base


class CapabilityStatusRecord(Base):
    """Capability state and guidance for graceful degradation."""
    __tablename__ = "capability_status_records"
    
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    capability_name = Column(String(24), nullable=False, index=True)
    status_value = Column(String(12), nullable=False, default="healthy")
    cause_category = Column(String(24), nullable=False, default="unknown")
    customer_message_code = Column(String(48), nullable=True)
    recovery_guidance_code = Column(String(48), nullable=True)
    effective_from = Column(DateTime(timezone=True), nullable=False)
    effective_to = Column(DateTime(timezone=True), nullable=True)
    correlation_id = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    __table_args__ = (
        CheckConstraint("capability_name IN ('accounts_overview','saved_payees','payments','payment_status','loan_view')", name="ck_csr_capability"),
        CheckConstraint("status_value IN ('healthy','stale','partial','unavailable','restricted')", name="ck_csr_status"),
        CheckConstraint("cause_category IN ('dependency_outage','freshness_breach','security_containment','manual_control','unknown')", name="ck_csr_cause"),
        CheckConstraint("effective_to IS NULL OR effective_to >= effective_from", name="ck_csr_window"),
    )
