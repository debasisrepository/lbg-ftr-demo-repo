"""
Device registrations model (table 4.4).
Requirement: FR-AUTH-003
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


class DeviceRegistration(Base):
    """Seeded pre-registered synthetic devices."""
    __tablename__ = "device_registrations"
    
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    customer_profile_ref_id = Column(Uuid, ForeignKey("customer_profile_refs.id"), nullable=False, index=True)
    device_identifier_hash = Column(String(64), nullable=False, index=True)
    mobile_platform = Column(String(8), nullable=False)
    registration_status = Column(String(12), nullable=False, default="active")
    ciam_subject_reference = Column(String(128), nullable=False)
    registered_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    __table_args__ = (
        CheckConstraint("mobile_platform IN ('iOS','Android')", name="ck_dr_platform"),
        CheckConstraint("registration_status IN ('active','revoked','suspended')", name="ck_dr_status"),
        UniqueConstraint("customer_profile_ref_id", "device_identifier_hash", name="uq_dr_customer_device"),
    )
