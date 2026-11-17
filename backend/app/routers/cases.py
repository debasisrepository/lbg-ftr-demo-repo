"""Cases router."""
import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.adapters.customer_case_adapter import CustomerCaseAdapter
from app.adapters.identity_adapter import IdentityAdapter
from app.adapters.management_api_adapter import ManagementApiAdapter
from app.core.clock import Clock
from app.core.errors import NotFoundError
from app.database import get_db
from app.deps import get_principal, require_scope
from app.repositories.action_repository import ActionRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.case_repository import CaseRepository
from app.repositories.config_repository import ConfigRepository
from app.repositories.continuity_repository import ContinuityRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.ownership_repository import OwnershipRepository
from app.schemas.case import (
    CaseCreateRequest,
    CaseCreationResult,
    CaseDetail,
    CaseSummary,
    CaseTransitionRequest,
    CaseTransitionResult,
    ExpectedByRevisionRequest,
    ExpectedByView,
    OwnerChangeRequest,
    OwnerView,
    Page,
)
from app.services.action_service import ActionService
from app.services.audit_service import AuditService
from app.services.case_service import CaseService
from app.services.continuity_service import ContinuityService
from app.services.history_service import HistoryService
from app.services.ownership_service import OwnershipService
from app.services.policy_service import PolicyService


class HandoffRequest(BaseModel):
    """Channel handoff request."""
    from_channel: str
    to_channel: str
    context_presented_flag: bool = False


class ReturnVisitRequest(BaseModel):
    """Return visit request."""
    return_session_token: str
    channel: str = "mobile_app"


class ProtectedActionRequest(BaseModel):
    """Protected action request."""
    action_type: str
    action_domain: str
    action_payload: dict


class SCAOutcomeRequest(BaseModel):
    """SCA outcome request."""
    sca_outcome: str
    sca_verification_token: str


class HistoryRequest(BaseModel):
    """History request parameters."""
    limit: int = 20
    offset: int = 0
    event_type: str | None = None


router = APIRouter()


def get_case_service(db: Session = Depends(get_db)) -> CaseService:
    """Get case service instance."""
    case_repo = CaseRepository(db)
    history_repo = HistoryRepository(db)
    ownership_repo = OwnershipRepository(db)
    config_repo = ConfigRepository(db)
    audit_repo = AuditRepository(db)

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


@router.post("/cases", response_model=CaseCreationResult)
def create_case(
    request_body: CaseCreateRequest,
    request: Request,
    response: Response,
    principal = Depends(require_scope("customer")),
    service: CaseService = Depends(get_case_service),
    db: Session = Depends(get_db)
):
    """Create a new case or surface existing one.

    Returns 201 for created, 200 for surfaced or not_eligible.
    """
    # Get correlation ID from request state (set by middleware)
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))

    result = service.create_case(
        principal_customer_party_id=principal.customer_party_id,
        principal_brand=principal.brand,
        request=request_body,
        correlation_id=correlation_id
    )

    # Commit the transaction
    db.commit()

    # Set status code based on outcome
    if result.outcome == "created":
        response.status_code = status.HTTP_201_CREATED

    return result


def get_continuity_service(db: Session = Depends(get_db)) -> ContinuityService:
    """Get continuity service instance."""
    continuity_repo = ContinuityRepository(db)
    case_repo = CaseRepository(db)
    ownership_repo = OwnershipRepository(db)
    history_repo = HistoryRepository(db)
    audit_repo = AuditRepository(db)

    audit_service = AuditService(audit_repo, Clock())

    return ContinuityService(
        continuity_repo=continuity_repo,
        case_repo=case_repo,
        ownership_repo=ownership_repo,
        history_repo=history_repo,
        audit_repo=audit_repo,
        audit_service=audit_service,
        clock=Clock()
    )


@router.get("/cases/{case_reference}/continuity")
def get_continuity_package(
    case_reference: str,
    principal = Depends(require_scope("customer")),
    service: ContinuityService = Depends(get_continuity_service)
) -> dict:
    """
    Get continuity package for a case (FR-013).

    Returns ContinuityPackage with context_version, customer_issue_summary,
    structured_context, shared_field_names, current_state, recent_updates,
    and channel_history.
    """
    try:
        return service.get_package(
            case_reference=case_reference,
            customer_party_id=principal.customer_party_id
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/cases/{case_reference}/handoffs", status_code=201)
def record_handoff(
    case_reference: str,
    request_body: HandoffRequest,
    request: Request,
    principal = Depends(require_scope("customer")),
    service: ContinuityService = Depends(get_continuity_service),
    db: Session = Depends(get_db)
):
    """
    Record a channel handoff (FR-015).

    Records handoff with from_channel, to_channel, and context_presented_flag.
    Sets continuity_state to refresh_pending.
    """
    # Get correlation ID from request state (set by middleware)
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))

    try:
        service.record_handoff(
            case_reference=case_reference,
            customer_party_id=principal.customer_party_id,
            from_channel=request_body.from_channel,
            to_channel=request_body.to_channel,
            context_presented_flag=request_body.context_presented_flag,
            correlation_id=correlation_id
        )

        # Commit the transaction
        db.commit()

        return {"message": "Handoff recorded"}
    except NotFoundError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


def get_ownership_service(db: Session = Depends(get_db)) -> OwnershipService:
    """Get ownership service instance."""
    ownership_repo = OwnershipRepository(db)
    case_repo = CaseRepository(db)
    history_repo = HistoryRepository(db)
    audit_repo = AuditRepository(db)

    audit_service = AuditService(audit_repo, Clock())

    return OwnershipService(
        ownership_repo=ownership_repo,
        case_repo=case_repo,
        history_repo=history_repo,
        audit_service=audit_service,
        clock=Clock()
    )


@router.post("/cases/{case_reference}/owner-changes", response_model=OwnerView, status_code=201)
def change_owner(
    case_reference: str,
    request_body: OwnerChangeRequest,
    request: Request,
    principal = Depends(require_scope("colleague")),
    service: OwnershipService = Depends(get_ownership_service),
    db: Session = Depends(get_db)
):
    """
    Change case owner (FR-008).

    Requires colleague scope.
    Validates owner_team_code, closes current ownership, inserts successor,
    appends OwnerChanged event, and queues continuity refresh.
    """
    # Get correlation ID from request state (set by middleware)
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))

    result = service.change_owner(
        case_reference=case_reference,
        request=request_body,
        correlation_id=correlation_id
    )

    # Commit the transaction
    db.commit()

    return result


@router.post("/cases/{case_reference}/expected-by-revisions", response_model=ExpectedByView, status_code=201)
def revise_expected_by(
    case_reference: str,
    request_body: ExpectedByRevisionRequest,
    request: Request,
    principal = Depends(require_scope("colleague")),
    service: OwnershipService = Depends(get_ownership_service),
    db: Session = Depends(get_db)
):
    """
    Revise expected-by commitment (FR-009).

    Requires colleague scope.
    Applies revision rules, closes current commitment, inserts successor,
    and appends ExpectedByChanged event.
    """
    # Get correlation ID from request state (set by middleware)
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))

    result = service.revise_expected_by(
        case_reference=case_reference,
        request=request_body,
        correlation_id=correlation_id
    )

    # Commit the transaction
    db.commit()

    return result


@router.get("/cases", response_model=Page[CaseSummary])
def list_cases(
    lifecycle_state: str | None = None,
    include_closed: bool = True,
    limit: int = 20,
    offset: int = 0,
    principal = Depends(require_scope("customer")),
    service: CaseService = Depends(get_case_service)
):
    """List cases for a customer with pagination."""
    # Validate limit
    if limit < 1 or limit > 100:
        limit = 20
    if offset < 0:
        offset = 0

    summaries, total = service.list_cases(
        customer_party_id=principal.customer_party_id,
        lifecycle_state=lifecycle_state,
        include_closed=include_closed,
        limit=limit,
        offset=offset
    )

    return Page(items=summaries, total=total, limit=limit, offset=offset)


@router.get("/cases/{case_reference}", response_model=CaseDetail)
def get_case(
    case_reference: str,
    principal = Depends(require_scope("customer")),
    service: CaseService = Depends(get_case_service)
):
    """Get a case by reference."""
    try:
        return service.get_case(
            customer_party_id=principal.customer_party_id,
            case_reference=case_reference
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/cases/{case_reference}/transitions", response_model=CaseTransitionResult, status_code=201)
def transition_case(
    case_reference: str,
    request_body: CaseTransitionRequest,
    request: Request,
    principal = Depends(get_principal),
    service: CaseService = Depends(get_case_service),
    db: Session = Depends(get_db)
):
    """
    Transition a case to a new lifecycle state.

    Requires colleague scope with entitlement for the customer.
    Returns 201 with the updated case and the transition event.
    """
    # Get correlation ID from request state (set by middleware)
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))

    result = service.transition(
        case_reference=case_reference,
        request=request_body,
        correlation_id=correlation_id
    )

    # Commit the transaction
    db.commit()

    return result


@router.post("/cases/{case_reference}/return-visits")
def restore_return_visit(
    case_reference: str,
    request_body: ReturnVisitRequest,
    request: Request,
    principal = Depends(require_scope("customer")),
    service: ContinuityService = Depends(get_continuity_service),
    db: Session = Depends(get_db)
):
    """
    Restore continuity for return visit after re-authentication (FR-017).

    Validates return session token, retrieves current case state,
    and returns continuity package with recent updates.

    Returns:
        dict with case, recent_updates, context_version, return_visit_restored_at
    """
    # Get correlation ID from request state (set by middleware)
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))

    try:
        result = service.restore_return_visit(
            case_reference=case_reference,
            return_session_token=request_body.return_session_token,
            channel=request_body.channel,
            correlation_id=correlation_id
        )

        # Commit the transaction
        db.commit()

        return result
    except NotFoundError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


def get_action_service(db: Session = Depends(get_db)) -> ActionService:
    """Get action service instance."""
    action_repo = ActionRepository(db)
    case_repo = CaseRepository(db)
    history_repo = HistoryRepository(db)
    audit_repo = AuditRepository(db)

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


@router.post("/cases/{case_reference}/actions", status_code=201)
def start_protected_action(
    case_reference: str,
    request_body: ProtectedActionRequest,
    request: Request,
    principal = Depends(require_scope("customer")),
    service: ActionService = Depends(get_action_service),
    db: Session = Depends(get_db)
):
    """
    Start a protected action with SCA (FR-029, FR-032).

    Returns 201 with action_id and sca_challenge_reference.
    """
    # Get correlation ID from request state (set by middleware)
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))

    try:
        result = service.start(
            customer_party_id=principal.customer_party_id,
            case_reference=case_reference,
            action_type=request_body.action_type,
            action_domain=request_body.action_domain,
            action_payload=request_body.action_payload,
            correlation_id=correlation_id
        )

        # Commit the transaction
        db.commit()

        return result
    except NotFoundError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to start protected action: {str(e)}"
        )


@router.post("/cases/{case_reference}/actions/{action_id}/sca-outcome")
def report_sca_outcome(
    case_reference: str,
    action_id: str,
    request_body: SCAOutcomeRequest,
    request: Request,
    principal = Depends(require_scope("customer")),
    service: ActionService = Depends(get_action_service),
    db: Session = Depends(get_db)
):
    """
    Report SCA outcome and execute or abort action (FR-029, FR-032).

    Returns action status with request_status, sca_outcome, and completion details.
    Idempotent: repeat calls return stored state.
    """
    # Get correlation ID from request state (set by middleware)
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))

    try:
        result = service.report_outcome(
            customer_party_id=principal.customer_party_id,
            case_reference=case_reference,
            action_id=uuid.UUID(action_id),
            sca_outcome=request_body.sca_outcome,
            sca_verification_token=request_body.sca_verification_token,
            correlation_id=correlation_id
        )

        # Commit the transaction
        db.commit()

        return result
    except NotFoundError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/cases/{case_reference}/actions/{action_id}")
def get_protected_action(
    case_reference: str,
    action_id: str,
    principal = Depends(require_scope("customer")),
    db: Session = Depends(get_db)
):
    """
    Get protected action status (FR-029, FR-032).

    Returns current action state with request_status, sca_outcome, and timestamps.
    """
    action_repo = ActionRepository(db)

    try:
        action = action_repo.get_for_case(
            action_id=uuid.UUID(action_id),
            customer_party_id=principal.customer_party_id
        )

        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Action {action_id} not found"
            )

        return {
            "action_id": str(action.id),
            "action_type": action.action_type,
            "action_domain": action.action_domain,
            "request_status": action.request_status,
            "sca_outcome": action.sca_outcome,
            "sca_invoked_at": action.sca_invoked_at.isoformat() if action.sca_invoked_at else None,
            "sca_completed_at": action.sca_completed_at.isoformat() if action.sca_completed_at else None,
            "management_api_reference": action.management_api_reference,
            "fallback_guidance_text": action.fallback_guidance_text,
            "completed_at": action.completed_at.isoformat() if action.completed_at else None,
            "created_at": action.created_at.isoformat()
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action_id format"
        )


def get_history_service(db: Session = Depends(get_db)) -> HistoryService:
    """Get history service instance."""
    history_repo = HistoryRepository(db)
    return HistoryService(repo=history_repo)


@router.get("/cases/{case_reference}/history")
def get_case_history(
    case_reference: str,
    limit: int = 20,
    offset: int = 0,
    event_type: str | None = None,
    principal = Depends(require_scope("customer")),
    service: HistoryService = Depends(get_history_service),
    db: Session = Depends(get_db)
):
    """
    Get case history (FR-003).

    Returns paginated chronological events.
    Customer scope sees customer_visible_flag=TRUE rows only.
    Derives is_superseded for OwnerChanged and ExpectedByChanged events.
    """
    # Validate limit
    if limit < 1 or limit > 100:
        limit = 20
    if offset < 0:
        offset = 0

    from app.schemas.case import HistoryEvent

    # Get case to validate ownership and get case_id
    case_repo = CaseRepository(db)
    case = case_repo.get_by_reference_for_customer(case_reference, principal.customer_party_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_reference} not found"
        )

    # Build history pages
    customer_visible_only = (principal.scope == "customer")
    event_dicts, total = service.build_pages(
        case_id=case.id,
        limit=limit,
        offset=offset,
        event_type=event_type,
        customer_visible_only=customer_visible_only
    )

    # Convert to HistoryEvent schema
    history_events = []
    for event_dict in event_dicts:
        payload = event_dict.get("event_payload_json") or {}
        history_event = HistoryEvent(
            id=UUID(event_dict["id"]),
            sequence_number=event_dict["sequence_number"],
            event_type=event_dict["event_type"],
            event_timestamp=event_dict["event_timestamp"],
            summary_text=event_dict["summary_text"],
            customer_visible_flag=event_dict["customer_visible_flag"],
            actor_type=event_dict["actor_type"] if principal.scope == "colleague" else None,
            actor_reference=event_dict["actor_reference"] if principal.scope == "colleague" else None,
            basis_type=event_dict["basis_type"] if principal.scope == "colleague" else None,
            basis_reference=event_dict["basis_reference"] if principal.scope == "colleague" else None,
            lifecycle_from=payload.get("lifecycle_from"),
            lifecycle_to=payload.get("lifecycle_to")
        )
        history_events.append(history_event)

    return Page(items=history_events, total=total, limit=limit, offset=offset)
