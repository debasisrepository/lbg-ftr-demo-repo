"""Unit tests for ownership service (FR-008, FR-009)."""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest

from app.core.clock import Clock
from app.core.errors import NotFoundError, ValidationError
from app.models.case import Case
from app.models.config import OwnerTeamMapping
from app.models.ownership import CaseOwnership, ExpectedByCommitment
from app.schemas.case import ExpectedByRevisionRequest, OwnerChangeRequest
from app.services.ownership_service import OwnershipService


@pytest.fixture
def mock_repos():
    """Create mock repositories."""
    ownership_repo = Mock()
    case_repo = Mock()
    history_repo = Mock()
    audit_service = Mock()
    clock = Clock()
    clock.utcnow = Mock(return_value=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc))
    
    return {
        "ownership_repo": ownership_repo,
        "case_repo": case_repo,
        "history_repo": history_repo,
        "audit_service": audit_service,
        "clock": clock,
    }


@pytest.fixture
def ownership_service(mock_repos):
    """Create ownership service with mocked dependencies."""
    return OwnershipService(
        ownership_repo=mock_repos["ownership_repo"],
        case_repo=mock_repos["case_repo"],
        history_repo=mock_repos["history_repo"],
        audit_service=mock_repos["audit_service"],
        clock=mock_repos["clock"]
    )


def test_change_owner_success(ownership_service, mock_repos):
    """Test successful owner change."""
    # Arrange
    case_id = uuid.uuid4()
    case = Case(
        id=case_id,
        case_reference="CP-TEST123",
        customer_party_id="CUST-001",
        brand="lloyds",
        issue_type="card_declined",
        classification_source="eligibility_rule",
        issue_title="Test Case",
        issue_summary="Test summary",
        origin_channel="mobile_app",
        current_lifecycle_state="case_created",
        current_status_code="received",
        current_status_label="Received",
        opened_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        created_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    )
    
    current_ownership = CaseOwnership(
        id=uuid.uuid4(),
        case_id=case_id,
        owner_team_code="INTAKE_DEFAULT",
        owner_semantic_label="Intake Team",
        owner_display_name="Intake & Triage",
        effective_from=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        is_current=True,
        created_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    )
    
    new_mapping = OwnerTeamMapping(
        id=uuid.uuid4(),
        owner_team_code="CARDS_DISPUTES",
        owner_semantic_label="Card Disputes Team",
        owner_display_name="Card Disputes",
        is_active=True,
        created_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    )
    
    event = Mock()
    event.id = uuid.uuid4()
    
    mock_repos["case_repo"].get_by_reference.return_value = case
    mock_repos["ownership_repo"].active_mapping.return_value = new_mapping
    mock_repos["ownership_repo"].current_ownership.return_value = current_ownership
    mock_repos["ownership_repo"].insert_ownership.return_value = Mock()
    mock_repos["history_repo"].next_sequence.return_value = 3
    
    request = OwnerChangeRequest(
        owner_team_code="CARDS_DISPUTES",
        handoff_reason_code="case_type_match"
    )
    
    # Act
    result = ownership_service.change_owner(
        case_reference="CP-TEST123",
        request=request,
        correlation_id="test-corr-001"
    )
    
    # Assert
    assert result.owner_semantic_label == "Card Disputes Team"
    assert result.owner_display_name == "Card Disputes"
    assert result.owner_type == "team"
    assert current_ownership.is_current == False
    assert current_ownership.effective_to == datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    assert case.continuity_state == "refresh_pending"
    mock_repos["history_repo"].next_sequence.assert_called_once_with(case.id)
    mock_repos["history_repo"].add_event.assert_called_once()
    mock_repos["audit_service"].record.assert_called_once()


def test_change_owner_case_not_found(ownership_service, mock_repos):
    """Test owner change when case doesn't exist."""
    mock_repos["case_repo"].get_by_reference.return_value = None
    
    request = OwnerChangeRequest(
        owner_team_code="CARDS_DISPUTES",
        handoff_reason_code="case_type_match"
    )
    
    with pytest.raises(NotFoundError, match="Case CP-NOTFOUND not found"):
        ownership_service.change_owner(
            case_reference="CP-NOTFOUND",
            request=request,
            correlation_id="test-corr-001"
        )


def test_change_owner_invalid_team_code(ownership_service, mock_repos):
    """Test owner change with invalid team code."""
    case = Mock()
    case.id = uuid.uuid4()
    
    mock_repos["case_repo"].get_by_reference.return_value = case
    mock_repos["ownership_repo"].active_mapping.return_value = None
    
    request = OwnerChangeRequest(
        owner_team_code="INVALID_CODE",
        handoff_reason_code="case_type_match"
    )
    
    with pytest.raises(ValidationError, match="Owner team code INVALID_CODE not found or inactive"):
        ownership_service.change_owner(
            case_reference="CP-TEST123",
            request=request,
            correlation_id="test-corr-001"
        )


def test_change_owner_unchanged(ownership_service, mock_repos):
    """Test owner change when owner is already set to requested team."""
    case = Mock()
    case.id = uuid.uuid4()
    
    current_ownership = Mock()
    current_ownership.owner_team_code = "CARDS_DISPUTES"
    
    new_mapping = Mock()
    new_mapping.owner_team_code = "CARDS_DISPUTES"
    
    mock_repos["case_repo"].get_by_reference.return_value = case
    mock_repos["ownership_repo"].active_mapping.return_value = new_mapping
    mock_repos["ownership_repo"].current_ownership.return_value = current_ownership
    
    request = OwnerChangeRequest(
        owner_team_code="CARDS_DISPUTES",
        handoff_reason_code="case_type_match"
    )
    
    with pytest.raises(ValidationError, match="Owner is already set to the requested team"):
        ownership_service.change_owner(
            case_reference="CP-TEST123",
            request=request,
            correlation_id="test-corr-001"
        )


def test_revise_expected_by_to_committed(ownership_service, mock_repos):
    """Test revising expected-by to committed state."""
    case_id = uuid.uuid4()
    case = Mock()
    case.id = case_id
    case.case_reference = "CP-TEST123"
    
    current_commitment = ExpectedByCommitment(
        id=uuid.uuid4(),
        case_id=case_id,
        commitment_state="under_review",
        expected_by_at=None,
        customer_explanatory_text="Timing is under review",
        effective_from=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        is_current=True,
        created_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    )
    
    event = Mock()
    event.id = uuid.uuid4()
    
    mock_repos["case_repo"].get_by_reference.return_value = case
    mock_repos["ownership_repo"].current_expected_by.return_value = current_commitment
    mock_repos["ownership_repo"].insert_expected_by.return_value = Mock()
    mock_repos["history_repo"].next_sequence.return_value = 5
    
    future_date = datetime(2024, 1, 20, 12, 0, 0, tzinfo=timezone.utc)
    request = ExpectedByRevisionRequest(
        commitment_state="committed",
        expected_by_at=future_date,
        customer_explanatory_text=None,
        confidence_basis="team_capacity",
        withdrawn_reason_code=None
    )
    
    # Act
    result = ownership_service.revise_expected_by(
        case_reference="CP-TEST123",
        request=request,
        correlation_id="test-corr-001"
    )
    
    # Assert
    assert result.commitment_state == "committed"
    assert result.expected_by_at == future_date
    assert current_commitment.is_current == False
    assert current_commitment.effective_to == datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    mock_repos["history_repo"].next_sequence.assert_called_once_with(case.id)
    mock_repos["history_repo"].add_event.assert_called_once()
    mock_repos["audit_service"].record.assert_called_once()


def test_revise_expected_by_to_withdrawn(ownership_service, mock_repos):
    """Test revising expected-by to withdrawn state."""
    case = Mock()
    case.id = uuid.uuid4()
    
    current_commitment = Mock()
    current_commitment.commitment_state = "committed"
    current_commitment.expected_by_at = datetime(2024, 1, 20, 12, 0, 0, tzinfo=timezone.utc)
    
    event = Mock()
    event.id = uuid.uuid4()
    
    mock_repos["case_repo"].get_by_reference.return_value = case
    mock_repos["ownership_repo"].current_expected_by.return_value = current_commitment
    mock_repos["ownership_repo"].insert_expected_by.return_value = Mock()
    mock_repos["history_repo"].next_sequence.return_value = 6
    
    request = ExpectedByRevisionRequest(
        commitment_state="withdrawn",
        expected_by_at=None,
        customer_explanatory_text="We're experiencing delays with this type of request.",
        confidence_basis=None,
        withdrawn_reason_code="service_delay"
    )
    
    # Act
    result = ownership_service.revise_expected_by(
        case_reference="CP-TEST123",
        request=request,
        correlation_id="test-corr-001"
    )
    
    # Assert
    assert result.commitment_state == "withdrawn"
    assert result.expected_by_at is None
    assert result.customer_explanatory_text == "We're experiencing delays with this type of request."
    mock_repos["history_repo"].next_sequence.assert_called_once_with(case.id)
    mock_repos["history_repo"].add_event.assert_called_once()


def test_revise_expected_by_committed_without_date(ownership_service, mock_repos):
    """Test that committed state requires expected_by_at."""
    case = Mock()
    case.id = uuid.uuid4()
    
    mock_repos["case_repo"].get_by_reference.return_value = case
    mock_repos["ownership_repo"].current_expected_by.return_value = None
    
    request = ExpectedByRevisionRequest(
        commitment_state="committed",
        expected_by_at=None,  # Missing required date
        customer_explanatory_text=None,
        confidence_basis="team_capacity",
        withdrawn_reason_code=None
    )
    
    with pytest.raises(ValidationError, match="committed state requires expected_by_at"):
        ownership_service.revise_expected_by(
            case_reference="CP-TEST123",
            request=request,
            correlation_id="test-corr-001"
        )


def test_revise_expected_by_withdrawn_without_text(ownership_service, mock_repos):
    """Test that withdrawn state requires customer_explanatory_text."""
    case = Mock()
    case.id = uuid.uuid4()
    
    mock_repos["case_repo"].get_by_reference.return_value = case
    mock_repos["ownership_repo"].current_expected_by.return_value = None
    
    request = ExpectedByRevisionRequest(
        commitment_state="withdrawn",
        expected_by_at=None,
        customer_explanatory_text=None,  # Missing required text
        confidence_basis=None,
        withdrawn_reason_code="service_delay"
    )
    
    with pytest.raises(ValidationError, match="withdrawn state requires customer_explanatory_text"):
        ownership_service.revise_expected_by(
            case_reference="CP-TEST123",
            request=request,
            correlation_id="test-corr-001"
        )


def test_revise_expected_by_withdrawn_without_reason_code(ownership_service, mock_repos):
    """Test that withdrawn state requires withdrawn_reason_code."""
    case = Mock()
    case.id = uuid.uuid4()
    
    mock_repos["case_repo"].get_by_reference.return_value = case
    mock_repos["ownership_repo"].current_expected_by.return_value = None
    
    request = ExpectedByRevisionRequest(
        commitment_state="withdrawn",
        expected_by_at=None,
        customer_explanatory_text="Delays expected",
        confidence_basis=None,
        withdrawn_reason_code=None  # Missing required code
    )
    
    with pytest.raises(ValidationError, match="withdrawn state requires withdrawn_reason_code"):
        ownership_service.revise_expected_by(
            case_reference="CP-TEST123",
            request=request,
            correlation_id="test-corr-001"
        )


def test_revise_expected_by_date_in_past(ownership_service, mock_repos):
    """Test that expected_by_at must be in the future."""
    case = Mock()
    case.id = uuid.uuid4()
    
    mock_repos["case_repo"].get_by_reference.return_value = case
    mock_repos["ownership_repo"].current_expected_by.return_value = None
    
    past_date = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    request = ExpectedByRevisionRequest(
        commitment_state="committed",
        expected_by_at=past_date,  # In the past
        customer_explanatory_text=None,
        confidence_basis="team_capacity",
        withdrawn_reason_code=None
    )
    
    with pytest.raises(ValidationError, match="expected_by_at must be in the future"):
        ownership_service.revise_expected_by(
            case_reference="CP-TEST123",
            request=request,
            correlation_id="test-corr-001"
        )


def test_current_owner_returns_view(ownership_service, mock_repos):
    """Test current_owner returns proper view."""
    case_id = uuid.uuid4()
    ownership = CaseOwnership(
        id=uuid.uuid4(),
        case_id=case_id,
        owner_team_code="CARDS_DISPUTES",
        owner_semantic_label="Card Disputes Team",
        owner_display_name="Card Disputes",
        effective_from=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        is_current=True,
        created_at=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    )
    
    mock_repos["ownership_repo"].current_ownership.return_value = ownership
    
    result = ownership_service.current_owner(case_id)
    
    assert result.owner_type == "team"
    assert result.owner_semantic_label == "Card Disputes Team"
    assert result.owner_display_name == "Card Disputes"


def test_current_expected_by_returns_default_when_none(ownership_service, mock_repos):
    """Test current_expected_by returns default under_review when none exists."""
    case_id = uuid.uuid4()
    mock_repos["ownership_repo"].current_expected_by.return_value = None
    
    result = ownership_service.current_expected_by(case_id)
    
    assert result.commitment_state == "under_review"
    assert result.expected_by_at is None
    assert result.customer_explanatory_text == "Timing is under review"
    assert result.effective_from is None
