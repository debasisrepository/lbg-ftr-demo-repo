"""
Acceptance tests for auth feature acceptance criteria.
Requirement: FR-AUTH-003, FR-AUTH-006
"""


class TestFRAuth003PasscodeSignIn:
    """
    FR-AUTH-003: Passcode sign-in
    
    Acceptance Criteria:
    - The sign-in flow is available only on a previously registered eligible device.
    - Incorrect passcode entry does not grant access.
    - Successful passcode entry transitions the customer into the authenticated app experience.
    - Sign-in failures display clear and accessible feedback without disclosing sensitive security internals.
    """
    
    def test_signin_only_on_registered_device(self, client, db_session):
        """AC: The sign-in flow is available only on a previously registered eligible device."""
        # Attempt login with unregistered device
        response = client.post(
            "/api/v1/auth/login",
            json={
                "device_identifier": "unregistered-device-xyz",
                "mobile_platform": "iOS",
                "passcode": "Pass1234"
            }
        )
        
        assert response.status_code == 401
        assert "couldn't sign you in" in response.json()["detail"]
        
        # Login with registered device succeeds
        response = client.post(
            "/api/v1/auth/login",
            json={
                "device_identifier": "device-CUST-SYNTH-001-iOS",
                "mobile_platform": "iOS",
                "passcode": "Pass1234"
            }
        )
        
        assert response.status_code == 200
    
    def test_incorrect_passcode_no_access(self, client, db_session):
        """AC: Incorrect passcode entry does not grant access."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "device_identifier": "device-CUST-SYNTH-001-iOS",
                "mobile_platform": "iOS",
                "passcode": "Wrong999"  # Valid length but wrong
            }
        )
        
        assert response.status_code == 401
        assert "access_token" not in response.json()
    
    def test_successful_passcode_grants_authenticated_access(self, client, db_session):
        """AC: Successful passcode entry transitions the customer into the authenticated app experience."""
        # Login successfully
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "device_identifier": "device-CUST-SYNTH-001-iOS",
                "mobile_platform": "iOS",
                "passcode": "Pass1234"
            }
        )
        
        assert login_response.status_code == 200
        data = login_response.json()
        
        # Verify authenticated access
        assert "access_token" in data
        assert data["user"]["display_name"] == "Alex Taylor"
        
        # Verify token works for protected endpoint
        token = data["access_token"]
        session_response = client.get(
            "/api/v1/auth/session",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert session_response.status_code == 200
        assert session_response.json()["authenticated"] is True
    
    def test_signin_failures_no_sensitive_disclosure(self, client, db_session):
        """AC: Sign-in failures display clear and accessible feedback without disclosing sensitive security internals."""
        # Test various failure scenarios
        failure_scenarios = [
            {
                "device_identifier": "unregistered-device",
                "mobile_platform": "iOS",
                "passcode": "Pass1234",
                "reason": "unregistered device"
            },
            {
                "device_identifier": "device-CUST-SYNTH-001-iOS",
                "mobile_platform": "iOS",
                "passcode": "Wrong999",  # Valid length but wrong
                "reason": "wrong passcode"
            },
        ]
        
        for scenario in failure_scenarios:
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "device_identifier": scenario["device_identifier"],
                    "mobile_platform": scenario["mobile_platform"],
                    "passcode": scenario["passcode"]
                }
            )
            
            assert response.status_code == 401
            data = response.json()
            
            # Verify same generic message for all failures
            assert "couldn't sign you in" in data["detail"]
            assert "Check your details and try again" in data["detail"]
            
            # Verify no sensitive internals disclosed
            detail_lower = data["detail"].lower()
            assert "unregistered" not in detail_lower
            assert "wrong" not in detail_lower
            assert "hash" not in detail_lower


class TestFRAuth006SessionContinuity:
    """
    FR-AUTH-006: Session continuity and protected-route enforcement
    
    Acceptance Criteria:
    - Attempting to access protected app routes without a valid session returns the customer to the sign-in journey.
    - Protected content is not displayed before authentication completes.
    - Session interruption during a protected journey results in a clear re-authentication path.
    - The customer is not left in an ambiguous state about whether an action completed after session interruption.
    """
    
    def test_protected_routes_require_valid_session(self, client, db_session):
        """AC: Attempting to access protected app routes without a valid session returns the customer to the sign-in journey."""
        # Attempt to access protected endpoint without token
        response = client.get("/api/v1/auth/session")
        
        assert response.status_code in [401, 403]  # Auth middleware returns 401 or 403 for missing auth
        
        # Attempt with invalid token
        response = client.get(
            "/api/v1/auth/session",
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        assert response.status_code == 401
    
    def test_protected_content_only_after_authentication(self, client, db_session):
        """AC: Protected content is not displayed before authentication completes."""
        # Cannot access session endpoint without auth
        response = client.get("/api/v1/auth/session")
        assert response.status_code != 200
        
        # Login first
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
        
        # Now can access protected content
        session_response = client.get(
            "/api/v1/auth/session",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert session_response.status_code == 200
        assert "user" in session_response.json()
    
    def test_session_interruption_clear_reauth_path(self, client, db_session):
        """AC: Session interruption during a protected journey results in a clear re-authentication path."""
        # Login and get token
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
        
        # Revoke session (simulate interruption)
        logout_response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert logout_response.status_code == 204
        
        # Attempt to use revoked token
        session_response = client.get(
            "/api/v1/auth/session",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert session_response.status_code == 401
        data = session_response.json()
        
        # Verify clear error indicating re-authentication needed
        assert "detail" in data
        assert "revoked" in data["detail"].lower() or "invalid" in data["detail"].lower()
    
    def test_no_ambiguous_state_after_interruption(self, client, db_session):
        """AC: The customer is not left in an ambiguous state about whether an action completed after session interruption."""
        # Login
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
        
        # Verify session is active
        session_response = client.get(
            "/api/v1/auth/session",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert session_response.status_code == 200
        assert session_response.json()["authenticated"] is True
        
        # Logout
        logout_response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert logout_response.status_code == 204
        
        # Verify session is definitively ended (not ambiguous)
        session_response2 = client.get(
            "/api/v1/auth/session",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert session_response2.status_code == 401
        
        # Second logout attempt also returns clear 401 (not 204 or ambiguous state)
        logout_response2 = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert logout_response2.status_code == 401


def test_health_endpoint_no_database(client):
    """Test E-13: health endpoint returns 200 with no database round trip."""
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_endpoint_checks_database(client, db_session):
    """Test E-14: readiness endpoint checks database connectivity."""
    response = client.get("/health/ready")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
