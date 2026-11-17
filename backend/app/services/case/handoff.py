"""Handoff pack assembly for colleague view."""
import uuid
from dataclasses import dataclass
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.case.models import CaseRecord, ConversationEntry, EvidenceItem


@dataclass
class HandoffPack:
    """Hand-off pack for colleague view."""
    case_id: uuid.UUID
    case_ref: str
    status_code: str
    problem_statement: str
    classification_code: str
    route_reason: str
    arrival_source: str
    expected_by_at: datetime
    owner_team_display: str
    owner_colleague_display: str | None
    handoff_summary_text: str
    vulnerability_flag: bool
    entry_count: int
    evidence_count: int


class HandoffPackAssembler:
    """Assemble hand-off pack for colleague view (FR-004)."""
    
    def assemble(self, db: Session, case_id: uuid.UUID) -> HandoffPack:
        """
        Assemble hand-off pack for colleague.
        Read transaction with bounded queries (NFR-005).
        
        Args:
            db: Database session
            case_id: Case UUID
        
        Returns:
            HandoffPack
        """
        # Load case
        case = db.query(CaseRecord).filter(CaseRecord.id == case_id).first()
        if not case:
            raise ValueError(f"Case {case_id} not found")
        
        # Get thread for this case
        from app.services.case.models import ConversationThread
        thread = db.query(ConversationThread).filter(ConversationThread.case_id == case_id).first()
        thread_id = thread.id if thread else None
        
        # Count entries and evidence
        entry_count = 0
        evidence_count = 0
        if thread_id:
            entry_count = db.query(ConversationEntry).filter(
                ConversationEntry.thread_id == thread_id
            ).count()
            
            evidence_count = db.query(EvidenceItem).filter(
                EvidenceItem.thread_id == thread_id
            ).count()
        
        return HandoffPack(
            case_id=case.id,
            case_ref=case.case_ref,
            status_code=case.status,
            problem_statement=case.problem_statement,
            classification_code=case.classification or "unclassified",
            route_reason=case.route_reason or "out_of_scope",
            arrival_source=case.origin_source,
            expected_by_at=case.expected_by_at,
            owner_team_display=case.owner_team_display or "Customer Support Team",
            owner_colleague_display=case.owner_colleague_display,
            handoff_summary_text="Case summary pending",
            vulnerability_flag=False,
            entry_count=entry_count,
            evidence_count=evidence_count
        )
