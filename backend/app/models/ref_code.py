"""Reference data model - ref_code table"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class RefCode(Base):
    """Reference code lookup table for enumerations and customer messages"""
    __tablename__ = "ref_code"

    ref_code_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code_group: Mapped[str] = mapped_column(String(48), nullable=False)
    code_value: Mapped[str] = mapped_column(String(64), nullable=False)
    display_label: Mapped[str] = mapped_column(String(120), nullable=False)
    customer_message: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        UniqueConstraint('code_group', 'code_value', name='uq_ref_code_group_value'),
        CheckConstraint(
            "code_group IN ('payment_internal_state', 'risk_treatment_reason', 'notification_template', 'security_event_type', 'scam_claim_reason')",
            name='ck_ref_code_group'
        ),
        Index('idx_ref_code_group_active', 'code_group', 'is_active', 'sort_order'),
    )
