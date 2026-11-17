import logging
from datetime import timedelta
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from app.core.clock import Clock
from app.services.case.models import CaseRecord, CaseTimelineEvent
from app.core.ids import IdGenerator

logger = logging.getLogger(__name__)


class HeartbeatScanner:
    SILENCE_THRESHOLD_HOURS = 48
    SCAN_BUFFER_HOURS = 8

    def __init__(self, db: Session):
        self.db = db

    def scan_silent_cases(self) -> list[str]:
        now = Clock.utc_now()
        threshold = now - timedelta(hours=self.SILENCE_THRESHOLD_HOURS - self.SCAN_BUFFER_HOURS)

        open_statuses = ["new", "assigned", "in_progress", "awaiting_customer", "awaiting_internal", "reopened"]
        stmt = select(CaseRecord).where(
            and_(
                CaseRecord.status.in_(open_statuses),
                CaseRecord.last_heartbeat_at < threshold,
            )
        )
        cases = self.db.execute(stmt).scalars().all()

        updated_case_refs = []
        for case in cases:
            self._create_heartbeat_update(case)
            case.last_heartbeat_at = now
            updated_case_refs.append(case.case_ref)

        if updated_case_refs:
            self.db.commit()
            logger.info(f"Heartbeat updates for {len(updated_case_refs)} cases: {updated_case_refs}")

        return updated_case_refs

    def _create_heartbeat_update(self, case: CaseRecord):
        update_text = (
            f"Your case is being worked on. "
            f"Owner: {case.owner_team_display or 'Customer Support Team'}. "
            f"Expected update by: {case.expected_by_at.strftime('%Y-%m-%d %H:%M') if case.expected_by_at else 'soon'}."
        )

        timeline_event = CaseTimelineEvent(
            id=IdGenerator.uuid4(),
            case_id=case.id,
            domain_event_id=None,
            event_type="heartbeat_update",
            summary_text=update_text,
            actor_display="System",
            occurred_at=Clock.utc_now(),
        )
        self.db.add(timeline_event)
