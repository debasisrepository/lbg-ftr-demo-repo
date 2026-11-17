from sqlalchemy.orm import Session
from app.services.case.models import CaseRecord, ConversationThread, ConversationEntry, CaseAssignment
from app.services.case.schemas import CreateCaseRequest, CaseResponse
from uuid import uuid4, UUID
from app.core.clock import Clock
from datetime import timedelta


class CaseService:
    """Case service - customer-visible continuity record of truth"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_case(
        self,
        customer_user_id: int,
        request: CreateCaseRequest,
        thread_id: UUID | None = None
    ) -> CaseResponse:
        """Create a Case with unique case_ref, attach thread, route to queue"""
        case_id = uuid4()
        case_ref = self._generate_case_ref()
        
        # Create or attach thread
        if thread_id:
            thread = self.db.query(ConversationThread).filter(
                ConversationThread.id == thread_id
            ).first()
        else:
            thread = self._create_thread(case_id)
            thread_id = thread.id
        
        # Calculate expected_by (48 hours for demo)
        expected_by_at = Clock.utc_now() + timedelta(hours=48)
        
        case = CaseRecord(
            id=case_id,
            case_ref=case_ref,
            customer_user_id=customer_user_id,
            status="new",
            origin_source=request.origin_source,
            problem_statement=request.problem_statement,
            classification=request.classification,
            arrangement_reference=request.arrangement_reference,
            current_queue_ref="general_support_queue",
            owner_team_display="Customer Support Team",
            owner_colleague_display=None,
            route_reason=request.route_reason or "Created from app entry",
            continuation_path="conversation",
            regulatory_clock_applicable=False,
            regulatory_clock_type=None,
            expected_by_at=expected_by_at,
            last_update_at=Clock.utc_now(),
            last_heartbeat_at=Clock.utc_now(),
            closed_at=None,
            created_at=Clock.utc_now()
        )
        
        self.db.add(case)
        self.db.flush()  # Flush case before creating assignment that references it
        
        # Update thread to link to case
        if thread:
            thread.case_id = case_id
        
        # Create initial assignment
        assignment = CaseAssignment(
            id=uuid4(),
            case_id=case_id,
            assignment_type="queue_owner",
            queue_ref="general_support_queue",
            team_ref=None,
            colleague_user_id=None,
            is_current=True,
            assigned_at=Clock.utc_now()
        )
        self.db.add(assignment)
        
        self.db.flush()
        
        return CaseResponse(
            id=case.id,
            case_ref=case.case_ref,
            customer_user_id=case.customer_user_id,
            status=case.status,
            problem_statement=case.problem_statement,
            classification=case.classification,
            owner_team_display=case.owner_team_display,
            expected_by_at=case.expected_by_at,
            created_at=case.created_at
        )
    
    def _generate_case_ref(self) -> str:
        """Generate unique case reference CP-YYYY-NNNNNN"""
        from datetime import datetime
        year = datetime.now().year
        # Simplified: use UUID as integer mod 1000000 for numeric 6-digit sequence
        seq = uuid4().int % 1000000
        return f"CP-{year}-{seq:06d}"
    
    def _create_thread(self, case_id: UUID) -> ConversationThread:
        thread = ConversationThread(
            id=uuid4(),
            case_id=case_id,
            entry_point="resolve_assistant",
            entry_context_type="none",
            entry_context_ref=None,
            ai_disclosure_at=Clock.utc_now(),
            human_path_shown=True,
            created_at=Clock.utc_now()
        )
        self.db.add(thread)
        self.db.flush()
        return thread
    
    def get_case(self, case_id: UUID) -> CaseRecord | None:
        return self.db.query(CaseRecord).filter(CaseRecord.id == case_id).first()
    
    def list_customer_cases(self, customer_user_id: int, limit: int = 50, offset: int = 0):
        query = self.db.query(CaseRecord).filter(
            CaseRecord.customer_user_id == customer_user_id
        ).order_by(CaseRecord.last_update_at.desc())
        
        total = query.count()
        items = query.limit(limit).offset(offset).all()
        
        return {
            "items": items,
            "total": total
        }
