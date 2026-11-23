"""
Sandbox entitlements model (table 4.3).
Requirement: FR-ACCT-001, FR-PAY-001, FR-PAY-002
Release 2: BR-PAY-012 (business payment entitlements: view, pay, approve)
"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    Uuid,
)

from app.database import Base


class SandboxEntitlement(Base):
    """Working-tier seed of entitlement service answers."""
    __tablename__ = "sandbox_entitlements"
    
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    customer_profile_ref_id = Column(Uuid, ForeignKey("customer_profile_refs.id"), nullable=False, index=True)
    resource_type = Column(String(16), nullable=False)
    resource_reference = Column(String(64), nullable=False)
    decision = Column(String(12), nullable=False)
    entitlement_type = Column(String(16), nullable=True, default="view")  # Release 2: view, pay, approve
    reason_code = Column(String(40), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    __table_args__ = (
        CheckConstraint("resource_type IN ('account','payee','payment')", name="ck_se_resource_type"),
        CheckConstraint("decision IN ('allow','deny','conditional')", name="ck_se_decision"),
        CheckConstraint("entitlement_type IS NULL OR entitlement_type IN ('view','pay','approve')", name="ck_se_entitlement_type"),
        UniqueConstraint("customer_profile_ref_id", "resource_type", "resource_reference", name="uq_se_customer_resource"),
    )
