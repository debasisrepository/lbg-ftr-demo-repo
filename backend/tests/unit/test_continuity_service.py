"""Unit tests for continuity service."""
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock

import pytest

from app.core.clock import Clock
from app.core.errors import NotFoundError
from app.models.audit import CaseEvent
from app.models.case import Case
from app.models.continuity import ChannelHandoff, ContinuityContext
from app.models.ownership import CaseOwnership, ExpectedByCommitment
from app.repositories.audit_repository import AuditRepository
from app.repositories.case_repository import CaseRepository
from app.repositories.continuity_repository import ContinuityRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.ownership_repository import OwnershipRepository
from app.services.audit_service import AuditService
from app.services.continuity_service import ContinuityPackageBuilder, ContinuityService


@pytest.fixture
def mock_continuity_repo():
    """Mock continuity repository."""
    repo = Mock(spec=ContinuityRepository)
    repo.session = Mock()
    return repo


@pytest.fixture
def mock_case_repo():
    """Mock case repository."""
    repo = Mock(spec=CaseRepository)
    repo.session = Mock()
    return repo


@pytest.fixture
def mock_ownership_repo():
    """Mock ownership repository."""
    return Mock(spec=OwnershipRepository)


@pytest.fixture
def mock_history_repo():
    """Mock history repository."""
    return Mock(spec=HistoryRepository)


@pytest.fixture
def mock_audit_repo():
    """Mock audit repository."""
    return Mock(spec=AuditRepository)


@pytest.fixture
def mock_audit_service():
    """Mock audit service."""
    return Mock(spec=AuditService)


@pytest.fixture
def mock_clock():
    """Mock clock."""
    clock = Mock(spec=Clock)
    clock.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    return clock


@pytest.fixture
def continuity_service(
    mock_continuity_repo,
    mock_case_repo,
    mock_ownership_repo,
    mock_history_repo,
    mock_audit_repo,
    mock_audit_service,
    mock_clock
):
    """Create continuity service with mocks."""
    return ContinuityService(
        continuity_repo=mock_continuity_repo,
        case_repo=mock_case_repo,
        ownership_repo=mock_ownership_repo,
        history_repo=mock_history_repo,
        audit_repo=mock_audit_repo,
        audit_service=mock_audit_service,
        clock=mock_clock
    )


@pytest.fixture
def sample_case():
    """Sample case."""
    return Case(
        id=uuid.UUID(int=1),
        case_reference="CP-TEST1",
        customer_party_id="CUST-001",
        brand="lloyds",
        issue_type="card_declined",
        classification_source="eligibility_rule",
        issue_title="Card Declined",
        issue_summary="My card was declined",
        origin_channel="mobile_app",
        current_lifecycle_state="case_created",
        current_status_code="received",
        current_status_label="Received",
        continuity_state="current",
        opened_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    )


@pytest.fixture
def sample_owner():
    """Sample owner."""
    return CaseOwnership(
        id=uuid.UUID(int=2),
        case_id=uuid.UUID(int=1),
        owner_team_code="CARDS_DISPUTES",
        owner_semantic_label="Card Disputes Team",
        owner_display_name="Card Disputes",
        effective_from=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        is_current=True,
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    )


@pytest.fixture
def sample_expected_by():
    """Sample expected-by."""
    return ExpectedByCommitment(
        id=uuid.UUID(int=3),
        case_id=uuid.UUID(int=1),
        commitment_state="committed",
        expected_by_at=datetime(2024, 1, 5, 12, 0, 0, tzinfo=timezone.utc),
        customer_explanatory_text="We'll resolve this by Jan 5",
        confidence_basis="team_capacity",
        effective_from=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        is_current=True,
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    )


@pytest.fixture
def sample_events():
    """Sample events."""
    return [
        CaseEvent(
            id=uuid.UUID(int=4),
            case_id=uuid.UUID(int=1),
            sequence_number=1,
            event_type="CaseCaptured",
            event_timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            summary_text="Case created",
            customer_visible_flag=True,
            actor_type="customer",
            correlation_id="test-001",
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        )
    ]


@pytest.fixture
def sample_handoffs():
    """Sample handoffs."""
    return [
        ChannelHandoff(
            id=uuid.UUID(int=5),
            case_id=uuid.UUID(int=1),
            from_channel="mobile_app",
            to_channel="chat",
            context_presented_flag=True,
            handoff_timestamp=datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc),
            correlation_id="test-handoff-001",
            created_at=datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)
        )
    ]


def test_package_builder_build(sample_case, sample_owner, sample_expected_by, sample_events, sample_handoffs):
    """Test ContinuityPackageBuilder.build()."""
    builder = ContinuityPackageBuilder()
    
    package = builder.build(
        sample_case,
        sample_owner,
        sample_expected_by,
        sample_events,
        sample_handoffs,
        context_version=1
    )
    
    assert package["context_version"] == 1
    assert package["customer_issue_summary"] == "My card was declined"
    assert package["current_state"] == "case_created"
    assert len(package["recent_updates"]) == 1
    assert len(package["channel_history"]) == 1
    assert "structured_context" in package
    assert "colleague_payload" in package
    assert "llm_safe_payload" in package


def test_package_builder_colleague_view(sample_case, sample_owner, sample_expected_by, sample_events, sample_handoffs):
    """Test ContinuityPackageBuilder.colleague_view()."""
    builder = ContinuityPackageBuilder()
    
    view = builder.colleague_view(
        sample_case,
        sample_owner,
        sample_expected_by,
        sample_events,
        sample_handoffs,
        context_version=1
    )
    
    assert view["case_reference"] == "CP-TEST1"
    assert view["customer_party_id"] == "CUST-001"
    assert view["issue_type"] == "card_declined"
    assert view["current_state"] == "case_created"
    assert len(view["recent_updates"]) == 1
    assert len(view["channel_history"]) == 1


def test_get_package_with_persisted_context(
    continuity_service,
    mock_case_repo,
    mock_continuity_repo,
    sample_case
):
    """Test get_package() with persisted context."""
    # Setup mocks
    mock_case_repo.get_by_reference_for_customer.return_value = sample_case
    
    persisted_context = ContinuityContext(
        id=uuid.UUID(int=10),
        case_id=sample_case.id,
        package_version=1,
        structured_context_json={"case_reference": "CP-TEST1"},
        llm_safe_payload_json={},
        colleague_payload_json={},
        restricted_fields_excluded_flag=True,
        effective_from=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        is_current=True,
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    )
    mock_continuity_repo.current_package.return_value = persisted_context
    
    # Execute
    package = continuity_service.get_package("CP-TEST1", "CUST-001")
    
    # Verify
    assert package["context_version"] == 1
    assert "structured_context" in package
    mock_case_repo.get_by_reference_for_customer.assert_called_once_with("CP-TEST1", "CUST-001")


def test_get_package_case_not_found(continuity_service, mock_case_repo):
    """Test get_package() raises NotFoundError when case not found."""
    mock_case_repo.get_by_reference_for_customer.return_value = None
    
    with pytest.raises(NotFoundError, match="Case CP-TEST1 not found"):
        continuity_service.get_package("CP-TEST1", "CUST-001")


def test_record_handoff(
    continuity_service,
    mock_case_repo,
    mock_continuity_repo,
    mock_audit_service,
    sample_case
):
    """Test record_handoff()."""
    # Setup mocks
    mock_case_repo.get_by_reference_for_customer.return_value = sample_case
    
    # Execute
    continuity_service.record_handoff(
        case_reference="CP-TEST1",
        customer_party_id="CUST-001",
        from_channel="mobile_app",
        to_channel="chat",
        context_presented_flag=True,
        correlation_id="test-001"
    )
    
    # Verify
    mock_continuity_repo.insert_handoff.assert_called_once()
    assert sample_case.continuity_state == "refresh_pending"
    mock_audit_service.record.assert_called_once()


def test_colleague_retrieve(
    continuity_service,
    mock_case_repo,
    mock_ownership_repo,
    mock_history_repo,
    mock_continuity_repo,
    mock_audit_service,
    sample_case,
    sample_owner,
    sample_expected_by,
    sample_events,
    sample_handoffs
):
    """Test colleague_retrieve()."""
    # Setup mocks
    mock_case_repo.get_by_reference.return_value = sample_case
    mock_ownership_repo.current_ownership.return_value = sample_owner
    mock_ownership_repo.current_expected_by.return_value = sample_expected_by
    mock_history_repo.page_for_case.return_value = (sample_events, 1)
    mock_continuity_repo.handoffs_for_case.return_value = sample_handoffs
    mock_continuity_repo.current_package.return_value = None
    
    # Execute
    package = continuity_service.colleague_retrieve(
        case_reference="CP-TEST1",
        colleague_reference="COLL-001",
        correlation_id="test-001"
    )
    
    # Verify
    assert package["case_reference"] == "CP-TEST1"
    assert package["customer_party_id"] == "CUST-001"
    mock_audit_service.record.assert_called_once()


def test_list_colleague_cases(
    continuity_service,
    mock_case_repo,
    sample_case
):
    """Test list_colleague_cases()."""
    # Setup mocks
    mock_case_repo.list_for_customer.return_value = ([sample_case], 1)
    
    # Execute
    summaries, total = continuity_service.list_colleague_cases(
        customer_party_id="CUST-001",
        limit=20,
        offset=0
    )
    
    # Verify
    assert total == 1
    assert len(summaries) == 1
    assert summaries[0]["case_reference"] == "CP-TEST1"


def test_refresh_if_pending(
    continuity_service,
    mock_case_repo,
    mock_ownership_repo,
    mock_history_repo,
    mock_continuity_repo,
    sample_case,
    sample_owner,
    sample_expected_by,
    sample_events,
    sample_handoffs
):
    """Test refresh_if_pending()."""
    # Setup mocks
    sample_case.continuity_state = "refresh_pending"
    mock_case_repo.session.get.return_value = sample_case
    mock_ownership_repo.current_ownership.return_value = sample_owner
    mock_ownership_repo.current_expected_by.return_value = sample_expected_by
    mock_history_repo.page_for_case.return_value = (sample_events, 1)
    mock_continuity_repo.handoffs_for_case.return_value = sample_handoffs
    mock_continuity_repo.current_package.return_value = None
    
    # Execute
    continuity_service.refresh_if_pending(sample_case.id)
    
    # Verify
    mock_continuity_repo.insert_context.assert_called_once()
    assert sample_case.continuity_state == "current"
