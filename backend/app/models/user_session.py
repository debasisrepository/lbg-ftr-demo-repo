"""
User sessions model (table 4.5).
Requirement: FR-AUTH-003, FR-AUTH-006
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


class UserSession(Base):
    """Server-side session record with hashed token."""
    __tablename__ = "user_sessions"
    
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    customer_profile_ref_id = Column(Uuid, ForeignKey("customer_profile_refs.id"), nullable=False, index=True)
    device_registration_id = Column(Uuid, ForeignKey("device_registrations.id"), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True)
    issued_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity_at = Column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revocation_reason = Column(String(16), nullable=True)
    correlation_id = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    __table_args__ = (
        CheckConstraint("expires_at > issued_at", name="ck_us_expiry"),
        CheckConstraint("revocation_reason IS NULL OR revocation_reason IN ('logout','inactivity','security','expired')", name="ck_us_reason"),
        CheckConstraint("revoked_at IS NULL OR revocation_reason IS NOT NULL", name="ck_us_revoked_reason"),
        Index("ix_us_customer_revoked", "customer_profile_ref_id", "revoked_at"),
    )
