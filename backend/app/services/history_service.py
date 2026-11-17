"""History service for case event history."""
from uuid import UUID

from app.models.audit import CaseEvent
from app.repositories.history_repository import HistoryRepository


class HistoryService:
    """Service for building case history with is_superseded computation."""

    def __init__(self, repo: HistoryRepository):
        self.repo = repo

    def build_pages(
        self,
        case_id: UUID,
        limit: int = 20,
        offset: int = 0,
        event_type: str | None = None,
        customer_visible_only: bool = False
    ) -> tuple[list[dict], int]:
        """Build paginated history with is_superseded flag.

        Args:
            case_id: Case UUID
            limit: Page size
            offset: Page offset
            event_type: Optional event type filter
            customer_visible_only: If True, filter to customer_visible_flag=TRUE

        Returns:
            Tuple of (event_dicts, total_count) where event_dicts include is_superseded
        """
        # Get events from repository
        events, total = self.repo.page_for_case(
            case_id=case_id,
            limit=limit,
            offset=offset,
            customer_visible_only=customer_visible_only
        )

        # Filter by event_type if specified (post-filter for now)
        if event_type:
            events = [e for e in events if e.event_type == event_type]
            total = len(events)

        # Compute is_superseded for each event
        event_dicts = []
        for event in events:
            event_dict = {
                "id": str(event.id),
                "case_id": str(event.case_id),
                "sequence_number": event.sequence_number,
                "event_type": event.event_type,
                "event_timestamp": event.event_timestamp,
                "summary_text": event.summary_text,
                "event_payload_json": event.event_payload_json,
                "customer_visible_flag": event.customer_visible_flag,
                "actor_type": event.actor_type,
                "actor_reference": event.actor_reference,
                "basis_type": event.basis_type,
                "basis_reference": event.basis_reference,
                "correlation_id": event.correlation_id,
                "created_at": event.created_at,
                "is_superseded": self.compute_is_superseded(event, events)
            }
            event_dicts.append(event_dict)

        return event_dicts, total

    def compute_is_superseded(self, event: CaseEvent, all_events: list[CaseEvent]) -> bool:
        """Compute whether an OwnerChanged or ExpectedByChanged event is superseded.

        An event is superseded if a later event of the same type exists for the same case.

        Args:
            event: The event to check
            all_events: All events in the current page

        Returns:
            True if superseded, False otherwise
        """
        if event.event_type not in ["OwnerChanged", "ExpectedByChanged"]:
            return False

        # Check if there's a later event of the same type in the current page
        for other in all_events:
            if (other.event_type == event.event_type and
                other.case_id == event.case_id and
                other.sequence_number > event.sequence_number):
                return True

        return False
