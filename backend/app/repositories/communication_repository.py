"""Communication repository."""
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.communication import CommunicationRecord, NotificationRecord


class CommunicationRepository:
    """Repository for communication and notification records."""

    def __init__(self, session: Session):
        self.session = session

    def by_source_event(self, source_event_id: UUID) -> CommunicationRecord | None:
        """Get communication record by source event ID."""
        stmt = select(CommunicationRecord).where(
            CommunicationRecord.source_event_id == source_event_id
        )
        return self.session.scalars(stmt).first()

    def by_token_hash(self, token_hash: str) -> NotificationRecord | None:
        """Get notification record by deep link token hash."""
        stmt = select(NotificationRecord).where(
            NotificationRecord.deep_link_token_hash == token_hash
        )
        return self.session.scalars(stmt).first()

    def page_for_customer(
        self,
        customer_party_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[list[NotificationRecord], int]:
        """Get paginated notifications for a customer."""
        stmt = select(NotificationRecord).where(
            NotificationRecord.customer_party_id == customer_party_id
        )
        
        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.session.scalar(count_stmt) or 0
        
        # Apply sorting and pagination
        stmt = stmt.order_by(
            NotificationRecord.created_at.desc()
        ).limit(limit).offset(offset)
        
        notifications = list(self.session.scalars(stmt))
        return notifications, total

    def create_communication(self, record: CommunicationRecord) -> CommunicationRecord:
        """Create a communication record."""
        self.session.add(record)
        self.session.flush()
        return record

    def create_notification(self, record: NotificationRecord) -> NotificationRecord:
        """Create a notification record."""
        self.session.add(record)
        self.session.flush()
        return record

    def update_notification(self, record: NotificationRecord) -> NotificationRecord:
        """Update a notification record."""
        self.session.flush()
        return record
