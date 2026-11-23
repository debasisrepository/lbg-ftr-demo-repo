"""
AuditEvent model - audit log for security-relevant business events.
Requirement: REQ-AUD-001
"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AuditEvent(Base):
    """
    Audit event record for security and compliance.
    """
    __tablename__ = "audit_events"
    
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_reference: Mapped[str] = mapped_column(String(128), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(32), nullable=False)
    resource_reference: Mapped[str] = mapped_column(String(128), nullable=False)
    action_category: Mapped[str] = mapped_column(String(32), nullable=False)
    action_detail: Mapped[str] = mapped_column(String(64), nullable=False)
    outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
