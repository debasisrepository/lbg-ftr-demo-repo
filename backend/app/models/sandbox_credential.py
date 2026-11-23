"""
Sandbox credentials model (table 4.2).
Requirement: FR-AUTH-003
"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Uuid,
)

from app.database import Base


class SandboxCredential(Base):
    """Working-tier synthetic passcode hashes for sandbox CIAM adapter."""
    __tablename__ = "sandbox_credentials"
    
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    customer_profile_ref_id = Column(Uuid, ForeignKey("customer_profile_refs.id"), nullable=False, unique=True)
    passcode_hash = Column(String(128), nullable=False)
    failed_attempt_count = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    __table_args__ = (
        CheckConstraint("failed_attempt_count >= 0", name="ck_sc_failed_count"),
    )
