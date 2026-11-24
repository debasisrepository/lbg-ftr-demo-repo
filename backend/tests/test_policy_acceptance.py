"""Acceptance tests for FR-DTC-001: Deterministic policy enforcement."""
import uuid
from datetime import datetime, timezone

import pytest

from app.core.clock import FixedClock
from app.models.policy import PolicyRule, PolicyRuleSetVersion
from app.services.policy_engine_service import PolicyEngineService


@pytest.fixture
def policy_service(db_session):
    """Create policy service with fixed clock."""
    now = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    clock = FixedClock(now)
    return PolicyEngineService(db_session, clock)


@pytest.fixture
def rule_set_v1(db_session):
    """Create rule set version 1."""
    now = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    
    rule_set = PolicyRuleSetVersion(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        version_number=1,
        version_label="Rules v1",
        region_code="ALL",
        rule_set_status="active",
        effective_from=now,
    )
    db_session.add(rule_set)
    
    # Add rules to v1
    rules = [
        PolicyRule(
            id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
            rule_set_version_id=rule_set.id,
            rule_code="AMOUNT_REQUIRED",
            rule_category="data_quality",
            action_type="promise_create",
            rule_description="Amount must be greater than zero",
            condition_json={
                "type": "decimal_greater_than",
                "parameters": {"field": "promised_amount", "threshold": "0"}
            },
            parameters_json={},
            failure_message="Promise amount must be greater than zero",
            evaluation_order=1,
            is_enabled=True,
        ),
        PolicyRule(
            id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
            rule_set_version_id=rule_set.id,
            rule_code="SCOPE_VALID",
            rule_category="data_quality",
            action_type="promise_create",
            rule_description="Scope type must be valid",
            condition_json={
                "type": "field_in_set",
                "parameters": {
                    "field": "promise_scope_type",
                    "allowed_values": ["invoice", "account_balance", "partial"]
                }
            },
            parameters_json={},
            failure_message="Promise scope type must be invoice, account_balance, or partial",
            evaluation_order=2,
            is_enabled=True,
        ),
    ]
    
    for rule in rules:
        db_session.add(rule)
    
    db_session.commit()
    db_session.refresh(rule_set)
    return rule_set


@pytest.fixture
def rule_set_v2(db_session, rule_set_v1):
    """Create rule set version 2 with updated rules."""
    now = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    
    # Mark v1 as superseded
    rule_set_v1.rule_set_status = "superseded"
    rule_set_v1.effective_to = now
    
    # Create v2
    rule_set = PolicyRuleSetVersion(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        version_number=2,
        version_label="Rules v2",
        region_code="ALL",
        rule_set_status="active",
        effective_from=now,
    )
    db_session.add(rule_set)
    
    # Add rules to v2 (more restrictive)
    rules = [
        PolicyRule(
            id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
            rule_set_version_id=rule_set.id,
            rule_code="AMOUNT_REQUIRED",
            rule_category="data_quality",
            action_type="promise_create",
            rule_description="Amount must be at least 100",
            condition_json={
                "type": "decimal_greater_than",
                "parameters": {"field": "promised_amount", "threshold": "99.99"}
            },
            parameters_json={},
            failure_message="Promise amount must be at least 100",
            evaluation_order=1,
            is_enabled=True,
        ),
        PolicyRule(
            id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
            rule_set_version_id=rule_set.id,
            rule_code="SCOPE_VALID",
            rule_category="data_quality",
            action_type="promise_create",
            rule_description="Scope type must be invoice only",
            condition_json={
                "type": "field_in_set",
                "parameters": {
                    "field": "promise_scope_type",
                    "allowed_values": ["invoice"]  # More restrictive
                }
            },
            parameters_json={},
            failure_message="Promise scope type must be invoice",
            evaluation_order=2,
            is_enabled=True,
        ),
    ]
    
    for rule in rules:
        db_session.add(rule)
    
    db_session.commit()
    db_session.refresh(rule_set)
    return rule_set


def test_ac1_all_configured_policy_validations_applied(policy_service, db_session, rule_set_v1):
    """
    AC1: Given a user attempts a governed action, when the action is evaluated,
    then all configured policy validations are applied.
    """
    # Arrange: context with valid data
    context_data = {
        "promised_amount": 100.00,
        "promise_scope_type": "invoice"
    }
    
    # Act: evaluate
    record = policy_service.evaluate(
        action_type="promise_create",
        context_data=context_data,
        actor_user_id=str(uuid.uuid4()),
        actor_role_code="collections_analyst",
        evaluation_context_type="promise_capture",
        subject_entity_type="promise",
        subject_entity_id=str(uuid.uuid4()),
        correlation_id="test-ac1",
    )
    
    # Assert: both rules were evaluated
    assert len(record.rules_applied_json) == 2
    assert "AMOUNT_REQUIRED" in record.rules_applied_json
    assert "SCOPE_VALID" in record.rules_applied_json
    assert record.rules_applied_json["AMOUNT_REQUIRED"]["result"] == "pass"
    assert record.rules_applied_json["SCOPE_VALID"]["result"] == "pass"
    assert record.evaluation_result == "pass"
    
    # Assert: input snapshot preserved
    assert record.input_snapshot_json == context_data
    
    # Assert: evaluation record persisted
    assert record.id is not None
    from app.models.policy import PolicyEvaluationRecord
    persisted = db_session.query(PolicyEvaluationRecord).filter(
        PolicyEvaluationRecord.id == record.id
    ).first()
    assert persisted is not None


def test_ac2_policy_validation_fails_action_rejected_with_condition(policy_service, db_session, rule_set_v1):
    """
    AC2: Given a policy validation fails, when the action is submitted,
    then the action is rejected with the failed condition identified.
    """
    # Arrange: context that will fail SCOPE_VALID rule
    context_data = {
        "promised_amount": 100.00,
        "promise_scope_type": "invalid_type"
    }
    
    # Act: evaluate
    record = policy_service.evaluate(
        action_type="promise_create",
        context_data=context_data,
        actor_user_id=str(uuid.uuid4()),
        actor_role_code="collections_analyst",
        evaluation_context_type="promise_capture",
        subject_entity_type="promise",
        subject_entity_id=str(uuid.uuid4()),
        correlation_id="test-ac2",
    )
    
    # Assert: action denied
    assert record.evaluation_result == "fail"
    
    # Assert: failed condition identified
    assert record.failed_condition_code == "SCOPE_VALID"
    assert "SCOPE_VALID" in record.failed_conditions_json
    
    # Assert: failure details available
    failed_condition = record.failed_conditions_json["SCOPE_VALID"]
    assert failed_condition["condition"] == "field_in_set"
    assert failed_condition["message"] == "Promise scope type must be invoice, account_balance, or partial"
    assert "parameters" in failed_condition
    
    # Assert: rule evaluation status recorded
    assert record.rules_applied_json["AMOUNT_REQUIRED"]["result"] == "pass"
    assert record.rules_applied_json["SCOPE_VALID"]["result"] == "fail"


def test_ac2_multiple_failures_all_identified(policy_service, db_session, rule_set_v1):
    """
    AC2 (extended): When multiple validations fail, all failed conditions are identified.
    """
    # Arrange: context that will fail both rules
    context_data = {
        "promised_amount": 0,
        "promise_scope_type": "invalid_type"
    }
    
    # Act: evaluate
    record = policy_service.evaluate(
        action_type="promise_create",
        context_data=context_data,
        actor_user_id=str(uuid.uuid4()),
        actor_role_code="collections_analyst",
        evaluation_context_type="promise_capture",
        subject_entity_type="promise",
        subject_entity_id=str(uuid.uuid4()),
        correlation_id="test-ac2-multiple",
    )
    
    # Assert: action denied
    assert record.evaluation_result == "fail"
    
    # Assert: all failed conditions identified
    assert len(record.failed_conditions_json) == 2
    assert "AMOUNT_REQUIRED" in record.failed_conditions_json
    assert "SCOPE_VALID" in record.failed_conditions_json
    
    # Assert: both rules marked as failed
    assert record.rules_applied_json["AMOUNT_REQUIRED"]["result"] == "fail"
    assert record.rules_applied_json["SCOPE_VALID"]["result"] == "fail"


def test_ac3_new_rules_take_effect_historical_decisions_unchanged(policy_service, db_session, rule_set_v1):
    """
    AC3: Given policy changes are approved, when new rules take effect,
    then subsequent actions are validated against the updated rule set
    without altering historical decisions.
    """
    # Arrange: context that passes v1 rules but fails v2 rules
    context_data = {
        "promised_amount": 50.00,  # Passes v1 (> 0), fails v2 (< 100)
        "promise_scope_type": "account_balance"  # Passes v1, fails v2 (invoice only)
    }
    
    # Act 1: evaluate under v1 rules (v1 is active)
    record_v1 = policy_service.evaluate(
        action_type="promise_create",
        context_data=context_data,
        actor_user_id=str(uuid.uuid4()),
        actor_role_code="collections_analyst",
        evaluation_context_type="promise_capture",
        subject_entity_type="promise",
        subject_entity_id=str(uuid.uuid4()),
        correlation_id="test-ac3-v1",
    )
    
    # Assert: v1 evaluation allowed
    assert record_v1.evaluation_result == "pass"
    assert record_v1.rule_set_version_id == rule_set_v1.id
    
    # Store v1 record ID
    v1_record_id = record_v1.id
    
    # Act 2: activate v2 rules (supersede v1, create v2)
    now = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    
    # Mark v1 as superseded
    rule_set_v1.rule_set_status = "superseded"
    rule_set_v1.effective_to = now
    
    # Create v2
    rule_set_v2 = PolicyRuleSetVersion(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        version_number=2,
        version_label="Rules v2",
        region_code="ALL",
        rule_set_status="active",
        effective_from=now,
    )
    db_session.add(rule_set_v2)
    
    # Add rules to v2 (more restrictive)
    rules_v2 = [
        PolicyRule(
            id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
            rule_set_version_id=rule_set_v2.id,
            rule_code="AMOUNT_REQUIRED",
            rule_category="data_quality",
            action_type="promise_create",
            rule_description="Amount must be at least 100",
            condition_json={
                "type": "decimal_greater_than",
                "parameters": {"field": "promised_amount", "threshold": "99.99"}
            },
            parameters_json={},
            failure_message="Promise amount must be at least 100",
            evaluation_order=1,
            is_enabled=True,
        ),
        PolicyRule(
            id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
            rule_set_version_id=rule_set_v2.id,
            rule_code="SCOPE_VALID",
            rule_category="data_quality",
            action_type="promise_create",
            rule_description="Scope type must be invoice only",
            condition_json={
                "type": "field_in_set",
                "parameters": {
                    "field": "promise_scope_type",
                    "allowed_values": ["invoice"]  # More restrictive
                }
            },
            parameters_json={},
            failure_message="Promise scope type must be invoice",
            evaluation_order=2,
            is_enabled=True,
        ),
    ]
    
    for rule in rules_v2:
        db_session.add(rule)
    
    db_session.commit()
    db_session.refresh(rule_set_v1)
    db_session.refresh(rule_set_v2)
    
    # Verify v1 is superseded
    assert rule_set_v1.rule_set_status == "superseded"
    
    # Act 3: evaluate same context under v2 rules
    record_v2 = policy_service.evaluate(
        action_type="promise_create",
        context_data=context_data,
        actor_user_id=str(uuid.uuid4()),
        actor_role_code="collections_analyst",
        evaluation_context_type="promise_capture",
        subject_entity_type="promise",
        subject_entity_id=str(uuid.uuid4()),
        correlation_id="test-ac3-v2",
    )
    
    # Assert: v2 evaluation denied (more restrictive rules)
    assert record_v2.evaluation_result == "fail"
    assert record_v2.rule_set_version_id == rule_set_v2.id
    assert len(record_v2.failed_conditions_json) == 2  # Both rules fail
    
    # Assert: historical v1 record unchanged
    from app.models.policy import PolicyEvaluationRecord
    historical_record = db_session.query(PolicyEvaluationRecord).filter(
        PolicyEvaluationRecord.id == v1_record_id
    ).first()
    
    assert historical_record is not None
    assert historical_record.evaluation_result == "pass"  # Still allowed
    assert historical_record.rule_set_version_id == rule_set_v1.id  # Still references v1
    assert historical_record.rules_applied_json["AMOUNT_REQUIRED"]["result"] == "pass"
    assert historical_record.rules_applied_json["SCOPE_VALID"]["result"] == "pass"


def test_deterministic_evaluation_same_input_same_result(policy_service, db_session, rule_set_v1):
    """
    Test deterministic behavior: same input produces same result across multiple evaluations.
    """
    # Arrange: same context
    context_data = {
        "promised_amount": 100.00,
        "promise_scope_type": "invoice"
    }
    
    actor_id = str(uuid.uuid4())
    subject_id = str(uuid.uuid4())
    
    # Act: evaluate multiple times
    record1 = policy_service.evaluate(
        action_type="promise_create",
        context_data=context_data.copy(),
        actor_user_id=actor_id,
        actor_role_code="collections_analyst",
        evaluation_context_type="promise_capture",
        subject_entity_type="promise",
        subject_entity_id=subject_id,
        correlation_id="test-det-1",
    )
    
    record2 = policy_service.evaluate(
        action_type="promise_create",
        context_data=context_data.copy(),
        actor_user_id=actor_id,
        actor_role_code="collections_analyst",
        evaluation_context_type="promise_capture",
        subject_entity_type="promise",
        subject_entity_id=subject_id,
        correlation_id="test-det-2",
    )
    
    # Assert: same results
    assert record1.evaluation_result == record2.evaluation_result
    assert record1.evaluation_result == "pass"
    assert record1.failed_condition_code == record2.failed_condition_code
    assert len(record1.rules_applied_json) == len(record2.rules_applied_json)
    
    # Assert: rule evaluation order consistent
    for rule_code in record1.rules_applied_json:
        assert record1.rules_applied_json[rule_code]["result"] == record2.rules_applied_json[rule_code]["result"]
