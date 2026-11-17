"""Integration tests for protected actions with SCA."""
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from app.adapters.identity_adapter import IdentityAdapter
from app.adapters.management_api_adapter import ManagementApiAdapter
from app.core.clock import Clock
from app.core.errors import NotFoundError, ValidationError
from app.models.case import Case, CaseAnchorLink, CaseStatusProjection
from app.models.ownership import CaseOwnership, ExpectedByCommitment
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
    """Create a test case."""
    now = datetime.now(timezone.utc)
    case_id = uuid.uuid4()
    
    case = Case(
        id=case_id,
        case_reference="CP-INTTEST1",
        customer_party_id="CUST-INT-001",
        brand="lloyds",
        issue_type="card_declined",
        classification_source="eligibility_rule",
        issue_title="Card Declined",
        issue_summary="Test case for protected actions",
        origin_channel="mobile_app",
        current_lifecycle_state="case_created",
        current_status_code="received",
        current_status_label="Received",
        opened_at=now,
        created_at=now,
        updated_at=now
    )
    db_session.add(case)
    
    # Add required projections
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


def test_start_and_complete_protected_action_success(
    action_service: ActionService,
    test_case: Case,
    db_session: Session
):
    """Test full flow: start action, report success outcome."""
    # Start protected action
    start_result = action_service.start(
        customer_party_id=test_case.customer_party_id,
        case_reference=test_case.case_reference,
        action_type="stop_card",
        action_domain="card",
        action_payload={"card_last_four": "1234", "reason": "lost"},
        correlation_id="int-test-001"
    )
    
    db_session.commit()
    
    # Verify start result
    assert "action_id" in start_result
    assert "sca_challenge_reference" in start_result
    action_id = uuid.UUID(start_result["action_id"])
    
    # Report SCA success outcome
    outcome_result = action_service.report_outcome(
        customer_party_id=test_case.customer_party_id,
        case_reference=test_case.case_reference,
        action_id=action_id,
        sca_outcome="success",
        sca_verification_token="INT-TOKEN-123",
        correlation_id="int-test-002"
    )
    
    db_session.commit()
    
    # Verify outcome result
    assert outcome_result["request_status"] == "released"
    assert outcome_result["sca_outcome"] == "success"
    assert outcome_result["management_api_reference"] is not None
    assert outcome_result["completed_at"] is not None


def test_start_and_complete_protected_action_failed(
    action_service: ActionService,
    test_case: Case,
    db_session: Session
):
    """Test full flow: start action, report failed outcome."""
    # Start protected action
    start_result = action_service.start(
        customer_party_id=test_case.customer_party_id,
        case_reference=test_case.case_reference,
        action_type="stop_card",
        action_domain="card",
        action_payload={"card_last_four": "5678", "reason": "stolen"},
        correlation_id="int-test-003"
    )
    
    db_session.commit()
    
    action_id = uuid.UUID(start_result["action_id"])
    
    # Report SCA failed outcome
    outcome_result = action_service.report_outcome(
        customer_party_id=test_case.customer_party_id,
        case_reference=test_case.case_reference,
        action_id=action_id,
        sca_outcome="failed",
        sca_verification_token="INT-TOKEN-456",
        correlation_id="int-test-004"
    )
    
    db_session.commit()
    
    # Verify outcome result
    assert outcome_result["request_status"] == "not_executed"
    assert outcome_result["sca_outcome"] == "failed"
    assert outcome_result["fallback_guidance_text"] is not None
    assert "call us" in outcome_result["fallback_guidance_text"].lower()


def test_start_protected_action_case_not_found(
    action_service: ActionService
):
    """Test error when case not found."""
    with pytest.raises(NotFoundError, match="Case CP-NOTFOUND not found"):
        action_service.start(
            customer_party_id="CUST-WRONG",
            case_reference="CP-NOTFOUND",
            action_type="stop_card",
            action_domain="card",
            action_payload={"card_last_four": "9999"},
            correlation_id="int-test-005"
        )


def test_report_outcome_action_not_found(
    action_service: ActionService,
    test_case: Case
):
    """Test error when action not found."""
    with pytest.raises(NotFoundError, match="Action .* not found"):
        action_service.report_outcome(
            customer_party_id=test_case.customer_party_id,
            case_reference=test_case.case_reference,
            action_id=uuid.uuid4(),
            sca_outcome="success",
            sca_verification_token="TOKEN",
            correlation_id="int-test-006"
        )


def test_report_outcome_idempotent(
    action_service: ActionService,
    test_case: Case,
    db_session: Session
):
    """Test idempotent behavior when reporting same outcome twice."""
    # Start and complete action
    start_result = action_service.start(
        customer_party_id=test_case.customer_party_id,
        case_reference=test_case.case_reference,
        action_type="stop_card",
        action_domain="card",
        action_payload={"card_last_four": "4321"},
        correlation_id="int-test-007"
    )
    db_session.commit()
    
    action_id = uuid.UUID(start_result["action_id"])
    
    # Report outcome first time
    first_result = action_service.report_outcome(
        customer_party_id=test_case.customer_party_id,
        case_reference=test_case.case_reference,
        action_id=action_id,
        sca_outcome="success",
        sca_verification_token="TOKEN-FIRST",
        correlation_id="int-test-008"
    )
    db_session.commit()
    
    # Report same outcome again (idempotent)
    second_result = action_service.report_outcome(
        customer_party_id=test_case.customer_party_id,
        case_reference=test_case.case_reference,
        action_id=action_id,
        sca_outcome="success",  # Same outcome
        sca_verification_token="TOKEN-SECOND",
        correlation_id="int-test-009"
    )
    db_session.commit()
    
    # Verify both results are identical
    assert second_result["request_status"] == first_result["request_status"]
    assert second_result["sca_outcome"] == first_result["sca_outcome"]
    assert second_result["management_api_reference"] == first_result["management_api_reference"]
