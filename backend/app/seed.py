"""Idempotent seed data for local/dev environment"""
import hashlib
import uuid
from datetime import UTC, date, datetime, timedelta

from cryptography.fernet import Fernet
from sqlalchemy.orm import Session

from .config import settings
from .database import SessionLocal
from .models.customer import (
    BankAccount,
    Customer,
    Device,
    Entitlement,
    LoanSnapshot,
    Profile,
    ProfileAccountVisibility,
)
from .models.payee import CopCheck, Payee
from .models.ref_code import RefCode


def seed_database() -> None:
    """Seed database with initial reference data (idempotent)"""
    db = SessionLocal()
    try:
        _seed_ref_codes(db)
        _seed_demo_customer(db)
        _seed_demo_entitlements(db)
        _seed_demo_accounts(db)
        _seed_demo_loans(db)
        _seed_demo_payees(db)
        _seed_payment_limits(db)
        _seed_demo_payment(db)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Seed error: {e}")
        raise
    finally:
        db.close()


def _seed_ref_codes(db: Session) -> None:
    """Seed ref_code table with required reference data"""
    # Check if ref_codes already exist
    existing_count = db.query(RefCode).count()
    if existing_count > 0:
        print(f"RefCode table already has {existing_count} entries, skipping seed")
        return

    ref_codes = [
        # payment_internal_state group
        {
            "ref_code_id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
            "code_group": "payment_internal_state",
            "code_value": "prepared",
            "display_label": "Prepared",
            "customer_message": "Payment is being prepared",
            "sort_order": 1,
        },
        {
            "ref_code_id": uuid.UUID("00000000-0000-0000-0000-000000000002"),
            "code_group": "payment_internal_state",
            "code_value": "awaiting_sca",
            "display_label": "Awaiting Approval",
            "customer_message": "Payment is awaiting your approval",
            "sort_order": 2,
        },
        {
            "ref_code_id": uuid.UUID("00000000-0000-0000-0000-000000000003"),
            "code_group": "payment_internal_state",
            "code_value": "submitted",
            "display_label": "Submitted",
            "customer_message": "Payment has been submitted",
            "sort_order": 3,
        },
        {
            "ref_code_id": uuid.UUID("00000000-0000-0000-0000-000000000004"),
            "code_group": "payment_internal_state",
            "code_value": "completed",
            "display_label": "Completed",
            "customer_message": "Payment has been completed",
            "sort_order": 4,
        },
        {
            "ref_code_id": uuid.UUID("00000000-0000-0000-0000-000000000005"),
            "code_group": "payment_internal_state",
            "code_value": "rejected",
            "display_label": "Rejected",
            "customer_message": "Payment was rejected",
            "sort_order": 5,
        },

        # risk_treatment_reason group
        {
            "ref_code_id": uuid.UUID("00000000-0000-0000-0000-000000000101"),
            "code_group": "risk_treatment_reason",
            "code_value": "high_risk_score",
            "display_label": "High Risk Score",
            "customer_message": "This payment requires additional verification",
            "sort_order": 1,
        },
        {
            "ref_code_id": uuid.UUID("00000000-0000-0000-0000-000000000102"),
            "code_group": "risk_treatment_reason",
            "code_value": "suspicious_pattern",
            "display_label": "Suspicious Pattern",
            "customer_message": "We noticed unusual activity and need to verify this payment",
            "sort_order": 2,
        },

        # notification_template group
        {
            "ref_code_id": uuid.UUID("00000000-0000-0000-0000-000000000201"),
            "code_group": "notification_template",
            "code_value": "payment_sent",
            "display_label": "Payment Sent",
            "customer_message": "Your payment has been sent",
            "sort_order": 1,
        },
        {
            "ref_code_id": uuid.UUID("00000000-0000-0000-0000-000000000202"),
            "code_group": "notification_template",
            "code_value": "payment_pending",
            "display_label": "Payment Pending",
            "customer_message": "Your payment is being processed",
            "sort_order": 2,
        },
        {
            "ref_code_id": uuid.UUID("00000000-0000-0000-0000-000000000203"),
            "code_group": "notification_template",
            "code_value": "payment_failed",
            "display_label": "Payment Failed",
            "customer_message": "Your payment could not be completed",
            "sort_order": 3,
        },

        # security_event_type group
        {
            "ref_code_id": uuid.UUID("00000000-0000-0000-0000-000000000301"),
            "code_group": "security_event_type",
            "code_value": "login_success",
            "display_label": "Successful Login",
            "customer_message": "You have successfully logged in",
            "sort_order": 1,
        },
        {
            "ref_code_id": uuid.UUID("00000000-0000-0000-0000-000000000302"),
            "code_group": "security_event_type",
            "code_value": "login_failure",
            "display_label": "Failed Login Attempt",
            "customer_message": "A failed login attempt was detected",
            "sort_order": 2,
        },

        # scam_claim_reason group
        {
            "ref_code_id": uuid.UUID("00000000-0000-0000-0000-000000000401"),
            "code_group": "scam_claim_reason",
            "code_value": "unauthorized_payment",
            "display_label": "Unauthorized Payment",
            "customer_message": "I did not authorize this payment",
            "sort_order": 1,
        },
        {
            "ref_code_id": uuid.UUID("00000000-0000-0000-0000-000000000402"),
            "code_group": "scam_claim_reason",
            "code_value": "suspected_fraud",
            "display_label": "Suspected Fraud",
            "customer_message": "I believe this payment was fraudulent",
            "sort_order": 2,
        },
    ]

    for ref_data in ref_codes:
        ref_code = RefCode(
            ref_code_id=ref_data["ref_code_id"],
            code_group=ref_data["code_group"],
            code_value=ref_data["code_value"],
            display_label=ref_data["display_label"],
            customer_message=ref_data.get("customer_message"),
            sort_order=ref_data["sort_order"],
            is_active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        db.add(ref_code)

    print(f"Seeded {len(ref_codes)} ref_code entries")


def _seed_demo_customer(db: Session) -> None:
    """Seed demo customer with device and profile"""
    # Check if demo customer already exists
    demo_customer_id = uuid.UUID("10000000-0000-0000-0000-000000000001")
    existing_customer = db.get(Customer, demo_customer_id)
    if existing_customer:
        print("Demo customer already exists, skipping customer seed")
        return

    # Create demo customer (matches CIAM stub credentials)
    customer = Customer(
        customer_id=demo_customer_id,
        external_identity_ref="ciam_sasha_001",
        customer_type="retail",
        first_name="Sasha",
        primary_contact_ref="sasha.patel@gmail.com",
        status="active",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(customer)

    # Create personal profile
    profile_personal = Profile(
        profile_id=uuid.UUID("10000000-0000-0000-0000-000000000101"),
        customer_id=customer.customer_id,
        profile_type="personal",
        external_profile_ref="profile_sasha_personal",
        display_name="Personal",
        status="active",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(profile_personal)

    # Create business profile
    profile_business = Profile(
        profile_id=uuid.UUID("10000000-0000-0000-0000-000000000102"),
        customer_id=customer.customer_id,
        profile_type="business",
        external_profile_ref="profile_sasha_business",
        display_name="Sasha's Consulting Ltd",
        status="active",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(profile_business)

    # Create trusted device
    device = Device(
        device_id=uuid.UUID("10000000-0000-0000-0000-000000000201"),
        customer_id=customer.customer_id,
        device_public_key_ref="device_key_sasha_001",
        platform_type="ios",
        platform_device_ref="ios_device_sasha_001",
        device_label="Sasha's iPhone",
        trust_state="trusted",
        integrity_state="ok",
        biometric_enabled=True,
        passcode_failed_count=0,
        registered_at=datetime.now(UTC),
        last_seen_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(device)

    print("Seeded demo customer (Sasha), profile, and trusted device")
    print("Demo credentials: sasha.patel@gmail.com / Demo1234! / passcode: 123456")


def _seed_demo_entitlements(db: Session) -> None:
    """Seed entitlements for demo profiles"""
    demo_profile_personal_id = uuid.UUID("10000000-0000-0000-0000-000000000101")
    demo_profile_business_id = uuid.UUID("10000000-0000-0000-0000-000000000102")

    # Check if entitlements already exist
    existing = db.query(Entitlement).filter(Entitlement.profile_id == demo_profile_personal_id).count()
    if existing > 0:
        print("Demo entitlements already exist, skipping")
        return

    now = datetime.now(UTC)

    # Personal profile entitlement
    entitlement_personal = Entitlement(
        entitlement_id=uuid.UUID("10000000-0000-0000-0000-000000000301"),
        profile_id=demo_profile_personal_id,
        entitlement_code="retail_full_access",
        capability_type="payer",
        can_view_accounts=True,
        can_manage_payees=True,
        can_initiate_payments=True,
        source_system_ref="stub_mandate_001",
        effective_from=now,
        effective_to=None,
        created_at=now,
        updated_at=now,
    )
    db.add(entitlement_personal)

    # Business profile entitlement
    entitlement_business = Entitlement(
        entitlement_id=uuid.UUID("10000000-0000-0000-0000-000000000302"),
        profile_id=demo_profile_business_id,
        entitlement_code="business_full_access",
        capability_type="business_admin",
        can_view_accounts=True,
        can_manage_payees=True,
        can_initiate_payments=True,
        source_system_ref="stub_mandate_002",
        effective_from=now,
        effective_to=None,
        created_at=now,
        updated_at=now,
    )
    db.add(entitlement_business)

    print("Seeded demo entitlements (personal + business full access)")


def _seed_demo_accounts(db: Session) -> None:
    """Seed bank accounts for demo customer"""
    demo_profile_id = uuid.UUID("10000000-0000-0000-0000-000000000101")

    # Check if accounts already exist
    account_id_1 = uuid.uuid5(uuid.NAMESPACE_DNS, "account:acc_current_001")
    existing = db.get(BankAccount, account_id_1)
    if existing:
        print("Demo accounts already exist, skipping")
        return

    now = datetime.now(UTC)

    # Current account
    account_1 = BankAccount(
        bank_account_id=account_id_1,
        external_account_ref="acc_current_001",
        account_type="current",
        account_name="Personal Current Account",
        sort_code_masked="12-34-56",
        account_number_masked="****5678",
        currency_code="GBP",
        account_holder_name="Sasha Patel",
        current_balance_minor=124836,  # £1248.36
        available_balance_minor=124836,
        overdraft_limit_minor=None,
        freshness_at=now,
        source_status="available",
        created_at=now,
        updated_at=now,
    )
    db.add(account_1)

    # Visibility mapping
    visibility_1 = ProfileAccountVisibility(
        profile_account_visibility_id=uuid.uuid4(),
        profile_id=demo_profile_id,
        bank_account_id=account_id_1,
        visibility_reason="profile_owned",
        payment_permission=True,
        visible_from=now,
        visible_to=None,
        created_at=now,
        updated_at=now,
    )
    db.add(visibility_1)

    # Credit card
    account_id_2 = uuid.uuid5(uuid.NAMESPACE_DNS, "account:acc_credit_001")
    account_2 = BankAccount(
        bank_account_id=account_id_2,
        external_account_ref="acc_credit_001",
        account_type="credit_card",
        account_name="Visa Credit Card",
        sort_code_masked="",
        account_number_masked="****1234",
        currency_code="GBP",
        account_holder_name="Sasha Patel",
        current_balance_minor=-18240,  # £182.40 owed
        available_balance_minor=281760,  # £2817.60 available credit
        overdraft_limit_minor=None,
        freshness_at=now,
        source_status="available",
        created_at=now,
        updated_at=now,
    )
    db.add(account_2)

    visibility_2 = ProfileAccountVisibility(
        profile_account_visibility_id=uuid.uuid4(),
        profile_id=demo_profile_id,
        bank_account_id=account_id_2,
        visibility_reason="profile_owned",
        payment_permission=False,  # Credit cards can't be payment source
        visible_from=now,
        visible_to=None,
        created_at=now,
        updated_at=now,
    )
    db.add(visibility_2)

    print("Seeded demo accounts (current account £1248.36, credit card £182.40 owed)")


def _seed_demo_loans(db: Session) -> None:
    """Seed loans for demo customer"""
    demo_profile_id = uuid.UUID("10000000-0000-0000-0000-000000000101")

    # Check if loans already exist
    loan_id = uuid.uuid5(uuid.NAMESPACE_DNS, "loan:loan_personal_001")
    existing = db.get(LoanSnapshot, loan_id)
    if existing:
        print("Demo loans already exist, skipping")
        return

    now = datetime.now(UTC)
    next_payment_date = date.today() + timedelta(days=15)

    loan = LoanSnapshot(
        loan_snapshot_id=loan_id,
        profile_id=demo_profile_id,
        external_loan_ref="loan_personal_001",
        loan_name="Personal Loan",
        outstanding_balance_minor=842500,  # £8,425.00
        next_repayment_minor=29500,  # £295.00
        next_repayment_date=next_payment_date,
        currency_code="GBP",
        freshness_at=now,
        source_status="available",
        created_at=now,
        updated_at=now,
    )
    db.add(loan)

    print(f"Seeded demo loan (£8,425 outstanding, next payment £295 on {next_payment_date})")


def _seed_demo_payees(db: Session) -> None:
    """Seed payees for demo customer"""
    demo_customer_id = uuid.UUID("10000000-0000-0000-0000-000000000001")
    demo_profile_id = uuid.UUID("10000000-0000-0000-0000-000000000101")

    # Check if payees already exist
    payee_id_1 = uuid.UUID("10000000-0000-0000-0000-000000000501")
    existing = db.get(Payee, payee_id_1)
    if existing:
        print("Demo payees already exist, skipping")
        return

    now = datetime.now(UTC)

    # Encryption key for account numbers
    import base64
    key_bytes = settings.secret_key.encode()[:32].ljust(32, b'0')
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    fernet = Fernet(fernet_key)

    # Payee 1: Jamie Clarke
    account_number_1 = "12345678"
    sort_code_1 = "12-34-56"
    encrypted_1 = fernet.encrypt(account_number_1.encode()).decode()
    hash_1 = hashlib.sha256(f"{sort_code_1}:{account_number_1}".encode()).hexdigest()

    payee_1 = Payee(
        payee_id=payee_id_1,
        customer_id=demo_customer_id,
        profile_id=demo_profile_id,
        external_payee_ref=f"payee_{payee_id_1.hex[:16]}",
        payee_name="Jamie Clarke",
        sort_code=sort_code_1,
        account_number_encrypted=encrypted_1,
        account_number_masked="****5678",
        account_number_hash=hash_1,
        payee_type="personal",
        is_saved=True,
        status="active",
        last_verified_at=now,
        created_at=now,
        updated_at=now,
    )
    db.add(payee_1)

    # CoP check for payee 1
    cop_1 = CopCheck(
        cop_check_id=uuid.uuid4(),
        payee_id=payee_id_1,
        request_reference=f"cop_{uuid.uuid4().hex[:16]}",
        check_trigger="new_payee",
        checked_name="Jamie Clarke",
        checked_sort_code=sort_code_1,
        checked_account_number_hash=hash_1,
        outcome="match",
        suggested_name=None,
        policy_treatment="allow",
        customer_acknowledged_at=None,
        provider_reference="stub_cop_001",
        checked_at=now,
        expires_at=now + timedelta(days=90),
        raw_response_digest=None,
        correlation_id=f"corr_{uuid.uuid4().hex[:16]}",
        created_at=now,
    )
    db.add(cop_1)

    # Payee 2: K Evans Lettings
    payee_id_2 = uuid.UUID("10000000-0000-0000-0000-000000000502")
    account_number_2 = "87654321"
    sort_code_2 = "65-43-21"
    encrypted_2 = fernet.encrypt(account_number_2.encode()).decode()
    hash_2 = hashlib.sha256(f"{sort_code_2}:{account_number_2}".encode()).hexdigest()

    payee_2 = Payee(
        payee_id=payee_id_2,
        customer_id=demo_customer_id,
        profile_id=demo_profile_id,
        external_payee_ref=f"payee_{payee_id_2.hex[:16]}",
        payee_name="K Evans Lettings",
        sort_code=sort_code_2,
        account_number_encrypted=encrypted_2,
        account_number_masked="****4321",
        account_number_hash=hash_2,
        payee_type="business",
        is_saved=True,
        status="active",
        last_verified_at=now,
        created_at=now,
        updated_at=now,
    )
    db.add(payee_2)

    # CoP check for payee 2
    cop_2 = CopCheck(
        cop_check_id=uuid.uuid4(),
        payee_id=payee_id_2,
        request_reference=f"cop_{uuid.uuid4().hex[:16]}",
        check_trigger="new_payee",
        checked_name="K Evans Lettings",
        checked_sort_code=sort_code_2,
        checked_account_number_hash=hash_2,
        outcome="match",
        suggested_name=None,
        policy_treatment="allow",
        customer_acknowledged_at=None,
        provider_reference="stub_cop_002",
        checked_at=now,
        expires_at=now + timedelta(days=90),
        raw_response_digest=None,
        correlation_id=f"corr_{uuid.uuid4().hex[:16]}",
        created_at=now,
    )
    db.add(cop_2)

    print("Seeded demo payees (Jamie Clarke, K Evans Lettings)")


def _seed_payment_limits(db: Session) -> None:
    """Seed payment limits for demo profile"""
    from .seed_payment_data import _seed_payment_limits as seed_limits
    seed_limits(db)


def _seed_demo_payment(db: Session) -> None:
    """Seed a demo payment order"""
    from .seed_payment_data import _seed_demo_payment as seed_payment
    seed_payment(db)


if __name__ == "__main__":
    seed_database()
    print("Database seeded successfully")
