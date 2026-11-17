"""Colleague cases API router."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.deps import get_current_user
from app.auth.models import AppUser
from app.services.case.models import CaseRecord, ConversationEntry, CaseAssignment
from app.services.case.service import CaseService
from app.services.case.evidence import EvidenceService
from app.services.case.handoff import HandoffPackAssembler

from app.api.colleague.schemas import (
    CreateColleagueCaseRequest,
    ColleagueCaseListResponse,
    HandoffPackResponse,
    ThreadResponse,
    ColleagueReplyRequest,
    EvidenceRequestRequest,
    PickupRequest
)
from app.api.colleague.presenters import present_case_list_item, present_transcript_entry
from app.core.clock import Clock


router = APIRouter()


@router.post("/colleague/cases")
async def create_colleague_case(
    payload: CreateColleagueCaseRequest,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create Case from colleague desktop (H14).
    Returns Case response.
    """
    if not current_user.is_colleague:
        raise HTTPException(status_code=403, detail="Colleague role required")
    
    # Create case through service
    case_service = CaseService(db)
    from app.services.case.schemas import CreateCaseRequest
    case = case_service.create_case(
        customer_user_id=current_user.id,
        request=CreateCaseRequest(
            origin_source=payload.origin_source,
            problem_statement=payload.problem_statement,
            classification="unclassified",
            route_reason="colleague_created"
        )
    )
    db.commit()
    
    return {
        "case_id": str(case.id),
        "case_ref": case.case_ref,
        "status": case.status,
        "problem_statement": payload.problem_statement
    }


@router.get("/colleague/cases")
async def list_colleague_cases(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ColleagueCaseListResponse:
    """
    List colleague worklist (H15).
    Returns paginated list of Cases with status, owner, expected_by.
    """
    if not current_user.is_colleague:
        raise HTTPException(status_code=403, detail="Colleague role required")
    
    # Query open cases
    query = db.query(CaseRecord).filter(
        CaseRecord.status.in_(["new", "assigned", "in_progress", "awaiting_customer", "awaiting_internal", "reopened"])
    )
    
    total = query.count()
    
    offset = (page - 1) * page_size
    cases = query.order_by(CaseRecord.last_update_at.desc()).offset(offset).limit(page_size).all()
    
    items = [present_case_list_item(case) for case in cases]
    
    return ColleagueCaseListResponse(items=items, total=total)


@router.get("/colleague/cases/{case_id}")
async def get_colleague_case(
    case_id: uuid.UUID,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> HandoffPackResponse:
    """
    Get hand-off pack for Case (H16).
    Returns one-screen summary with handling indicators, route reason, arrival source.
    """
    if not current_user.is_colleague:
        raise HTTPException(status_code=403, detail="Colleague role required")
    
    # Assemble handoff pack
    assembler = HandoffPackAssembler()
    pack = assembler.assemble(db, case_id)
    
    # Copilot note not included in read path (NFR-001, NFR-008)
    # Read path must remain independent of AI/agent availability
    copilot_note = None
    
    return HandoffPackResponse(
        case_id=str(pack.case_id),
        case_ref=pack.case_ref,
        status_code=pack.status_code,
        problem_statement=pack.problem_statement,
        classification_code=pack.classification_code,
        route_reason=pack.route_reason,
        arrival_source=pack.arrival_source,
        expected_by_at=pack.expected_by_at,
        owner_team_display=pack.owner_team_display,
        owner_colleague_display=pack.owner_colleague_display,
        handoff_summary_text=pack.handoff_summary_text,
        vulnerability_flag=pack.vulnerability_flag,
        entry_count=pack.entry_count,
        evidence_count=pack.evidence_count,
        copilot_note=copilot_note
    )


@router.get("/colleague/cases/{case_id}/thread")
async def get_thread(
    case_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ThreadResponse:
    """
    Get paginated conversation thread (H17).
    Returns entries with role labels and visibility scopes.
    """
    if not current_user.is_colleague:
        raise HTTPException(status_code=403, detail="Colleague role required")
    
    # Load case to get thread_id
    case = db.query(CaseRecord).filter(CaseRecord.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Get thread for this case
    from app.services.case.models import ConversationThread
    thread = db.query(ConversationThread).filter(ConversationThread.case_id == case_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found for case")
    
    # Query entries
    query = db.query(ConversationEntry).filter(
        ConversationEntry.thread_id == thread.id
    )
    
    total = query.count()
    
    offset = (page - 1) * page_size
    entries = query.order_by(ConversationEntry.thread_seq).offset(offset).limit(page_size).all()
    
    entry_responses = [present_transcript_entry(e) for e in entries]
    
    return ThreadResponse(entries=entry_responses, total=total)


@router.post("/colleague/cases/{case_id}/thread/entries")
async def post_colleague_reply(
    case_id: uuid.UUID,
    payload: ColleagueReplyRequest,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Post colleague reply to thread (H18).
    Allows customer-visible or colleague-only visibility.
    """
    if not current_user.is_colleague:
        raise HTTPException(status_code=403, detail="Colleague role required")
    
    # Load case
    case = db.query(CaseRecord).filter(CaseRecord.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Get thread for this case
    from app.services.case.models import ConversationThread
    thread = db.query(ConversationThread).filter(ConversationThread.case_id == case_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found for case")
    
    # Create entry - thread_seq not entry_seq
    entry = ConversationEntry(
        id=uuid.uuid4(),
        thread_id=thread.id,
        thread_seq=db.query(ConversationEntry).filter(
            ConversationEntry.thread_id == thread.id
        ).count() + 1,
        role="colleague",
        content_text=payload.content_text,
        visibility_scope=payload.visibility_scope,
        redaction_status="clean",
        occurred_at=Clock().utc_now()
    )
    db.add(entry)
    db.commit()
    
    return present_transcript_entry(entry).model_dump()


@router.post("/colleague/cases/{case_id}/evidence-requests")
async def request_evidence(
    case_id: uuid.UUID,
    payload: EvidenceRequestRequest,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Request additional evidence (H19).
    Creates evidence_item in requested state.
    """
    if not current_user.is_colleague:
        raise HTTPException(status_code=403, detail="Colleague role required")
    
    # Load case
    case = db.query(CaseRecord).filter(CaseRecord.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Get thread for this case
    from app.services.case.models import ConversationThread
    thread = db.query(ConversationThread).filter(ConversationThread.case_id == case_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found for case")
    
    # Record evidence request
    evidence_service = EvidenceService(Clock())
    evidence = evidence_service.record_evidence(
        db=db,
        thread_id=thread.id,
        display_label=payload.display_label,
        evidence_type=payload.evidence_type,
        request_only=True,
        requested_by_type="colleague"
    )
    db.commit()
    
    return {
        "evidence_id": str(evidence.id),
        "display_label": evidence.display_label,
        "state": evidence.state
    }


@router.post("/colleague/cases/{case_id}/pickup")
async def pickup_case(
    case_id: uuid.UUID,
    payload: PickupRequest,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Pickup case assignment (H21).
    Assigns Case to colleague, records colleague_owner in case_assignment.
    """
    if not current_user.is_colleague:
        raise HTTPException(status_code=403, detail="Colleague role required")
    
    # Load case
    case = db.query(CaseRecord).filter(CaseRecord.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Check if already owned by another colleague
    existing = db.query(CaseAssignment).filter(
        CaseAssignment.case_id == case_id,
        CaseAssignment.assignment_type == "colleague_owner",
        CaseAssignment.is_current == True
    ).first()
    
    colleague_user_id_int = int(payload.colleague_user_id) if payload.colleague_user_id else current_user.id
    
    if existing and existing.colleague_user_id != colleague_user_id_int:
        raise HTTPException(
            status_code=409,
            detail=f"Case already owned by another colleague"
        )
    
    if existing and existing.colleague_user_id == colleague_user_id_int:
        # Already owned by this colleague, return unchanged
        return {
            "case_id": str(case.id),
            "case_ref": case.case_ref,
            "owner_colleague_display": case.owner_colleague_display
        }
    
    # Release existing colleague owner if present
    if existing:
        existing.is_current = False
    
    # Create new assignment
    assignment = CaseAssignment(
        id=uuid.uuid4(),
        case_id=case_id,
        assignment_type="colleague_owner",
        colleague_user_id=colleague_user_id_int,
        is_current=True,
        assigned_at=Clock().utc_now()
    )
    db.add(assignment)
    
    # Update case
    case.owner_colleague_display = current_user.email
    db.commit()
    
    return {
        "case_id": str(case.id),
        "case_ref": case.case_ref,
        "owner_colleague_display": case.owner_colleague_display
    }


@router.get("/colleague/cases/{case_id}/evidence/{evidence_id}/content")
async def get_evidence_content(
    case_id: uuid.UUID,
    evidence_id: uuid.UUID,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get evidence content (H20).
    Returns evidence file stream.
    """
    if not current_user.is_colleague:
        raise HTTPException(status_code=403, detail="Colleague role required")
    
    # For demo: stub response
    # In production: EvidenceStorage.open(storage_ref) returns stream
    return {
        "evidence_id": str(evidence_id),
        "content_available": False,
        "message": "Evidence content retrieval not implemented in demo"
    }
