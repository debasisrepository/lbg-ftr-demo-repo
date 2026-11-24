"""Policy repository."""
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.policy import PolicyEvaluationRecord, PolicyRule, PolicyRuleSetVersion


class PolicyRepository:
    """Repository for policy operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_active_rule_set(self, region_code: Optional[str] = None) -> Optional[PolicyRuleSetVersion]:
        """Get active rule set version."""
        query = self.db.query(PolicyRuleSetVersion).filter(
            PolicyRuleSetVersion.rule_set_status == "active"
        )

        if region_code:
            query = query.filter(PolicyRuleSetVersion.region_code == region_code)

        return query.first()

    def get_rules_for_set(self, rule_set_version_id: str) -> List[PolicyRule]:
        """Get enabled rules for a rule set version, ordered by evaluation_order."""
        # Convert string to UUID
        rule_set_uuid = uuid.UUID(rule_set_version_id) if isinstance(rule_set_version_id, str) else rule_set_version_id
        
        return (
            self.db.query(PolicyRule)
            .filter(
                PolicyRule.rule_set_version_id == rule_set_uuid,
                PolicyRule.is_enabled == True,  # noqa: E712
            )
            .order_by(PolicyRule.evaluation_order, PolicyRule.rule_code)
            .all()
        )

    def create_evaluation_record(self, record: PolicyEvaluationRecord) -> PolicyEvaluationRecord:
        """Create policy evaluation record."""
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def list_evaluations(
        self,
        evaluation_result: Optional[str] = None,
        evaluation_context_type: Optional[str] = None,
        action_type: Optional[str] = None,
        subject_entity_type: Optional[str] = None,
        subject_entity_id: Optional[str] = None,
        actor_user_id: Optional[str] = None,
        rule_set_version_number: Optional[int] = None,
        from_date: Optional[object] = None,
        to_date: Optional[object] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[List[PolicyEvaluationRecord], int]:
        """List policy evaluations with filters."""
        query = self.db.query(PolicyEvaluationRecord)

        if evaluation_result:
            query = query.filter(PolicyEvaluationRecord.evaluation_result == evaluation_result)
        if evaluation_context_type:
            query = query.filter(PolicyEvaluationRecord.evaluation_context_type == evaluation_context_type)
        if action_type:
            query = query.filter(PolicyEvaluationRecord.action_type == action_type)
        if subject_entity_type:
            query = query.filter(PolicyEvaluationRecord.subject_entity_type == subject_entity_type)
        if subject_entity_id:
            query = query.filter(PolicyEvaluationRecord.subject_entity_id == subject_entity_id)
        if actor_user_id:
            actor_uuid = uuid.UUID(actor_user_id) if isinstance(actor_user_id, str) else actor_user_id
            query = query.filter(PolicyEvaluationRecord.actor_user_id == actor_uuid)
        if rule_set_version_number:
            # Join to get rule set by version number
            query = query.join(PolicyRuleSetVersion).filter(
                PolicyRuleSetVersion.version_number == rule_set_version_number
            )
        if from_date:
            query = query.filter(PolicyEvaluationRecord.evaluated_at >= from_date)
        if to_date:
            query = query.filter(PolicyEvaluationRecord.evaluated_at <= to_date)

        total = query.count()
        evaluations = query.order_by(PolicyEvaluationRecord.evaluated_at.desc()).limit(limit).offset(offset).all()

        return evaluations, total

    def list_rule_sets(
        self,
        rule_set_status: Optional[str] = None,
        region_code: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[List[PolicyRuleSetVersion], int]:
        """List rule set versions with filters."""
        query = self.db.query(PolicyRuleSetVersion)

        if rule_set_status:
            query = query.filter(PolicyRuleSetVersion.rule_set_status == rule_set_status)
        if region_code:
            query = query.filter(PolicyRuleSetVersion.region_code == region_code)

        total = query.count()
        rule_sets = query.order_by(PolicyRuleSetVersion.version_number.desc()).limit(limit).offset(offset).all()

        return rule_sets, total
