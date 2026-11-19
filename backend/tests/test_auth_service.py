"""Unit tests for auth service"""
import uuid

import pytest

from app.core.errors import AuthenticationError
from app.schemas.auth_schemas import ProofRequest, SignInRequest
from app.services.auth_service import AuthService
from app.services.login_rate_limiter import get_rate_limiter


def test_sign_in_success(db_session, demo_customer):
    """Test successful password authentication"""
    customer, profile, device = demo_customer

    # Reset rate limiter
    get_rate_limiter().reset()

    service = AuthService(db_session)
    request = SignInRequest(
        username="sasha.patel@gmail.com",
        password="Demo1234!",
        device_id=str(device.device_id)
    )

    response = service.sign_in(request, "127.0.0.1", "test-correlation-id")

    assert response.auth_level == "password_only"
    assert response.requires_proof is True
    assert "passcode" in response.proof_methods or "biometric" in response.proof_methods
    assert response.customer_id == str(customer.customer_id)


def test_sign_in_invalid_credentials(db_session, demo_customer):
    """Test sign in with invalid credentials returns generic error"""
    get_rate_limiter().reset()

    service = AuthService(db_session)
    request = SignInRequest(
        username="sasha.patel@gmail.com",
        password="WrongPassword",
        device_id=None
    )

    with pytest.raises(AuthenticationError) as exc_info:
        service.sign_in(request, "127.0.0.1", "test-correlation-id")

    # Generic error message per FR-001
    assert "Invalid credentials" in str(exc_info.value.message)


def test_sign_in_unknown_user(db_session):
    """Test sign in with unknown username returns generic error"""
    get_rate_limiter().reset()

    service = AuthService(db_session)
    request = SignInRequest(
        username="unknown@example.com",
        password="SomePassword",
        device_id=None
    )

    with pytest.raises(AuthenticationError) as exc_info:
        service.sign_in(request, "127.0.0.1", "test-correlation-id")

    assert "Invalid credentials" in str(exc_info.value.message)


def test_submit_proof_passcode_success(db_session, demo_customer):
    """Test successful passcode proof submission"""
    customer, profile, device = demo_customer
    get_rate_limiter().reset()

    # First sign in
    auth_service = AuthService(db_session)
    sign_in_req = SignInRequest(
        username="sasha.patel@gmail.com",
        password="Demo1234!",
        device_id=str(device.device_id)
    )
    sign_in_resp = auth_service.sign_in(sign_in_req, "127.0.0.1", "test-correlation-id")

    # Submit proof
    proof_req = ProofRequest(
        session_id=sign_in_resp.session_id,
        proof_type="passcode",
        proof_value="123456",
        device_id=str(device.device_id)
    )
    proof_resp = auth_service.submit_proof(proof_req, "test-correlation-id")

    assert proof_resp.auth_level == "proven"
    assert proof_resp.access_token is not None
    assert proof_resp.token_type == "Bearer"


def test_submit_proof_invalid_passcode(db_session, demo_customer):
    """Test passcode proof with invalid passcode"""
    customer, profile, device = demo_customer
    get_rate_limiter().reset()

    # First sign in
    auth_service = AuthService(db_session)
    sign_in_req = SignInRequest(
        username="sasha.patel@gmail.com",
        password="Demo1234!",
        device_id=str(device.device_id)
    )
    sign_in_resp = auth_service.sign_in(sign_in_req, "127.0.0.1", "test-correlation-id")

    # Submit wrong passcode
    proof_req = ProofRequest(
        session_id=sign_in_resp.session_id,
        proof_type="passcode",
        proof_value="999999",  # Wrong passcode
        device_id=str(device.device_id)
    )

    with pytest.raises(AuthenticationError) as exc_info:
        auth_service.submit_proof(proof_req, "test-correlation-id")

    assert "Proof verification failed" in str(exc_info.value.message)


def test_submit_proof_passcode_lockout(db_session, demo_customer):
    """Test passcode lockout after 3 failed attempts"""
    customer, profile, device = demo_customer
    get_rate_limiter().reset()

    auth_service = AuthService(db_session)

    # Sign in
    sign_in_req = SignInRequest(
        username="sasha.patel@gmail.com",
        password="Demo1234!",
        device_id=str(device.device_id)
    )
    sign_in_resp = auth_service.sign_in(sign_in_req, "127.0.0.1", "test-correlation-id")

    # Fail 3 times
    for i in range(3):
        # Need fresh session each time since proof can only be submitted once per session
        sign_in_resp = auth_service.sign_in(sign_in_req, "127.0.0.1", f"test-correlation-id-{i}")

        proof_req = ProofRequest(
            session_id=sign_in_resp.session_id,
            proof_type="passcode",
            proof_value="999999",
            device_id=str(device.device_id)
        )

        try:
            auth_service.submit_proof(proof_req, f"test-correlation-id-{i}")
        except AuthenticationError:
            pass  # Expected

    # Verify device is locked
    from app.repositories.device_repository import DeviceRepository
    device_repo = DeviceRepository(db_session)
    locked_device = device_repo.get_by_id(device.device_id)
    assert locked_device.passcode_failed_count == 3
    assert locked_device.passcode_paused_until is not None


def test_submit_proof_biometric_success(db_session, demo_customer):
    """Test successful biometric proof submission"""
    customer, profile, device = demo_customer
    get_rate_limiter().reset()

    # Sign in
    auth_service = AuthService(db_session)
    sign_in_req = SignInRequest(
        username="sasha.patel@gmail.com",
        password="Demo1234!",
        device_id=str(device.device_id)
    )
    sign_in_resp = auth_service.sign_in(sign_in_req, "127.0.0.1", "test-correlation-id")

    # Submit biometric proof
    proof_req = ProofRequest(
        session_id=sign_in_resp.session_id,
        proof_type="biometric",
        proof_value="valid-biometric-attestation-data-12345",  # Stub accepts long strings
        device_id=str(device.device_id)
    )
    proof_resp = auth_service.submit_proof(proof_req, "test-correlation-id")

    assert proof_resp.auth_level == "proven"
    assert proof_resp.access_token is not None


def test_submit_proof_invalid_session(db_session, demo_customer):
    """Test proof submission with invalid session ID"""
    get_rate_limiter().reset()

    auth_service = AuthService(db_session)
    proof_req = ProofRequest(
        session_id=str(uuid.uuid4()),  # Non-existent session
        proof_type="passcode",
        proof_value="123456",
        device_id=str(uuid.uuid4())
    )

    with pytest.raises(AuthenticationError) as exc_info:
        auth_service.submit_proof(proof_req, "test-correlation-id")

    assert "Invalid session" in str(exc_info.value.message)
