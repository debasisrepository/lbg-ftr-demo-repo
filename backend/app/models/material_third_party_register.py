"""
Material third-party register for operational resilience requirements.
Requirement: BR-OPS-009, TPR-01, TPR-02, TPR-03
Release 2: Material third-party register with exit plans
"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Index,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MaterialThirdPartyRegister(Base):
    """Register of material third parties with exit plan status."""
    __tablename__ = "material_third_party_register"
    
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    third_party_name: Mapped[str] = mapped_column(String(160), nullable=False)
    service_category: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., 'cloud', 'cop_provider', 'fraud_engine', 'push_notification'
    service_description: Mapped[str] = mapped_column(String(500), nullable=False)
    criticality: Mapped[str] = mapped_column(String(20), nullable=False)  # 'critical', 'important', 'standard'
    contract_start_date = Column(Date, nullable=True)
    contract_review_date = Column(Date, nullable=True)
    exit_plan_status: Mapped[str] = mapped_column(String(20), nullable=False, default="required")  # 'required', 'draft', 'approved', 'tested'
    exit_plan_last_tested = Column(Date, nullable=True)
    regulatory_reportable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    __table_args__ = (
        CheckConstraint("criticality IN ('critical', 'important', 'standard')", name="ck_mtpr_criticality"),
        CheckConstraint("exit_plan_status IN ('required', 'draft', 'approved', 'tested')", name="ck_mtpr_exit_plan"),
        Index("ix_mtpr_third_party_name", "third_party_name"),
        Index("ix_mtpr_criticality", "criticality"),
    )
