"""Unit tests for customer360 service."""
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.core.clock import FixedClock
from app.core.context import RoleContext, RequestContext
from app.models.customers import Customer, CustomerAccount, Invoice
from app.models.receivables import ReceivableItem
from app.services.customer360_service import Customer360Service


def test_search_customers(db_session):
    """Test customer search."""
    clock = FixedClock(datetime(2026, 11, 24, 10, 0, 0, tzinfo=timezone.utc))
    now = clock.now()

    # Create test customer
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
    db_session.commit()

    service = Customer360Service(db_session, clock)
    result = service.search_customers(q="ABC", limit=10, offset=0)

    assert result.total == 1
    assert len(result.items) == 1
    assert result.items[0].customer_name == "ABC Corp"
    assert result.items[0].account_count == 1


def test_get_customer_view_with_masking(db_session):
    """Test customer 360 view with field masking."""
    clock = FixedClock(datetime(2026, 11, 24, 10, 0, 0, tzinfo=timezone.utc))
    now = clock.now()

    # Create test customer
    customer = Customer(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        sap_customer_ref="CUST001",
        customer_name="ABC Corp",
        regional_business_unit="UK",
        credit_status_indicator="high_risk",
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

    # Test with non-sensitive role (analyst)
    analyst_role = RoleContext(
        role_code="collections_analyst",
        role_label="Collections Analyst",
        allowed_widgets=[],
        entitled_queue_states=[],
        allowed_actions=["customer.view"],
        can_view_sensitive_fields=False,
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

    result = service.get_customer_view(str(customer.id), analyst_ctx)

    # Profile section should be masked
    assert result.profile.status == "masked"
    assert result.profile.data["credit_status_indicator"] is None

    # Other sections should be available
    assert result.accounts.status == "available"
    assert len(result.accounts.data) == 1

    assert result.invoices.status == "available"
    assert len(result.invoices.data) == 1

    assert result.receivable_items.status == "available"
    assert len(result.receivable_items.data) == 1


def test_get_customer_view_with_sensitive_access(db_session):
    """Test customer 360 view with sensitive field access."""
    clock = FixedClock(datetime(2026, 11, 24, 10, 0, 0, tzinfo=timezone.utc))
    now = clock.now()

    # Create test customer
    customer = Customer(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        sap_customer_ref="CUST001",
        customer_name="ABC Corp",
        regional_business_unit="UK",
        credit_status_indicator="high_risk",
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
    db_session.commit()

    service = Customer360Service(db_session, clock)

    # Test with sensitive role (reviewer)
    reviewer_role = RoleContext(
        role_code="collections_reviewer",
        role_label="Collections Reviewer",
        allowed_widgets=[],
        entitled_queue_states=[],
        allowed_actions=["customer.view", "view_sensitive"],
        can_view_sensitive_fields=True,
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

    result = service.get_customer_view(str(customer.id), reviewer_ctx)

    # Profile section should be available with sensitive data
    assert result.profile.status == "available"
    assert result.profile.data["credit_status_indicator"] == "high_risk"
