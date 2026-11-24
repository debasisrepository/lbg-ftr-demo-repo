"""Policy router integration tests."""
import uuid
from datetime import datetime, timezone

from app.models.users import User
from app.models.roles import RoleProfile, RoleAssignment
from app.models.policy import PolicyRuleSetVersion, PolicyRule, PolicyEvaluationRecord
from app.core.security import hash_password


def test_get_policy_evaluations(client, db_session):
    """Test GET /api/v1/policy/evaluations."""
    now = datetime.now(timezone.utc)
    
    # Create user and role with view_policy_history permission
    role = RoleProfile(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        role_code="analyst",
        role_label="Analyst",
        allowed_widgets_json={"codes": []},
        entitled_queue_states_json={"states": []},
        allowed_actions_json={"actions": ["policy.read"]},
        can_view_sensitive_fields=False,
        profile_status="active",
    )
    db_session.add(role)
    
    user = User(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        username="analyst1",
        display_name="Analyst One",
        email="analyst1@example.com",
        password_hash=hash_password("analyst123"),
        status="active",
    )
    db_session.add(user)
    db_session.flush()
    
    assignment = RoleAssignment(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        user_id=user.id,
        role_code="analyst",
        assignment_status="active",
    )
    db_session.add(assignment)
    
    # Create rule set
    rule_set = PolicyRuleSetVersion(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        version_number=1,
        version_label="v1.0",
        rule_set_status="active",
        effective_from=now,
    )
    db_session.add(rule_set)
    db_session.flush()
    
    # Create evaluation records
    eval1 = PolicyEvaluationRecord(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        rule_set_version_id=rule_set.id,
        evaluation_context_type="promise_capture",
        action_type="promise_create",
        subject_entity_type="promise_to_pay",
        subject_entity_id=uuid.uuid4(),
        actor_user_id=user.id,
        actor_role_code="analyst",
        evaluation_result="pass",
        evaluated_at=now,
        evaluated_by_component="policy_engine_service",
    )
    db_session.add(eval1)
    
    eval2 = PolicyEvaluationRecord(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        rule_set_version_id=rule_set.id,
        evaluation_context_type="promise_capture",
        action_type="promise_create",
        subject_entity_type="promise_to_pay",
        subject_entity_id=uuid.uuid4(),
        actor_user_id=user.id,
        actor_role_code="analyst",
        evaluation_result="fail",
        failed_condition_code="PROMISE_AMOUNT_REQUIRED",
        evaluated_at=now,
        evaluated_by_component="policy_engine_service",
    )
    db_session.add(eval2)
    db_session.commit()
    
    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "analyst1", "password": "analyst123"},
    )
    token = login_response.json()["access_token"]
    
    # Get policy evaluations
    response = client.get(
        "/api/v1/policy/evaluations",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 2


def test_get_policy_evaluations_filtered(client, db_session):
    """Test GET /api/v1/policy/evaluations with filters."""
    now = datetime.now(timezone.utc)
    
    # Create user and role
    role = RoleProfile(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        role_code="analyst",
        role_label="Analyst",
        allowed_widgets_json={"codes": []},
        entitled_queue_states_json={"states": []},
        allowed_actions_json={"actions": ["policy.read"]},
        can_view_sensitive_fields=False,
        profile_status="active",
    )
    db_session.add(role)
    
    user = User(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        username="analyst1",
        display_name="Analyst One",
        email="analyst1@example.com",
        password_hash=hash_password("analyst123"),
        status="active",
    )
    db_session.add(user)
    db_session.flush()
    
    assignment = RoleAssignment(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        user_id=user.id,
        role_code="analyst",
        assignment_status="active",
    )
    db_session.add(assignment)
    
    # Create rule set
    rule_set = PolicyRuleSetVersion(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        version_number=1,
        version_label="v1.0",
        rule_set_status="active",
        effective_from=now,
    )
    db_session.add(rule_set)
    db_session.flush()
    
    # Create evaluation with deny result
    eval_deny = PolicyEvaluationRecord(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        rule_set_version_id=rule_set.id,
        evaluation_context_type="promise_capture",
        action_type="promise_create",
        subject_entity_type="promise_to_pay",
        subject_entity_id=uuid.uuid4(),
        actor_user_id=user.id,
        actor_role_code="analyst",
        evaluation_result="fail",
        evaluated_at=now,
        evaluated_by_component="policy_engine_service",
    )
    db_session.add(eval_deny)
    db_session.commit()
    
    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "analyst1", "password": "analyst123"},
    )
    token = login_response.json()["access_token"]
    
    # Get policy evaluations filtered by result
    response = client.get(
        "/api/v1/policy/evaluations?evaluation_result=fail",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    # All returned items should have deny result
    for item in data["items"]:
        assert item["evaluation_result"] == "fail"


def test_get_rule_sets(client, db_session):
    """Test GET /api/v1/policy/rule-sets."""
    now = datetime.now(timezone.utc)
    
    # Create user and role with view_policy_config permission
    role = RoleProfile(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        role_code="reviewer",
        role_label="Reviewer",
        allowed_widgets_json={"codes": []},
        entitled_queue_states_json={"states": []},
        allowed_actions_json={"actions": ["policy.read"]},
        can_view_sensitive_fields=True,
        profile_status="active",
    )
    db_session.add(role)
    
    user = User(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        username="reviewer1",
        display_name="Reviewer One",
        email="reviewer1@example.com",
        password_hash=hash_password("reviewer123"),
        status="active",
    )
    db_session.add(user)
    db_session.flush()
    
    assignment = RoleAssignment(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        user_id=user.id,
        role_code="reviewer",
        assignment_status="active",
    )
    db_session.add(assignment)
    
    # Create rule set with rules
    rule_set = PolicyRuleSetVersion(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        version_number=1,
        version_label="v1.0",
        rule_set_status="active",
        effective_from=now,
    )
    db_session.add(rule_set)
    db_session.flush()
    
    rule = PolicyRule(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        rule_set_version_id=rule_set.id,
        rule_code="PROMISE_AMOUNT_REQUIRED",
        rule_category="validation",
        action_type="promise_create",
        rule_description="Promise amount must be present",
        condition_json={"condition_type": "field_present", "field": "promised_amount"},
        parameters_json={},
        failure_message="Promise amount is required",
        evaluation_order=1,
        is_enabled=True,
    )
    db_session.add(rule)
    db_session.commit()
    
    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "reviewer1", "password": "reviewer123"},
    )
    token = login_response.json()["access_token"]
    
    # Get rule sets
    response = client.get(
        "/api/v1/policy/rule-sets",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


def test_get_rule_sets_with_rules(client, db_session):
    """Test GET /api/v1/policy/rule-sets?include_rules=true."""
    now = datetime.now(timezone.utc)
    
    # Create user and role
    role = RoleProfile(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        role_code="reviewer",
        role_label="Reviewer",
        allowed_widgets_json={"codes": []},
        entitled_queue_states_json={"states": []},
        allowed_actions_json={"actions": ["policy.read"]},
        can_view_sensitive_fields=True,
        profile_status="active",
    )
    db_session.add(role)
    
    user = User(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        username="reviewer1",
        display_name="Reviewer One",
        email="reviewer1@example.com",
        password_hash=hash_password("reviewer123"),
        status="active",
    )
    db_session.add(user)
    db_session.flush()
    
    assignment = RoleAssignment(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        user_id=user.id,
        role_code="reviewer",
        assignment_status="active",
    )
    db_session.add(assignment)
    
    # Create rule set with rules
    rule_set = PolicyRuleSetVersion(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        version_number=1,
        version_label="v1.0",
        rule_set_status="active",
        effective_from=now,
    )
    db_session.add(rule_set)
    db_session.flush()
    
    rule = PolicyRule(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        rule_set_version_id=rule_set.id,
        rule_code="PROMISE_AMOUNT_REQUIRED",
        rule_category="validation",
        action_type="promise_create",
        rule_description="Promise amount must be present",
        condition_json={"condition_type": "field_present", "field": "promised_amount"},
        parameters_json={},
        failure_message="Promise amount is required",
        evaluation_order=1,
        is_enabled=True,
    )
    db_session.add(rule)
    db_session.commit()
    
    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "reviewer1", "password": "reviewer123"},
    )
    token = login_response.json()["access_token"]
    
    # Get rule sets with rules included
    response = client.get(
        "/api/v1/policy/rule-sets?include_rules=true",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    # Verify rules are included
    if data["items"]:
        assert "rules" in data["items"][0]
