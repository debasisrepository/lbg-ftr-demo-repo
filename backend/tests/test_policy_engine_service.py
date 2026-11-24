"""Unit tests for policy engine service."""
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
def active_rule_set(db_session):
    """Create active rule set."""
    now = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    
    rule_set = PolicyRuleSetVersion(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        version_number=1,
        version_label="Test Rules v1",
        region_code="ALL",
        rule_set_status="active",
        effective_from=now,
    )
    db_session.add(rule_set)
    db_session.commit()
    db_session.refresh(rule_set)
    return rule_set


@pytest.fixture
def promise_amount_rule(db_session, active_rule_set):
    """Create rule requiring promise amount > 0."""
    now = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    
    rule = PolicyRule(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        rule_set_version_id=active_rule_set.id,
        rule_code="PROMISE_AMOUNT_REQUIRED",
        rule_category="data_quality",
        action_type="promise_create",
        rule_description="Promise amount must be greater than zero",
        condition_json={
            "type": "decimal_greater_than",
            "parameters": {
                "field": "promised_amount",
                "threshold": "0"
            }
        },
        parameters_json={},
        failure_message="Promise amount must be greater than zero",
        evaluation_order=1,
        is_enabled=True,
    )
    db_session.add(rule)
    db_session.commit()
    db_session.refresh(rule)
    return rule


@pytest.fixture
def promise_scope_rule(db_session, active_rule_set):
    """Create rule requiring valid promise scope type."""
    now = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    
    rule = PolicyRule(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        rule_set_version_id=active_rule_set.id,
        rule_code="PROMISE_SCOPE_VALID",
        rule_category="data_quality",
        action_type="promise_create",
        rule_description="Promise scope must be valid",
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
    )
    db_session.add(rule)
    db_session.commit()
    db_session.refresh(rule)
    return rule


def test_evaluate_no_active_rule_set_allows(policy_service, db_session):
    """Test evaluation allows when no active rule set exists."""
    context_data = {
        "promised_amount": 100.00,
        "promise_scope_type": "invoice"
    }
    
    record = policy_service.evaluate(
        action_type="promise_create",
        context_data=context_data,
        actor_user_id=str(uuid.uuid4()),
        actor_role_code="collections_analyst",
        evaluation_context_type="promise_capture",
        subject_entity_type="promise",
        subject_entity_id=str(uuid.uuid4()),
        correlation_id="test-corr-id",
    )
    
    assert record.evaluation_result == "pass"
    assert record.rule_set_version_id is None
    assert record.failed_condition_code is None


def test_evaluate_all_rules_pass(policy_service, db_session, active_rule_set, promise_amount_rule, promise_scope_rule):
    """Test evaluation allows when all rules pass."""
    context_data = {
        "promised_amount": 100.00,
        "promise_scope_type": "invoice"
    }
    
    record = policy_service.evaluate(
        action_type="promise_create",
        context_data=context_data,
        actor_user_id=str(uuid.uuid4()),
        actor_role_code="collections_analyst",
        evaluation_context_type="promise_capture",
        subject_entity_type="promise",
        subject_entity_id=str(uuid.uuid4()),
        correlation_id="test-corr-id",
    )
    
    assert record.evaluation_result == "pass"
    assert record.rule_set_version_id == active_rule_set.id
    assert record.failed_condition_code is None
    assert len(record.rules_applied_json) == 2
    assert record.rules_applied_json["PROMISE_AMOUNT_REQUIRED"]["result"] == "pass"
    assert record.rules_applied_json["PROMISE_SCOPE_VALID"]["result"] == "pass"


def test_evaluate_one_rule_fails(policy_service, db_session, active_rule_set, promise_amount_rule, promise_scope_rule):
    """Test evaluation denies when one rule fails."""
    context_data = {
        "promised_amount": 100.00,
        "promise_scope_type": "invalid_scope"
    }
    
    record = policy_service.evaluate(
        action_type="promise_create",
        context_data=context_data,
        actor_user_id=str(uuid.uuid4()),
        actor_role_code="collections_analyst",
        evaluation_context_type="promise_capture",
        subject_entity_type="promise",
        subject_entity_id=str(uuid.uuid4()),
        correlation_id="test-corr-id",
    )
    
    assert record.evaluation_result == "fail"
    assert record.rule_set_version_id == active_rule_set.id
    assert record.failed_condition_code == "PROMISE_SCOPE_VALID"
    assert "PROMISE_SCOPE_VALID" in record.failed_conditions_json
    assert record.failed_conditions_json["PROMISE_SCOPE_VALID"]["condition"] == "field_in_set"
    assert record.rules_applied_json["PROMISE_AMOUNT_REQUIRED"]["result"] == "pass"
    assert record.rules_applied_json["PROMISE_SCOPE_VALID"]["result"] == "fail"


def test_evaluate_multiple_rules_fail(policy_service, db_session, active_rule_set, promise_amount_rule, promise_scope_rule):
    """Test evaluation denies when multiple rules fail."""
    context_data = {
        "promised_amount": 0,
        "promise_scope_type": "invalid_scope"
    }
    
    record = policy_service.evaluate(
        action_type="promise_create",
        context_data=context_data,
        actor_user_id=str(uuid.uuid4()),
        actor_role_code="collections_analyst",
        evaluation_context_type="promise_capture",
        subject_entity_type="promise",
        subject_entity_id=str(uuid.uuid4()),
        correlation_id="test-corr-id",
    )
    
    assert record.evaluation_result == "fail"
    assert len(record.failed_conditions_json) == 2
    assert "PROMISE_AMOUNT_REQUIRED" in record.failed_conditions_json
    assert "PROMISE_SCOPE_VALID" in record.failed_conditions_json


def test_evaluate_stores_input_snapshot(policy_service, db_session, active_rule_set, promise_amount_rule):
    """Test evaluation stores input snapshot."""
    context_data = {
        "promised_amount": 100.00,
        "promise_scope_type": "invoice",
        "customer_id": "cust123"
    }
    
    record = policy_service.evaluate(
        action_type="promise_create",
        context_data=context_data,
        actor_user_id=str(uuid.uuid4()),
        actor_role_code="collections_analyst",
        evaluation_context_type="promise_capture",
        subject_entity_type="promise",
        subject_entity_id=str(uuid.uuid4()),
        correlation_id="test-corr-id",
    )
    
    assert record.input_snapshot_json == context_data
    assert record.input_snapshot_json["customer_id"] == "cust123"


def test_evaluate_disabled_rule_not_evaluated(policy_service, db_session, active_rule_set):
    """Test disabled rules are not evaluated."""
    now = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    
    # Create disabled rule
    disabled_rule = PolicyRule(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        rule_set_version_id=active_rule_set.id,
        rule_code="DISABLED_RULE",
        rule_category="data_quality",
        action_type="promise_create",
        rule_description="Disabled rule",
        condition_json={
            "type": "field_present",
            "parameters": {"field": "nonexistent_field"}
        },
        parameters_json={},
        failure_message="Should not be evaluated",
        evaluation_order=1,
        is_enabled=False,
    )
    db_session.add(disabled_rule)
    db_session.commit()
    
    context_data = {
        "promised_amount": 100.00
    }
    
    record = policy_service.evaluate(
        action_type="promise_create",
        context_data=context_data,
        actor_user_id=str(uuid.uuid4()),
        actor_role_code="collections_analyst",
        evaluation_context_type="promise_capture",
        subject_entity_type="promise",
        subject_entity_id=str(uuid.uuid4()),
        correlation_id="test-corr-id",
    )
    
    assert record.evaluation_result == "pass"
    assert "DISABLED_RULE" not in record.rules_applied_json


def test_evaluate_only_evaluates_matching_action_type(policy_service, db_session, active_rule_set, promise_amount_rule):
    """Test only rules for the action type are evaluated."""
    now = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    
    # Create rule for different action type
    other_rule = PolicyRule(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        rule_set_version_id=active_rule_set.id,
        rule_code="QUEUE_RULE",
        rule_category="eligibility",
        action_type="queue_entry",
        rule_description="Queue entry rule",
        condition_json={
            "type": "field_present",
            "parameters": {"field": "some_field"}
        },
        parameters_json={},
        failure_message="Queue rule failure",
        evaluation_order=1,
        is_enabled=True,
    )
    db_session.add(other_rule)
    db_session.commit()
    
    context_data = {
        "promised_amount": 100.00
    }
    
    record = policy_service.evaluate(
        action_type="promise_create",
        context_data=context_data,
        actor_user_id=str(uuid.uuid4()),
        actor_role_code="collections_analyst",
        evaluation_context_type="promise_capture",
        subject_entity_type="promise",
        subject_entity_id=str(uuid.uuid4()),
        correlation_id="test-corr-id",
    )
    
    assert "PROMISE_AMOUNT_REQUIRED" in record.rules_applied_json
    assert "QUEUE_RULE" not in record.rules_applied_json


def test_evaluate_persists_evaluation_record(policy_service, db_session, active_rule_set, promise_amount_rule):
    """Test evaluation record is persisted."""
    context_data = {
        "promised_amount": 100.00
    }
    
    record = policy_service.evaluate(
        action_type="promise_create",
        context_data=context_data,
        actor_user_id=str(uuid.uuid4()),
        actor_role_code="collections_analyst",
        evaluation_context_type="promise_capture",
        subject_entity_type="promise",
        subject_entity_id=str(uuid.uuid4()),
        correlation_id="test-corr-id",
    )
    
    assert record.id is not None
    
    # Verify persisted
    from app.models.policy import PolicyEvaluationRecord
    persisted = db_session.query(PolicyEvaluationRecord).filter(
        PolicyEvaluationRecord.id == record.id
    ).first()
    
    assert persisted is not None
    assert persisted.evaluation_result == "pass"
    assert persisted.evaluated_by_component == "policy_engine_service"
