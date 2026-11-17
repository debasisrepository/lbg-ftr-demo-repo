"""History repository for case events."""
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit import CaseEvent


class HistoryRepository:
    """Repository for case event history."""

    def __init__(self, session: Session):
        self.session = session

    def add_event(self, event: CaseEvent) -> CaseEvent:
        """Add a new case event."""
        self.session.add(event)
        self.session.flush()
        return event

    def next_sequence(self, case_id: UUID) -> int:
        """Get the next sequence number for a case."""
        stmt = select(func.coalesce(func.max(CaseEvent.sequence_number), 0) + 1).where(
            CaseEvent.case_id == case_id
        )
        return self.session.scalar(stmt) or 1

    def page_for_case(
        self,
        case_id: UUID,
        limit: int = 50,
        offset: int = 0,
        customer_visible_only: bool = True
    ) -> tuple[list[CaseEvent], int]:
        """Get paginated events for a case."""
        stmt = select(CaseEvent).where(CaseEvent.case_id == case_id)
        
        if customer_visible_only:
            stmt = stmt.where(CaseEvent.customer_visible_flag == True)  # noqa: E712
        
        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.session.scalar(count_stmt) or 0
        
        # Apply ordering and pagination
        stmt = stmt.order_by(CaseEvent.sequence_number.desc()).limit(limit).offset(offset)
        
        events = list(self.session.scalars(stmt))
        return events, total
