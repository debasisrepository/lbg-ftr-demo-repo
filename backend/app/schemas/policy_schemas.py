"""Policy endpoint schemas."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class PolicyEvaluationResultSchema(BaseModel):
    """Policy evaluation result schema."""
    evaluation_result: str
    failed_condition_code: Optional[str] = None
    failed_conditions_json: Dict[str, Any]
    rules_applied_json: Dict[str, Any]


class PolicyEvaluationItem(BaseModel):
    """Policy evaluation item."""
    evaluation_id: str
    rule_set_version_id: Optional[str] = None
    evaluation_context_type: str
    action_type: str
    subject_entity_type: str
    subject_entity_id: str
    actor_user_id: str
    actor_role_code: str
    evaluation_result: str
    failed_condition_code: Optional[str] = None
    evaluated_at: datetime
    evaluated_by_component: str


class PolicyEvaluationListResponse(BaseModel):
    """Policy evaluation list response."""
    items: List[PolicyEvaluationItem]
    total: int
    limit: int
    offset: int


class RuleItem(BaseModel):
    """Policy rule item."""
    rule_id: str
    rule_code: str
    rule_category: str
    action_type: str
    rule_description: str
    failure_message: str
    evaluation_order: int
    is_enabled: bool


class RuleSetItem(BaseModel):
    """Policy rule set item."""
    rule_set_version_id: str
    version_number: int
    version_label: str
    region_code: Optional[str] = None
    rule_set_status: str
    effective_from: datetime
    effective_to: Optional[datetime] = None
    rules: Optional[List[RuleItem]] = None


class RuleSetListResponse(BaseModel):
    """Policy rule set list response."""
    items: List[RuleSetItem]
    total: int
    limit: int
    offset: int
