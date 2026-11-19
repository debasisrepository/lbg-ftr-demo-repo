"""Tests for payment orchestration service."""
import pytest
from datetime import datetime, timezone
from app.services.payment_orchestration_service import PaymentOrchestrationService
from app.repositories.payment_repository import PaymentRepository
from app.repositories.account_repository import AccountRepository
from app.repositories.payee_repository import PayeeRepository
from app.repositories.profile_repository import ProfileRepository
from app.models.accounts import AccountSnapshot
from app.models.payees import Payee
from app.models.profiles import UserProfile, ProfileEntitlement
from app.models.auth import UserIdentity, AuthSession
from app.common.enums import (
    AccountType, ProfileType, UserStatus, SessionState,
    FreshnessState, InstructionState, ChallengeMethod
)
from app.common.security import hash_password
from app.common.errors import ValidationError, AuthorizationError
import hashlib


def test_prepare_payment_exceeds_balance(db_session):
    """Test that payment preparation fails when amount exceeds available balance."""
    # Create user
    now = datetime.now(timezone.utc)
    user = UserIdentity(
        external_identity_id="test-user",
        username="test@example.com",
        hashed_password=hash_password("Test123!"),
        status=UserStatus.ACTIVE.value,
        created_at=now,
        updated_at=now
    )
    db_session.add(user)
    db_session.flush()

    # Create profile
    profile = UserProfile(
        user_identity_id=user.id,
        profile_type=ProfileType.PERSONAL.value,
        display_name="Test User",
        business_name=None,
        external_profile_id="profile-test",
        is_default=True,
        created_at=now,
        updated_at=now
    )
    db_session.add(profile)
    db_session.flush()

    # Create entitlement
    entitlement = ProfileEntitlement(
        profile_id=profile.id,
        account_external_id="acc-test",
        can_view_accounts=True,
        can_create_payee=True,
        can_approve_payment=True,
        entitlement_source_version="v1.0",
        created_at=now,
        updated_at=now
    )
    db_session.add(entitlement)

    # Create account with limited balance
    account = AccountSnapshot(
        profile_id=profile.id,
        external_account_id="acc-test",
        account_type=AccountType.CURRENT_ACCOUNT.value,
        account_name="Test Account",
        masked_account_number="****1234",
        sort_code="12-34-56",
        currency="GBP",
        current_balance_minor=50000,  # £500
        available_balance_minor=50000,
        overdraft_available_minor=0,
        available_credit_minor=None,
        freshness_state=FreshnessState.CURRENT.value,
        last_updated_at=now,
        created_at=now,
        updated_at=now
    )
    db_session.add(account)
    db_session.flush()

    # Create payee
    payee = Payee(
        profile_id=profile.id,
        display_name="Test Payee",
        nickname=None,
        sort_code="20-00-00",
        account_number_last4="5678",
        account_number_hash=hashlib.sha256(b"20-00-00-12345678").hexdigest(),
        can_proceed=True,
        created_in_journey=False,
        payee_action_sca_verified_at=now,
        created_at=now,
        updated_at=now
    )
    db_session.add(payee)
    db_session.flush()

    # Create session
    session = AuthSession(
        user_identity_id=user.id,
        token_hash="test-hash",
        session_state=SessionState.ACTIVE.value,
        issued_at=now,
        expires_at=now,
        last_activity_at=now,
        active_profile_id=profile.id,
        created_at=now,
        updated_at=now
    )
    db_session.add(session)
    db_session.flush()

    # Attempt to prepare payment exceeding balance
    service = PaymentOrchestrationService(db_session, "test-correlation")
    
    with pytest.raises(ValidationError, match="Payment validation failed"):
        service.prepare_payment(
            profile_id=profile.id,
            source_account_id=account.id,
            payee_id=payee.id,
            amount_minor=100000,  # £1000 - exceeds £500 balance
            currency="GBP",
            reference="Test payment",
            client_idempotency_key="test-key-1",
            auth_session_id=session.id,
            user_identity_id=user.id
        )


def test_prepare_payment_exceeds_limit(db_session):
    """Test that payment preparation fails when amount exceeds limit."""
    # Create user
    now = datetime.now(timezone.utc)
    user = UserIdentity(
        external_identity_id="test-user",
        username="test@example.com",
        hashed_password=hash_password("Test123!"),
        status=UserStatus.ACTIVE.value,
        created_at=now,
        updated_at=now
    )
    db_session.add(user)
    db_session.flush()

    # Create profile
    profile = UserProfile(
        user_identity_id=user.id,
        profile_type=ProfileType.PERSONAL.value,
        display_name="Test User",
        business_name=None,
        external_profile_id="profile-test",
        is_default=True,
        created_at=now,
        updated_at=now
    )
    db_session.add(profile)
    db_session.flush()

    # Create entitlement
    entitlement = ProfileEntitlement(
        profile_id=profile.id,
        account_external_id="acc-test",
        can_view_accounts=True,
        can_create_payee=True,
        can_approve_payment=True,
        entitlement_source_version="v1.0",
        created_at=now,
        updated_at=now
    )
    db_session.add(entitlement)

    # Create account with high balance
    account = AccountSnapshot(
        profile_id=profile.id,
        external_account_id="acc-test",
        account_type=AccountType.CURRENT_ACCOUNT.value,
        account_name="Test Account",
        masked_account_number="****1234",
        sort_code="12-34-56",
        currency="GBP",
        current_balance_minor=2000000,  # £20,000
        available_balance_minor=2000000,
        overdraft_available_minor=0,
        available_credit_minor=None,
        freshness_state=FreshnessState.CURRENT.value,
        last_updated_at=now,
        created_at=now,
        updated_at=now
    )
    db_session.add(account)
    db_session.flush()

    # Create payee
    payee = Payee(
        profile_id=profile.id,
        display_name="Test Payee",
        nickname=None,
        sort_code="20-00-00",
        account_number_last4="5678",
        account_number_hash=hashlib.sha256(b"20-00-00-12345678").hexdigest(),
        can_proceed=True,
        created_in_journey=False,
        payee_action_sca_verified_at=now,
        created_at=now,
        updated_at=now
    )
    db_session.add(payee)
    db_session.flush()

    # Create session
    session = AuthSession(
        user_identity_id=user.id,
        token_hash="test-hash",
        session_state=SessionState.ACTIVE.value,
        issued_at=now,
        expires_at=now,
        last_activity_at=now,
        active_profile_id=profile.id,
        created_at=now,
        updated_at=now
    )
    db_session.add(session)
    db_session.flush()

    # Attempt to prepare payment exceeding limit (£10,000)
    service = PaymentOrchestrationService(db_session, "test-correlation")
    
    with pytest.raises(ValidationError, match="Payment validation failed"):
        service.prepare_payment(
            profile_id=profile.id,
            source_account_id=account.id,
            payee_id=payee.id,
            amount_minor=1100000,  # £11,000 - exceeds £10,000 limit
            currency="GBP",
            reference="Test payment",
            client_idempotency_key="test-key-2",
            auth_session_id=session.id,
            user_identity_id=user.id
        )


def test_prepare_payment_no_approval_entitlement(db_session):
    """Test that payment preparation fails when user lacks approval entitlement."""
    # Create user
    now = datetime.now(timezone.utc)
    user = UserIdentity(
        external_identity_id="test-user",
        username="test@example.com",
        hashed_password=hash_password("Test123!"),
        status=UserStatus.ACTIVE.value,
        created_at=now,
        updated_at=now
    )
    db_session.add(user)
    db_session.flush()

    # Create business profile
    profile = UserProfile(
        user_identity_id=user.id,
        profile_type=ProfileType.BUSINESS.value,
        display_name="Test User",
        business_name="Test Business",
        external_profile_id="profile-test",
        is_default=True,
        created_at=now,
        updated_at=now
    )
    db_session.add(profile)
    db_session.flush()

    # Create entitlement WITHOUT approval permission
    entitlement = ProfileEntitlement(
        profile_id=profile.id,
        account_external_id="acc-test",
        can_view_accounts=True,
        can_create_payee=True,
        can_approve_payment=False,  # No approval permission
        entitlement_source_version="v1.0",
        created_at=now,
        updated_at=now
    )
    db_session.add(entitlement)

    # Create account
    account = AccountSnapshot(
        profile_id=profile.id,
        external_account_id="acc-test",
        account_type=AccountType.BUSINESS_ACCOUNT.value,
        account_name="Test Account",
        masked_account_number="****1234",
        sort_code="12-34-56",
        currency="GBP",
        current_balance_minor=100000,  # £1,000
        available_balance_minor=100000,
        overdraft_available_minor=0,
        available_credit_minor=None,
        freshness_state=FreshnessState.CURRENT.value,
        last_updated_at=now,
        created_at=now,
        updated_at=now
    )
    db_session.add(account)
    db_session.flush()

    # Create payee
    payee = Payee(
        profile_id=profile.id,
        display_name="Test Payee",
        nickname=None,
        sort_code="20-00-00",
        account_number_last4="5678",
        account_number_hash=hashlib.sha256(b"20-00-00-12345678").hexdigest(),
        can_proceed=True,
        created_in_journey=False,
        payee_action_sca_verified_at=now,
        created_at=now,
        updated_at=now
    )
    db_session.add(payee)
    db_session.flush()

    # Create session
    session = AuthSession(
        user_identity_id=user.id,
        token_hash="test-hash",
        session_state=SessionState.ACTIVE.value,
        issued_at=now,
        expires_at=now,
        last_activity_at=now,
        active_profile_id=profile.id,
        created_at=now,
        updated_at=now
    )
    db_session.add(session)
    db_session.flush()

    # Attempt to prepare payment without approval entitlement
    service = PaymentOrchestrationService(db_session, "test-correlation")
    
    with pytest.raises(AuthorizationError, match="You do not have permission to approve payments"):
        service.prepare_payment(
            profile_id=profile.id,
            source_account_id=account.id,
            payee_id=payee.id,
            amount_minor=50000,  # £500
            currency="GBP",
            reference="Test payment",
            client_idempotency_key="test-key-3",
            auth_session_id=session.id,
            user_identity_id=user.id
        )


def test_prepare_payment_success_with_approval_challenge(db_session):
    """Test successful payment preparation with approval challenge."""
    # Create user
    now = datetime.now(timezone.utc)
    user = UserIdentity(
        external_identity_id="test-user",
        username="test@example.com",
        hashed_password=hash_password("Test123!"),
        status=UserStatus.ACTIVE.value,
        created_at=now,
        updated_at=now
    )
    db_session.add(user)
    db_session.flush()

    # Create profile
    profile = UserProfile(
        user_identity_id=user.id,
        profile_type=ProfileType.PERSONAL.value,
        display_name="Test User",
        business_name=None,
        external_profile_id="profile-test",
        is_default=True,
        created_at=now,
        updated_at=now
    )
    db_session.add(profile)
    db_session.flush()

    # Create entitlement
    entitlement = ProfileEntitlement(
        profile_id=profile.id,
        account_external_id="acc-test",
        can_view_accounts=True,
        can_create_payee=True,
        can_approve_payment=True,
        entitlement_source_version="v1.0",
        created_at=now,
        updated_at=now
    )
    db_session.add(entitlement)

    # Create account
    account = AccountSnapshot(
        profile_id=profile.id,
        external_account_id="acc-test",
        account_type=AccountType.CURRENT_ACCOUNT.value,
        account_name="Test Account",
        masked_account_number="****1234",
        sort_code="12-34-56",
        currency="GBP",
        current_balance_minor=100000,  # £1,000
        available_balance_minor=100000,
        overdraft_available_minor=0,
        available_credit_minor=None,
        freshness_state=FreshnessState.CURRENT.value,
        last_updated_at=now,
        created_at=now,
        updated_at=now
    )
    db_session.add(account)
    db_session.flush()

    # Create payee
    payee = Payee(
        profile_id=profile.id,
        display_name="Test Payee",
        nickname=None,
        sort_code="20-00-00",
        account_number_last4="5678",
        account_number_hash=hashlib.sha256(b"20-00-00-12345678").hexdigest(),
        can_proceed=True,
        created_in_journey=False,
        payee_action_sca_verified_at=now,
        created_at=now,
        updated_at=now
    )
    db_session.add(payee)
    db_session.flush()

    # Create session
    session = AuthSession(
        user_identity_id=user.id,
        token_hash="test-hash",
        session_state=SessionState.ACTIVE.value,
        issued_at=now,
        expires_at=now,
        last_activity_at=now,
        active_profile_id=profile.id,
        created_at=now,
        updated_at=now
    )
    db_session.add(session)
    db_session.flush()

    # Prepare payment
    service = PaymentOrchestrationService(db_session, "test-correlation")
    
    result = service.prepare_payment(
        profile_id=profile.id,
        source_account_id=account.id,
        payee_id=payee.id,
        amount_minor=50000,  # £500
        currency="GBP",
        reference="Test payment",
        client_idempotency_key="test-key-4",
        auth_session_id=session.id,
        user_identity_id=user.id
    )

    # Verify result structure
    assert result["payment_id"] is not None
    assert result["payment_state"] == InstructionState.PREPARED.value
    assert result["amount_minor"] == 50000
    assert result["balance_check"]["passed"] is True
    assert result["limit_check"]["passed"] is True
    assert result["fraud_decision"]["decision"] in ["allow", "warn", "step_up", "hold"]
    assert result["approval_required"] is True
    
    # Verify approval challenge only if not held
    if result["fraud_decision"]["decision"] != "hold":
        assert result["approval_challenge"] is not None
        assert result["approval_challenge"]["challenge_id"] is not None
        assert result["approval_challenge"]["dynamic_link_summary"]["payee_name"] == "Test Payee"
        assert result["approval_challenge"]["dynamic_link_summary"]["amount_minor"] == 50000
