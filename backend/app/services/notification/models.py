from datetime import datetime
from sqlalchemy import String, DateTime, Uuid, Text, CheckConstraint, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
import uuid
from app.database import Base
from app.core.clock import Clock


class NotificationRecord(Base):
    __tablename__ = "notification_record"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    case_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("case_record.id"), nullable=False)
    event_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("domain_event.id"), nullable=False)
    template_ref: Mapped[str] = mapped_column(String(40), nullable=False)
    reentry_route: Mapped[str] = mapped_column(String(100), nullable=False)
    privacy_classification: Mapped[str] = mapped_column(String(20), nullable=False, default='generic')
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=Clock.utc_now, server_default=func.current_timestamp())
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("privacy_classification = 'generic'", name="ck_notification_record_privacy"),
        CheckConstraint("status IN ('pending', 'dispatched', 'failed')", name="ck_notification_record_status"),
        Index("ix_notification_record_status_requested", "status", "requested_at"),
    )
