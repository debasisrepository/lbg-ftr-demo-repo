"""Acceptance tests for FR-PTP-001: Promise-to-pay capture."""
import uuid
from datetime import datetime, timezone

import pytest

from app.core.clock import FixedClock
from app.core.context import RoleContext, RequestContext
from app.core.errors import PolicyFailureError, NotFoundError
from app.models.customers import Customer, CustomerAccount, Invoice
from app.models.policy import PolicyRuleSetVersion, PolicyRule
from app.models.roles import RoleProfile
from app.schemas.promise_schemas import PromiseCreateRequest, ScopeLinkInput
from app.services.promise_service import PromiseService


def test_fr_ptp_001_criterion_1_mandatory_fields(db_session):
    """FR-PTP-001 Criterion 1: Given a user records a promise, when the promise is saved,
    then amount, date, scope, and source interaction are mandatory.
    """
    clock = FixedClock(datetime(2026, 11, 24, 10, 0, 0, tzinfo=timezone.utc))
    now = clock.now()

    # Create customer and account
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

    # Create rule set that validates mandatory fields
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

    # Rule: Amount required
    rule1 = PolicyRule(
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
    db_session.add(rule1)

    # Rule: Date required
    rule2 = PolicyRule(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        rule_set_version_id=rule_set.id,
        rule_code="PROMISE_DATE_REQUIRED",
        rule_category="validation",
        action_type="promise_create",
        rule_description="Promise date must be present",
        condition_json={"type": "field_present", "parameters": {"field": "promised_date"}},
        parameters_json={},
        failure_message="Promise date is required",
        evaluation_order=2,
        is_enabled=True,
    )
    db_session.add(rule2)

    # Rule: Scope required
    rule3 = PolicyRule(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        rule_set_version_id=rule_set.id,
        rule_code="PROMISE_SCOPE_REQUIRED",
        rule_category="validation",
        action_type="promise_create",
        rule_description="Promise scope type must be present",
        condition_json={"type": "field_present", "parameters": {"field": "scope_type"}},
        parameters_json={},
        failure_message="Promise scope type is required",
        evaluation_order=3,
        is_enabled=True,
    )
    db_session.add(rule3)

    # Rule: Source interaction required
    rule4 = PolicyRule(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        rule_set_version_id=rule_set.id,
        rule_code="PROMISE_SOURCE_REQUIRED",
        rule_category="validation",
        action_type="promise_create",
        rule_description="Promise must have source interaction",
        condition_json={"type": "field_equals_context", "parameters": {"field": "has_source_interaction", "expected": True}},
        parameters_json={},
        failure_message="Source interaction is required",
        evaluation_order=4,
        is_enabled=True,
    )
    db_session.add(rule4)

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

    # When user creates promise with all mandatory fields
    from app.schemas.promise_schemas import SourceInteractionInput

    request = PromiseCreateRequest(
        customer_account_id=str(account.id),
        promised_amount="5000.00",  # Mandatory: amount
        currency_code="GBP",
        promised_date=datetime(2026, 12, 1, tzinfo=timezone.utc),  # Mandatory: date
        promise_scope_type="full_account",  # Mandatory: scope
        source_interaction=SourceInteractionInput(  # Mandatory: source interaction
            interaction_type="call",
            interaction_direction="outbound",
            interaction_channel="phone",
            occurred_at=now,
            summary_text="Customer promised payment",
        ),
    )

    response, status_code = service.create_promise(
        request=request,
        ctx=ctx,
        idempotency_key="test-key-ptp-001",
        correlation_id="test",
    )

    # Then promise is saved successfully
    assert status_code == 201
    assert response.promise_id is not None
    assert response.promised_amount == "5000.00"
    # Compare dates without timezone (SQLite loses timezone info)
    assert response.promised_date.replace(tzinfo=None) == datetime(2026, 12, 1, 0, 0, 0)
    assert response.promise_scope_type == "full_account"


def test_fr_ptp_001_criterion_2_scope_links(db_session):
    """FR-PTP-001 Criterion 2: Given the promise relates to specific invoices or account balances,
    when the user saves the record, then those links are stored.
    """
    clock = FixedClock(datetime(2026, 11, 24, 10, 0, 0, tzinfo=timezone.utc))
    now = clock.now()

    # Create customer and account
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

    # Create invoices
    invoice1 = Invoice(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        customer_account_id=account.id,
        sap_invoice_ref="INV001",
        invoice_number="9000001",
        document_date=now,
        due_date=now,
        invoice_amount=5000.00,
        open_amount=5000.00,
        currency_code="GBP",
        invoice_status="open",
    )
    db_session.add(invoice1)

    invoice2 = Invoice(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        customer_account_id=account.id,
        sap_invoice_ref="INV002",
        invoice_number="9000002",
        document_date=now,
        due_date=now,
        invoice_amount=3000.00,
        open_amount=3000.00,
        currency_code="GBP",
        invoice_status="open",
    )
    db_session.add(invoice2)

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

    # When user creates promise with specific invoice links
    request = PromiseCreateRequest(
        customer_account_id=str(account.id),
        promised_amount="8000.00",
        currency_code="GBP",
        promised_date=datetime(2026, 12, 1, tzinfo=timezone.utc),
        promise_scope_type="invoice_specific",
        scope_links=[
            ScopeLinkInput(
                link_type="invoice",
                invoice_id=str(invoice1.id),
                linked_amount="5000.00",
            ),
            ScopeLinkInput(
                link_type="invoice",
                invoice_id=str(invoice2.id),
                linked_amount="3000.00",
            ),
        ],
    )

    response, status_code = service.create_promise(
        request=request,
        ctx=ctx,
        idempotency_key="test-key-ptp-002",
        correlation_id="test",
    )

    # Then links are stored
    assert status_code == 201
    assert len(response.scope_links) == 2
    assert response.scope_links[0].link_type == "invoice"
    assert response.scope_links[0].invoice_id == str(invoice1.id)
    assert response.scope_links[1].invoice_id == str(invoice2.id)


def test_fr_ptp_001_criterion_3_validation_rejection(db_session):
    """FR-PTP-001 Criterion 3: Given the user omits required information,
    when the save is attempted, then the system rejects the promise record.
    """
    clock = FixedClock(datetime(2026, 11, 24, 10, 0, 0, tzinfo=timezone.utc))
    now = clock.now()

    # Create customer and account
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

    # Create rule set that validates mandatory source interaction
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
        rule_code="PROMISE_SOURCE_REQUIRED",
        rule_category="validation",
        action_type="promise_create",
        rule_description="Promise must have source interaction",
        condition_json={"type": "field_in_set", "parameters": {"field": "has_source_interaction", "allowed_values": [True]}},
        parameters_json={},
        failure_message="Source interaction is required",
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

    # When user omits required source interaction
    request = PromiseCreateRequest(
        customer_account_id=str(account.id),
        promised_amount="5000.00",
        currency_code="GBP",
        promised_date=datetime(2026, 12, 1, tzinfo=timezone.utc),
        promise_scope_type="full_account",
        # Missing: source_interaction_id or source_interaction
    )

    # Then system rejects the promise
    with pytest.raises(PolicyFailureError, match="Promise validation failed"):
        service.create_promise(
            request=request,
            ctx=ctx,
            idempotency_key="test-key-ptp-003",
            correlation_id="test",
        )
