"""
Scam report model for in-app scam and unauthorised payment reporting.
Requirement: BR-PAY-014, CON-01
Release 2: Scam reporting with PSR SD20 and PSRs 2017 compliance
"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ScamReport(Base):
    """Scam or unauthorised payment report from customer."""
    __tablename__ = "scam_reports"
    
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    report_reference: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    customer_profile_ref_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("customer_profile_refs.id"), nullable=False)
    payment_reference: Mapped[str] = mapped_column(String(32), nullable=False)
    report_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'scam_app' or 'unauthorised'
    report_reason = Column(String(500), nullable=True)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="submitted")
    decision = Column(String(20), nullable=True)  # 'approved', 'denied', 'partial'
    decided_at = Column(DateTime(timezone=True), nullable=True)
    decided_by = Column(String(120), nullable=True)  # Authorised colleague name (FRD-03, AI-03)
    customer_notified_at = Column(DateTime(timezone=True), nullable=True)
    timeline_message = Column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    __table_args__ = (
        CheckConstraint("report_type IN ('scam_app', 'unauthorised')", name="ck_sr_report_type"),
        CheckConstraint("status IN ('submitted', 'under_review', 'decided', 'closed')", name="ck_sr_status"),
        CheckConstraint("decision IS NULL OR decision IN ('approved', 'denied', 'partial')", name="ck_sr_decision"),
        Index("ix_sr_customer", "customer_profile_ref_id"),
        Index("ix_sr_payment_ref", "payment_reference"),
        Index("ix_sr_report_ref", "report_reference"),
    )
