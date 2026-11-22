"""Incident reporting model (BR-OPS-008)"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class IncidentReport(Base):
    """Incident report for operational issues (BR-OPS-008)"""
    __tablename__ = "incident_report"

    incident_report_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    incident_reference: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    incident_category: Mapped[str] = mapped_column(String(64), nullable=False)
    incident_title: Mapped[str] = mapped_column(String(255), nullable=False)
    incident_description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default='medium')
    status: Mapped[str] = mapped_column(String(32), nullable=False, default='reported')
    external_incident_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    __table_args__ = (
        CheckConstraint(
            "incident_category IN ('technical_issue', 'service_outage', 'data_issue', 'security_concern', 'other')",
            name='ck_incident_category'
        ),
        CheckConstraint(
            "severity IN ('low', 'medium', 'high', 'critical')",
            name='ck_incident_severity'
        ),
        CheckConstraint(
            "status IN ('reported', 'acknowledged', 'investigating', 'resolved', 'closed')",
            name='ck_incident_status'
        ),
        Index('idx_incident_customer', 'customer_id', 'reported_at'),
        Index('idx_incident_reference', 'incident_reference'),
        Index('idx_incident_status', 'status', 'reported_at'),
    )
