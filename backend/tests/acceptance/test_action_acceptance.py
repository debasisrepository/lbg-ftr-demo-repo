"""Acceptance tests for protected actions with SCA (FR-029, FR-032)."""
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from app.adapters.identity_adapter import IdentityAdapter
from app.adapters.management_api_adapter import ManagementApiAdapter
from app.core.clock import Clock
from app.models.actions import ProtectedActionRequest
from app.models.case import Case, CaseStatusProjection
from app.models.ownership import CaseOwnership, ExpectedByCommitment
from app.models.audit import CaseEvent
from app.repositories.action_repository import ActionRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.case_repository import CaseRepository
from app.repositories.history_repository import HistoryRepository
from app.services.action_service import ActionService
from app.services.audit_service import AuditService


@pytest.fixture
def action_service(db_session: Session) -> ActionService:
    """Create action service with real dependencies."""
    action_repo = ActionRepository(db_session)
    case_repo = CaseRepository(db_session)
    history_repo = HistoryRepository(db_session)
    audit_repo = AuditRepository(db_session)
    
    audit_service = AuditService(audit_repo, Clock())
    identity_adapter = IdentityAdapter()
    management_api_adapter = ManagementApiAdapter()
    
    return ActionService(
        action_repo=action_repo,
        case_repo=case_repo,
        history_repo=history_repo,
        audit_service=audit_service,
        identity_adapter=identity_adapter,
        management_api_adapter=management_api_adapter,
        clock=Clock()
    )


@pytest.fixture
def test_case(db_session: Session) -> Case:
    """Create a test case with full projections."""
    now = datetime.now(timezone.utc)
    case_id = uuid.uuid4()
    
    case = Case(
        id=case_id,
        case_reference="CP-ACCTEST1",
        customer_party_id="CUST-ACC-001",
        brand="lloyds",
        issue_type="card_declined",
        classification_source="eligibility_rule",
        issue_title="Card Declined",
        issue_summary="Acceptance test case",
        origin_channel="mobile_app",
        current_lifecycle_state="case_created",
        current_status_code="received",
        current_status_label="Received",
        opened_at=now,
        created_at=now,
        updated_at=now
    )
    db_session.add(case)
    
    projection = CaseStatusProjection(
        id=uuid.uuid4(),
        case_id=case_id,
        status_code="received",
        status_label="Received",
        lifecycle_state="case_created",
        status_icon="in_progress",
        status_color="blue",
        customer_facing_text="Your case has been received.",
        next_step_text="We're reviewing your case.",
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(projection)
    
    ownership = CaseOwnership(
        id=uuid.uuid4(),
        case_id=case_id,
        owner_team_code="INTAKE_DEFAULT",
        owner_semantic_label="Intake Team",
        owner_display_name="Intake & Triage",
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(ownership)
    
    expected_by = ExpectedByCommitment(
        id=uuid.uuid4(),
        case_id=case_id,
        commitment_state="under_review",
        customer_explanatory_text="We're reviewing the timing.",
        confidence_basis="initial",
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(expected_by)
    
    db_session.commit()
    return case


def test_protected_action_requires_sca_success(
    action_service: ActionService,
    test_case: Case,
    db_session: Session
):
    """AC: A protected action cannot complete without successful SCA."""
    # Start protected action (SCA invoked)
    start_result = action_service.start(
        customer_party_id=test_case.customer_party_id,
        case_reference=test_case.case_reference,
        action_type="stop_card",
        action_domain="card",
        action_payload={"card_last_four": "1234"},
        correlation_id="acc-test-001"
    )
    db_session.commit()
    
    action_id = uuid.UUID(start_result["action_id"])
    
    # Verify action is pending SCA
    action_repo = ActionRepository(db_session)
    action = action_repo.get_for_case(action_id, test_case.customer_party_id)
    assert action is not None
    assert action.request_status == "pending_sca"
    assert action.requires_sca_flag is True
    
    # Complete with SCA success
    outcome_result = action_service.report_outcome(
        customer_party_id=test_case.customer_party_id,
        case_reference=test_case.case_reference,
        action_id=action_id,
        sca_outcome="success",
        sca_verification_token="TOKEN-SUCCESS",
        correlation_id="acc-test-002"
    )
    db_session.commit()
    
    # Verify action is released
    assert outcome_result["request_status"] == "released"
    assert outcome_result["management_api_reference"] is not None


def test_protected_action_sca_failure_shows_fallback(
    action_service: ActionService,
    test_case: Case,
    db_session: Session
):
    """AC: If SCA fails or is abandoned, action does not execute and customer sees fallback guidance."""
    # Start protected action
    start_result = action_service.start(
        customer_party_id=test_case.customer_party_id,
        case_reference=test_case.case_reference,
        action_type="stop_card",
        action_domain="card",
        action_payload={"card_last_four": "5678"},
        correlation_id="acc-test-003"
    )
    db_session.commit()
    
    action_id = uuid.UUID(start_result["action_id"])
    
    # Complete with SCA failure
    outcome_result = action_service.report_outcome(
        customer_party_id=test_case.customer_party_id,
        case_reference=test_case.case_reference,
        action_id=action_id,
        sca_outcome="failed",
        sca_verification_token="TOKEN-FAILED",
        correlation_id="acc-test-004"
    )
    db_session.commit()
    
    # Verify action is not executed
    assert outcome_result["request_status"] == "not_executed"
    assert outcome_result["management_api_reference"] is None
    
    # Verify fallback guidance is provided
    assert outcome_result["fallback_guidance_text"] is not None
    assert len(outcome_result["fallback_guidance_text"]) > 0
    # Guidance should mention calling or visiting
    guidance_lower = outcome_result["fallback_guidance_text"].lower()
    assert any(word in guidance_lower for word in ["call", "phone", "branch", "visit"])


def test_protected_action_sca_abandoned_shows_fallback(
    action_service: ActionService,
    test_case: Case,
    db_session: Session
):
    """AC: If SCA is abandoned, action does not execute and customer sees fallback guidance."""
    # Start protected action
    start_result = action_service.start(
        customer_party_id=test_case.customer_party_id,
        case_reference=test_case.case_reference,
        action_type="transfer",
        action_domain="money",
        action_payload={"amount": "100.00", "to_account": "12345678"},
        correlation_id="acc-test-005"
    )
    db_session.commit()
    
    action_id = uuid.UUID(start_result["action_id"])
    
    # Complete with SCA abandoned
    outcome_result = action_service.report_outcome(
        customer_party_id=test_case.customer_party_id,
        case_reference=test_case.case_reference,
        action_id=action_id,
        sca_outcome="abandoned",
        sca_verification_token="TOKEN-ABANDONED",
        correlation_id="acc-test-006"
    )
    db_session.commit()
    
    # Verify action is not executed
    assert outcome_result["request_status"] == "not_executed"
    assert outcome_result["management_api_reference"] is None
    
    # Verify fallback guidance is provided
    assert outcome_result["fallback_guidance_text"] is not None


def test_system_records_sca_invocation_and_outcome(
    action_service: ActionService,
    test_case: Case,
    db_session: Session
):
    """AC: The system records whether SCA was invoked and the resulting action state."""
    # Start protected action
    start_result = action_service.start(
        customer_party_id=test_case.customer_party_id,
        case_reference=test_case.case_reference,
        action_type="stop_card",
        action_domain="card",
        action_payload={"card_last_four": "9999"},
        correlation_id="acc-test-007"
    )
    db_session.commit()
    
    action_id = uuid.UUID(start_result["action_id"])
    
    # Verify SCA invocation is recorded
    action_repo = ActionRepository(db_session)
    action = action_repo.get_for_case(action_id, test_case.customer_party_id)
    assert action.sca_invoked_at is not None
    assert action.sca_outcome == "not_invoked"  # Before outcome reported
    
    # Complete with SCA success
    action_service.report_outcome(
        customer_party_id=test_case.customer_party_id,
        case_reference=test_case.case_reference,
        action_id=action_id,
        sca_outcome="success",
        sca_verification_token="TOKEN-RECORD",
        correlation_id="acc-test-008"
    )
    db_session.commit()
    
    # Verify SCA outcome and action state are recorded
    db_session.expire_all()
    action = action_repo.get_for_case(action_id, test_case.customer_party_id)
    assert action.sca_outcome == "success"
    assert action.sca_completed_at is not None
    assert action.request_status == "released"
    assert action.completed_at is not None


def test_history_records_protected_action_events(
    action_service: ActionService,
    test_case: Case,
    db_session: Session
):
    """AC: Case history records ProtectedActionRequested and ProtectedActionOutcome events."""
    history_repo = HistoryRepository(db_session)
    
    # Get initial event count
    initial_events, _ = history_repo.page_for_case(test_case.id, limit=100, offset=0)
    initial_count = len(initial_events)
    
    # Start protected action
    start_result = action_service.start(
        customer_party_id=test_case.customer_party_id,
        case_reference=test_case.case_reference,
        action_type="stop_card",
        action_domain="card",
        action_payload={"card_last_four": "1111"},
        correlation_id="acc-test-009"
    )
    db_session.commit()
    
    # Verify ProtectedActionRequested event
    events_after_start, _ = history_repo.page_for_case(test_case.id, limit=100, offset=0)
    assert len(events_after_start) == initial_count + 1
    
    latest_event = events_after_start[0]  # Most recent first
    assert latest_event.event_type == "ProtectedActionRequested"
    assert latest_event.customer_visible_flag is True
    
    # Complete with SCA success
    action_id = uuid.UUID(start_result["action_id"])
    action_service.report_outcome(
        customer_party_id=test_case.customer_party_id,
        case_reference=test_case.case_reference,
        action_id=action_id,
        sca_outcome="success",
        sca_verification_token="TOKEN-HISTORY",
        correlation_id="acc-test-010"
    )
    db_session.commit()
    
    # Verify ProtectedActionOutcome event
    events_after_outcome, _ = history_repo.page_for_case(test_case.id, limit=100, offset=0)
    assert len(events_after_outcome) == initial_count + 2
    
    outcome_event = events_after_outcome[0]  # Most recent first
    assert outcome_event.event_type == "ProtectedActionOutcome"
    assert outcome_event.customer_visible_flag is True
    assert outcome_event.event_payload_json["sca_outcome"] == "success"
    assert outcome_event.event_payload_json["request_status"] == "released"


def test_get_history_shows_complete_timeline(
    action_service: ActionService,
    test_case: Case,
    db_session: Session
):
    """AC: GET /history returns chronological events including protected action events."""
    history_repo = HistoryRepository(db_session)
    case_repo = CaseRepository(db_session)
    
    # Perform a complete protected action flow
    start_result = action_service.start(
        customer_party_id=test_case.customer_party_id,
        case_reference=test_case.case_reference,
        action_type="stop_card",
        action_domain="card",
        action_payload={"card_last_four": "2222"},
        correlation_id="acc-test-011"
    )
    db_session.commit()
    
    action_id = uuid.UUID(start_result["action_id"])
    action_service.report_outcome(
        customer_party_id=test_case.customer_party_id,
        case_reference=test_case.case_reference,
        action_id=action_id,
        sca_outcome="success",
        sca_verification_token="TOKEN-TIMELINE",
        correlation_id="acc-test-012"
    )
    db_session.commit()
    
    # Get full history
    events, total = history_repo.page_for_case(test_case.id, limit=100, offset=0)
    
    # Verify events are in chronological order (newest first in page, but sequence numbers ascending)
    event_types = [e.event_type for e in reversed(events)]  # Reverse to get chronological order
    
    # Should contain ProtectedActionRequested and ProtectedActionOutcome
    assert "ProtectedActionRequested" in event_types
    assert "ProtectedActionOutcome" in event_types
    
    # Verify sequence numbers are ordered
    sequence_numbers = [e.sequence_number for e in events]
    assert sequence_numbers == sorted(sequence_numbers, reverse=True)  # Descending in page


def test_get_action_status_endpoint(
    action_service: ActionService,
    test_case: Case,
    db_session: Session
):
    """AC: GET /actions/{action_id} retrieves current action state."""
    # Start and complete action
    start_result = action_service.start(
        customer_party_id=test_case.customer_party_id,
        case_reference=test_case.case_reference,
        action_type="stop_card",
        action_domain="card",
        action_payload={"card_last_four": "3333"},
        correlation_id="acc-test-013"
    )
    db_session.commit()
    
    action_id = uuid.UUID(start_result["action_id"])
    
    # Get status while pending
    action_repo = ActionRepository(db_session)
    action_pending = action_repo.get_for_case(action_id, test_case.customer_party_id)
    assert action_pending is not None
    assert action_pending.request_status == "pending_sca"
    assert action_pending.sca_outcome == "not_invoked"
    
    # Complete action
    action_service.report_outcome(
        customer_party_id=test_case.customer_party_id,
        case_reference=test_case.case_reference,
        action_id=action_id,
        sca_outcome="success",
        sca_verification_token="TOKEN-STATUS",
        correlation_id="acc-test-014"
    )
    db_session.commit()
    
    # Get status after completion
    db_session.expire_all()
    action_completed = action_repo.get_for_case(action_id, test_case.customer_party_id)
    assert action_completed is not None
    assert action_completed.request_status == "released"
    assert action_completed.sca_outcome == "success"
    assert action_completed.management_api_reference is not None
