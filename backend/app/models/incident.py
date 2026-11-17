"""Service status and lifeline models."""
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.database import Base


class ServiceIncident(Base):
    """Service incident record."""

    __tablename__ = "service_incidents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    incident_reference: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    incident_state: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    affected_service_code: Mapped[str] = mapped_column(String(100), nullable=False)
    customer_impact_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, onupdate=lambda: datetime.now(datetime.now().tzinfo or None)
    )

    __table_args__ = (
        CheckConstraint(
            "incident_state IN ('declared', 'monitoring', 'resolved')",
            name="ck_incident_state",
        ),
        Index("ix_incident_state_resolved", incident_state, resolved_at),
    )


class ServiceStatusPublication(Base):
    """Service status publication."""

    __tablename__ = "service_status_publications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    publication_state: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    headline_text: Mapped[str] = mapped_column(String(500), nullable=False)
    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    affected_journeys_json: Mapped[list] = mapped_column(JSON().with_variant(JSONB(), "postgresql"), nullable=False)
    content_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "publication_state IN ('active', 'withdrawn')",
            name="ck_publication_state",
        ),
        Index("ix_status_pub_incident_active", incident_id, publication_state),
    )


class LifelineGuidance(Base):
    """Lifeline guidance."""

    __tablename__ = "lifeline_guidance"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    guidance_title: Mapped[str] = mapped_column(String(500), nullable=False)
    guidance_content: Mapped[str] = mapped_column(Text, nullable=False)
    guidance_type: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, onupdate=lambda: datetime.now(datetime.now().tzinfo or None)
    )

    __table_args__ = (
        CheckConstraint(
            "guidance_type IN ('fallback', 'safe_action', 'phone')",
            name="ck_guidance_type",
        ),
    )
