from datetime import timedelta
import uuid
from app.core.clock import Clock
from app.core.ids import IdGenerator
from app.services.case.models import CaseRecord, CaseTimelineEvent
from app.services.heartbeat.scanner import HeartbeatScanner


def test_heartbeat_scanner_detects_silent_cases(db_session):
    now = Clock.utc_now()
    old_heartbeat = now - timedelta(hours=41)
    heartbeat_before = old_heartbeat.replace(microsecond=0)

    case1 = CaseRecord(
        id=IdGenerator.uuid4(),
        case_ref="CP-2026-000001",
        customer_user_id=1,
        status="in_progress",
        origin_source="assistant_escalation",
        problem_statement="Test problem",
        owner_team_display="Support Team",
        last_update_at=now,
        last_heartbeat_at=old_heartbeat,
    )
    case2 = CaseRecord(
        id=IdGenerator.uuid4(),
        case_ref="CP-2026-000002",
        customer_user_id=1,
        status="in_progress",
        origin_source="assistant_escalation",
        problem_statement="Another problem",
        owner_team_display="Support Team",
        last_update_at=now,
        last_heartbeat_at=now,
    )
    db_session.add(case1)
    db_session.add(case2)
    db_session.commit()

    scanner = HeartbeatScanner(db_session)
    updated_refs = scanner.scan_silent_cases()

    assert "CP-2026-000001" in updated_refs
    assert "CP-2026-000002" not in updated_refs

    db_session.refresh(case1)
    assert case1.last_heartbeat_at.replace(tzinfo=None) > heartbeat_before.replace(tzinfo=None)

    timeline_events = db_session.query(CaseTimelineEvent).filter_by(case_id=case1.id).all()
    assert len(timeline_events) == 1
    assert timeline_events[0].event_type == "heartbeat_update"
    assert "being worked on" in timeline_events[0].summary_text


def test_heartbeat_scanner_ignores_closed_cases(db_session):
    now = Clock.utc_now()
    old_heartbeat = now - timedelta(hours=50)

    closed_case = CaseRecord(
        id=IdGenerator.uuid4(),
        case_ref="CP-2026-000003",
        customer_user_id=1,
        status="closed",
        origin_source="assistant_escalation",
        problem_statement="Closed problem",
        last_update_at=now,
        last_heartbeat_at=old_heartbeat,
    )
    db_session.add(closed_case)
    db_session.commit()

    scanner = HeartbeatScanner(db_session)
    updated_refs = scanner.scan_silent_cases()

    assert "CP-2026-000003" not in updated_refs


def test_heartbeat_update_includes_owner_and_expected_by(db_session):
    now = Clock.utc_now()
    old_heartbeat = now - timedelta(hours=45)
    expected_by = now + timedelta(hours=24)

    case = CaseRecord(
        id=IdGenerator.uuid4(),
        case_ref="CP-2026-000004",
        customer_user_id=1,
        status="assigned",
        origin_source="colleague_desktop",
        problem_statement="Test with expected by",
        owner_team_display="Fraud Team",
        expected_by_at=expected_by,
        last_update_at=now,
        last_heartbeat_at=old_heartbeat,
    )
    db_session.add(case)
    db_session.commit()

    scanner = HeartbeatScanner(db_session)
    scanner.scan_silent_cases()

    timeline_events = db_session.query(CaseTimelineEvent).filter_by(case_id=case.id).all()
    assert len(timeline_events) == 1
    assert "Fraud Team" in timeline_events[0].summary_text
    assert "2026" in timeline_events[0].summary_text


def test_heartbeat_scanner_handles_multiple_cases(db_session):
    now = Clock.utc_now()
    old_heartbeat = now - timedelta(hours=42)

    for i in range(5):
        case = CaseRecord(
            id=IdGenerator.uuid4(),
            case_ref=f"CP-2026-{str(i).zfill(6)}",
            customer_user_id=1,
            status="in_progress",
            origin_source="assistant_escalation",
            problem_statement=f"Problem {i}",
            last_update_at=now,
            last_heartbeat_at=old_heartbeat,
        )
        db_session.add(case)
    db_session.commit()

    scanner = HeartbeatScanner(db_session)
    updated_refs = scanner.scan_silent_cases()

    assert len(updated_refs) == 5
