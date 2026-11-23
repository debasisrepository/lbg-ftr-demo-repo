"""
Customer profile reference model (table 4.1).
Requirement: FR-AUTH-006, FR-ACCT-001, FR-PAY-001
Release 2: BR-ACCT-002, BR-ACCT-003 (business profiles)
"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, String, Uuid

from app.database import Base


class CustomerProfileRef(Base):
    """Customer profile reference and in-scope personal profile."""
    __tablename__ = "customer_profile_refs"
    
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    customer_party_id = Column(String(64), nullable=False, unique=True)
    # Release 2: Allow multiple profiles per identity (personal + business) - removed unique constraint
    ciam_subject_reference = Column(String(128), nullable=False, unique=False, index=True)
    display_name = Column(String(120), nullable=False)
    profile_type = Column(String(16), nullable=False, default="personal")
    business_name = Column(String(160), nullable=True)  # Release 2: BR-ACCT-003
    release_scope_status = Column(String(16), nullable=False, default="in_scope")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    __table_args__ = (
        CheckConstraint("profile_type IN ('personal', 'business')", name="ck_cpr_profile_type"),
        CheckConstraint("release_scope_status IN ('in_scope','out_of_scope')", name="ck_cpr_release_scope"),
    )
