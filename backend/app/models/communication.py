"""Communication and notification models."""
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CommunicationRecord(Base):
    """Communication record."""

    __tablename__ = "communication_records"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    communication_type: Mapped[str] = mapped_column(String(50), nullable=False)
    subject_text: Mapped[str | None] = mapped_column(String(500), nullable=True)
    body_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_wording_set: Mapped[str] = mapped_column(String(100), nullable=False)
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class NotificationRecord(Base):
    """Notification record."""

    __tablename__ = "notification_records"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    communication_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    case_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    customer_party_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    safe_preview_text: Mapped[str] = mapped_column(String(500), nullable=False)
    deep_link_token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    deep_link_target: Mapped[str] = mapped_column(String(50), nullable=False)
    deep_link_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notification_template_code: Mapped[str] = mapped_column(String(100), nullable=False)
    delivery_state: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    delivery_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "deep_link_target IN ('case_list', 'case_view')",
            name="ck_deep_link_target",
        ),
        CheckConstraint(
            "delivery_state IN ('pending', 'sent', 'delivered', 'failed')",
            name="ck_delivery_state",
        ),
        Index("ix_notification_delivery_state", delivery_state, delivered_at),
    )
