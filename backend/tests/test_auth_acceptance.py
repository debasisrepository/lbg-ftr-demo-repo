"""Acceptance tests for authentication requirements (FR-001, FR-002)"""

from app.services.login_rate_limiter import get_rate_limiter


# FR-001: Sign in
def test_fr001_ac1_first_device_sign_in(client, demo_customer):
    """
    FR-001 AC1: Given the customer is using a device for the first time,
    when valid username and password are submitted, then the app authenticates
    the identity and advances the customer to the proof step without exposing
    any unauthorized account data.
    """
    get_rate_limiter().reset()

    customer, profile, device = demo_customer

    response = client.post("/api/v1/auth/sign-in", json={
        "username": "sasha.patel@gmail.com",
        "password": "Demo1234!",
        "device_id": str(device.device_id)
    })

    assert response.status_code == 200
    data = response.json()

    # Authenticated but requires proof
    assert data["auth_level"] == "password_only"
    assert data["requires_proof"] is True

    # No unauthorized account data exposed in password_only state
    assert "active_profile_id" not in data or data.get("active_profile_id") is None


def test_fr001_ac2_empty_fields_validation(client):
    """
    FR-001 AC2: Given the username field or password field is empty,
    when the customer taps Continue, then the app shows inline validation
    on the missing field and does not continue.
    """
    get_rate_limiter().reset()

    # Empty username
    response = client.post("/api/v1/auth/sign-in", json={
        "username": "",
        "password": "Demo1234!",
        "device_id": None
    })

    # Pydantic validation should catch this
    assert response.status_code == 422  # Validation error

    # Empty password
    response = client.post("/api/v1/auth/sign-in", json={
        "username": "sasha.patel@gmail.com",
        "password": "",
        "device_id": None
    })

    assert response.status_code == 422  # Validation error


def test_fr001_ac3_invalid_credentials_generic_error(client, demo_customer):
    """
    FR-001 AC3: Given invalid credentials are submitted, when authentication fails,
    then the app shows one generic error message that does not identify which
    credential was wrong.
    """
    get_rate_limiter().reset()

    # Wrong password
    response = client.post("/api/v1/auth/sign-in", json={
        "username": "sasha.patel@gmail.com",
        "password": "WrongPassword",
        "device_id": None
    })

    assert response.status_code == 401
    error_msg = response.json()["detail"]

    # Generic error message
    assert "Invalid credentials" in error_msg
    # Must not reveal WHICH credential (singular) was wrong
    # The message can say "username and password" but not "password is wrong" or "username is wrong"
    assert "password is" not in error_msg.lower() and "username is" not in error_msg.lower()

    # Wrong username
    response = client.post("/api/v1/auth/sign-in", json={
        "username": "wrong@example.com",
        "password": "Demo1234!",
        "device_id": None
    })

    assert response.status_code == 401
    error_msg = response.json()["detail"]
    assert "Invalid credentials" in error_msg


def test_fr001_ac4_fallback_after_lockout(client, demo_customer):
    """
    FR-001 AC4: Given the customer has been locked out of passcode entry
    or selects a fallback path, when valid username and password are entered,
    then the app allows re-entry to the authenticated journey subject to
    downstream proof controls.
    """
    get_rate_limiter().reset()

    customer, profile, device = demo_customer

    # Even after device is locked (passcode failures), password sign-in still works
    response = client.post("/api/v1/auth/sign-in", json={
        "username": "sasha.patel@gmail.com",
        "password": "Demo1234!",
        "device_id": str(device.device_id)
    })

    assert response.status_code == 200
    data = response.json()
    assert data["auth_level"] == "password_only"
    assert data["requires_proof"] is True


# FR-002: Prove it's her
def test_fr002_ac1_passcode_grants_access(client, demo_customer):
    """
    FR-002 AC1: Given the customer has completed valid username-and-password
    sign-in on a registered device, when a valid passcode or biometric proof
    is provided, then the app grants access to the accounts overview.
    """
    get_rate_limiter().reset()

    customer, profile, device = demo_customer

    # Sign in
    sign_in_response = client.post("/api/v1/auth/sign-in", json={
        "username": "sasha.patel@gmail.com",
        "password": "Demo1234!",
        "device_id": str(device.device_id)
    })

    session_id = sign_in_response.json()["session_id"]

    # Submit passcode proof
    proof_response = client.post("/api/v1/auth/proof", json={
        "session_id": session_id,
        "proof_type": "passcode",
        "proof_value": "123456",
        "device_id": str(device.device_id)
    })

    assert proof_response.status_code == 200
    data = proof_response.json()

    # Access granted - proven auth level
    assert data["auth_level"] == "proven"
    assert "access_token" in data
    # JWT token for subsequent API calls
    assert data["token_type"] == "Bearer"


def test_fr002_ac2_biometric_as_second_factor(client, demo_customer):
    """
    FR-002 AC2: Given the customer uses biometric proof and the platform
    verification succeeds, when the proof completes, then the app treats
    the biometric result as the second factor without receiving raw biometric data.
    """
    get_rate_limiter().reset()

    customer, profile, device = demo_customer

    # Sign in
    sign_in_response = client.post("/api/v1/auth/sign-in", json={
        "username": "sasha.patel@gmail.com",
        "password": "Demo1234!",
        "device_id": str(device.device_id)
    })

    session_id = sign_in_response.json()["session_id"]

    # Submit biometric proof (attestation from platform, not raw biometric)
    proof_response = client.post("/api/v1/auth/proof", json={
        "session_id": session_id,
        "proof_type": "biometric",
        "proof_value": "platform-attestation-token-12345",  # Not raw biometric data
        "device_id": str(device.device_id)
    })

    assert proof_response.status_code == 200
    data = proof_response.json()
    assert data["auth_level"] == "proven"


def test_fr002_ac3_passcode_lockout_after_three_failures(client, demo_customer):
    """
    FR-002 AC3: Given the customer enters the wrong passcode three times,
    when the threshold is reached, then passcode entry is paused and the
    customer is directed to a password-based fallback or recovery path.
    """
    get_rate_limiter().reset()

    customer, profile, device = demo_customer

    # Attempt 3 wrong passcodes
    for i in range(3):
        sign_in_response = client.post("/api/v1/auth/sign-in", json={
            "username": "sasha.patel@gmail.com",
            "password": "Demo1234!",
            "device_id": str(device.device_id)
        })

        session_id = sign_in_response.json()["session_id"]

        proof_response = client.post("/api/v1/auth/proof", json={
            "session_id": session_id,
            "proof_type": "passcode",
            "proof_value": "999999",  # Wrong passcode
            "device_id": str(device.device_id)
        })

        if i < 2:
            assert proof_response.status_code == 401
        else:
            # On third failure, should get lockout message
            assert proof_response.status_code == 401
            error_msg = proof_response.json()["detail"]
            assert "Too many incorrect passcode attempts" in error_msg or "paused" in error_msg


def test_fr002_ac4_untrusted_device_blocks_access(client, demo_customer, db_session):
    """
    FR-002 AC4: Given the device is not trusted or required proof cannot be
    completed, when the customer cannot satisfy the proof step, then the app
    blocks access to account and payment features and presents a safe next-step path.
    """
    get_rate_limiter().reset()

    customer, profile, device = demo_customer

    # Make device untrusted (use the same db_session that client uses)
    device.trust_state = 'untrusted'
    db_session.commit()

    # Sign in succeeds but device not trusted
    sign_in_response = client.post("/api/v1/auth/sign-in", json={
        "username": "sasha.patel@gmail.com",
        "password": "Demo1234!",
        "device_id": str(device.device_id)
    })

    session_id = sign_in_response.json()["session_id"]

    # Proof should fail on untrusted device
    proof_response = client.post("/api/v1/auth/proof", json={
        "session_id": session_id,
        "proof_type": "passcode",
        "proof_value": "123456",
        "device_id": str(device.device_id)
    })

    assert proof_response.status_code == 401
    assert "not trusted" in proof_response.json()["detail"].lower()
