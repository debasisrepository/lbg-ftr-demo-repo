"""Customer, profile, entitlement, account, loan, and device models"""
import uuid
from datetime import UTC, date, datetime

from sqlalchemy import JSON as SQLiteJSON
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

# JSON type that works with both PostgreSQL and SQLite
JSON = JSONB().with_variant(SQLiteJSON(), "sqlite")


class Customer(Base):
    """Customer entity (FR-001, FR-002, NFR-005, NFR-037, NFR-038)"""
    __tablename__ = "customer"

    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    external_identity_ref: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    customer_type: Mapped[str] = mapped_column(String(16), nullable=False)
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    primary_contact_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default='active')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    profiles: Mapped[list["Profile"]] = relationship(back_populates="customer", lazy="select")
    devices: Mapped[list["Device"]] = relationship(back_populates="customer", lazy="select")

    __table_args__ = (
        CheckConstraint("customer_type IN ('retail', 'dual_profile', 'business_user')", name='ck_customer_type'),
        CheckConstraint("status IN ('active', 'locked', 'closed')", name='ck_customer_status'),
    )


class Profile(Base):
    """Customer profile (personal or business) (FR-003, FR-004, FR-005, NFR-020, NFR-021)"""
    __tablename__ = "profile"

    profile_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("customer.customer_id"), nullable=False)
    profile_type: Mapped[str] = mapped_column(String(16), nullable=False)
    external_profile_ref: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(140), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default='inactive')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    customer: Mapped["Customer"] = relationship(back_populates="profiles")
    entitlements: Mapped[list["Entitlement"]] = relationship(back_populates="profile", lazy="select")

    __table_args__ = (
        CheckConstraint("profile_type IN ('personal', 'business')", name='ck_profile_type'),
        CheckConstraint("status IN ('active', 'inactive', 'suspended')", name='ck_profile_status'),
        Index('idx_profile_customer', 'customer_id', 'status'),
    )


class Entitlement(Base):
    """Profile entitlement and capability (FR-003, FR-004, FR-005, NFR-033, NFR-065)"""
    __tablename__ = "entitlement"

    entitlement_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("profile.profile_id"), nullable=False)
    entitlement_code: Mapped[str] = mapped_column(String(64), nullable=False)
    capability_type: Mapped[str] = mapped_column(String(24), nullable=False)
    can_view_accounts: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_manage_payees: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_initiate_payments: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    source_system_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_snapshot_json: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    profile: Mapped["Profile"] = relationship(back_populates="entitlements")

    __table_args__ = (
        CheckConstraint("capability_type IN ('viewer', 'payer', 'payee_manager', 'business_admin')", name='ck_entitlement_capability'),
        CheckConstraint("capability_type <> 'viewer' OR can_initiate_payments = FALSE", name='ck_entitlement_viewer_no_pay'),
        CheckConstraint("effective_to IS NULL OR effective_to > effective_from", name='ck_entitlement_window'),
        Index('idx_entitlement_profile_capability', 'profile_id', 'capability_type', 'effective_to'),
    )


class BankAccount(Base):
    """Bank account aggregation snapshot (FR-003, FR-005, NFR-021, NFR-039, NFR-064)"""
    __tablename__ = "bank_account"

    bank_account_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    external_account_ref: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    account_type: Mapped[str] = mapped_column(String(24), nullable=False)
    account_name: Mapped[str] = mapped_column(String(140), nullable=False)
    sort_code_masked: Mapped[str] = mapped_column(String(16), nullable=False)
    account_number_masked: Mapped[str] = mapped_column(String(16), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default='GBP')
    account_holder_name: Mapped[str] = mapped_column(String(140), nullable=False)
    current_balance_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    available_balance_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    overdraft_limit_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    freshness_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_status: Mapped[str] = mapped_column(String(16), nullable=False, default='available')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        CheckConstraint("account_type IN ('current', 'savings', 'business_current', 'credit_card')", name='ck_bank_account_type'),
        CheckConstraint("source_status IN ('available', 'stale', 'unavailable')", name='ck_bank_account_source_status'),
    )


class ProfileAccountVisibility(Base):
    """Profile to bank account visibility mapping (FR-003, FR-004, FR-005, NFR-020)"""
    __tablename__ = "profile_account_visibility"

    profile_account_visibility_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("profile.profile_id"), nullable=False)
    bank_account_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("bank_account.bank_account_id"), nullable=False)
    visibility_reason: Mapped[str] = mapped_column(String(48), nullable=False)
    payment_permission: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    visible_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    visible_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        UniqueConstraint('profile_id', 'bank_account_id', name='uq_profile_account_visibility'),
        CheckConstraint("visible_to IS NULL OR visible_to > visible_from", name='ck_pav_window'),
        Index('idx_pav_account', 'bank_account_id'),
    )


class LoanSnapshot(Base):
    """Loan product snapshot (FR-003, NFR-011, NFR-021, NFR-064)"""
    __tablename__ = "loan_snapshot"

    loan_snapshot_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("profile.profile_id"), nullable=False)
    external_loan_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    loan_name: Mapped[str] = mapped_column(String(140), nullable=False)
    outstanding_balance_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    next_repayment_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    next_repayment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default='GBP')
    freshness_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_status: Mapped[str] = mapped_column(String(16), nullable=False, default='available')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        UniqueConstraint('profile_id', 'external_loan_ref', name='uq_loan_snapshot_profile_ref'),
        CheckConstraint("source_status IN ('available', 'stale', 'unavailable')", name='ck_loan_snapshot_source_status'),
    )


class Device(Base):
    """Registered customer device (FR-001, FR-002, FR-008, NFR-004, NFR-008, NFR-041)"""
    __tablename__ = "device"

    device_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("customer.customer_id"), nullable=False)
    device_public_key_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    platform_type: Mapped[str] = mapped_column(String(16), nullable=False)
    platform_device_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    device_label: Mapped[str | None] = mapped_column(String(80), nullable=True)
    trust_state: Mapped[str] = mapped_column(String(16), nullable=False, default='pending')
    integrity_state: Mapped[str] = mapped_column(String(16), nullable=False, default='unknown')
    biometric_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    passcode_failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    passcode_paused_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    customer: Mapped["Customer"] = relationship(back_populates="devices")

    __table_args__ = (
        UniqueConstraint('customer_id', 'platform_device_ref', name='uq_device_customer_platform_ref'),
        CheckConstraint("platform_type IN ('ios', 'android')", name='ck_device_platform'),
        CheckConstraint("trust_state IN ('pending', 'trusted', 'untrusted', 'revoked')", name='ck_device_trust'),
        CheckConstraint("integrity_state IN ('unknown', 'ok', 'suspect', 'compromised')", name='ck_device_integrity'),
        CheckConstraint("passcode_failed_count >= 0", name='ck_device_passcode_failed'),
        Index('idx_device_customer_trust', 'customer_id', 'trust_state'),
    )
