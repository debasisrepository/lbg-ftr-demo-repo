from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import JourneyOutcomeCode, JourneyStep
from app.database import Base


class JourneyEvent(Base):
    """Journey event record for observability."""
    __tablename__ = "journey_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    correlation_id: Mapped[str] = mapped_column(String(100), nullable=False)
    auth_session_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("auth_session.id"), nullable=True)
    profile_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("user_profile.id"), nullable=True)
    journey_step: Mapped[str] = mapped_column(String(30), nullable=False)
    outcome_code: Mapped[str] = mapped_column(String(30), nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    event_payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_journey_event_correlation_id", "correlation_id"),
        Index("ix_journey_event_auth_session_id", "auth_session_id"),
        Index("ix_journey_event_profile_id", "profile_id"),
        Index("ix_journey_event_journey_step", "journey_step"),
        Index("ix_journey_event_occurred_at", "occurred_at"),
    )
