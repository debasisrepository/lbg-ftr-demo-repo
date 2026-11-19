"""Session, authentication attempt, and step-up challenge models"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Session(Base):
    """Customer session (FR-001, FR-002, FR-007, NFR-006, NFR-007, NFR-033, NFR-046)"""
    __tablename__ = "session"

    session_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("customer.customer_id"), nullable=False)
    device_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("device.device_id"), nullable=True)
    active_profile_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("profile.profile_id"), nullable=True)
    session_token_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    auth_level: Mapped[str] = mapped_column(String(16), nullable=False, default='password_only')
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    inactivity_timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_reason: Mapped[str | None] = mapped_column(String(32), nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        CheckConstraint("auth_level IN ('password_only', 'proven', 'step_up')", name='ck_session_auth_level'),
        CheckConstraint("expires_at > started_at", name='ck_session_expiry'),
        CheckConstraint("inactivity_timeout_seconds > 0", name='ck_session_inactivity'),
        CheckConstraint(
            "end_reason IS NULL OR end_reason IN ('logout', 'inactivity_timeout', 'background_expiry', 'revoked', 'security_intervention', 'expired')",
            name='ck_session_end_reason'
        ),
        CheckConstraint("(ended_at IS NULL) = (end_reason IS NULL)", name='ck_session_end_pair'),
        Index('idx_session_customer_expires', 'customer_id', 'expires_at'),
        Index('idx_session_device', 'device_id'),
        Index('idx_session_profile', 'active_profile_id'),
        Index('idx_session_correlation', 'correlation_id'),
    )


class AuthAttempt(Base):
    """Authentication attempt log (FR-001, FR-002, NFR-005, NFR-007, NFR-033)"""
    __tablename__ = "auth_attempt"

    auth_attempt_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("customer.customer_id"), nullable=True)
    device_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("device.device_id"), nullable=True)
    identifier_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    attempt_type: Mapped[str] = mapped_column(String(16), nullable=False)
    outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    client_ip_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(128), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    __table_args__ = (
        CheckConstraint("attempt_type IN ('password', 'passcode', 'biometric')", name='ck_auth_attempt_type'),
        CheckConstraint("outcome IN ('success', 'failure', 'rate_limited', 'locked_out')", name='ck_auth_attempt_outcome'),
        Index('idx_auth_attempt_identifier_time', 'identifier_hash', 'occurred_at'),
        Index('idx_auth_attempt_customer_time', 'customer_id', 'occurred_at'),
        Index('idx_auth_attempt_device', 'device_id'),
        Index('idx_auth_attempt_correlation', 'correlation_id'),
    )


class StepUpChallenge(Base):
    """Step-up authentication challenge (FR-001, FR-002, FR-005, NFR-001, NFR-007)"""
    __tablename__ = "step_up_challenge"

    step_up_challenge_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("customer.customer_id"), nullable=False)
    device_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("device.device_id"), nullable=True)
    session_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("session.session_id"), nullable=True)
    purpose: Mapped[str] = mapped_column(String(24), nullable=False)
    method: Mapped[str] = mapped_column(String(32), nullable=False)
    challenge_reference: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    result: Mapped[str] = mapped_column(String(16), nullable=False, default='issued')
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        CheckConstraint(
            "purpose IN ('device_registration', 'sign_in_proof', 'sign_in_recovery', 'payee_change', 'payment_approval')",
            name='ck_step_up_purpose'
        ),
        CheckConstraint(
            "method IN ('sms_one_time_code', 'registered_device_approval', 'passcode', 'biometric_attestation')",
            name='ck_step_up_method'
        ),
        CheckConstraint("result IN ('issued', 'passed', 'failed', 'expired', 'cancelled')", name='ck_step_up_result'),
        CheckConstraint("attempt_count >= 0", name='ck_step_up_attempts'),
        CheckConstraint("expires_at > issued_at", name='ck_step_up_expiry'),
        Index('idx_step_up_customer_issued', 'customer_id', 'issued_at'),
        Index('idx_step_up_device', 'device_id'),
        Index('idx_step_up_session', 'session_id'),
    )
