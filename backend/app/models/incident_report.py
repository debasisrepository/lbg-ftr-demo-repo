"""
Incident report model for PS26/2 and PS7/26 operational resilience readiness.
Requirement: BR-OPS-008, BR-OPS-009, RES-05
Release 2: FCA PS26/2 and PRA PS7/26 incident classification and reporting readiness (by 18 March 2027)
"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Index,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class IncidentReport(Base):
    """Operational incident with PS26/2 and PS7/26 classification."""
    __tablename__ = "incident_reports"
    
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    incident_reference: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    incident_type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., 'service_outage', 'data_breach', 'payment_disruption'
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # 'critical', 'major', 'minor'
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    affected_service = Column(String(100), nullable=True)
    
    # PS26/2 (FCA) and PS7/26 (PRA) classification
    fca_ps26_2_applicable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pra_ps7_26_applicable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    material_impact_threshold_met: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reporting_route = Column(String(20), nullable=True)  # 'standard' or 'enhanced'
    reported_to_regulator_at = Column(DateTime(timezone=True), nullable=True)
    
    # Lifecycle
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="detected")
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    root_cause = Column(String(1000), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    __table_args__ = (
        CheckConstraint("severity IN ('critical', 'major', 'minor')", name="ck_ir_severity"),
        CheckConstraint("reporting_route IS NULL OR reporting_route IN ('standard', 'enhanced')", name="ck_ir_route"),
        CheckConstraint("status IN ('detected', 'investigating', 'reported', 'resolved', 'closed')", name="ck_ir_status"),
        Index("ix_ir_incident_ref", "incident_reference"),
        Index("ix_ir_detected_at", "detected_at"),
        Index("ix_ir_applicable", "fca_ps26_2_applicable", "pra_ps7_26_applicable"),
    )
