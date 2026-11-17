from sqlalchemy.orm import Session
from app.services.policy.models import PolicyDecision, ActionControl
from app.services.policy.schemas import PolicyEvaluationRequest, PolicyDecisionResponse
from uuid import uuid4
from app.core.clock import Clock


class PolicyEngine:
    """Deterministic policy engine - sole authority for L0-L3 autonomy enforcement"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def evaluate(self, request: PolicyEvaluationRequest) -> PolicyDecisionResponse:
        """
        Apply seven policy rules in order:
        1. Kill switch check (agent + action)
        2. L3 actions always human-only
        3. Vulnerability/distress → escalate
        4. Low confidence/repeated failure → escalate
        5. Explicit human request → escalate
        6. SCA requirement for card/money actions
        7. Approval within autonomy level
        """
        action = self.db.query(ActionControl).filter(
            ActionControl.action_code == request.action_code
        ).first()
        
        if not action:
            return self._deny("autonomy_exceeded", None, request)
        
        # Rule 1: Kill switch
        if action.kill_switch_active:
            return self._escalate("kill_switch_active", action, request)
        
        # Rule 2: L3 always human
        if action.max_autonomy_level >= 3:
            return self._escalate("l3_human_only", action, request)
        
        # Rule 3: Vulnerability/distress
        vuln_triggers = {'vulnerability', 'distress', 'scam_in_progress'}
        if any(v in request.vulnerability_indicators for v in vuln_triggers):
            return self._escalate("vulnerability_detected", action, request)
        
        # Rule 4: Low confidence
        if request.confidence_pct is not None and request.confidence_pct < 70:
            return self._escalate("low_confidence", action, request)
        
        if request.repeated_failure:
            return self._escalate("repeated_failure", action, request)
        
        # Rule 5: Explicit human request
        if request.explicit_human_request:
            return self._escalate("explicit_human_request", action, request)
        
        # Rule 6 & 7: SCA check and approval
        sca_required = action.sca_required
        
        if sca_required and not request.authenticated:
            return self._deny("sca_required", action, request)
        
        # Approve within autonomy level
        return self._approve(action, sca_required, request)
    
    def _approve(self, action: ActionControl, sca_required: bool, request: PolicyEvaluationRequest) -> PolicyDecisionResponse:
        decision_id = uuid4()
        decision = PolicyDecision(
            id=decision_id,
            session_id=request.session_id or uuid4(),
            action_code=action.action_code,
            outcome="approved",
            reason_code="within_autonomy_level",
            sca_reference=None,
            evaluation_context={},
            occurred_at=Clock.utc_now()
        )
        self.db.add(decision)
        self.db.flush()
        
        return PolicyDecisionResponse(
            outcome="approved",
            reason_code="within_autonomy_level",
            sca_required=sca_required,
            decision_id=decision_id,
            evaluation_context={}
        )
    
    def _deny(self, reason: str, action: ActionControl | None = None, request: PolicyEvaluationRequest | None = None) -> PolicyDecisionResponse:
        decision_id = uuid4()
        action_code = action.action_code if action else "unknown"
        decision = PolicyDecision(
            id=decision_id,
            session_id=request.session_id if request and request.session_id else uuid4(),
            action_code=action_code,
            outcome="denied",
            reason_code=reason,
            sca_reference=None,
            evaluation_context={},
            occurred_at=Clock.utc_now()
        )
        self.db.add(decision)
        self.db.flush()
        
        return PolicyDecisionResponse(
            outcome="denied",
            reason_code=reason,
            sca_required=False,
            decision_id=decision_id,
            evaluation_context={}
        )
    
    def _escalate(self, reason: str, action: ActionControl, request: PolicyEvaluationRequest) -> PolicyDecisionResponse:
        decision_id = uuid4()
        decision = PolicyDecision(
            id=decision_id,
            session_id=request.session_id or uuid4(),
            action_code=action.action_code,
            outcome="escalate_human",
            reason_code=reason,
            sca_reference=None,
            evaluation_context={},
            occurred_at=Clock.utc_now()
        )
        self.db.add(decision)
        self.db.flush()
        
        return PolicyDecisionResponse(
            outcome="escalate_human",
            reason_code=reason,
            sca_required=False,
            decision_id=decision_id,
            evaluation_context={}
        )
