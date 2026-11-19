from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import ChallengeMethod, ChallengeStatus, ChallengeType
from app.database import Base


class StepUpChallenge(Base):
    """Step-up authentication challenge record."""
    __tablename__ = "step_up_challenge"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    auth_session_id: Mapped[int] = mapped_column(Integer, ForeignKey("auth_session.id"), nullable=False)
    payment_instruction_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    challenge_type: Mapped[str] = mapped_column(String(30), nullable=False)
    method: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=ChallengeStatus.PENDING.value)
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    attempts_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    dynamic_link_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    challenge_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_step_up_challenge_auth_session_id", "auth_session_id"),
        Index("ix_step_up_challenge_payment_instruction_id", "payment_instruction_id"),
        Index("ix_step_up_challenge_status", "status"),
    )
