"""Continuity repository."""
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.continuity import ChannelHandoff, ContinuityContext


class ContinuityRepository:
    """Repository for continuity operations."""

    def __init__(self, session: Session):
        self.session = session

    def current_package(self, case_id: UUID) -> ContinuityContext | None:
        """Get the current continuity package for a case."""
        stmt = select(ContinuityContext).where(
            ContinuityContext.case_id == case_id,
            ContinuityContext.is_current == True  # noqa: E712
        )
        return self.session.scalars(stmt).first()

    def handoffs_for_case(self, case_id: UUID, limit: int = 20) -> list[ChannelHandoff]:
        """Get recent handoffs for a case."""
        stmt = (
            select(ChannelHandoff)
            .where(ChannelHandoff.case_id == case_id)
            .order_by(ChannelHandoff.handoff_timestamp.desc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt))

    def insert_context(self, context: ContinuityContext) -> ContinuityContext:
        """Insert a new continuity context."""
        self.session.add(context)
        self.session.flush()
        return context

    def insert_handoff(self, handoff: ChannelHandoff) -> ChannelHandoff:
        """Insert a new handoff record."""
        self.session.add(handoff)
        self.session.flush()
        return handoff

    def close_current_context(self, case_id: UUID, effective_to: datetime) -> None:
        """Close the current continuity context for a case."""
        stmt = select(ContinuityContext).where(
            ContinuityContext.case_id == case_id,
            ContinuityContext.is_current == True  # noqa: E712
        )
        current = self.session.scalars(stmt).first()
        if current:
            current.is_current = False
            current.effective_to = effective_to
