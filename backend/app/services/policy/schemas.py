from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class PolicyEvaluationRequest(BaseModel):
    action_code: str
    customer_user_id: int
    session_id: UUID | None = None
    issue_classification: str | None
    authenticated: bool
    vulnerability_indicators: list[str]
    confidence_pct: int | None
    repeated_failure: bool
    explicit_human_request: bool


class PolicyDecisionResponse(BaseModel):
    outcome: str  # approved, denied, escalate, downgrade
    reason_code: str
    sca_required: bool
    decision_id: UUID
    evaluation_context: dict


class ToolInvocationRequest(BaseModel):
    action_code: str
    policy_decision_id: UUID
    execution_mode: str
    input_params: dict
