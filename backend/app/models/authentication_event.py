"""
Authentication events model (table 4.6).
Requirement: FR-AUTH-003, FR-PAY-008
"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Uuid,
)

from app.database import Base


class AuthenticationEvent(Base):
    """Append-only authentication attempt outcomes."""
    __tablename__ = "authentication_events"
    
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    customer_profile_ref_id = Column(Uuid, ForeignKey("customer_profile_refs.id"), nullable=True, index=True)
    device_registration_id = Column(Uuid, ForeignKey("device_registrations.id"), nullable=True, index=True)
    client_address_hash = Column(String(64), nullable=True, index=True)
    authentication_type = Column(String(24), nullable=False)
    outcome = Column(String(16), nullable=False)
    failure_category = Column(String(32), nullable=True)
    ciam_transaction_reference = Column(String(128), nullable=True)
    linked_business_action_type = Column(String(16), nullable=True)
    linked_business_action_id = Column(Uuid, nullable=True, index=True)
    correlation_id = Column(String(64), nullable=False, index=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), index=True)
    
    __table_args__ = (
        CheckConstraint("authentication_type IN ('passcode','dynamic_link_approval')", name="ck_ae_type"),
        CheckConstraint("outcome IN ('success','failed','abandoned','denied','expired','rate_limited')", name="ck_ae_outcome"),
        CheckConstraint("linked_business_action_type IS NULL OR linked_business_action_type = 'payment_intent'", name="ck_ae_action_type"),
        Index("ix_ae_customer_time", "customer_profile_ref_id", "occurred_at"),
        Index("ix_ae_address_time", "client_address_hash", "occurred_at"),
    )
