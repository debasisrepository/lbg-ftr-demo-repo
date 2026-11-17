from app.services.case.service import CaseService
from app.services.case.schemas import CreateCaseRequest


def test_case_service_create_case(db_session):
    """Test case service creates case with unique ref"""
    service = CaseService(db_session)
    
    request = CreateCaseRequest(
        origin_source="assistant_escalation",
        problem_statement="I need help with my payment that failed",
        classification="payment_query",
        route_reason="Out of scope for assistant"
    )
    
    case = service.create_case(1, request)
    
    assert case.id is not None
    assert case.case_ref is not None
    assert "CP-" in case.case_ref
    assert case.customer_user_id == 1
    assert case.status == "new"
    assert case.owner_team_display is not None
    assert case.expected_by_at is not None


def test_case_service_list_customer_cases(db_session):
    """Test case service lists customer cases"""
    service = CaseService(db_session)
    
    # Create a case
    request = CreateCaseRequest(
        origin_source="assistant_escalation",
        problem_statement="Problem 1"
    )
    service.create_case(1, request)
    
    # List cases
    result = service.list_customer_cases(1)
    
    assert result["total"] >= 1
    assert len(result["items"]) >= 1
    assert result["items"][0].customer_user_id == 1


def test_case_service_get_case(db_session):
    """Test case service gets case by ID"""
    service = CaseService(db_session)
    
    request = CreateCaseRequest(
        origin_source="assistant_escalation",
        problem_statement="Problem for retrieval"
    )
    created = service.create_case(1, request)
    
    # Get case
    retrieved = service.get_case(created.id)
    
    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.case_ref == created.case_ref
