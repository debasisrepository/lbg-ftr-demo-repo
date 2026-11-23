"""
Acceptance tests for accounts features.
Requirement: FR-ACCT-001, FR-ACCT-002, FR-ACCT-003
"""
import uuid
from datetime import UTC, datetime, timedelta

from app.models.account_read_model import AccountReadModel
from app.models.capability_status_record import CapabilityStatusRecord
from app.models.customer_profile_ref import CustomerProfileRef
from app.models.sandbox_entitlement import SandboxEntitlement


def test_fr_acct_001_accounts_overview_authenticated_entitled(auth_client, db_session):
    """
    FR-ACCT-001: Accounts overview for in-scope personal accounts.
    
    Acceptance Criteria:
    - The overview contains each in-scope personal account made available for Release 1.
    - The customer can distinguish one account from another by clear identifying information.
    - The overview is available only after authentication and entitlement checks succeed.
    - If account data cannot be shown for all accounts, the app communicates the affected
      capability state clearly rather than implying full success.
    """
    customer = db_session.query(CustomerProfileRef).first()
    
    # Check entitlement exists (seed should have created it)
    existing_entitlement = db_session.query(SandboxEntitlement).filter_by(
        customer_profile_ref_id=customer.id,
        resource_type="account",
        resource_reference="*"
    ).first()
    
    if not existing_entitlement:
        entitlement = SandboxEntitlement(
            id=uuid.uuid4(),
            customer_profile_ref_id=customer.id,
            resource_type="account",
            resource_reference="*",
            decision="allow"
        )
        db_session.add(entitlement)
    
    # Check capability exists (seed should have created it)
    existing_capability = db_session.query(CapabilityStatusRecord).filter_by(
        capability_name="accounts_overview",
        effective_to=None
    ).first()
    
    if not existing_capability:
        capability = CapabilityStatusRecord(
            id=uuid.uuid4(),
            capability_name="accounts_overview",
            status_value="healthy",
            cause_category="unknown",
            effective_from=datetime.now(UTC)
        )
        db_session.add(capability)
    
    # Clear existing accounts and add accounts with distinguishing information
    db_session.query(AccountReadModel).filter_by(customer_profile_ref_id=customer.id).delete()
    db_session.commit()
    accounts_data = [
        ("current", "Main Current Account", "****1234", 124836),
        ("savings", "Instant Saver", "****5678", 350000),
        ("current", "Joint Account", "****9012", 500000),
    ]
    
    for acc_type, name, masked_id, balance in accounts_data:
        account = AccountReadModel(
            id=uuid.uuid4(),
            customer_profile_ref_id=customer.id,
            account_system_reference=f"ACC-{masked_id}",
            account_type=acc_type,
            display_name=name,
            masked_account_identifier=masked_id,
            balance_amount_minor=balance,
            balance_currency="GBP",
            balance_availability_state="current",
            as_of_timestamp=datetime.now(UTC),
            freshness_status="within_target",
            freshness_breach_indicator=False,
            source_system_type="core_banking",
            provenance_reference=f"test-{masked_id}",
            projection_updated_at=datetime.now(UTC)
        )
        db_session.add(account)
    db_session.commit()
    
    # Test: Overview available after authentication and entitlement
    response = auth_client.get("/api/v1/accounts")
    assert response.status_code == 200
    data = response.json()
    
    # Verify all in-scope accounts present
    assert data["total"] == 3
    assert len(data["items"]) == 3
    
    # Verify distinguishing information
    names = [item["display_name"] for item in data["items"]]
    assert "Main Current Account" in names
    assert "Instant Saver" in names
    assert "Joint Account" in names
    
    masked_ids = [item["masked_account_identifier"] for item in data["items"]]
    assert "****1234" in masked_ids
    assert "****5678" in masked_ids
    
    # Verify capability state communicated
    assert data["overview_state"] == "complete"
    assert data["capability"]["status_value"] == "healthy"


def test_fr_acct_001_partial_data_communicated(auth_client, db_session):
    """
    FR-ACCT-001: Partial data failure communicated clearly.
    """
    customer = db_session.query(CustomerProfileRef).first()
    
    if not db_session.query(SandboxEntitlement).filter_by(
        customer_profile_ref_id=customer.id,
        resource_type="account",
        resource_reference="*"
    ).first():
        entitlement = SandboxEntitlement(
            id=uuid.uuid4(),
            customer_profile_ref_id=customer.id,
            resource_type="account",
            resource_reference="*",
            decision="allow"
        )
        db_session.add(entitlement)
    
    if not db_session.query(CapabilityStatusRecord).filter_by(
        capability_name="accounts_overview",
        effective_to=None
    ).first():
        capability = CapabilityStatusRecord(
            id=uuid.uuid4(),
            capability_name="accounts_overview",
            status_value="healthy",
            cause_category="unknown",
            effective_from=datetime.now(UTC)
        )
        db_session.add(capability)
    
    # Add one available and one unavailable account
    account1 = AccountReadModel(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer.id,
        account_system_reference="ACC-AVAILABLE",
        account_type="current",
        display_name="Available Account",
        masked_account_identifier="****1111",
        balance_amount_minor=100000,
        balance_currency="GBP",
        balance_availability_state="current",
        as_of_timestamp=datetime.now(UTC),
        freshness_status="within_target",
        freshness_breach_indicator=False,
        source_system_type="core_banking",
        provenance_reference="test-avail",
        projection_updated_at=datetime.now(UTC)
    )
    db_session.add(account1)
    
    account2 = AccountReadModel(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer.id,
        account_system_reference="ACC-UNAVAILABLE",
        account_type="savings",
        display_name="Unavailable Account",
        masked_account_identifier="****2222",
        balance_amount_minor=None,
        balance_currency=None,
        balance_availability_state="unavailable",
        as_of_timestamp=None,
        freshness_status="unknown",
        freshness_breach_indicator=False,
        source_system_type="core_banking",
        provenance_reference="test-unavail",
        projection_updated_at=datetime.now(UTC)
    )
    db_session.add(account2)
    db_session.commit()
    
    response = auth_client.get("/api/v1/accounts")
    assert response.status_code == 200
    data = response.json()
    
    # Verify partial state communicated
    assert data["overview_state"] == "partial"
    assert any(item["item_state"] == "partial" for item in data["items"])
    assert any(item["item_state"] == "available" for item in data["items"])


def test_fr_acct_002_freshness_indicator_visible(auth_client, db_session):
    """
    FR-ACCT-002: Freshness timestamp on accounts overview.
    
    Acceptance Criteria:
    - Each account overview response includes a customer-visible freshness indicator
      or as-of timestamp.
    - If freshness cannot be established, the app indicates that the data is unavailable
      or not current.
    - Freshness messaging remains visible when the customer revisits or refreshes the overview.
    - The freshness indicator is presented in accessible plain language.
    """
    customer = db_session.query(CustomerProfileRef).first()
    
    if not db_session.query(SandboxEntitlement).filter_by(
        customer_profile_ref_id=customer.id,
        resource_type="account",
        resource_reference="*"
    ).first():
        entitlement = SandboxEntitlement(
            id=uuid.uuid4(),
            customer_profile_ref_id=customer.id,
            resource_type="account",
            resource_reference="*",
            decision="allow"
        )
        db_session.add(entitlement)
    
    if not db_session.query(CapabilityStatusRecord).filter_by(
        capability_name="accounts_overview",
        effective_to=None
    ).first():
        capability = CapabilityStatusRecord(
            id=uuid.uuid4(),
            capability_name="accounts_overview",
            status_value="healthy",
            cause_category="unknown",
            effective_from=datetime.now(UTC)
        )
        db_session.add(capability)
    
    # Add account with known freshness
    account = AccountReadModel(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer.id,
        account_system_reference="ACC-FRESH",
        account_type="current",
        display_name="Fresh Account",
        masked_account_identifier="****3333",
        balance_amount_minor=100000,
        balance_currency="GBP",
        balance_availability_state="current",
        as_of_timestamp=datetime.now(UTC) - timedelta(minutes=1),
        freshness_status="within_target",
        freshness_breach_indicator=False,
        source_system_type="core_banking",
        provenance_reference="test-fresh",
        projection_updated_at=datetime.now(UTC)
    )
    db_session.add(account)
    db_session.commit()
    
    response = auth_client.get("/api/v1/accounts")
    assert response.status_code == 200
    data = response.json()
    
    item = data["items"][0]
    
    # Verify freshness indicator present
    assert "as_of_timestamp" in item
    assert item["as_of_timestamp"] is not None
    assert "freshness_status" in item
    assert item["freshness_status"] == "within_target"
    
    # Verify plain-language freshness text
    assert "freshness_text" in item
    assert len(item["freshness_text"]) > 0
    # Text should be accessible (not just "within_target")
    assert "minute" in item["freshness_text"].lower() or "ago" in item["freshness_text"].lower()


def test_fr_acct_002_unknown_freshness_indicated(auth_client, db_session):
    """
    FR-ACCT-002: Unknown freshness clearly indicated.
    """
    customer = db_session.query(CustomerProfileRef).first()
    
    if not db_session.query(SandboxEntitlement).filter_by(
        customer_profile_ref_id=customer.id,
        resource_type="account",
        resource_reference="*"
    ).first():
        entitlement = SandboxEntitlement(
            id=uuid.uuid4(),
            customer_profile_ref_id=customer.id,
            resource_type="account",
            resource_reference="*",
            decision="allow"
        )
        db_session.add(entitlement)
    
    if not db_session.query(CapabilityStatusRecord).filter_by(
        capability_name="accounts_overview",
        effective_to=None
    ).first():
        capability = CapabilityStatusRecord(
            id=uuid.uuid4(),
            capability_name="accounts_overview",
            status_value="healthy",
            cause_category="unknown",
            effective_from=datetime.now(UTC)
        )
        db_session.add(capability)
    
    # Clear existing accounts and add account with unknown freshness
    db_session.query(AccountReadModel).filter_by(customer_profile_ref_id=customer.id).delete()
    db_session.commit()
    account = AccountReadModel(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer.id,
        account_system_reference="ACC-UNKNOWN",
        account_type="current",
        display_name="Unknown Freshness Account",
        masked_account_identifier="****4444",
        balance_amount_minor=None,
        balance_currency=None,
        balance_availability_state="unknown",
        as_of_timestamp=None,
        freshness_status="unknown",
        freshness_breach_indicator=False,
        source_system_type="core_banking",
        provenance_reference="test-unknown",
        projection_updated_at=datetime.now(UTC)
    )
    db_session.add(account)
    db_session.commit()
    
    response = auth_client.get("/api/v1/accounts")
    assert response.status_code == 200
    data = response.json()
    
    item = data["items"][0]
    
    # Verify unknown freshness communicated
    assert item["as_of_timestamp"] is None
    assert item["freshness_status"] == "unknown"
    assert "cannot" in item["freshness_text"].lower() or "unknown" in item["freshness_text"].lower()


def test_fr_acct_003_never_show_missing_as_zero(auth_client, db_session):
    """
    FR-ACCT-003: Never show missing balance as zero.
    
    Acceptance Criteria:
    - When a balance value is unavailable, the app shows an unavailable or stale-data
      state instead of a numeric zero.
    - Any dependent overview or detail screen that cannot trust the balance value clearly
      communicates that condition.
    - A partial data failure does not silently substitute zero for any missing monetary value.
    - This rule applies consistently across overview, detail, and degraded-mode experiences.
    """
    customer = db_session.query(CustomerProfileRef).first()
    
    if not db_session.query(SandboxEntitlement).filter_by(
        customer_profile_ref_id=customer.id,
        resource_type="account",
        resource_reference="*"
    ).first():
        entitlement = SandboxEntitlement(
            id=uuid.uuid4(),
            customer_profile_ref_id=customer.id,
            resource_type="account",
            resource_reference="*",
            decision="allow"
        )
        db_session.add(entitlement)
    
    if not db_session.query(CapabilityStatusRecord).filter_by(
        capability_name="accounts_overview",
        effective_to=None
    ).first():
        capability = CapabilityStatusRecord(
            id=uuid.uuid4(),
            capability_name="accounts_overview",
            status_value="healthy",
            cause_category="unknown",
            effective_from=datetime.now(UTC)
        )
        db_session.add(capability)
    
    # Clear existing accounts and add account with unavailable balance
    db_session.query(AccountReadModel).filter_by(customer_profile_ref_id=customer.id).delete()
    db_session.commit()
    account = AccountReadModel(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer.id,
        account_system_reference="ACC-MISSING",
        account_type="current",
        display_name="Missing Balance Account",
        masked_account_identifier="****5555",
        balance_amount_minor=None,  # Missing - must NOT be shown as 0
        balance_currency=None,
        balance_availability_state="unavailable",
        as_of_timestamp=None,
        freshness_status="unknown",
        freshness_breach_indicator=False,
        source_system_type="core_banking",
        provenance_reference="test-missing",
        projection_updated_at=datetime.now(UTC)
    )
    db_session.add(account)
    db_session.commit()
    
    response = auth_client.get("/api/v1/accounts")
    assert response.status_code == 200
    data = response.json()
    
    item = data["items"][0]
    
    # Verify NULL balance, never 0
    assert item["balance"]["amount_minor"] is None
    assert item["balance"]["currency"] is None
    assert item["balance"]["availability_state"] == "unavailable"
    
    # Verify clear unavailable message (not "£0.00")
    assert "unavailable" in item["balance"]["display_text"].lower()
    assert "0" not in item["balance"]["display_text"]
    
    # Verify item state indicates partial
    assert item["item_state"] == "partial"
    assert item["payment_source_eligible"] is False
