"""Acceptance tests for FR-C360-001: Unified customer account view."""
import uuid
from datetime import datetime, timezone

from app.core.clock import FixedClock
from app.core.context import RoleContext, RequestContext
from app.models.customers import Customer, CustomerAccount, Invoice
from app.models.receivables import ReceivableItem
from app.services.customer360_service import Customer360Service


def test_fr_c360_001_criterion_1_unified_view(db_session):
    """FR-C360-001 Criterion 1: Given customer data is available from authorized sources,
    when the user opens Customer 360, then the user sees receivables-relevant context
    in a single view.
    """
    clock = FixedClock(datetime(2026, 11, 24, 10, 0, 0, tzinfo=timezone.utc))
    now = clock.now()

    # Create customer with multiple data points
    customer = Customer(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        sap_customer_ref="CUST001",
        customer_name="ABC Corp",
        regional_business_unit="UK",
        credit_status_indicator="normal",
        master_data_source="SAP",
        last_sync_at=now,
    )
    db_session.add(customer)

    # Create account
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

    # Create invoice
    invoice = Invoice(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        customer_account_id=account.id,
        sap_invoice_ref="INV001",
        invoice_number="9000001",
        document_date=now,
        due_date=now,
        invoice_amount=10000.00,
        open_amount=10000.00,
        currency_code="GBP",
        invoice_status="open",
    )
    db_session.add(invoice)

    # Create receivable item
    item = ReceivableItem(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        invoice_id=invoice.id,
        customer_account_id=account.id,
        sap_open_item_ref="ITEM001",
        aging_bucket="61-90",
        days_past_due=75,
        open_amount=10000.00,
        currency_code="GBP",
        dispute_indicator=False,
        deduction_indicator=False,
        unapplied_cash_indicator=False,
        pending_evidence_indicator=False,
        promise_indicator=False,
        current_collectibility_status="collectible",
    )
    db_session.add(item)
    db_session.commit()

    service = Customer360Service(db_session, clock)

    role = RoleContext(
        role_code="collections_analyst",
        role_label="Collections Analyst",
        allowed_widgets=[],
        entitled_queue_states=[],
        allowed_actions=["customer.view"],
        can_view_sensitive_fields=False,
    )

    ctx = RequestContext(
        user_id=str(uuid.uuid4()),
        username="analyst1",
        display_name="Analyst",
        email="analyst@example.com",
        session_id=str(uuid.uuid4()),
        active_role=role,
        available_roles=[role],
        correlation_id="test",
    )

    # When user opens Customer 360
    result = service.get_customer_view(str(customer.id), ctx)

    # Then user sees receivables-relevant context in a single view
    assert result.customer_id == str(customer.id)
    assert result.profile.status in ["available", "masked"]
    assert result.accounts.status == "available"
    assert result.invoices.status == "available"
    assert result.receivable_items.status == "available"

    # Verify data presence
    assert len(result.accounts.data) >= 1
    assert len(result.invoices.data) >= 1
    assert len(result.receivable_items.data) >= 1


def test_fr_c360_001_criterion_2_unavailable_sections(db_session):
    """FR-C360-001 Criterion 2: Given some context is unavailable, when the view loads,
    then unavailable sections are clearly marked without blocking access to available data.
    """
    clock = FixedClock(datetime(2026, 11, 24, 10, 0, 0, tzinfo=timezone.utc))
    now = clock.now()

    # Create customer with account but NO invoices/receivables/promises
    customer = Customer(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        sap_customer_ref="CUST002",
        customer_name="XYZ Ltd",
        regional_business_unit="UK",
        credit_status_indicator="normal",
        master_data_source="SAP",
        last_sync_at=now,
    )
    db_session.add(customer)

    account = CustomerAccount(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        customer_id=customer.id,
        sap_account_ref="ACCT002",
        company_code="1000",
        currency_code="GBP",
        account_status="active",
    )
    db_session.add(account)
    db_session.commit()

    service = Customer360Service(db_session, clock)

    role = RoleContext(
        role_code="collections_analyst",
        role_label="Collections Analyst",
        allowed_widgets=[],
        entitled_queue_states=[],
        allowed_actions=["customer.view"],
        can_view_sensitive_fields=False,
    )

    ctx = RequestContext(
        user_id=str(uuid.uuid4()),
        username="analyst1",
        display_name="Analyst",
        email="analyst@example.com",
        session_id=str(uuid.uuid4()),
        active_role=role,
        available_roles=[role],
        correlation_id="test",
    )

    # When view loads
    result = service.get_customer_view(str(customer.id), ctx)

    # Then unavailable sections are marked without blocking available data
    assert result.accounts.status == "available"  # Accounts exist
    assert result.invoices.status == "unavailable"  # No invoices
    assert result.invoices.reason is not None
    assert result.receivable_items.status == "unavailable"  # No receivables
    assert result.receivable_items.reason is not None
    assert result.promises.status == "unavailable"  # No promises
    assert result.promises.reason is not None

    # Available data is accessible
    assert len(result.accounts.data) == 1


def test_fr_c360_001_criterion_3_field_masking(db_session):
    """FR-C360-001 Criterion 3: Given the user lacks permission to sensitive fields,
    when the view renders, then those fields are hidden or masked.
    """
    clock = FixedClock(datetime(2026, 11, 24, 10, 0, 0, tzinfo=timezone.utc))
    now = clock.now()

    # Create customer with sensitive credit status
    customer = Customer(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        sap_customer_ref="CUST003",
        customer_name="Sensitive Corp",
        regional_business_unit="UK",
        credit_status_indicator="high_risk",  # Sensitive field
        master_data_source="SAP",
        last_sync_at=now,
    )
    db_session.add(customer)

    account = CustomerAccount(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        customer_id=customer.id,
        sap_account_ref="ACCT003",
        company_code="1000",
        currency_code="GBP",
        account_status="active",
    )
    db_session.add(account)
    db_session.commit()

    service = Customer360Service(db_session, clock)

    # Analyst role WITHOUT sensitive field permission
    analyst_role = RoleContext(
        role_code="collections_analyst",
        role_label="Collections Analyst",
        allowed_widgets=[],
        entitled_queue_states=[],
        allowed_actions=["customer.view"],
        can_view_sensitive_fields=False,  # No permission
    )

    analyst_ctx = RequestContext(
        user_id=str(uuid.uuid4()),
        username="analyst1",
        display_name="Analyst",
        email="analyst@example.com",
        session_id=str(uuid.uuid4()),
        active_role=analyst_role,
        available_roles=[analyst_role],
        correlation_id="test",
    )

    # When analyst views customer
    result = service.get_customer_view(str(customer.id), analyst_ctx)

    # Then sensitive field is masked
    assert result.profile.status == "masked"
    assert result.profile.data["credit_status_indicator"] is None

    # Other fields still visible
    assert result.profile.data["customer_name"] == "Sensitive Corp"

    # Reviewer role WITH sensitive field permission
    reviewer_role = RoleContext(
        role_code="collections_reviewer",
        role_label="Collections Reviewer",
        allowed_widgets=[],
        entitled_queue_states=[],
        allowed_actions=["customer.view", "view_sensitive"],
        can_view_sensitive_fields=True,  # Has permission
    )

    reviewer_ctx = RequestContext(
        user_id=str(uuid.uuid4()),
        username="reviewer1",
        display_name="Reviewer",
        email="reviewer@example.com",
        session_id=str(uuid.uuid4()),
        active_role=reviewer_role,
        available_roles=[reviewer_role],
        correlation_id="test",
    )

    # When reviewer views customer
    result = service.get_customer_view(str(customer.id), reviewer_ctx)

    # Then sensitive field is visible
    assert result.profile.status == "available"
    assert result.profile.data["credit_status_indicator"] == "high_risk"
