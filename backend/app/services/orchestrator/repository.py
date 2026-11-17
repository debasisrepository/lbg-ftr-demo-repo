from sqlalchemy.orm import Session
from app.services.orchestrator.models import OrchestrationSession, OrchestrationStep, AgentCaseState
from uuid import UUID
from datetime import datetime
from app.core.clock import Clock


class OrchestrationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_session(
        self,
        session_id: UUID,
        thread_id: UUID,
        trigger_type: str,
        entry_context_ref: str | None,
        status_context_shown: bool
    ) -> OrchestrationSession:
        session = OrchestrationSession(
            id=session_id,
            thread_id=thread_id,
            case_id=None,
            trigger_type=trigger_type,
            state="started",
            entry_context_ref=entry_context_ref,
            status_context_shown=None,  # This is Text, not bool
            created_at=Clock.utc_now(),
            updated_at=Clock.utc_now()
        )
        self.db.add(session)
        self.db.flush()
        return session

    def get_session(self, session_id: UUID) -> OrchestrationSession | None:
        return self.db.query(OrchestrationSession).filter(OrchestrationSession.id == session_id).first()

    def update_session_state(self, session_id: UUID, state: str, case_id: UUID | None = None) -> None:
        session = self.get_session(session_id)
        if session:
            session.state = state
            if case_id:
                session.case_id = case_id
            session.updated_at = Clock.utc_now()
            self.db.flush()

    def record_step(
        self,
        session_id: UUID,
        step_no: int,
        agent_code: str,
        proposed_actions: dict,
        policy_decision_refs: list[UUID],
        execution_outcomes: dict
    ) -> OrchestrationStep:
        step = OrchestrationStep(
            session_id=session_id,
            step_no=step_no,
            agent_code=agent_code,
            proposed_actions=proposed_actions,
            policy_decision_refs=policy_decision_refs,
            execution_outcomes=execution_outcomes,
            occurred_at=Clock.utc_now()
        )
        self.db.add(step)
        self.db.flush()
        return step

    def get_or_create_agent_state(self, case_id: UUID, agent_code: str) -> AgentCaseState:
        state = self.db.query(AgentCaseState).filter(
            AgentCaseState.case_id == case_id,
            AgentCaseState.agent_code == agent_code
        ).first()
        if not state:
            state = AgentCaseState(
                case_id=case_id,
                agent_code=agent_code,
                state_json={},
                created_at=Clock.utc_now(),
                updated_at=Clock.utc_now()
            )
            self.db.add(state)
            self.db.flush()
        return state

    def update_agent_state(self, case_id: UUID, agent_code: str, state_json: dict) -> None:
        state = self.get_or_create_agent_state(case_id, agent_code)
        state.state_json = state_json
        state.updated_at = Clock.utc_now()
        self.db.flush()
