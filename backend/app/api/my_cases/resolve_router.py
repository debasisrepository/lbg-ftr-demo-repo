from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.deps import get_current_user
from app.auth.models import AppUser
from app.api.my_cases.schemas import (
    StartResolveRequest, SendMessageRequest,
    ResolveTurnResponse, ResolveSessionView, HumanRequestResponse
)
from app.services.orchestrator.orchestrator import Orchestrator
from uuid import UUID


router = APIRouter()


@router.post("/resolve", response_model=ResolveTurnResponse, tags=["resolve"])
def start_resolve(
    payload: StartResolveRequest,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new resolve session"""
    orchestrator = Orchestrator(db)
    
    from app.services.orchestrator.schemas import StartSessionRequest
    request = StartSessionRequest(
        message_text=payload.message_text,
        entry_context_type=payload.entry_context_type,
        entry_context_ref=payload.entry_context_ref,
        status_context_shown=payload.status_context_shown
    )
    
    result = orchestrator.start_session(current_user.id, request)
    db.commit()
    
    from app.api.my_cases.schemas import ResolveTurnEntry as ApiEntry
    new_entries = [
        ApiEntry(
            role=e.role,
            content_text=e.content_text,
            occurred_at=e.occurred_at
        )
        for e in result.new_entries
    ]
    
    return ResolveTurnResponse(
        session_id=result.session_id,
        thread_id=result.thread_id,
        state=result.state,
        ai_disclosure=result.ai_disclosure,
        human_path_shown=result.human_path_shown,
        new_entries=new_entries,
        case_ref=result.case_ref,
        case_id=result.case_id,
        classification=result.classification
    )


@router.get("/resolve/{session_id}", response_model=ResolveSessionView, tags=["resolve"])
def get_resolve_session(
    session_id: UUID,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current session state with transcript"""
    orchestrator = Orchestrator(db)
    
    try:
        view = orchestrator.get_session_view(session_id)
        return view
    except ValueError:
        raise HTTPException(status_code=404, detail="Session not found")


@router.post("/resolve/{session_id}/messages", response_model=ResolveTurnResponse, tags=["resolve"])
def send_message(
    session_id: UUID,
    payload: SendMessageRequest,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send customer message in existing session"""
    orchestrator = Orchestrator(db)
    
    try:
        result = orchestrator.handle_message(session_id, current_user.id, payload.message_text)
        db.commit()
        
        from app.api.my_cases.schemas import ResolveTurnEntry as ApiEntry
        new_entries = [
            ApiEntry(
                role=e.role,
                content_text=e.content_text,
                occurred_at=e.occurred_at
            )
            for e in result.new_entries
        ]
        
        return ResolveTurnResponse(
            session_id=result.session_id,
            thread_id=result.thread_id,
            state=result.state,
            ai_disclosure=result.ai_disclosure,
            human_path_shown=result.human_path_shown,
            new_entries=new_entries,
            case_ref=result.case_ref,
            case_id=result.case_id,
            classification=result.classification
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Session not found")


@router.post("/resolve/{session_id}/human-request", response_model=HumanRequestResponse, tags=["resolve"])
def request_human(
    session_id: UUID,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Explicit escalation to human via Case creation"""
    orchestrator = Orchestrator(db)
    
    try:
        result = orchestrator.request_human(session_id, current_user.id)
        db.commit()
        return HumanRequestResponse(**result)
    except ValueError:
        raise HTTPException(status_code=404, detail="Session not found")
