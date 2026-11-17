from sqlalchemy.orm import Session
from app.services.orchestrator.repository import OrchestrationRepository
from app.services.orchestrator.schemas import StartSessionRequest, ResolveTurn, ResolveTurnEntry, ResolveSessionView
from app.services.redaction.boundary import RedactionBoundary
from app.agents.intake_triage import IntakeTriageAgent
from app.agents.guardrail import GuardrailSupervisorAgent
from app.services.case.service import CaseService
from app.services.case.schemas import CreateCaseRequest
from app.services.case.models import ConversationThread, ConversationEntry
from uuid import uuid4, UUID
from app.core.clock import Clock


class Orchestrator:
    """Coordinates agent flows and consumes interactive stimuli"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = OrchestrationRepository(db)
        self.redaction = RedactionBoundary()
        self.intake_agent = IntakeTriageAgent()
        self.guardrail = GuardrailSupervisorAgent()
        self.case_service = CaseService(db)
    
    def start_session(self, customer_user_id: int, request: StartSessionRequest) -> ResolveTurn:
        """Start a new resolve session"""
        session_id = uuid4()
        thread_id = uuid4()
        
        # Create thread
        thread = ConversationThread(
            id=thread_id,
            case_id=None,
            entry_point="resolve_assistant",
            entry_context_type=request.entry_context_type or "none",
            entry_context_ref=request.entry_context_ref,
            ai_disclosure_at=Clock.utc_now(),
            human_path_shown=True,
            created_at=Clock.utc_now()
        )
        self.db.add(thread)
        
        # Create orchestration session
        self.repo.create_session(
            session_id=session_id,
            thread_id=thread_id,
            trigger_type="customer_message",
            entry_context_ref=request.entry_context_ref,
            status_context_shown=request.status_context_shown
        )
        
        # Redact customer input
        redacted = self.redaction.redact(request.message_text)
        
        # Record customer message
        customer_entry = self._add_entry(thread_id, "customer", redacted.text, 1)
        
        # AI disclosure
        disclosure_entry = self._add_entry(
            thread_id, "system",
            "This assistant is AI. You can ask for a person at any time.",
            2
        )
        
        # Run intake agent
        agent_result = self.intake_agent.process(redacted.text, {})
        
        # Run guardrail check
        guardrail_result = self.guardrail.screen(redacted.text, {
            'confidence_pct': agent_result.confidence_pct
        })
        
        new_entries = [
            ResolveTurnEntry(
                role="customer",
                content_text=redacted.text,
                occurred_at=customer_entry.occurred_at
            ),
            ResolveTurnEntry(
                role="system",
                content_text=disclosure_entry.content_text,
                occurred_at=disclosure_entry.occurred_at
            )
        ]
        
        # If out of scope or guardrail triggers, prepare for case creation
        if not agent_result.in_scope or guardrail_result.force_human:
            # Add assistant response indicating handoff
            assistant_msg = "I'll connect you with our team who can help with this."
            assistant_entry = self._add_entry(thread_id, "assistant", assistant_msg, 3)
            new_entries.append(ResolveTurnEntry(
                role="assistant",
                content_text=assistant_msg,
                occurred_at=assistant_entry.occurred_at
            ))
        else:
            # In scope - assistant can proceed
            assistant_msg = f"I understand you're asking about {agent_result.classification}. How can I help?"
            assistant_entry = self._add_entry(thread_id, "assistant", assistant_msg, 3)
            new_entries.append(ResolveTurnEntry(
                role="assistant",
                content_text=assistant_msg,
                occurred_at=assistant_entry.occurred_at
            ))
        
        self.db.flush()
        
        return ResolveTurn(
            session_id=session_id,
            thread_id=thread_id,
            state="started",
            ai_disclosure=True,
            human_path_shown=True,
            new_entries=new_entries,
            case_ref=None,
            case_id=None,
            classification=agent_result.classification
        )
    
    def handle_message(self, session_id: UUID, customer_user_id: int, message_text: str) -> ResolveTurn:
        """Handle customer message in existing session"""
        session = self.repo.get_session(session_id)
        if not session:
            raise ValueError("Session not found")
        
        # Redact input
        redacted = self.redaction.redact(message_text)
        
        # Get next seq
        last_entry = self.db.query(ConversationEntry).filter(
            ConversationEntry.thread_id == session.thread_id
        ).order_by(ConversationEntry.thread_seq.desc()).first()
        next_seq = (last_entry.thread_seq + 1) if last_entry else 1
        
        # Add customer message
        customer_entry = self._add_entry(session.thread_id, "customer", redacted.text, next_seq)
        
        # Simple response
        assistant_msg = "Thank you for that information. Let me help you with this."
        assistant_entry = self._add_entry(session.thread_id, "assistant", assistant_msg, next_seq + 1)
        
        self.db.flush()
        
        new_entries = [
            ResolveTurnEntry(
                role="customer",
                content_text=redacted.text,
                occurred_at=customer_entry.occurred_at
            ),
            ResolveTurnEntry(
                role="assistant",
                content_text=assistant_msg,
                occurred_at=assistant_entry.occurred_at
            )
        ]
        
        return ResolveTurn(
            session_id=session_id,
            thread_id=session.thread_id,
            state=session.state,
            ai_disclosure=True,
            human_path_shown=True,
            new_entries=new_entries,
            case_ref=None,
            case_id=session.case_id,
            classification=None
        )
    
    def request_human(self, session_id: UUID, customer_user_id: int) -> dict:
        """Explicit escalation to human via Case creation"""
        session = self.repo.get_session(session_id)
        if not session:
            raise ValueError("Session not found")
        
        # Get problem statement from thread
        entries = self.db.query(ConversationEntry).filter(
            ConversationEntry.thread_id == session.thread_id,
            ConversationEntry.role == "customer"
        ).order_by(ConversationEntry.thread_seq).all()
        
        problem_statement = " ".join([e.content_text for e in entries[:2]])
        
        # Create case
        case = self.case_service.create_case(
            customer_user_id=customer_user_id,
            request=CreateCaseRequest(
                origin_source="assistant_escalation",
                problem_statement=problem_statement,
                classification="general_query",
                route_reason="Explicit human request"
            ),
            thread_id=session.thread_id
        )
        
        # Update session
        self.repo.update_session_state(session_id, "handed_off", case.id)
        
        self.db.flush()
        
        return {
            "session_id": session_id,
            "thread_id": session.thread_id,
            "case_ref": case.case_ref,
            "case_id": case.id,
            "owner_team_display": case.owner_team_display,
            "expected_by_at": case.expected_by_at
        }
    
    def get_session_view(self, session_id: UUID) -> ResolveSessionView:
        """Get current session state with full transcript"""
        session = self.repo.get_session(session_id)
        if not session:
            raise ValueError("Session not found")
        
        entries = self.db.query(ConversationEntry).filter(
            ConversationEntry.thread_id == session.thread_id
        ).order_by(ConversationEntry.thread_seq).all()
        
        entry_list = [
            ResolveTurnEntry(
                role=e.role,
                content_text=e.content_text,
                occurred_at=e.occurred_at
            )
            for e in entries
        ]
        
        case_ref = None
        if session.case_id:
            case = self.case_service.get_case(session.case_id)
            case_ref = case.case_ref if case else None
        
        return ResolveSessionView(
            session_id=session_id,
            thread_id=session.thread_id,
            state=session.state,
            entries=entry_list,
            case_ref=case_ref,
            classification=None
        )
    
    def _add_entry(self, thread_id: UUID, role: str, content: str, seq: int) -> ConversationEntry:
        entry = ConversationEntry(
            id=uuid4(),
            thread_id=thread_id,
            thread_seq=seq,
            role=role,
            content_text=content,
            visibility_scope="customer_visible",
            redaction_status="clean",
            metadata_json=None,
            occurred_at=Clock.utc_now()
        )
        self.db.add(entry)
        return entry
