"""
Entitlement decisions model (table 4.7).
Requirement: FR-ACCT-001, FR-PAY-001, FR-PAY-002
"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    String,
    Uuid,
)

from app.database import Base


class EntitlementDecision(Base):
    """Append-only entitlement decision provenance."""
    __tablename__ = "entitlement_decisions"
    
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    customer_profile_ref_id = Column(Uuid, ForeignKey("customer_profile_refs.id"), nullable=False, index=True)
    resource_type = Column(String(16), nullable=False)
    resource_reference = Column(String(64), nullable=False)
    decision_outcome = Column(String(12), nullable=False)
    decision_reason_code = Column(String(40), nullable=True)
    source_service_reference = Column(String(64), nullable=False)
    correlation_id = Column(String(64), nullable=False, index=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), index=True)
    
    __table_args__ = (
        CheckConstraint("resource_type IN ('account','payee','payment')", name="ck_ed_resource_type"),
        CheckConstraint("decision_outcome IN ('allow','deny','conditional')", name="ck_ed_outcome"),
    )
