"""Integration tests for auth endpoints"""
import uuid

from app.services.login_rate_limiter import get_rate_limiter


def test_sign_in_endpoint(client, demo_customer):
    """Test POST /api/v1/auth/sign-in endpoint"""
    get_rate_limiter().reset()

    customer, profile, device = demo_customer

    response = client.post("/api/v1/auth/sign-in", json={
        "username": "sasha.patel@gmail.com",
        "password": "Demo1234!",
        "device_id": str(device.device_id)
    })

    assert response.status_code == 200
    data = response.json()
    assert data["auth_level"] == "password_only"
    assert data["requires_proof"] is True
    assert "session_id" in data
    assert "customer_id" in data


def test_sign_in_invalid_credentials(client, demo_customer):
    """Test sign in with invalid credentials"""
    get_rate_limiter().reset()

    response = client.post("/api/v1/auth/sign-in", json={
        "username": "sasha.patel@gmail.com",
        "password": "WrongPassword",
        "device_id": None
    })

    assert response.status_code == 401
    data = response.json()
    assert "Invalid credentials" in data["detail"]


def test_sign_in_and_proof_flow(client, demo_customer):
    """Test complete sign-in and proof flow"""
    get_rate_limiter().reset()

    customer, profile, device = demo_customer

    # Step 1: Sign in with username/password
    sign_in_response = client.post("/api/v1/auth/sign-in", json={
        "username": "sasha.patel@gmail.com",
        "password": "Demo1234!",
        "device_id": str(device.device_id)
    })

    assert sign_in_response.status_code == 200
    sign_in_data = sign_in_response.json()
    session_id = sign_in_data["session_id"]

    # Step 2: Submit passcode proof
    proof_response = client.post("/api/v1/auth/proof", json={
        "session_id": session_id,
        "proof_type": "passcode",
        "proof_value": "123456",
        "device_id": str(device.device_id)
    })

    assert proof_response.status_code == 200
    proof_data = proof_response.json()
    assert proof_data["auth_level"] == "proven"
    assert "access_token" in proof_data
    assert proof_data["token_type"] == "Bearer"


def test_proof_with_invalid_session(client):
    """Test proof submission with invalid session"""
    get_rate_limiter().reset()

    response = client.post("/api/v1/auth/proof", json={
        "session_id": str(uuid.uuid4()),
        "proof_type": "passcode",
        "proof_value": "123456",
        "device_id": str(uuid.uuid4())
    })

    assert response.status_code == 401
    assert "Invalid session" in response.json()["detail"]


def test_proof_with_wrong_passcode(client, demo_customer):
    """Test proof with incorrect passcode"""
    get_rate_limiter().reset()

    customer, profile, device = demo_customer

    # Sign in first
    sign_in_response = client.post("/api/v1/auth/sign-in", json={
        "username": "sasha.patel@gmail.com",
        "password": "Demo1234!",
        "device_id": str(device.device_id)
    })

    session_id = sign_in_response.json()["session_id"]

    # Submit wrong passcode
    proof_response = client.post("/api/v1/auth/proof", json={
        "session_id": session_id,
        "proof_type": "passcode",
        "proof_value": "999999",
        "device_id": str(device.device_id)
    })

    assert proof_response.status_code == 401
    assert "Proof verification failed" in proof_response.json()["detail"]


def test_biometric_proof_flow(client, demo_customer):
    """Test biometric proof flow"""
    get_rate_limiter().reset()

    customer, profile, device = demo_customer

    # Sign in
    sign_in_response = client.post("/api/v1/auth/sign-in", json={
        "username": "sasha.patel@gmail.com",
        "password": "Demo1234!",
        "device_id": str(device.device_id)
    })

    session_id = sign_in_response.json()["session_id"]

    # Submit biometric proof
    proof_response = client.post("/api/v1/auth/proof", json={
        "session_id": session_id,
        "proof_type": "biometric",
        "proof_value": "valid-biometric-attestation-12345",
        "device_id": str(device.device_id)
    })

    assert proof_response.status_code == 200
    data = proof_response.json()
    assert data["auth_level"] == "proven"
    assert "access_token" in data


def test_session_extend(client, demo_customer):
    """Test session extend endpoint"""
    get_rate_limiter().reset()

    customer, profile, device = demo_customer

    # Complete auth flow
    sign_in_response = client.post("/api/v1/auth/sign-in", json={
        "username": "sasha.patel@gmail.com",
        "password": "Demo1234!",
        "device_id": str(device.device_id)
    })
    session_id = sign_in_response.json()["session_id"]

    # Extend session
    extend_response = client.post(
        "/api/v1/auth/session/extend",
        headers={"X-Session-ID": session_id}
    )

    assert extend_response.status_code == 200
    data = extend_response.json()
    assert data["session_id"] == session_id
    assert "expires_at" in data


def test_sign_out(client, demo_customer):
    """Test sign out endpoint"""
    get_rate_limiter().reset()

    customer, profile, device = demo_customer

    # Complete auth flow
    sign_in_response = client.post("/api/v1/auth/sign-in", json={
        "username": "sasha.patel@gmail.com",
        "password": "Demo1234!",
        "device_id": str(device.device_id)
    })
    session_id = sign_in_response.json()["session_id"]

    # Sign out
    signout_response = client.post(
        "/api/v1/auth/sign-out",
        headers={"X-Session-ID": session_id}
    )

    assert signout_response.status_code == 200
    data = signout_response.json()
    assert "Signed out" in data["message"]


def test_recovery_endpoint(client):
    """Test recovery endpoint (placeholder)"""
    response = client.post("/api/v1/auth/recovery", json={
        "username": "sasha.patel@gmail.com"
    })

    assert response.status_code == 200
    data = response.json()
    # Backend returns secure message that doesn't reveal whether account exists
    assert "recovery instructions have been sent" in data["message"].lower()
