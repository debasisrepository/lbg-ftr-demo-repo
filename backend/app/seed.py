"""Idempotent seed data for development and demonstration."""
import hashlib
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.common.enums import (
    AccountType,
    AuditEventType,
    AuditSeverity,
    ChallengeMethod,
    ChallengeStatus,
    ChallengeType,
    CoPDecisionState,
    CoPResultCode,
    DispatchState,
    FreshnessState,
    FraudDecisionCode,
    InstructionState,
    JourneyOutcomeCode,
    JourneyStep,
    NotificationType,
    PaymentStatusCode,
    ProfileType,
    SessionState,
    UserStatus,
)
from app.common.security import hash_password
from app.database import SessionLocal
from app.models.accounts import AccountDataGap, AccountSnapshot, LoanContextSnapshot
from app.models.audit import AuditLog, NotificationDispatch
from app.models.auth import AuthSession, RegisteredDevice, UserIdentity
from app.models.payees import CoPResult, Payee
from app.models.payments import (
    FraudDecision,
    PaymentApproval,
    PaymentInstruction,
    PaymentStatusHistory,
)
from app.models.profiles import ProfileEntitlement, UserProfile
from app.models.sca import StepUpChallenge
from app.models.telemetry import JourneyEvent


def seed_database(db: Session) -> None:
    """Seed the database with sample data. Idempotent - can be run multiple times."""
    now = datetime.now(timezone.utc)

    # Check if seed data already exists
    existing_user = db.query(UserIdentity).filter_by(username="admin@example.com").first()
    if existing_user:
        print("Seed data already exists. Skipping.")
        return

    print("Seeding database...")

    # 1. User Identities
    admin_user = UserIdentity(
        external_identity_id="ext-admin-001",
        username="admin@example.com",
        hashed_password=hash_password("admin123"),
        status=UserStatus.ACTIVE.value,
        created_at=now,
        updated_at=now
    )
    db.add(admin_user)
    db.flush()

    personal_user = UserIdentity(
        external_identity_id="ext-user-002",
        username="john.smith@example.com",
        hashed_password=hash_password("Personal123!"),
        status=UserStatus.ACTIVE.value,
        created_at=now,
        updated_at=now
    )
    db.add(personal_user)
    db.flush()

    business_user = UserIdentity(
        external_identity_id="ext-user-003",
        username="jane.doe@businessexample.com",
        hashed_password=hash_password("Business123!"),
        status=UserStatus.ACTIVE.value,
        created_at=now,
        updated_at=now
    )
    db.add(business_user)
    db.flush()

    # 2. Registered Devices
    admin_device = RegisteredDevice(
        user_identity_id=admin_user.id,
        device_id="device-admin-mobile-001",
        device_label="Admin iPhone",
        public_key_ref="pubkey-admin-001",
        biometric_enabled=True,
        passcode_enabled=True,
        created_at=now,
        updated_at=now
    )
    db.add(admin_device)

    personal_device = RegisteredDevice(
        user_identity_id=personal_user.id,
        device_id="device-personal-mobile-001",
        device_label="John's iPhone",
        public_key_ref="pubkey-personal-001",
        biometric_enabled=True,
        passcode_enabled=True,
        created_at=now,
        updated_at=now
    )
    db.add(personal_device)

    # 3. User Profiles
    admin_profile = UserProfile(
        user_identity_id=admin_user.id,
        profile_type=ProfileType.PERSONAL.value,
        display_name="Admin User",
        business_name=None,
        external_profile_id="profile-admin-personal-001",
        is_default=True,
        created_at=now,
        updated_at=now
    )
    db.add(admin_profile)
    db.flush()

    personal_profile = UserProfile(
        user_identity_id=personal_user.id,
        profile_type=ProfileType.PERSONAL.value,
        display_name="John Smith",
        business_name=None,
        external_profile_id="profile-personal-001",
        is_default=True,
        created_at=now,
        updated_at=now
    )
    db.add(personal_profile)
    db.flush()

    business_profile = UserProfile(
        user_identity_id=business_user.id,
        profile_type=ProfileType.BUSINESS.value,
        display_name="Jane Doe",
        business_name="Acme Corporation Ltd",
        external_profile_id="profile-business-001",
        is_default=True,
        created_at=now,
        updated_at=now
    )
    db.add(business_profile)
    db.flush()

    # 4. Account Snapshots
    admin_current = AccountSnapshot(
        profile_id=admin_profile.id,
        external_account_id="acc-admin-current-001",
        account_type=AccountType.CURRENT_ACCOUNT.value,
        account_name="Admin Current Account",
        masked_account_number="****1234",
        sort_code="12-34-56",
        currency="GBP",
        current_balance_minor=124836,  # £1,248.36
        available_balance_minor=124836,
        overdraft_available_minor=0,
        available_credit_minor=None,
        freshness_state=FreshnessState.CURRENT.value,
        last_updated_at=now,
        created_at=now,
        updated_at=now
    )
    db.add(admin_current)
    db.flush()

    personal_current = AccountSnapshot(
        profile_id=personal_profile.id,
        external_account_id="acc-personal-current-001",
        account_type=AccountType.CURRENT_ACCOUNT.value,
        account_name="Personal Current Account",
        masked_account_number="****5678",
        sort_code="20-00-00",
        currency="GBP",
        current_balance_minor=124836,  # £1,248.36
        available_balance_minor=124836,
        overdraft_available_minor=100000,  # £1,000.00
        available_credit_minor=None,
        freshness_state=FreshnessState.CURRENT.value,
        last_updated_at=now,
        created_at=now,
        updated_at=now
    )
    db.add(personal_current)
    db.flush()

    personal_credit = AccountSnapshot(
        profile_id=personal_profile.id,
        external_account_id="acc-personal-credit-001",
        account_type=AccountType.CREDIT_CARD.value,
        account_name="Personal Credit Card",
        masked_account_number="****9012",
        sort_code=None,
        currency="GBP",
        current_balance_minor=-18240,  # -£182.40 (negative = owed)
        available_balance_minor=None,
        overdraft_available_minor=None,
        available_credit_minor=231760,  # £2,317.60 available credit
        freshness_state=FreshnessState.CURRENT.value,
        last_updated_at=now,
        created_at=now,
        updated_at=now
    )
    db.add(personal_credit)
    db.flush()

    personal_loan = AccountSnapshot(
        profile_id=personal_profile.id,
        external_account_id="acc-personal-loan-001",
        account_type=AccountType.LOAN.value,
        account_name="Personal Loan",
        masked_account_number="****3456",
        sort_code=None,
        currency="GBP",
        current_balance_minor=-486000,  # -£4,860.00 (negative = owed)
        available_balance_minor=None,
        overdraft_available_minor=None,
        available_credit_minor=None,
        freshness_state=FreshnessState.CURRENT.value,
        last_updated_at=now,
        created_at=now,
        updated_at=now
    )
    db.add(personal_loan)
    db.flush()

    business_current = AccountSnapshot(
        profile_id=business_profile.id,
        external_account_id="acc-business-current-001",
        account_type=AccountType.BUSINESS_ACCOUNT.value,
        account_name="Acme Corp Business Account",
        masked_account_number="****7890",
        sort_code="30-00-00",
        currency="GBP",
        current_balance_minor=642018,  # £6,420.18
        available_balance_minor=642018,
        overdraft_available_minor=500000,  # £5,000.00
        available_credit_minor=None,
        freshness_state=FreshnessState.CURRENT.value,
        last_updated_at=now,
        created_at=now,
        updated_at=now
    )
    db.add(business_current)
    db.flush()

    # 5. Loan Context Snapshot
    loan_context = LoanContextSnapshot(
        profile_id=personal_profile.id,
        account_snapshot_id=personal_loan.id,
        next_repayment_amount_minor=21250,  # £212.50
        next_repayment_due_date=(datetime(2026, 11, 28, tzinfo=timezone.utc)).date(),
        source_state=FreshnessState.CURRENT.value,
        created_at=now,
        updated_at=now
    )
    db.add(loan_context)

    # 6. Profile Entitlements
    entitlements = [
        ProfileEntitlement(
            profile_id=admin_profile.id,
            account_external_id="acc-admin-current-001",
            can_view_accounts=True,
            can_create_payee=True,
            can_approve_payment=True,
            entitlement_source_version="v1.0",
            created_at=now,
            updated_at=now
        ),
        ProfileEntitlement(
            profile_id=personal_profile.id,
            account_external_id="acc-personal-current-001",
            can_view_accounts=True,
            can_create_payee=True,
            can_approve_payment=True,
            entitlement_source_version="v1.0",
            created_at=now,
            updated_at=now
        ),
        ProfileEntitlement(
            profile_id=personal_profile.id,
            account_external_id="acc-personal-credit-001",
            can_view_accounts=True,
            can_create_payee=False,
            can_approve_payment=False,
            entitlement_source_version="v1.0",
            created_at=now,
            updated_at=now
        ),
        ProfileEntitlement(
            profile_id=personal_profile.id,
            account_external_id="acc-personal-loan-001",
            can_view_accounts=True,
            can_create_payee=False,
            can_approve_payment=False,
            entitlement_source_version="v1.0",
            created_at=now,
            updated_at=now
        ),
        ProfileEntitlement(
            profile_id=business_profile.id,
            account_external_id="acc-business-current-001",
            can_view_accounts=True,
            can_create_payee=True,
            can_approve_payment=True,
            entitlement_source_version="v1.0",
            created_at=now,
            updated_at=now
        ),
    ]
    for ent in entitlements:
        db.add(ent)

    # 7. Payees
    def hash_account(sort_code: str, account_number: str) -> str:
        data = f"{sort_code}{account_number}"
        return hashlib.sha256(data.encode()).hexdigest()

    # Admin profile payee
    payee_admin = Payee(
        profile_id=admin_profile.id,
        display_name="Test Supplier Ltd",
        nickname=None,
        sort_code="60-00-01",
        account_number_last4="1111",
        account_number_hash=hash_account("60-00-01", "12341111"),
        can_proceed=True,
        created_in_journey=False,
        payee_action_sca_verified_at=now - timedelta(days=45),
        created_at=now - timedelta(days=45),
        updated_at=now - timedelta(days=45)
    )
    db.add(payee_admin)
    db.flush()

    cop_admin = CoPResult(
        payee_id=payee_admin.id,
        result_code=CoPResultCode.MATCH.value,
        decision_state=CoPDecisionState.CONFIRMED.value,
        provider_reference="cop-ref-admin",
        returned_name="Test Supplier Ltd",
        warning_message=None,
        checked_at=now - timedelta(days=45),
        override_confirmed_at=None,
        created_at=now - timedelta(days=45),
        updated_at=now - timedelta(days=45)
    )
    db.add(cop_admin)

    payee1 = Payee(
        profile_id=admin_profile.id,
        display_name="Jamie Clarke",
        nickname=None,
        sort_code="04-00-04",
        account_number_last4="3746",
        account_number_hash=hash_account("04-00-04", "19283746"),
        can_proceed=True,
        created_in_journey=False,
        payee_action_sca_verified_at=now - timedelta(days=30),
        created_at=now - timedelta(days=30),
        updated_at=now - timedelta(days=30)
    )
    db.add(payee1)
    db.flush()

    cop1 = CoPResult(
        payee_id=payee1.id,
        result_code=CoPResultCode.MATCH.value,
        decision_state=CoPDecisionState.CONFIRMED.value,
        provider_reference="cop-ref-001",
        returned_name="Jamie Clarke",
        warning_message=None,
        checked_at=now - timedelta(days=30),
        override_confirmed_at=None,
        created_at=now - timedelta(days=30),
        updated_at=now - timedelta(days=30)
    )
    db.add(cop1)

    payee2 = Payee(
        profile_id=admin_profile.id,
        display_name="Priya Patel",
        nickname=None,
        sort_code="08-92-99",
        account_number_last4="2178",
        account_number_hash=hash_account("08-92-99", "65432178"),
        can_proceed=True,
        created_in_journey=False,
        payee_action_sca_verified_at=now - timedelta(days=60),
        created_at=now - timedelta(days=60),
        updated_at=now - timedelta(days=60)
    )
    db.add(payee2)
    db.flush()

    cop2 = CoPResult(
        payee_id=payee2.id,
        result_code=CoPResultCode.MATCH.value,
        decision_state=CoPDecisionState.CONFIRMED.value,
        provider_reference="cop-ref-002",
        returned_name="Priya Patel",
        warning_message=None,
        checked_at=now - timedelta(days=60),
        override_confirmed_at=None,
        created_at=now - timedelta(days=60),
        updated_at=now - timedelta(days=60)
    )
    db.add(cop2)

    payee3 = Payee(
        profile_id=admin_profile.id,
        display_name="K Evans Lettings",
        nickname=None,
        sort_code="20-45-77",
        account_number_last4="9842",
        account_number_hash=hash_account("20-45-77", "30019842"),
        can_proceed=True,
        created_in_journey=True,
        payee_action_sca_verified_at=now - timedelta(days=15),
        created_at=now - timedelta(days=15),
        updated_at=now - timedelta(days=15)
    )
    db.add(payee3)
    db.flush()

    cop3 = CoPResult(
        payee_id=payee3.id,
        result_code=CoPResultCode.MATCH.value,
        decision_state=CoPDecisionState.CONFIRMED.value,
        provider_reference="cop-ref-003",
        returned_name="K Evans Lettings",
        warning_message=None,
        checked_at=now - timedelta(days=15),
        override_confirmed_at=None,
        created_at=now - timedelta(days=15),
        updated_at=now - timedelta(days=15)
    )
    db.add(cop3)

    # 8. Auth Session for sample payment history
    sample_session = AuthSession(
        user_identity_id=personal_user.id,
        token_hash=hashlib.sha256(b"sample-token-001").hexdigest(),
        session_state=SessionState.EXPIRED.value,
        issued_at=now - timedelta(days=5),
        expires_at=now - timedelta(days=4),
        last_activity_at=now - timedelta(days=4),
        active_profile_id=personal_profile.id,
        created_at=now - timedelta(days=5),
        updated_at=now - timedelta(days=4)
    )
    db.add(sample_session)
    db.flush()

    # 9. Sample Payment History - SENT (£250.00 to K Evans Lettings reference "Invoice 2041", payment_reference PAY-20261119-000417)
    payment_sent = PaymentInstruction(
        profile_id=personal_profile.id,
        auth_session_id=sample_session.id,
        source_account_snapshot_id=personal_current.id,
        payee_id=payee3.id,  # K Evans Lettings
        amount_minor=25000,  # £250.00
        currency="GBP",
        reference_text="Invoice 2041",
        client_idempotency_key="idempotency-sent-001",
        payment_reference="PAY-20261119-000417",
        instruction_state=InstructionState.SENT.value,
        duplicate_submission_blocked=False,
        expected_arrival_message="Funds will arrive by end of business today.",
        failure_reason=None,
        created_at=now - timedelta(days=3),
        updated_at=now - timedelta(days=3)
    )
    db.add(payment_sent)
    db.flush()

    fraud_sent = FraudDecision(
        payment_instruction_id=payment_sent.id,
        decision_code=FraudDecisionCode.ALLOW.value,
        warning_message=None,
        hold_reason=None,
        provider_reference="fraud-ref-sent-001",
        decided_at=now - timedelta(days=3),
        created_at=now - timedelta(days=3),
        updated_at=now - timedelta(days=3)
    )
    db.add(fraud_sent)

    approval_sent = PaymentApproval(
        payment_instruction_id=payment_sent.id,
        challenge_id=None,
        sca_method=ChallengeMethod.DYNAMIC_LINK.value,
        dynamic_link_hash=hashlib.sha256(f"{payee3.id}:25000:GBP:{personal_profile.id}".encode()).hexdigest(),
        approved_at=now - timedelta(days=3),
        created_at=now - timedelta(days=3),
        updated_at=now - timedelta(days=3)
    )
    db.add(approval_sent)

    status_sent = PaymentStatusHistory(
        payment_instruction_id=payment_sent.id,
        status_code=PaymentStatusCode.SENT.value,
        rail_reference="RAIL-SENT-001",
        reason_code=None,
        reason_detail=None,
        effective_at=now - timedelta(days=3),
        created_at=now - timedelta(days=3),
        updated_at=now - timedelta(days=3)
    )
    db.add(status_sent)

    # 10. Sample Payment History - PENDING (£100.00 to Jamie Clarke)
    payment_pending = PaymentInstruction(
        profile_id=personal_profile.id,
        auth_session_id=sample_session.id,
        source_account_snapshot_id=personal_current.id,
        payee_id=payee1.id,  # Jamie Clarke
        amount_minor=10000,  # £100.00
        currency="GBP",
        reference_text=None,
        client_idempotency_key="idempotency-pending-001",
        payment_reference="PAY-PENDING-001",
        instruction_state=InstructionState.PENDING.value,
        duplicate_submission_blocked=True,
        expected_arrival_message=None,
        failure_reason=None,
        created_at=now - timedelta(days=1),
        updated_at=now - timedelta(days=1)
    )
    db.add(payment_pending)
    db.flush()

    fraud_pending = FraudDecision(
        payment_instruction_id=payment_pending.id,
        decision_code=FraudDecisionCode.ALLOW.value,
        warning_message=None,
        hold_reason=None,
        provider_reference="fraud-ref-pending-001",
        decided_at=now - timedelta(days=1),
        created_at=now - timedelta(days=1),
        updated_at=now - timedelta(days=1)
    )
    db.add(fraud_pending)

    approval_pending = PaymentApproval(
        payment_instruction_id=payment_pending.id,
        challenge_id=None,
        sca_method=ChallengeMethod.DYNAMIC_LINK.value,
        dynamic_link_hash=hashlib.sha256(f"{payee1.id}:10000:GBP:{personal_profile.id}".encode()).hexdigest(),
        approved_at=now - timedelta(days=1),
        created_at=now - timedelta(days=1),
        updated_at=now - timedelta(days=1)
    )
    db.add(approval_pending)

    status_pending = PaymentStatusHistory(
        payment_instruction_id=payment_pending.id,
        status_code=PaymentStatusCode.PENDING.value,
        rail_reference="RAIL-PENDING-001",
        reason_code="RAIL_DELAY",
        reason_detail="Payment rail confirmation delayed",
        effective_at=now - timedelta(days=1),
        created_at=now - timedelta(days=1),
        updated_at=now - timedelta(days=1)
    )
    db.add(status_pending)

    # 11. Sample Payment History - FAILED (£500.00 to Priya Patel with failure_reason)
    payment_failed = PaymentInstruction(
        profile_id=personal_profile.id,
        auth_session_id=sample_session.id,
        source_account_snapshot_id=personal_current.id,
        payee_id=payee2.id,  # Priya Patel
        amount_minor=50000,  # £500.00
        currency="GBP",
        reference_text=None,
        client_idempotency_key="idempotency-failed-001",
        payment_reference="PAY-FAILED-001",
        instruction_state=InstructionState.FAILED.value,
        duplicate_submission_blocked=False,
        expected_arrival_message=None,
        failure_reason="Payment could not be completed due to insufficient funds.",
        created_at=now - timedelta(hours=12),
        updated_at=now - timedelta(hours=12)
    )
    db.add(payment_failed)
    db.flush()

    fraud_failed = FraudDecision(
        payment_instruction_id=payment_failed.id,
        decision_code=FraudDecisionCode.ALLOW.value,
        warning_message=None,
        hold_reason=None,
        provider_reference="fraud-ref-failed-001",
        decided_at=now - timedelta(hours=12),
        created_at=now - timedelta(hours=12),
        updated_at=now - timedelta(hours=12)
    )
    db.add(fraud_failed)

    approval_failed = PaymentApproval(
        payment_instruction_id=payment_failed.id,
        challenge_id=None,
        sca_method=ChallengeMethod.DYNAMIC_LINK.value,
        dynamic_link_hash=hashlib.sha256(f"{payee2.id}:50000:GBP:{personal_profile.id}".encode()).hexdigest(),
        approved_at=now - timedelta(hours=12),
        created_at=now - timedelta(hours=12),
        updated_at=now - timedelta(hours=12)
    )
    db.add(approval_failed)

    status_failed = PaymentStatusHistory(
        payment_instruction_id=payment_failed.id,
        status_code=PaymentStatusCode.FAILED.value,
        rail_reference="RAIL-FAILED-001",
        reason_code="INSUFFICIENT_FUNDS",
        reason_detail="Insufficient funds after final balance check",
        effective_at=now - timedelta(hours=12),
        created_at=now - timedelta(hours=12),
        updated_at=now - timedelta(hours=12)
    )
    db.add(status_failed)

    db.commit()
    print("Database seeded successfully!")
    print("\nDefault credentials:")
    print("  Admin: admin@example.com / admin123")
    print("  Personal: john.smith@example.com / Personal123!")
    print("  Business: jane.doe@businessexample.com / Business123!")


def run_seed():
    """Run seed independently."""
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
