"""Unit tests for promise service."""
import uuid
from datetime import datetime, timezone

import pytest

from app.core.clock import FixedClock
from app.core.context import RoleContext, RequestContext
from app.core.errors import PolicyFailureError, ConflictError
from app.models.customers import Customer, CustomerAccount
from app.models.roles import RoleProfile
from app.models.policy import PolicyRuleSetVersion, PolicyRule
from app.schemas.promise_schemas import PromiseCreateRequest, ScopeLinkInput
from app.services.promise_service import PromiseService


def test_create_promise_success(db_session):
    """Test promise creation with valid input."""
    clock = FixedClock(datetime(2026, 11, 24, 10, 0, 0, tzinfo=timezone.utc))
    now = clock.now()

    # Create test customer and account
    customer = Customer(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        sap_customer_ref="CUST001",
        customer_name="ABC Corp",
        regional_business_unit="UK",
        credit_status_indicator="normal",
        master_data_source="SAP",
    )
    db_session.add(customer)

    account = CustomerAccount(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        customer_id=customer.id,
        sap_account_ref="ACCT001",
        company_code="1000",
        currency_code="GBP",
        account_status="active",
    )
    db_session.add(account)

    # Create role for user
    role = RoleProfile(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        role_code="collections_analyst",
        role_label="Collections Analyst",
        description="Analyst",
        allowed_widgets_json={},
        entitled_queue_states_json={},
        allowed_actions_json={"actions": ["capture_promise"]},
        can_view_sensitive_fields=False,
        profile_status="active",
    )
    db_session.add(role)

    # Create rule set with minimal rules
    rule_set = PolicyRuleSetVersion(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        version_number=1,
        version_label="v1.0",
        region_code=None,
        rule_set_status="active",
        effective_from=now,
    )
    db_session.add(rule_set)

    # Add a simple passing rule
    rule = PolicyRule(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        rule_set_version_id=rule_set.id,
        rule_code="PROMISE_AMOUNT_REQUIRED",
        rule_category="validation",
        action_type="promise_create",
        rule_description="Promise amount must be present",
        condition_json={"type": "field_present", "parameters": {"field": "promised_amount"}},
        parameters_json={},
        failure_message="Promise amount is required",
        evaluation_order=1,
        is_enabled=True,
    )
    db_session.add(rule)

    db_session.commit()

    service = PromiseService(db_session, clock)

    # Create request context
    analyst_role = RoleContext(
        role_code="collections_analyst",
        role_label="Collections Analyst",
        allowed_widgets=[],
        entitled_queue_states=[],
        allowed_actions=["capture_promise"],
        can_view_sensitive_fields=False,
    )

    user_id = uuid.uuid4()
    ctx = RequestContext(
        user_id=str(user_id),
        username="analyst1",
        display_name="Analyst",
        email="analyst@example.com",
        session_id=str(uuid.uuid4()),
        active_role=analyst_role,
        available_roles=[analyst_role],
        correlation_id="test",
    )

    # Create promise request
    request = PromiseCreateRequest(
        customer_account_id=str(account.id),
        promised_amount="5000.00",
        currency_code="GBP",
        promised_date=datetime(2026, 12, 1, tzinfo=timezone.utc),
        promise_scope_type="full_account",
    )

    response, status_code = service.create_promise(
        request=request,
        ctx=ctx,
        idempotency_key="test-key-001",
        correlation_id="test",
    )

    assert status_code == 201
    assert response.promise_id is not None
    assert response.promised_amount == "5000.00"
    assert response.promise_status == "captured"
    assert response.captured_by_user_id == str(user_id)


def test_create_promise_idempotency(db_session):
    """Test promise creation idempotency."""
    clock = FixedClock(datetime(2026, 11, 24, 10, 0, 0, tzinfo=timezone.utc))
    now = clock.now()

    # Create test data (same as above)
    customer = Customer(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        sap_customer_ref="CUST001",
        customer_name="ABC Corp",
        regional_business_unit="UK",
        credit_status_indicator="normal",
        master_data_source="SAP",
    )
    db_session.add(customer)

    account = CustomerAccount(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        customer_id=customer.id,
        sap_account_ref="ACCT001",
        company_code="1000",
        currency_code="GBP",
        account_status="active",
    )
    db_session.add(account)

    role = RoleProfile(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        role_code="collections_analyst",
        role_label="Collections Analyst",
        description="Analyst",
        allowed_widgets_json={},
        entitled_queue_states_json={},
        allowed_actions_json={"actions": ["capture_promise"]},
        can_view_sensitive_fields=False,
        profile_status="active",
    )
    db_session.add(role)

    rule_set = PolicyRuleSetVersion(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        version_number=1,
        version_label="v1.0",
        region_code=None,
        rule_set_status="active",
        effective_from=now,
    )
    db_session.add(rule_set)

    rule = PolicyRule(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        rule_set_version_id=rule_set.id,
        rule_code="PROMISE_AMOUNT_REQUIRED",
        rule_category="validation",
        action_type="promise_create",
        rule_description="Promise amount must be present",
        condition_json={"type": "field_present", "parameters": {"field": "promised_amount"}},
        parameters_json={},
        failure_message="Promise amount is required",
        evaluation_order=1,
        is_enabled=True,
    )
    db_session.add(rule)
    db_session.commit()

    service = PromiseService(db_session, clock)

    analyst_role = RoleContext(
        role_code="collections_analyst",
        role_label="Collections Analyst",
        allowed_widgets=[],
        entitled_queue_states=[],
        allowed_actions=["capture_promise"],
        can_view_sensitive_fields=False,
    )

    user_id = uuid.uuid4()
    ctx = RequestContext(
        user_id=str(user_id),
        username="analyst1",
        display_name="Analyst",
        email="analyst@example.com",
        session_id=str(uuid.uuid4()),
        active_role=analyst_role,
        available_roles=[analyst_role],
        correlation_id="test",
    )

    request = PromiseCreateRequest(
        customer_account_id=str(account.id),
        promised_amount="5000.00",
        currency_code="GBP",
        promised_date=datetime(2026, 12, 1, tzinfo=timezone.utc),
        promise_scope_type="full_account",
    )

    # First call
    response1, status1 = service.create_promise(
        request=request,
        ctx=ctx,
        idempotency_key="test-key-002",
        correlation_id="test",
    )

    assert status1 == 201
    promise_id = response1.promise_id

    # Second call with same key
    response2, status2 = service.create_promise(
        request=request,
        ctx=ctx,
        idempotency_key="test-key-002",
        correlation_id="test",
    )

    # Should replay
    assert status2 == 200
    assert response2.promise_id == promise_id


def test_create_promise_idempotency_conflict(db_session):
    """Test promise creation idempotency conflict."""
    clock = FixedClock(datetime(2026, 11, 24, 10, 0, 0, tzinfo=timezone.utc))
    now = clock.now()

    # Create test data
    customer = Customer(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        sap_customer_ref="CUST001",
        customer_name="ABC Corp",
        regional_business_unit="UK",
        credit_status_indicator="normal",
        master_data_source="SAP",
    )
    db_session.add(customer)

    account = CustomerAccount(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        customer_id=customer.id,
        sap_account_ref="ACCT001",
        company_code="1000",
        currency_code="GBP",
        account_status="active",
    )
    db_session.add(account)

    role = RoleProfile(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        role_code="collections_analyst",
        role_label="Collections Analyst",
        description="Analyst",
        allowed_widgets_json={},
        entitled_queue_states_json={},
        allowed_actions_json={"actions": ["capture_promise"]},
        can_view_sensitive_fields=False,
        profile_status="active",
    )
    db_session.add(role)

    rule_set = PolicyRuleSetVersion(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        version_number=1,
        version_label="v1.0",
        region_code=None,
        rule_set_status="active",
        effective_from=now,
    )
    db_session.add(rule_set)

    rule = PolicyRule(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        rule_set_version_id=rule_set.id,
        rule_code="PROMISE_AMOUNT_REQUIRED",
        rule_category="validation",
        action_type="promise_create",
        rule_description="Promise amount must be present",
        condition_json={"type": "field_present", "parameters": {"field": "promised_amount"}},
        parameters_json={},
        failure_message="Promise amount is required",
        evaluation_order=1,
        is_enabled=True,
    )
    db_session.add(rule)
    db_session.commit()

    service = PromiseService(db_session, clock)

    analyst_role = RoleContext(
        role_code="collections_analyst",
        role_label="Collections Analyst",
        allowed_widgets=[],
        entitled_queue_states=[],
        allowed_actions=["capture_promise"],
        can_view_sensitive_fields=False,
    )

    user_id = uuid.uuid4()
    ctx = RequestContext(
        user_id=str(user_id),
        username="analyst1",
        display_name="Analyst",
        email="analyst@example.com",
        session_id=str(uuid.uuid4()),
        active_role=analyst_role,
        available_roles=[analyst_role],
        correlation_id="test",
    )

    request1 = PromiseCreateRequest(
        customer_account_id=str(account.id),
        promised_amount="5000.00",
        currency_code="GBP",
        promised_date=datetime(2026, 12, 1, tzinfo=timezone.utc),
        promise_scope_type="full_account",
    )

    # First call
    service.create_promise(
        request=request1,
        ctx=ctx,
        idempotency_key="test-key-003",
        correlation_id="test",
    )

    # Second call with same key but different body
    request2 = PromiseCreateRequest(
        customer_account_id=str(account.id),
        promised_amount="10000.00",  # Different amount
        currency_code="GBP",
        promised_date=datetime(2026, 12, 1, tzinfo=timezone.utc),
        promise_scope_type="full_account",
    )

    with pytest.raises(ConflictError, match="Idempotency key conflict"):
        service.create_promise(
            request=request2,
            ctx=ctx,
            idempotency_key="test-key-003",
            correlation_id="test",
        )
