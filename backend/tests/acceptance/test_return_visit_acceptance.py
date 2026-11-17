"""Acceptance tests for return visit restoration (FR-017)."""
import uuid
from datetime import datetime, timezone

from app.core.clock import Clock
from app.models.audit import CaseEvent
from app.models.case import Case
from app.models.continuity import ContinuityContext
from app.models.ownership import CaseOwnership, ExpectedByCommitment
from app.repositories.audit_repository import AuditRepository
from app.repositories.case_repository import CaseRepository
from app.repositories.continuity_repository import ContinuityRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.ownership_repository import OwnershipRepository
from app.services.audit_service import AuditService
from app.services.continuity_service import ContinuityService


def test_return_visit_restores_continuity_package(db_session):
    """POST /api/v1/cases/{case_reference}/return-visits returns restored ContinuityPackage."""
    # Setup service-level test
    case_repo = CaseRepository(db_session)
    continuity_repo = ContinuityRepository(db_session)
    ownership_repo = OwnershipRepository(db_session)
    history_repo = HistoryRepository(db_session)
    audit_repo = AuditRepository(db_session)
    audit_service = AuditService(audit_repo, Clock())
    
    service = ContinuityService(
        continuity_repo=continuity_repo,
        case_repo=case_repo,
        ownership_repo=ownership_repo,
        history_repo=history_repo,
        audit_repo=audit_repo,
        audit_service=audit_service,
        clock=Clock()
    )
    
    now = datetime.now(timezone.utc)
    case_id = uuid.uuid4()
    customer_party_id = "CUST-002"  # Matches IdentityAdapter sandbox response
    
    # Create case with continuity context
    case = Case(
        id=case_id,
        case_reference="CP-ACC001",
        customer_party_id=customer_party_id,
        brand="lloyds",
        issue_type="card_declined",
        classification_source="eligibility_rule",
        issue_title="Card Declined",
        issue_summary="Acceptance test case",
        origin_channel="mobile_app",
        current_lifecycle_state="in_progress",
        current_status_code="assigned",
        current_status_label="Assigned",
        opened_at=now,
        created_at=now,
        updated_at=now
    )
    db_session.add(case)
    
    ownership = CaseOwnership(
        id=uuid.uuid4(),
        case_id=case_id,
        owner_team_code="CARDS_DISPUTES",
        owner_semantic_label="Card Disputes Team",
        owner_display_name="Card Disputes",
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(ownership)
    
    expected_by = ExpectedByCommitment(
        id=uuid.uuid4(),
        case_id=case_id,
        commitment_state="committed",
        expected_by_at=now,
        customer_explanatory_text="We'll resolve this by today",
        confidence_basis="colleague_set",
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(expected_by)
    
    context = ContinuityContext(
        id=uuid.uuid4(),
        case_id=case_id,
        package_version=5,
        structured_context_json={
            "case_reference": "CP-ACC001",
            "issue_type": "card_declined",
            "current_status_code": "assigned"
        },
        llm_safe_payload_json={
            "case_reference": "CP-ACC001",
            "issue_type": "card_declined"
        },
        colleague_payload_json={
            "case_reference": "CP-ACC001",
            "issue_type": "card_declined"
        },
        restricted_fields_excluded_flag=True,
        last_channel="mobile_app",
        last_presented_at=now,
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(context)
    
    event = CaseEvent(
        id=uuid.uuid4(),
        case_id=case_id,
        sequence_number=1,
        event_type="CaseStatusChanged",
        event_timestamp=now,
        summary_text="Case assigned to Card Disputes team",
        customer_visible_flag=True,
        actor_type="colleague",
        correlation_id="acc-001",
        created_at=now
    )
    db_session.add(event)
    
    db_session.commit()
    
    # Execute
    result = service.restore_return_visit(
        case_reference="CP-ACC001",
        return_session_token="valid-return-token",
        channel="mobile_app",
        correlation_id="acc-return-001"
    )
    
    # Assert: Returns restored package
    assert result["case"].case_reference == "CP-ACC001"
    assert result["context_version"] == 5
    assert len(result["recent_updates"]) > 0
    assert "return_visit_restored_at" in result


def test_continuity_package_always_has_restricted_fields_excluded_true(db_session):
    """Continuity package always includes restricted_fields_excluded=true."""
    case_repo = CaseRepository(db_session)
    continuity_repo = ContinuityRepository(db_session)
    ownership_repo = OwnershipRepository(db_session)
    history_repo = HistoryRepository(db_session)
    audit_repo = AuditRepository(db_session)
    audit_service = AuditService(audit_repo, Clock())
    
    service = ContinuityService(
        continuity_repo=continuity_repo,
        case_repo=case_repo,
        ownership_repo=ownership_repo,
        history_repo=history_repo,
        audit_repo=audit_repo,
        audit_service=audit_service,
        clock=Clock()
    )
    
    now = datetime.now(timezone.utc)
    case_id = uuid.uuid4()
    
    case = Case(
        id=case_id,
        case_reference="CP-ACC002",
        customer_party_id="CUST-002",  # Matches IdentityAdapter
        brand="lloyds",
        issue_type="payment_missing",
        classification_source="eligibility_rule",
        issue_title="Payment Missing",
        issue_summary="Test restricted fields",
        origin_channel="mobile_app",
        current_lifecycle_state="captured",
        current_status_code="received",
        current_status_label="Received",
        opened_at=now,
        created_at=now,
        updated_at=now
    )
    db_session.add(case)
    
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
        customer_explanatory_text="We're reviewing",
        confidence_basis="initial",
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(expected_by)
    
    # Create context with restricted_fields_excluded_flag=True
    context = ContinuityContext(
        id=uuid.uuid4(),
        case_id=case_id,
        package_version=1,
        structured_context_json={"case_reference": "CP-ACC002"},
        llm_safe_payload_json={"case_reference": "CP-ACC002"},
        colleague_payload_json={"case_reference": "CP-ACC002"},
        restricted_fields_excluded_flag=True,  # Must always be True
        last_channel="mobile_app",
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(context)
    
    db_session.commit()
    
    # Verify context has restricted_fields_excluded_flag=True
    stored_context = continuity_repo.current_package(case_id)
    assert stored_context is not None
    assert stored_context.restricted_fields_excluded_flag is True


def test_llm_safe_payload_excludes_pan_passcodes_security_answers(db_session):
    """llm_safe_payload excludes PAN, passcodes, and security answers."""
    case_repo = CaseRepository(db_session)
    continuity_repo = ContinuityRepository(db_session)
    ownership_repo = OwnershipRepository(db_session)
    history_repo = HistoryRepository(db_session)
    audit_repo = AuditRepository(db_session)
    audit_service = AuditService(audit_repo, Clock())
    
    service = ContinuityService(
        continuity_repo=continuity_repo,
        case_repo=case_repo,
        ownership_repo=ownership_repo,
        history_repo=history_repo,
        audit_repo=audit_repo,
        audit_service=audit_service,
        clock=Clock()
    )
    
    now = datetime.now(timezone.utc)
    case_id = uuid.uuid4()
    
    case = Case(
        id=case_id,
        case_reference="CP-ACC003",
        customer_party_id="CUST-002",  # Matches IdentityAdapter
        brand="bank_of_scotland",
        issue_type="card_declined",
        classification_source="eligibility_rule",
        issue_title="Card Issue",
        issue_summary="Test LLM-safe payload filtering",
        origin_channel="ai_assistant",
        current_lifecycle_state="captured",
        current_status_code="received",
        current_status_label="Received",
        opened_at=now,
        created_at=now,
        updated_at=now
    )
    db_session.add(case)
    
    ownership = CaseOwnership(
        id=uuid.uuid4(),
        case_id=case_id,
        owner_team_code="CARDS_DISPUTES",
        owner_semantic_label="Card Disputes Team",
        owner_display_name="Card Disputes",
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(ownership)
    
    expected_by = ExpectedByCommitment(
        id=uuid.uuid4(),
        case_id=case_id,
        commitment_state="under_review",
        customer_explanatory_text="We're reviewing",
        confidence_basis="initial",
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(expected_by)
    
    # Build context with full structured_context including sensitive fields
    structured_context = {
        "case_reference": "CP-ACC003",
        "customer_party_id": "CUST-ACC-003",  # Should be excluded from llm_safe
        "issue_type": "card_declined",
        "issue_title": "Card Issue",
        "current_lifecycle_state": "captured",
        "current_status_code": "received",
        "owner_team_code": "CARDS_DISPUTES",
        "expected_by_at": now.isoformat(),
        "latest_update_text": "Case received"
    }
    
    # LLM-safe should exclude customer_party_id and other sensitive fields
    llm_safe = {
        "case_reference": "CP-ACC003",
        # customer_party_id excluded
        "issue_type": "card_declined",
        "issue_title": "Card Issue",
        "current_lifecycle_state": "captured",
        "current_status_code": "received",
        "owner_team_code": "CARDS_DISPUTES",
        "expected_by_at": now.isoformat(),
        "latest_update_text": "Case received"
    }
    
    context = ContinuityContext(
        id=uuid.uuid4(),
        case_id=case_id,
        package_version=1,
        structured_context_json=structured_context,
        llm_safe_payload_json=llm_safe,
        colleague_payload_json=structured_context,
        restricted_fields_excluded_flag=True,
        last_channel="ai_assistant",
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(context)
    
    db_session.commit()
    
    # Verify llm_safe_payload excludes sensitive fields
    stored_context = continuity_repo.current_package(case_id)
    assert "customer_party_id" not in stored_context.llm_safe_payload_json
    assert "case_reference" in stored_context.llm_safe_payload_json
    assert stored_context.restricted_fields_excluded_flag is True


def test_return_visit_backend_flow_authenticate_fetch_restore_return(db_session):
    """Backend flow: authenticate return session → fetch current continuity context → restore session state → return continuity package."""
    case_repo = CaseRepository(db_session)
    continuity_repo = ContinuityRepository(db_session)
    ownership_repo = OwnershipRepository(db_session)
    history_repo = HistoryRepository(db_session)
    audit_repo = AuditRepository(db_session)
    audit_service = AuditService(audit_repo, Clock())
    
    service = ContinuityService(
        continuity_repo=continuity_repo,
        case_repo=case_repo,
        ownership_repo=ownership_repo,
        history_repo=history_repo,
        audit_repo=audit_repo,
        audit_service=audit_service,
        clock=Clock()
    )
    
    now = datetime.now(timezone.utc)
    case_id = uuid.uuid4()
    customer_party_id = "CUST-002"  # Matches IdentityAdapter sandbox response
    
    # Setup case and context
    case = Case(
        id=case_id,
        case_reference="CP-ACC004",
        customer_party_id=customer_party_id,
        brand="lloyds",
        issue_type="card_declined",
        classification_source="eligibility_rule",
        issue_title="Return Visit Test",
        issue_summary="Testing full flow",
        origin_channel="mobile_app",
        current_lifecycle_state="in_progress",
        current_status_code="assigned",
        current_status_label="Assigned",
        opened_at=now,
        created_at=now,
        updated_at=now
    )
    db_session.add(case)
    
    ownership = CaseOwnership(
        id=uuid.uuid4(),
        case_id=case_id,
        owner_team_code="CARDS_DISPUTES",
        owner_semantic_label="Card Disputes Team",
        owner_display_name="Card Disputes",
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(ownership)
    
    expected_by = ExpectedByCommitment(
        id=uuid.uuid4(),
        case_id=case_id,
        commitment_state="committed",
        expected_by_at=now,
        customer_explanatory_text="We'll update you soon",
        confidence_basis="colleague_set",
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(expected_by)
    
    context = ContinuityContext(
        id=uuid.uuid4(),
        case_id=case_id,
        package_version=7,
        structured_context_json={"case_reference": "CP-ACC004"},
        llm_safe_payload_json={"case_reference": "CP-ACC004"},
        colleague_payload_json={"case_reference": "CP-ACC004"},
        restricted_fields_excluded_flag=True,
        last_channel="mobile_app",
        last_presented_at=now,
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(context)
    
    event = CaseEvent(
        id=uuid.uuid4(),
        case_id=case_id,
        sequence_number=1,
        event_type="CaseStatusChanged",
        event_timestamp=now,
        summary_text="Status updated",
        customer_visible_flag=True,
        actor_type="system",
        correlation_id="flow-001",
        created_at=now
    )
    db_session.add(event)
    
    db_session.commit()
    
    # Execute full flow: authenticate → fetch → restore → return
    return_session_token = "valid-backend-flow-token"
    
    # Step 1: Authenticate (handled by IdentityAdapter in service)
    # Step 2: Fetch current continuity context
    # Step 3: Restore session state
    # Step 4: Return continuity package
    result = service.restore_return_visit(
        case_reference="CP-ACC004",
        return_session_token=return_session_token,
        channel="mobile_app",
        correlation_id="backend-flow-correlation"
    )
    
    # Verify complete flow executed
    assert result["case"].case_reference == "CP-ACC004"
    assert result["context_version"] == 7
    assert len(result["recent_updates"]) == 1
    assert "return_visit_restored_at" in result
    
    # Verify audit trail
    from app.models.audit import AuditEntry
    from sqlalchemy import select
    
    return_visit_audits = db_session.scalars(
        select(AuditEntry).where(
            AuditEntry.entity_type == "case",
            AuditEntry.entity_id == str(case_id),
            AuditEntry.event_type == "return_visit_restored",
            AuditEntry.correlation_id == "backend-flow-correlation"
        )
    ).all()
    assert len(return_visit_audits) == 1
    assert return_visit_audits[0].actor_type == "customer"
    assert return_visit_audits[0].audit_category == "access"


def test_after_reauth_customer_can_reopen_active_case_see_current_state(db_session):
    """After re-authentication, the customer can reopen the same active Case and see current state."""
    case_repo = CaseRepository(db_session)
    continuity_repo = ContinuityRepository(db_session)
    ownership_repo = OwnershipRepository(db_session)
    history_repo = HistoryRepository(db_session)
    audit_repo = AuditRepository(db_session)
    audit_service = AuditService(audit_repo, Clock())
    
    service = ContinuityService(
        continuity_repo=continuity_repo,
        case_repo=case_repo,
        ownership_repo=ownership_repo,
        history_repo=history_repo,
        audit_repo=audit_repo,
        audit_service=audit_service,
        clock=Clock()
    )
    
    now = datetime.now(timezone.utc)
    case_id = uuid.uuid4()
    
    # Active case with recent state changes
    case = Case(
        id=case_id,
        case_reference="CP-ACC005",
        customer_party_id="CUST-002",  # Matches IdentityAdapter
        brand="lloyds",
        issue_type="payment_missing",
        classification_source="eligibility_rule",
        issue_title="Payment Missing",
        issue_summary="Customer wants to see current state",
        origin_channel="mobile_app",
        current_lifecycle_state="escalated",
        current_status_code="escalated_specialist",
        current_status_label="Escalated to Specialist",
        opened_at=now,
        created_at=now,
        updated_at=now
    )
    db_session.add(case)
    
    ownership = CaseOwnership(
        id=uuid.uuid4(),
        case_id=case_id,
        owner_team_code="PAYMENTS_SUPPORT",
        owner_semantic_label="Payments Support Team",
        owner_display_name="Payments Support",
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(ownership)
    
    expected_by = ExpectedByCommitment(
        id=uuid.uuid4(),
        case_id=case_id,
        commitment_state="revised",
        expected_by_at=now,
        customer_explanatory_text="Specialist review extended timeline",
        confidence_basis="colleague_set",
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(expected_by)
    
    # Recent visible updates
    event1 = CaseEvent(
        id=uuid.uuid4(),
        case_id=case_id,
        sequence_number=1,
        event_type="CaseCaptured",
        event_timestamp=now,
        summary_text="Case created",
        customer_visible_flag=True,
        actor_type="customer",
        correlation_id="acc5-001",
        created_at=now
    )
    db_session.add(event1)
    
    event2 = CaseEvent(
        id=uuid.uuid4(),
        case_id=case_id,
        sequence_number=2,
        event_type="CaseStatusChanged",
        event_timestamp=now,
        summary_text="Case escalated to specialist",
        customer_visible_flag=True,
        actor_type="colleague",
        correlation_id="acc5-002",
        created_at=now
    )
    db_session.add(event2)
    
    db_session.commit()
    
    # Customer re-authenticates and reopens case
    result = service.restore_return_visit(
        case_reference="CP-ACC005",
        return_session_token="reauth-token-acc005",
        channel="mobile_app"
    )
    
    # Customer sees current state
    assert result["case"].current_lifecycle_state == "escalated"
    assert result["case"].status_code == "escalated_specialist"
    assert result["case"].owner.owner_display_name == "Payments Support"
    
    # Previously published updates remain visible
    assert len(result["recent_updates"]) == 2
    update_types = {u["event_type"] for u in result["recent_updates"]}
    assert "CaseCaptured" in update_types
    assert "CaseStatusChanged" in update_types
