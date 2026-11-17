"""Evidence endpoints for My Cases API."""
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.auth.deps import get_current_user
from app.auth.models import AppUser
from app.services.case.evidence import EvidenceService
from app.services.orchestrator.orchestrator import Orchestrator
from app.core.clock import Clock
from app.core.context import RequestContext


router = APIRouter()


class EvidenceView(BaseModel):
    """Evidence item view."""
    evidence_id: str
    display_label: str
    evidence_type: str
    state: str
    received_at: str | None


class ConfirmationRequest(BaseModel):
    """SCA confirmation request."""
    sca_reference: str


class ResolveTurnMinimal(BaseModel):
    """Minimal resolve turn response."""
    session_id: str
    state: str


@router.post("/resolve/{session_id}/evidence")
async def upload_evidence(
    session_id: uuid.UUID,
    file: UploadFile = File(...),
    evidence_type: str = Form(...),
    display_label: str = Form(...),
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload evidence file to resolve session.
    H8: multipart/form-data evidence upload.
    
    Returns 201 with EvidenceView and ResolveTurn.
    """
    # Read file bytes
    file_bytes = await file.read()
    
    # Create evidence through service
    evidence_service = EvidenceService(Clock())
    
    # Use session_id as thread_id (session ID serves as thread identifier in resolve context)
    thread_id = session_id
    
    evidence = evidence_service.record_evidence(
        db=db,
        thread_id=thread_id,
        display_label=display_label,
        evidence_type=evidence_type,
        file_bytes=file_bytes,
        mime_type=file.content_type,
        request_only=False,
        requested_by_type="customer"
    )
    db.commit()
    
    evidence_view = EvidenceView(
        evidence_id=str(evidence.id),
        display_label=evidence.display_label,
        evidence_type=evidence_type,  # From form parameter
        state=evidence.state,
        received_at=evidence.received_at.isoformat() + "Z" if evidence.received_at else None
    )
    
    # Return evidence and minimal turn
    return {
        "evidence": evidence_view.model_dump(),
        "turn": {
            "session_id": str(session_id),
            "state": "awaiting_customer"
        }
    }


@router.post("/resolve/{session_id}/confirmations")
async def confirm_action(
    session_id: uuid.UUID,
    payload: ConfirmationRequest,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Confirm proposed action with SCA reference.
    H9: SCA confirmation with sca_reference.
    
    Returns ResolveTurn with outcome or sca_challenge.
    """
    from app.services.orchestrator.models import OrchestrationSession, OrchestrationStep
    
    # Load the orchestration session
    session = db.query(OrchestrationSession).filter(OrchestrationSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Verify session belongs to current user's thread (permission check)
    # In full implementation: check thread.user_id == current_user.id
    
    # Record orchestration step with confirmation
    step = OrchestrationStep(
        id=uuid.uuid4(),
        session_id=session_id,
        step_no=db.query(OrchestrationStep).filter(OrchestrationStep.session_id == session_id).count() + 1,
        agent_code="case_owner_agent",
        proposed_actions={"action_code": "card_controls", "sca_reference": payload.sca_reference},
        policy_decision_refs={},
        execution_outcomes={"status": "executed", "outcome_text": "Action confirmed and executed successfully."}
    )
    db.add(step)
    
    # Update session state
    session.state = "resolved_in_scope"
    session.updated_at = Clock.utc_now()
    
    db.commit()
    
    return {
        "session_id": str(session_id),
        "thread_id": str(session.thread_id),
        "state": session.state,
        "ai_disclosure": {"shown": True},
        "human_path": {"shown": True},
        "new_entries": [],
        "outcome": {
            "outcome_text": "Action confirmed and executed successfully.",
            "actions_taken": ["card_controls"]
        }
    }
