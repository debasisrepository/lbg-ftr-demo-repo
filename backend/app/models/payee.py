"""Payee and Confirmation of Payee models"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Payee(Base):
    """Payee entity (FR-004, FR-005, NFR-012, NFR-038, NFR-057)"""
    __tablename__ = "payee"

    payee_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("customer.customer_id"), nullable=False)
    profile_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("profile.profile_id"), nullable=False)
    external_payee_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    payee_name: Mapped[str] = mapped_column(String(140), nullable=False)
    sort_code: Mapped[str] = mapped_column(String(8), nullable=False)
    account_number_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    account_number_masked: Mapped[str] = mapped_column(String(16), nullable=False)
    account_number_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    payee_type: Mapped[str] = mapped_column(String(16), nullable=False, default='personal')
    is_saved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default='pending_verification')
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationship
    cop_checks: Mapped[list["CopCheck"]] = relationship("CopCheck", back_populates="payee", lazy="selectin")

    __table_args__ = (
        UniqueConstraint('customer_id', 'profile_id', 'payee_name', 'sort_code', 'account_number_hash', name='uq_payee_identity'),
        CheckConstraint("payee_type IN ('personal', 'business')", name='ck_payee_type'),
        CheckConstraint("status IN ('pending_verification', 'active', 'blocked', 'removed')", name='ck_payee_status'),
        CheckConstraint("is_saved = FALSE OR status IN ('active', 'blocked', 'removed')", name='ck_payee_saved_verified'),
        Index('idx_payee_profile_status', 'profile_id', 'status', 'is_saved'),
        Index('idx_payee_customer', 'customer_id'),
    )


class CopCheck(Base):
    """Confirmation of Payee check result (FR-004, NFR-012, NFR-057, NFR-058, NFR-065)"""
    __tablename__ = "cop_check"

    cop_check_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    payee_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("payee.payee_id"), nullable=False)
    request_reference: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    check_trigger: Mapped[str] = mapped_column(String(16), nullable=False)
    checked_name: Mapped[str] = mapped_column(String(140), nullable=False)
    checked_sort_code: Mapped[str] = mapped_column(String(8), nullable=False)
    checked_account_number_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    outcome: Mapped[str] = mapped_column(String(20), nullable=False)
    suggested_name: Mapped[str | None] = mapped_column(String(140), nullable=True)
    policy_treatment: Mapped[str] = mapped_column(String(16), nullable=False)
    customer_acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provider_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_response_digest: Mapped[str | None] = mapped_column(String(128), nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    # Relationship
    payee: Mapped["Payee"] = relationship("Payee", back_populates="cop_checks")

    __table_args__ = (
        CheckConstraint("check_trigger IN ('new_payee', 'amended_payee', 'recheck')", name='ck_cop_check_trigger'),
        CheckConstraint("outcome IN ('match', 'partial_match', 'mismatch', 'unavailable')", name='ck_cop_check_outcome'),
        CheckConstraint("policy_treatment IN ('allow', 'warn', 'block', 'defer')", name='ck_cop_check_policy'),
        CheckConstraint("expires_at IS NULL OR expires_at > checked_at", name='ck_cop_check_expiry'),
        Index('idx_cop_check_payee_checked', 'payee_id', 'checked_at'),
        Index('idx_cop_check_correlation', 'correlation_id'),
    )
