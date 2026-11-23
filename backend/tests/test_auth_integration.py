"""
Integration tests for auth endpoints with real database.
Requirement: FR-AUTH-003, FR-AUTH-006
"""


def test_login_success(client, db_session):
    """Test E-01: successful login with seed credentials."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "device_identifier": "device-CUST-SYNTH-001-iOS",
            "mobile_platform": "iOS",
            "passcode": "Pass1234"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response shape
    assert "access_token" in data
    assert data["token_type"] == "Bearer"
    assert "expires_in" in data
    assert "expires_at" in data
    assert "inactivity_timeout_seconds" in data
    assert "session_id" in data
    
    # Verify user data
    assert "user" in data
    assert data["user"]["display_name"] == "Alex Taylor"
    assert data["user"]["profile_type"] == "personal"


def test_login_wrong_passcode(client, db_session):
    """Test E-01: login fails with wrong passcode."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "device_identifier": "device-CUST-SYNTH-001-iOS",
            "mobile_platform": "iOS",
            "passcode": "WrongPass"
        }
    )
    
    assert response.status_code == 401
    data = response.json()
    
    # Verify generic error message
    assert "couldn't sign you in" in data["detail"]


def test_login_unregistered_device(client, db_session):
    """Test E-01: login fails for unregistered device."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "device_identifier": "unknown-device-identifier",
            "mobile_platform": "iOS",
            "passcode": "Pass1234"
        }
    )
    
    assert response.status_code == 401
    data = response.json()
    
    # Verify generic error message (no detail about unregistered device)
    assert "couldn't sign you in" in data["detail"]


def test_login_validation_error(client, db_session):
    """Test E-01: login fails with invalid request."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "device_identifier": "short",  # Too short (min 8)
            "mobile_platform": "iOS",
            "passcode": "123"  # Too short (min 4)
        }
    )
    
    assert response.status_code == 422
    data = response.json()
    
    assert data["error_code"] == "validation_error"
    assert "errors" in data


def test_session_validation_success(client, db_session):
    """Test E-02: validate active session."""
    # First login
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "device_identifier": "device-CUST-SYNTH-001-iOS",
            "mobile_platform": "iOS",
            "passcode": "Pass1234"
        }
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Validate session
    response = client.get(
        "/api/v1/auth/session",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response shape
    assert data["authenticated"] is True
    assert "session_id" in data
    assert "issued_at" in data
    assert "expires_at" in data
    assert "last_activity_at" in data
    assert "inactivity_expires_at" in data
    
    # Verify user data
    assert "user" in data
    assert data["user"]["display_name"] == "Alex Taylor"


def test_session_validation_no_token(client, db_session):
    """Test E-02: validation fails without token."""
    response = client.get("/api/v1/auth/session")
    
    assert response.status_code in [401, 403]  # Auth middleware returns 401 or 403 for missing auth


def test_session_validation_invalid_token(client, db_session):
    """Test E-02: validation fails with invalid token."""
    response = client.get(
        "/api/v1/auth/session",
        headers={"Authorization": "Bearer invalid-token"}
    )
    
    assert response.status_code == 401


def test_logout_success(client, db_session):
    """Test E-03: successful logout."""
    # First login
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "device_identifier": "device-CUST-SYNTH-001-iOS",
            "mobile_platform": "iOS",
            "passcode": "Pass1234"
        }
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Logout
    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 204
    
    # Verify token no longer works
    session_response = client.get(
        "/api/v1/auth/session",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert session_response.status_code == 401


def test_logout_no_token(client, db_session):
    """Test E-03: logout fails without token."""
    response = client.post("/api/v1/auth/logout")
    
    assert response.status_code in [401, 403]  # Auth middleware returns 401 or 403 for missing auth


def test_correlation_id_propagation(client, db_session):
    """Test that correlation ID is echoed in response."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "device_identifier": "device-CUST-SYNTH-001-iOS",
            "mobile_platform": "iOS",
            "passcode": "Pass1234"
        },
        headers={"X-Correlation-ID": "test-correlation-123"}
    )
    
    assert response.status_code == 200
    assert response.headers.get("X-Correlation-ID") == "test-correlation-123"


def test_multiple_logins_create_separate_sessions(client, db_session):
    """Test that multiple logins create separate sessions."""
    # First login
    response1 = client.post(
        "/api/v1/auth/login",
        json={
            "device_identifier": "device-CUST-SYNTH-001-iOS",
            "mobile_platform": "iOS",
            "passcode": "Pass1234"
        }
    )
    assert response1.status_code == 200
    session1 = response1.json()["session_id"]
    
    # Second login
    response2 = client.post(
        "/api/v1/auth/login",
        json={
            "device_identifier": "device-CUST-SYNTH-001-iOS",
            "mobile_platform": "iOS",
            "passcode": "Pass1234"
        }
    )
    assert response2.status_code == 200
    session2 = response2.json()["session_id"]
    
    # Sessions should be different
    assert session1 != session2
