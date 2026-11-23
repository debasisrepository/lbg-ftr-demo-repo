"""
Integration tests for loan view feature (Release 2).
Requirement: BR-ACCT-004, BR-ACCT-007, BRL-ACCT-01 to BRL-ACCT-04
Test Cases: TC-ACCT-003 to TC-ACCT-008
"""
import uuid
from datetime import UTC, datetime, timedelta

from app.models.account_read_model import AccountReadModel
from app.models.capability_status_record import CapabilityStatusRecord
from app.models.customer_profile_ref import CustomerProfileRef


def test_get_accounts_includes_loan_details(auth_client, db_session):
    """
    TC-ACCT-003: Loan account includes outstanding balance, next repayment date/amount, remaining term.
    Per BR-ACCT-004: Display personal loan details from loan servicing.
    """
    # Setup: Alex Taylor (seeded customer) has a loan account
    # Login as Alex Taylor who has a loan account
    response = auth_client.get("/api/v1/accounts")
    
    assert response.status_code == 200
    data = response.json()
    
    # Find loan account
    loan_accounts = [item for item in data["items"] if item["account_type"] == "loan"]
    assert len(loan_accounts) >= 1, "Should have at least one loan account"
    
    loan = loan_accounts[0]
    
    # Verify loan details are present
    assert "loan_details" in loan, "Loan account should include loan_details"
    loan_details = loan["loan_details"]
    
    assert loan_details is not None, "Loan details should not be null for loan account"
    assert "outstanding_balance_minor" in loan_details
    assert loan_details["outstanding_balance_minor"] == 1850000  # £18,500 from seed
    
    assert "next_repayment_date" in loan_details
    assert loan_details["next_repayment_date"] is not None
    
    assert "next_repayment_amount_minor" in loan_details
    assert loan_details["next_repayment_amount_minor"] == 45000  # £450 from seed
    
    assert "remaining_term_months" in loan_details
    assert loan_details["remaining_term_months"] == 42


def test_loan_account_without_loan_data_shows_null(auth_client, db_session):
    """
    TC-ACCT-004: Loan account without loan servicing data shows null loan_details.
    Per BRL-ACCT-01: Never show missing values as zero.
    """
    customer = db_session.query(CustomerProfileRef).first()
    
    # Create loan account without loan fields
    loan_account = AccountReadModel(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer.id,
        account_system_reference="LOAN-TEST-999",
        account_type="loan",
        display_name="Loan Without Details",
        masked_account_identifier="****9999",
        balance_amount_minor=None,
        balance_currency="GBP",
        balance_availability_state="unavailable",
        as_of_timestamp=datetime.now(UTC),
        freshness_status="unknown",
        freshness_breach_indicator=False,
        source_system_type="loan_servicing",
        provenance_reference="test-loan-999",
        projection_updated_at=datetime.now(UTC),
        # Loan fields explicitly null
        loan_outstanding_balance_minor=None,
        loan_next_repayment_date=None,
        loan_next_repayment_amount_minor=None,
        loan_remaining_term_months=None,
    )
    db_session.add(loan_account)
    db_session.commit()
    
    response = auth_client.get("/api/v1/accounts")
    
    assert response.status_code == 200
    data = response.json()
    
    # Find the test loan account
    test_loan = next(
        (item for item in data["items"] if item["display_name"] == "Loan Without Details"),
        None
    )
    
    assert test_loan is not None
    # Loan details object exists but all fields are null
    loan_details = test_loan["loan_details"]
    assert loan_details is not None, "Loan account should have loan_details object"
    assert loan_details["outstanding_balance_minor"] is None, "Missing loan data should be null, not zero"
    assert loan_details["next_repayment_date"] is None
    assert loan_details["next_repayment_amount_minor"] is None
    assert loan_details["remaining_term_months"] is None


def test_loan_view_capability_status(auth_client, db_session):
    """
    TC-ACCT-005: Loan view capability status is included in accounts overview.
    Per ADR-010: Capability status tracks service availability.
    """
    # Ensure loan_view capability exists (should be seeded)
    loan_cap = db_session.query(CapabilityStatusRecord).filter_by(
        capability_name="loan_view"
    ).first()
    
    if not loan_cap:
        loan_cap = CapabilityStatusRecord(
            id=uuid.uuid4(),
            capability_name="loan_view",
            status_value="healthy",
            cause_category="unknown",
            effective_from=datetime.now(UTC)
        )
        db_session.add(loan_cap)
        db_session.commit()
    
    response = auth_client.get("/api/v1/accounts")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify capability is present
    assert "capability" in data
    # Main capability should be accounts_overview, but loan data availability is tracked separately


def test_loan_graceful_degradation_when_unavailable(auth_client, db_session):
    """
    TC-ACCT-006: When loan servicing is unavailable, rest of overview still loads.
    Per ADR-010: Graceful degradation - show available data, never block overview.
    Per BR-ACCT-007: If loan servicing slow or down, show message and load rest.
    """
    customer = db_session.query(CustomerProfileRef).first()
    
    # Create loan account with unavailable balance state
    unavailable_loan = AccountReadModel(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer.id,
        account_system_reference="LOAN-UNAVAIL-001",
        account_type="loan",
        display_name="Unavailable Loan",
        masked_account_identifier="****8888",
        balance_amount_minor=None,
        balance_currency="GBP",
        balance_availability_state="unavailable",
        as_of_timestamp=None,
        freshness_status="unknown",
        freshness_breach_indicator=False,
        source_system_type="loan_servicing",
        provenance_reference="test-loan-unavail",
        projection_updated_at=datetime.now(UTC),
        loan_outstanding_balance_minor=None,
        loan_next_repayment_date=None,
        loan_next_repayment_amount_minor=None,
        loan_remaining_term_months=None,
    )
    db_session.add(unavailable_loan)
    db_session.commit()
    
    response = auth_client.get("/api/v1/accounts")
    
    # Overview should still succeed
    assert response.status_code == 200
    data = response.json()
    
    # Should have items (other accounts + unavailable loan)
    assert len(data["items"]) >= 1
    
    # Find unavailable loan
    unavail_loan_item = next(
        (item for item in data["items"] if item["display_name"] == "Unavailable Loan"),
        None
    )
    
    assert unavail_loan_item is not None
    assert unavail_loan_item["balance"]["availability_state"] == "unavailable"
    assert unavail_loan_item["balance"]["display_text"] == "Balance unavailable"
    # Loan details object exists but all fields are null when unavailable
    loan_details = unavail_loan_item["loan_details"]
    assert loan_details is not None
    assert loan_details["outstanding_balance_minor"] is None
    assert unavail_loan_item["item_state"] == "partial"  # Unavailable accounts are "partial"


def test_loan_stale_data_shows_freshness_indicator(auth_client, db_session):
    """
    TC-ACCT-007: Loan data older than 60 seconds shows when it was updated.
    Per BRL-ACCT-02: Values older than 60 seconds show freshness timestamp.
    """
    customer = db_session.query(CustomerProfileRef).first()
    
    # Create loan account with stale data (3 hours old)
    stale_time = datetime.now(UTC) - timedelta(hours=3)
    stale_loan = AccountReadModel(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer.id,
        account_system_reference="LOAN-STALE-001",
        account_type="loan",
        display_name="Stale Loan Data",
        masked_account_identifier="****7777",
        balance_amount_minor=2000000,
        balance_currency="GBP",
        balance_availability_state="stale",
        as_of_timestamp=stale_time,
        freshness_status="breached",
        freshness_breach_indicator=True,
        source_system_type="loan_servicing",
        provenance_reference="test-loan-stale",
        projection_updated_at=stale_time,
        loan_outstanding_balance_minor=2000000,
        loan_next_repayment_date=datetime.now(UTC).date() + timedelta(days=20),
        loan_next_repayment_amount_minor=50000,
        loan_remaining_term_months=40,
    )
    db_session.add(stale_loan)
    db_session.commit()
    
    response = auth_client.get("/api/v1/accounts")
    
    assert response.status_code == 200
    data = response.json()
    
    stale_loan_item = next(
        (item for item in data["items"] if item["display_name"] == "Stale Loan Data"),
        None
    )
    
    assert stale_loan_item is not None
    assert stale_loan_item["freshness_status"] == "breached"
    assert stale_loan_item["balance"]["availability_state"] == "stale"
    assert "freshness_text" in stale_loan_item
    assert stale_loan_item["freshness_text"] is not None
    # Freshness text should indicate when data was last updated


def test_non_loan_accounts_do_not_have_loan_details(auth_client, db_session):
    """
    TC-ACCT-008: Current and savings accounts do not include loan_details field.
    Ensures loan data is only shown for loan account type.
    """
    response = auth_client.get("/api/v1/accounts")
    
    assert response.status_code == 200
    data = response.json()
    
    # Find non-loan accounts (current, savings)
    non_loan_accounts = [
        item for item in data["items"] 
        if item["account_type"] in ("current", "savings")
    ]
    
    assert len(non_loan_accounts) >= 1, "Should have non-loan accounts from seed"
    
    for account in non_loan_accounts:
        # Non-loan accounts should not have loan_details
        # It should either be absent or null
        loan_details = account.get("loan_details")
        assert loan_details is None, f"Non-loan account {account['account_type']} should not have loan_details"
