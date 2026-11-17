"""Unit tests for ActionService."""
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock

import pytest

from app.core.errors import NotFoundError, ValidationError
from app.models.actions import ProtectedActionRequest
from app.models.case import Case
from app.services.action_service import ActionService


@pytest.fixture
def mock_action_repo():
    """Mock action repository."""
    return Mock()


@pytest.fixture
def mock_case_repo():
    """Mock case repository."""
    return Mock()


@pytest.fixture
def mock_history_repo():
    """Mock history repository."""
    repo = Mock()
    repo.next_sequence = Mock(return_value=1)
    return repo


@pytest.fixture
def mock_audit_service():
    """Mock audit service."""
    return Mock()


@pytest.fixture
def mock_identity_adapter():
    """Mock identity adapter."""
    return Mock()


@pytest.fixture
def mock_management_api_adapter():
    """Mock management API adapter."""
    return Mock()


@pytest.fixture
def mock_clock():
    """Mock clock."""
    clock = Mock()
    clock.utcnow = Mock(return_value=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc))
    return clock


@pytest.fixture
def action_service(
    mock_action_repo,
    mock_case_repo,
    mock_history_repo,
    mock_audit_service,
    mock_identity_adapter,
    mock_management_api_adapter,
    mock_clock
):
    """Create ActionService instance with mocked dependencies."""
    return ActionService(
        action_repo=mock_action_repo,
        case_repo=mock_case_repo,
        history_repo=mock_history_repo,
        audit_service=mock_audit_service,
        identity_adapter=mock_identity_adapter,
        management_api_adapter=mock_management_api_adapter,
        clock=mock_clock
    )


def test_start_protected_action_success(
    action_service,
    mock_case_repo,
    mock_action_repo,
    mock_identity_adapter,
    mock_history_repo
):
    """Test starting a protected action successfully."""
    # Setup
    case = Case(
        id=uuid.UUID(int=1),
        case_reference="CP-TEST1",
        customer_party_id="CUST-001"
    )
    mock_case_repo.get_by_reference_for_customer.return_value = case
    
    action_request = ProtectedActionRequest(
        id=uuid.UUID(int=100),
        case_id=case.id,
        customer_party_id="CUST-001",
        action_type="stop_card",
        action_domain="card",
        action_payload_json={"card_last_four": "1234"},
        request_status="pending_sca",
        requires_sca_flag=True,
        sca_outcome="not_invoked",
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    )
    mock_action_repo.open_request_for.return_value = action_request
    
    mock_identity_adapter.start_sca.return_value = {
        "challenge_reference": "SCA-CHALLENGE-123",
        "challenge_url": "https://sca.example.com/challenge"
    }
    
    # Execute
    result = action_service.start(
        customer_party_id="CUST-001",
        case_reference="CP-TEST1",
        action_type="stop_card",
        action_domain="card",
        action_payload={"card_last_four": "1234"},
        correlation_id="test-001"
    )
    
    # Verify
    assert result["action_id"] == str(action_request.id)
    assert result["sca_challenge_reference"] == "SCA-CHALLENGE-123"
    mock_case_repo.get_by_reference_for_customer.assert_called_once_with("CP-TEST1", "CUST-001")
    mock_action_repo.open_request_for.assert_called_once()
    mock_identity_adapter.start_sca.assert_called_once_with(
        customer_party_id="CUST-001",
        action_type="stop_card"
    )
    mock_history_repo.add_event.assert_called_once()


def test_start_protected_action_case_not_found(
    action_service,
    mock_case_repo
):
    """Test starting action when case not found."""
    mock_case_repo.get_by_reference_for_customer.return_value = None
    
    with pytest.raises(NotFoundError, match="Case CP-TEST1 not found"):
        action_service.start(
            customer_party_id="CUST-001",
            case_reference="CP-TEST1",
            action_type="stop_card",
            action_domain="card",
            action_payload={"card_last_four": "1234"},
            correlation_id="test-001"
        )


def test_report_outcome_success(
    action_service,
    mock_action_repo,
    mock_case_repo,
    mock_management_api_adapter,
    mock_history_repo
):
    """Test reporting SCA success outcome."""
    # Setup
    case = Case(
        id=uuid.UUID(int=1),
        case_reference="CP-TEST1",
        customer_party_id="CUST-001"
    )
    mock_case_repo.get_by_reference_for_customer.return_value = case
    
    action_request = ProtectedActionRequest(
        id=uuid.UUID(int=100),
        case_id=case.id,
        customer_party_id="CUST-001",
        action_type="stop_card",
        action_domain="card",
        action_payload_json={"card_last_four": "1234"},
        request_status="pending_sca",
        requires_sca_flag=True,
        sca_outcome="not_invoked",
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    )
    mock_action_repo.get_for_case.return_value = action_request
    
    mock_management_api_adapter.execute_protected_action.return_value = {
        "reference": "MGMT-REF-123"
    }
    
    # Execute
    result = action_service.report_outcome(
        customer_party_id="CUST-001",
        case_reference="CP-TEST1",
        action_id=action_request.id,
        sca_outcome="success",
        sca_verification_token="TOKEN-123",
        correlation_id="test-001"
    )
    
    # Verify
    assert result["request_status"] == "released"
    assert result["sca_outcome"] == "success"
    assert result["management_api_reference"] == "MGMT-REF-123"
    assert action_request.request_status == "released"
    assert action_request.sca_outcome == "success"
    mock_management_api_adapter.execute_protected_action.assert_called_once()
    mock_history_repo.add_event.assert_called_once()


def test_report_outcome_failed(
    action_service,
    mock_action_repo,
    mock_case_repo,
    mock_history_repo
):
    """Test reporting SCA failed outcome."""
    # Setup
    case = Case(
        id=uuid.UUID(int=1),
        case_reference="CP-TEST1",
        customer_party_id="CUST-001"
    )
    mock_case_repo.get_by_reference_for_customer.return_value = case
    
    action_request = ProtectedActionRequest(
        id=uuid.UUID(int=100),
        case_id=case.id,
        customer_party_id="CUST-001",
        action_type="stop_card",
        action_domain="card",
        action_payload_json={"card_last_four": "1234"},
        request_status="pending_sca",
        requires_sca_flag=True,
        sca_outcome="not_invoked",
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    )
    mock_action_repo.get_for_case.return_value = action_request
    
    # Execute
    result = action_service.report_outcome(
        customer_party_id="CUST-001",
        case_reference="CP-TEST1",
        action_id=action_request.id,
        sca_outcome="failed",
        sca_verification_token="TOKEN-123",
        correlation_id="test-001"
    )
    
    # Verify
    assert result["request_status"] == "not_executed"
    assert result["sca_outcome"] == "failed"
    assert result["fallback_guidance_text"] is not None
    assert action_request.request_status == "not_executed"
    assert action_request.sca_outcome == "failed"
    mock_history_repo.add_event.assert_called_once()


def test_report_outcome_idempotent(
    action_service,
    mock_action_repo,
    mock_case_repo
):
    """Test idempotent behavior when outcome already reported."""
    # Setup
    case = Case(
        id=uuid.UUID(int=1),
        case_reference="CP-TEST1",
        customer_party_id="CUST-001"
    )
    mock_case_repo.get_by_reference_for_customer.return_value = case
    
    action_request = ProtectedActionRequest(
        id=uuid.UUID(int=100),
        case_id=case.id,
        customer_party_id="CUST-001",
        action_type="stop_card",
        action_domain="card",
        action_payload_json={"card_last_four": "1234"},
        request_status="released",
        requires_sca_flag=True,
        sca_outcome="success",
        management_api_reference="MGMT-REF-123",
        completed_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    )
    mock_action_repo.get_for_case.return_value = action_request
    
    # Execute - report same outcome again
    result = action_service.report_outcome(
        customer_party_id="CUST-001",
        case_reference="CP-TEST1",
        action_id=action_request.id,
        sca_outcome="success",
        sca_verification_token="TOKEN-123",
        correlation_id="test-001"
    )
    
    # Verify - returns existing state
    assert result["request_status"] == "released"
    assert result["sca_outcome"] == "success"


def test_report_outcome_different_outcome_after_finalized(
    action_service,
    mock_action_repo,
    mock_case_repo
):
    """Test error when reporting different outcome after finalized."""
    # Setup
    case = Case(
        id=uuid.UUID(int=1),
        case_reference="CP-TEST1",
        customer_party_id="CUST-001"
    )
    mock_case_repo.get_by_reference_for_customer.return_value = case
    
    action_request = ProtectedActionRequest(
        id=uuid.UUID(int=100),
        case_id=case.id,
        customer_party_id="CUST-001",
        action_type="stop_card",
        action_domain="card",
        action_payload_json={"card_last_four": "1234"},
        request_status="released",
        requires_sca_flag=True,
        sca_outcome="success",
        completed_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    )
    mock_action_repo.get_for_case.return_value = action_request
    
    # Execute - try to report different outcome
    with pytest.raises(ValidationError, match="already finalized"):
        action_service.report_outcome(
            customer_party_id="CUST-001",
            case_reference="CP-TEST1",
            action_id=action_request.id,
            sca_outcome="failed",  # Different from stored success
            sca_verification_token="TOKEN-123",
            correlation_id="test-001"
        )
