"""Policy router."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.core.context import RequestContext
from app.core.deps import get_db, get_clock, require_action
from app.schemas.policy_schemas import PolicyEvaluationListResponse, RuleSetListResponse
from app.repositories.policy_repository import PolicyRepository


router = APIRouter(tags=["policy"])


@router.get("/evaluations", response_model=PolicyEvaluationListResponse)
def list_policy_evaluations(
    evaluation_result: Optional[str] = Query(None),
    evaluation_context_type: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None),
    subject_entity_type: Optional[str] = Query(None),
    subject_entity_id: Optional[str] = Query(None),
    actor_user_id: Optional[str] = Query(None),
    rule_set_version_number: Optional[int] = Query(None),
    from_date: Optional[datetime] = Query(None, alias="from"),
    to_date: Optional[datetime] = Query(None, alias="to"),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
    ctx: RequestContext = require_action("policy.read"),
) -> PolicyEvaluationListResponse:
    """List policy evaluation history."""
    repo = PolicyRepository(db)

    evaluations, total = repo.list_evaluations(
        evaluation_result=evaluation_result,
        evaluation_context_type=evaluation_context_type,
        action_type=action_type,
        subject_entity_type=subject_entity_type,
        subject_entity_id=subject_entity_id,
        actor_user_id=actor_user_id,
        rule_set_version_number=rule_set_version_number,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
        offset=offset,
    )

    from app.schemas.policy_schemas import PolicyEvaluationItem

    items = [
        PolicyEvaluationItem(
            evaluation_id=str(e.id),
            rule_set_version_id=str(e.rule_set_version_id) if e.rule_set_version_id else None,
            evaluation_context_type=e.evaluation_context_type,
            action_type=e.action_type,
            subject_entity_type=e.subject_entity_type,
            subject_entity_id=str(e.subject_entity_id) if e.subject_entity_id else None,
            actor_user_id=str(e.actor_user_id),
            actor_role_code=e.actor_role_code,
            evaluation_result=e.evaluation_result,
            failed_condition_code=e.failed_condition_code,
            evaluated_at=e.evaluated_at,
            evaluated_by_component=e.evaluated_by_component,
        )
        for e in evaluations
    ]

    return PolicyEvaluationListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/rule-sets", response_model=RuleSetListResponse)
def list_rule_sets(
    rule_set_status: Optional[str] = Query(None),
    region_code: Optional[str] = Query(None),
    include_rules: bool = Query(False),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
    ctx: RequestContext = require_action("policy.read"),
) -> RuleSetListResponse:
    """List policy rule sets."""
    repo = PolicyRepository(db)

    rule_sets, total = repo.list_rule_sets(
        rule_set_status=rule_set_status,
        region_code=region_code,
        limit=limit,
        offset=offset,
    )

    from app.schemas.policy_schemas import RuleSetItem, RuleItem

    items = []
    for rs in rule_sets:
        rules = None
        if include_rules:
            rules_list = repo.get_rules_for_set(str(rs.id))
            rules = [
                RuleItem(
                    rule_id=str(r.id),
                    rule_code=r.rule_code,
                    rule_category=r.rule_category,
                    action_type=r.action_type,
                    rule_description=r.rule_description,
                    failure_message=r.failure_message,
                    evaluation_order=r.evaluation_order,
                    is_enabled=r.is_enabled,
                )
                for r in rules_list
            ]

        items.append(
            RuleSetItem(
                rule_set_version_id=str(rs.id),
                version_number=rs.version_number,
                version_label=rs.version_label,
                region_code=rs.region_code,
                rule_set_status=rs.rule_set_status,
                effective_from=rs.effective_from,
                effective_to=rs.effective_to,
                rules=rules,
            )
        )

    return RuleSetListResponse(items=items, total=total, limit=limit, offset=offset)
