"""Policy engine service."""
import uuid
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.models.policy import PolicyEvaluationRecord
from app.policy.evaluators import evaluator_registry
from app.repositories.policy_repository import PolicyRepository


class PolicyEngineService:
    """Service for policy evaluation."""

    def __init__(self, db: Session, clock: Clock):
        self.db = db
        self.clock = clock
        self.repo = PolicyRepository(db)

    def evaluate(
        self,
        action_type: str,
        context_data: Dict[str, Any],
        actor_user_id: str,
        actor_role_code: str,
        evaluation_context_type: str,
        subject_entity_type: str,
        subject_entity_id: str,
        correlation_id: str,
        region_code: Optional[str] = None,
    ) -> PolicyEvaluationRecord:
        """Evaluate policy rules.
        
        Args:
            action_type: Action being evaluated (e.g., "promise_create")
            context_data: Input data for evaluation
            actor_user_id: User performing action
            actor_role_code: Role of actor
            evaluation_context_type: Context type
            subject_entity_type: Entity type being acted on
            subject_entity_id: Entity ID
            correlation_id: Request correlation ID
            region_code: Optional region code
            
        Returns:
            PolicyEvaluationRecord with result
        """
        now = self.clock.now()

        # Get active rule set
        rule_set = self.repo.get_active_rule_set(region_code)
        if not rule_set:
            # No active rule set - pass by default
            record = PolicyEvaluationRecord(
                id=uuid.uuid4(),
                created_at=now,
                updated_at=now,
                rule_set_version_id=None,
                evaluation_context_type=evaluation_context_type,
                action_type=action_type,
                subject_entity_type=subject_entity_type,
                subject_entity_id=uuid.UUID(subject_entity_id) if subject_entity_id else None,
                actor_user_id=uuid.UUID(actor_user_id),
                actor_role_code=actor_role_code,
                evaluation_result="pass",
                failed_condition_code=None,
                failed_conditions_json={},
                rules_applied_json={},
                input_snapshot_json=context_data,
                evaluated_at=now,
                evaluated_by_component="policy_engine_service",
                correlation_id=correlation_id,
            )
            return self.repo.create_evaluation_record(record)

        # Get rules for action type
        rules = self.repo.get_rules_for_set(str(rule_set.id))
        applicable_rules = [r for r in rules if r.action_type == action_type]

        # Evaluate rules
        failed_conditions = {}
        rules_applied = {}

        for rule in applicable_rules:
            rules_applied[rule.rule_code] = {
                "rule_description": rule.rule_description,
                "result": "pending",
            }

            # Parse condition JSON
            condition_json = rule.condition_json
            condition_type = condition_json.get("type")
            parameters = condition_json.get("parameters", {})

            # Evaluate condition
            try:
                passed = evaluator_registry.evaluate(condition_type, parameters, context_data)
                rules_applied[rule.rule_code]["result"] = "pass" if passed else "fail"

                if not passed:
                    failed_conditions[rule.rule_code] = {
                        "condition": condition_type,
                        "message": rule.failure_message,
                        "parameters": parameters,
                    }
            except Exception as e:
                rules_applied[rule.rule_code]["result"] = "error"
                rules_applied[rule.rule_code]["error"] = str(e)

        # Determine overall result
        if failed_conditions:
            evaluation_result = "fail"
            failed_condition_code = list(failed_conditions.keys())[0]
        else:
            evaluation_result = "pass"
            failed_condition_code = None

        # Create evaluation record
        record = PolicyEvaluationRecord(
            id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
            rule_set_version_id=rule_set.id,
            evaluation_context_type=evaluation_context_type,
            action_type=action_type,
            subject_entity_type=subject_entity_type,
            subject_entity_id=uuid.UUID(subject_entity_id) if subject_entity_id else None,
            actor_user_id=uuid.UUID(actor_user_id),
            actor_role_code=actor_role_code,
            evaluation_result=evaluation_result,
            failed_condition_code=failed_condition_code,
            failed_conditions_json=failed_conditions,
            rules_applied_json=rules_applied,
            input_snapshot_json=context_data,
            evaluated_at=now,
            evaluated_by_component="policy_engine_service",
            correlation_id=correlation_id,
        )

        return self.repo.create_evaluation_record(record)
