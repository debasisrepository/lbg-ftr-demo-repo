"""Payee model - saved payees with Confirmation of Payee outcome"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Payee(Base):
    """
    Payee record for saved payees.
    
    Columns:
    - id: UUID primary key
    - customer_profile_ref_id: FK to customer_profile_refs
    - payee_name: VARCHAR(120), payee display name
    - payee_account_identifier: VARCHAR(34), full account number (never shown to customer)
    - payee_sort_code: VARCHAR(8), sort code
    - masked_account_identifier: VARCHAR(32), masked account number for display
    - payee_status: VARCHAR(12), CHECK IN ('saved_active', 'blocked'), DEFAULT 'saved_active'
    - activated_at: TIMESTAMPTZ, when payee was saved
    - cop_outcome_category: VARCHAR(24), CHECK IN ('match', 'close_match', 'no_match', 
      'unable_to_confirm', 'provider_unavailable', 'blocked'), Confirmation of Payee result
    - cop_provider_reference: VARCHAR(128), CoP provider transaction reference
    - cop_checked_at: TIMESTAMPTZ, when CoP check was performed
    - correlation_id: VARCHAR(64), correlation ID for audit trail
    - created_at: TIMESTAMPTZ, record creation
    - updated_at: TIMESTAMPTZ, last update
    """
    __tablename__ = "payees"
    
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    customer_profile_ref_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("customer_profile_refs.id"), nullable=False, index=True
    )
    payee_name: Mapped[str] = mapped_column(String(120), nullable=False)
    payee_account_identifier: Mapped[str] = mapped_column(String(34), nullable=False)
    payee_sort_code: Mapped[str] = mapped_column(String(8), nullable=False)
    masked_account_identifier: Mapped[str] = mapped_column(String(32), nullable=False)
    payee_status: Mapped[str] = mapped_column(
        String(12), 
        CheckConstraint("payee_status IN ('saved_active', 'blocked')", name="ck_payee_status"),
        nullable=False,
        default="saved_active",
        server_default="saved_active"
    )
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cop_outcome_category: Mapped[str | None] = mapped_column(
        String(24),
        CheckConstraint(
            "cop_outcome_category IN ('match', 'close_match', 'no_match', 'unable_to_confirm', "
            "'provider_unavailable', 'blocked')",
            name="ck_cop_outcome_category"
        ),
        nullable=True
    )
    cop_provider_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    cop_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(datetime.now().astimezone().tzinfo))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        default=lambda: datetime.now(datetime.now().astimezone().tzinfo),
        onupdate=lambda: datetime.now(datetime.now().astimezone().tzinfo)
    )
