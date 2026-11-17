"""Integration tests for case list functionality."""
import uuid
from datetime import datetime, timezone

import pytest

from app.core.clock import Clock
from app.models.case import Case, CaseStatusProjection
from app.models.config import IssueEligibilityRule, OwnerTeamMapping
from app.models.ownership import CaseOwnership, ExpectedByCommitment
from app.repositories.audit_repository import AuditRepository
from app.repositories.case_repository import CaseRepository
from app.repositories.config_repository import ConfigRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.ownership_repository import OwnershipRepository
from app.services.audit_service import AuditService
from app.services.case_service import CaseService
from app.services.policy_service import PolicyService
from app.adapters.customer_case_adapter import CustomerCaseAdapter


@pytest.fixture
def case_service(db_session):
    """Create case service with real repositories."""
    # Seed eligibility rules for tests
    now = datetime.now(timezone.utc)
    rules = [
        IssueEligibilityRule(
            id=uuid.uuid4(),
            issue_type="card_declined",
            is_eligible=True,
            priority_weight=100,
            created_at=now
        ),
        IssueEligibilityRule(
            id=uuid.uuid4(),
            issue_type="payment_missing",
            is_eligible=True,
            priority_weight=90,
            created_at=now
        ),
    ]
    for rule in rules:
        db_session.add(rule)
    
    # Seed owner mapping
    owner_mapping = OwnerTeamMapping(
        id=uuid.uuid4(),
        owner_team_code="INTAKE_DEFAULT",
        owner_semantic_label="Intake Team",
        owner_display_name="Intake & Triage",
        is_active=True,
        created_at=now
    )
    db_session.add(owner_mapping)
    db_session.commit()
    
    case_repo = CaseRepository(db_session)
    history_repo = HistoryRepository(db_session)
    ownership_repo = OwnershipRepository(db_session)
    config_repo = ConfigRepository(db_session)
    audit_repo = AuditRepository(db_session)
    
    policy_service = PolicyService(config_repo)
    audit_service = AuditService(audit_repo, Clock())
    customer_case_adapter = CustomerCaseAdapter()
    
    return CaseService(
        case_repo=case_repo,
        history_repo=history_repo,
        ownership_repo=ownership_repo,
        config_repo=config_repo,
        audit_repo=audit_repo,
        policy_service=policy_service,
        audit_service=audit_service,
        customer_case_adapter=customer_case_adapter,
        clock=Clock()
    )


def test_list_cases_pagination(case_service, db_session):
    """Test list_cases returns paginated results."""
    # Arrange: Create test cases
    now = datetime.now(timezone.utc)
    customer_party_id = "TEST-CUSTOMER-001"
    
    for i in range(3):
        case_id = uuid.uuid4()
        
        case = Case(
            id=case_id,
            case_reference=f"CP-TEST-{i}",
            customer_party_id=customer_party_id,
            brand="lloyds",
            issue_type="test_issue",
            classification_source="eligibility_rule",
            issue_title=f"Test Case {i}",
            issue_summary=f"Test summary {i}",
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
            customer_explanatory_text="Timing is under review",
            confidence_basis="initial",
            effective_from=now,
            is_current=True,
            created_at=now
        )
        db_session.add(expected_by)
    
    db_session.commit()
    
    # Act
    summaries, total = case_service.list_cases(
        customer_party_id=customer_party_id,
        limit=2,
        offset=0
    )
    
    # Assert
    assert total == 3
    assert len(summaries) == 2
    assert summaries[0].owner.owner_display_name == "Intake & Triage"
    assert summaries[0].expected_by.commitment_state == "under_review"


def test_list_cases_exclude_closed(case_service, db_session):
    """Test list_cases can exclude closed cases."""
    # Arrange: Create one open and one closed case
    now = datetime.now(timezone.utc)
    customer_party_id = "TEST-CUSTOMER-002"
    
    # Open case
    open_case_id = uuid.uuid4()
    open_case = Case(
        id=open_case_id,
        case_reference="CP-OPEN",
        customer_party_id=customer_party_id,
        brand="lloyds",
        issue_type="test_open",
        classification_source="eligibility_rule",
        issue_title="Open Case",
        issue_summary="Open",
        origin_channel="mobile_app",
        current_lifecycle_state="case_created",
        current_status_code="received",
        current_status_label="Received",
        opened_at=now,
        closed_at=None,
        created_at=now,
        updated_at=now
    )
    db_session.add(open_case)
    
    # Closed case
    closed_case_id = uuid.uuid4()
    closed_case = Case(
        id=closed_case_id,
        case_reference="CP-CLOSED",
        customer_party_id=customer_party_id,
        brand="lloyds",
        issue_type="test_closed",
        classification_source="eligibility_rule",
        issue_title="Closed Case",
        issue_summary="Closed",
        origin_channel="mobile_app",
        current_lifecycle_state="closed",
        current_status_code="closed",
        current_status_label="Closed",
        opened_at=now,
        closed_at=now,
        created_at=now,
        updated_at=now
    )
    db_session.add(closed_case)
    
    # Add required projections for both
    for case_id in [open_case_id, closed_case_id]:
        projection = CaseStatusProjection(
            id=uuid.uuid4(),
            case_id=case_id,
            status_code="received",
            status_label="Received",
            lifecycle_state="case_created",
            status_icon="in_progress",
            status_color="blue",
            customer_facing_text="Test",
            next_step_text="Test",
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
            customer_explanatory_text="Test",
            confidence_basis="initial",
            effective_from=now,
            is_current=True,
            created_at=now
        )
        db_session.add(expected_by)
    
    db_session.commit()
    
    # Act
    summaries, total = case_service.list_cases(
        customer_party_id=customer_party_id,
        include_closed=False
    )
    
    # Assert
    assert total == 1
    assert len(summaries) == 1
    assert summaries[0].case_reference == "CP-OPEN"


def test_list_cases_scoped_to_customer(case_service, db_session):
    """Test list_cases only returns cases for the specified customer."""
    # Arrange: Create cases for two different customers
    now = datetime.now(timezone.utc)
    
    for customer_id in ["CUST-A", "CUST-B"]:
        case_id = uuid.uuid4()
        
        case = Case(
            id=case_id,
            case_reference=f"CP-{customer_id}",
            customer_party_id=customer_id,
            brand="lloyds",
            issue_type="test_issue",
            classification_source="eligibility_rule",
            issue_title="Test",
            issue_summary="Test",
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
            customer_facing_text="Test",
            next_step_text="Test",
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
            customer_explanatory_text="Test",
            confidence_basis="initial",
            effective_from=now,
            is_current=True,
            created_at=now
        )
        db_session.add(expected_by)
    
    db_session.commit()
    
    # Act - query for CUST-A only
    summaries, total = case_service.list_cases(customer_party_id="CUST-A")
    
    # Assert - should only see CUST-A's case
    assert total == 1
    assert summaries[0].case_reference == "CP-CUST-A"
