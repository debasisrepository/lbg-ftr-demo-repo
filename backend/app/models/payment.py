"""Payment-related models: limits, orders, idempotency, approvals, risk, status"""
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class PaymentLimit(Base):
    """Payment limit configuration (FR-005, NFR-021, NFR-058, NFR-061)"""
    __tablename__ = "payment_limit"

    payment_limit_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("profile.profile_id"), nullable=True)
    bank_account_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("bank_account.bank_account_id"), nullable=True)
    limit_type: Mapped[str] = mapped_column(String(24), nullable=False)
    payment_type: Mapped[str] = mapped_column(String(32), nullable=False, default='faster_payment')
    amount_limit_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default='GBP')
    source_policy_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        CheckConstraint("limit_type IN ('per_payment', 'daily', 'scheme_maximum')", name='ck_payment_limit_type'),
        CheckConstraint("profile_id IS NOT NULL OR bank_account_id IS NOT NULL", name='ck_payment_limit_scope'),
        CheckConstraint("amount_limit_minor >= 0", name='ck_payment_limit_amount'),
        CheckConstraint("effective_to IS NULL OR effective_to > effective_from", name='ck_payment_limit_window'),
        Index('idx_payment_limit_profile', 'profile_id', 'limit_type', 'effective_to'),
        Index('idx_payment_limit_account', 'bank_account_id', 'limit_type', 'effective_to'),
    )


class PaymentOrder(Base):
    """Payment order orchestration (FR-005, FR-006, NFR-002, NFR-056, NFR-061, NFR-062)"""
    __tablename__ = "payment_order"

    payment_order_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("customer.customer_id"), nullable=False)
    profile_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("profile.profile_id"), nullable=False)
    source_account_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("bank_account.bank_account_id"), nullable=False)
    payee_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("payee.payee_id"), nullable=False)
    cop_check_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("cop_check.cop_check_id"), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    customer_payment_ref: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    payment_reference: Mapped[str | None] = mapped_column(String(35), nullable=True)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default='GBP')
    payment_type: Mapped[str] = mapped_column(String(32), nullable=False, default='faster_payment')
    dynamic_link_digest: Mapped[str] = mapped_column(String(255), nullable=False)
    external_payment_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    current_internal_state: Mapped[str] = mapped_column(String(32), nullable=False, default='prepared')
    normalized_status: Mapped[str] = mapped_column(String(16), nullable=False, default='pending')
    latest_status_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duplicate_suppression_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expected_arrival_text: Mapped[str | None] = mapped_column(String(140), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        CheckConstraint("amount_minor > 0", name='ck_payment_order_amount'),
        CheckConstraint("payment_type IN ('faster_payment')", name='ck_payment_order_type'),
        CheckConstraint("normalized_status IN ('sent', 'pending', 'failed')", name='ck_payment_order_normalized'),
        CheckConstraint(
            "current_internal_state IN ('prepared', 'awaiting_sca', 'risk_held', 'submitted', 'duplicate_suspected', 'notification_failed', 'support_routed', 'completed', 'rejected')",
            name='ck_payment_order_internal'
        ),
        CheckConstraint(
            "normalized_status <> 'pending' OR submitted_at IS NULL OR duplicate_suppression_until IS NOT NULL",
            name='ck_payment_order_pending_window'
        ),
        Index('idx_payment_order_customer_created', 'customer_id', 'created_at'),
        Index('idx_payment_order_profile', 'profile_id', 'created_at'),
        Index('idx_payment_order_external_ref', 'external_payment_ref'),
        Index('idx_payment_order_status_latest', 'normalized_status', 'latest_status_at'),
        Index('idx_payment_order_payee_amount', 'payee_id', 'amount_minor', 'created_at'),
        Index('idx_payment_order_source_account', 'source_account_id'),
        Index('idx_payment_order_cop_check', 'cop_check_id'),
        Index('idx_payment_order_correlation', 'correlation_id'),
    )


class IdempotencyRecord(Base):
    """Idempotency tracking (FR-005, FR-006, NFR-061, NFR-062)"""
    __tablename__ = "idempotency_record"

    idempotency_record_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    payment_order_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("payment_order.payment_order_id"), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    request_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    replay_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    response_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        CheckConstraint("replay_count >= 0", name='ck_idempotency_replay'),
        CheckConstraint("last_seen_at >= first_seen_at", name='ck_idempotency_seen'),
        Index('idx_idempotency_payment_order', 'payment_order_id'),
    )


class PaymentLimitCheck(Base):
    """Payment limit check result (FR-005, NFR-021, NFR-058, NFR-061)"""
    __tablename__ = "payment_limit_check"

    payment_limit_check_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    payment_order_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("payment_order.payment_order_id"), nullable=False)
    payment_limit_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("payment_limit.payment_limit_id"), nullable=True)
    check_type: Mapped[str] = mapped_column(String(24), nullable=False)
    evaluated_amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    limit_amount_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    available_balance_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    result: Mapped[str] = mapped_column(String(16), nullable=False)
    customer_message_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    __table_args__ = (
        CheckConstraint("check_type IN ('per_payment', 'daily', 'scheme_maximum', 'funds_available', 'entitlement')", name='ck_plc_check_type'),
        CheckConstraint("result IN ('passed', 'blocked_over_limit', 'blocked_insufficient_funds', 'blocked_entitlement', 'unavailable')", name='ck_plc_result'),
        CheckConstraint("evaluated_amount_minor > 0", name='ck_plc_amount'),
        Index('idx_plc_payment_order', 'payment_order_id', 'evaluated_at'),
        Index('idx_plc_payment_limit', 'payment_limit_id'),
    )


class ScaApproval(Base):
    """SCA approval with dynamic linking (FR-005, NFR-001, NFR-002, NFR-007, NFR-033, NFR-060)"""
    __tablename__ = "sca_approval"

    sca_approval_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    payment_order_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("payment_order.payment_order_id"), nullable=False)
    step_up_challenge_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("step_up_challenge.step_up_challenge_id"), nullable=True)
    device_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("device.device_id"), nullable=True)
    approval_method: Mapped[str] = mapped_column(String(32), nullable=False)
    source_account_ref_snapshot: Mapped[str] = mapped_column(String(128), nullable=False)
    payee_ref_snapshot: Mapped[str] = mapped_column(String(128), nullable=False)
    amount_minor_snapshot: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency_code_snapshot: Mapped[str] = mapped_column(String(3), nullable=False)
    payment_reference_snapshot: Mapped[str | None] = mapped_column(String(35), nullable=True)
    dynamic_link_digest: Mapped[str] = mapped_column(String(255), nullable=False)
    approval_result: Mapped[str] = mapped_column(String(16), nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    __table_args__ = (
        CheckConstraint("approval_method IN ('passcode', 'biometric_attestation', 'step_up_challenge')", name='ck_sca_method'),
        CheckConstraint("approval_result IN ('approved', 'rejected', 'expired', 'failed')", name='ck_sca_result'),
        CheckConstraint("amount_minor_snapshot > 0", name='ck_sca_amount'),
        CheckConstraint("approval_result <> 'approved' OR approved_at IS NOT NULL", name='ck_sca_approved_at'),
        Index('idx_sca_approval_order', 'payment_order_id', 'created_at'),
        Index('idx_sca_approval_challenge', 'step_up_challenge_id'),
        Index('idx_sca_approval_device', 'device_id'),
    )


class RiskAssessment(Base):
    """Fraud/risk assessment result (FR-005, NFR-007, NFR-058, NFR-061)"""
    __tablename__ = "risk_assessment"

    risk_assessment_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    payment_order_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("payment_order.payment_order_id"), nullable=False)
    risk_engine_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    risk_score: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    treatment_reason_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    warning_shown_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    purpose_answer_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    customer_acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    case_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    __table_args__ = (
        CheckConstraint("decision IN ('allow', 'warn', 'challenge', 'hold', 'block')", name='ck_risk_decision'),
        Index('idx_risk_assessment_order', 'payment_order_id', 'assessed_at'),
        Index('idx_risk_assessment_case', 'case_reference'),
    )


class PaymentStatusChange(Base):
    """Payment status transition log (FR-006, FR-009, NFR-022, NFR-061, NFR-066) - append-only"""
    __tablename__ = "payment_status_change"

    payment_status_change_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    payment_order_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("payment_order.payment_order_id"), nullable=False)
    internal_state: Mapped[str] = mapped_column(String(32), nullable=False)
    normalized_state: Mapped[str] = mapped_column(String(16), nullable=False)
    state_reason_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_event_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    event_occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    __table_args__ = (
        CheckConstraint("normalized_state IN ('sent', 'pending', 'failed')", name='ck_psc_normalized'),
        CheckConstraint(
            "internal_state IN ('prepared', 'awaiting_sca', 'risk_held', 'submitted', 'duplicate_suspected', 'notification_failed', 'support_routed', 'completed', 'rejected')",
            name='ck_psc_internal'
        ),
        Index('idx_psc_order_event', 'payment_order_id', 'event_occurred_at'),
        Index('idx_psc_internal_state', 'internal_state', 'event_occurred_at'),
    )


class DuplicatePaymentLink(Base):
    """Duplicate payment detection link (FR-006, FR-009, NFR-022, NFR-047, NFR-062)"""
    __tablename__ = "duplicate_payment_link"

    duplicate_payment_link_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    payment_order_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("payment_order.payment_order_id"), nullable=False)
    matched_payment_order_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("payment_order.payment_order_id"), nullable=False)
    detection_basis: Mapped[str] = mapped_column(String(32), nullable=False)
    customer_response: Mapped[str] = mapped_column(String(24), nullable=False, default='warning_shown')
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    __table_args__ = (
        UniqueConstraint('payment_order_id', 'matched_payment_order_id', name='uq_duplicate_payment_link_pair'),
        CheckConstraint("payment_order_id <> matched_payment_order_id", name='ck_dpl_different'),
        CheckConstraint(
            "detection_basis IN ('same_idempotency_key', 'same_payee_amount_pending', 'same_payee_amount_within_10_minutes')",
            name='ck_dpl_basis'
        ),
        CheckConstraint("customer_response IN ('warning_shown', 'cancelled', 'proceeded')", name='ck_dpl_response'),
        Index('idx_dpl_matched', 'matched_payment_order_id'),
    )
