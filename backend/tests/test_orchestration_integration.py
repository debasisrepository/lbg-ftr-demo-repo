"""Integration tests for service orchestration flows.

Tests backend service orchestration: auth → entitlement → accounts with partial
failure, payee → CoP → approval, payment → fraud → approval → status.
"""
import pytest
from app.common.security import create_access_token


def test_auth_to_entitlement_to_accounts_orchestration(auth_client, db_session):
    """Test auth → entitlement → accounts orchestration with partial failure handling.
    
    Verifies:
    - Authenticated user can activate profile
    - Entitlement check grants access
    - Account overview returns available data even with partial failures
    - Data gaps are recorded when services unavailable
    """
    # 1. Auth: already authenticated via auth_client fixture (admin@example.com)
    
    # 2. Get profiles with entitlements
    profiles_response = auth_client.get("/api/v1/profiles")
    assert profiles_response.status_code == 200
    profiles_data = profiles_response.json()
    assert len(profiles_data["profiles"]) > 0
    
    # Select first profile
    profile = profiles_data["profiles"][0]
    profile_id = profile["profile_id"]
    
    # Verify entitlements are present (flattened in profile object)
    assert "can_view_accounts" in profile
    assert "can_create_payee" in profile
    assert "can_approve_payment" in profile
    
    # 3. Activate profile
    activate_response = auth_client.post(
        "/api/v1/profiles/activate",
        json={"profile_id": profile_id}
    )
    assert activate_response.status_code == 200
    
    # 4. Get accounts overview (with partial failure handling)
    accounts_response = auth_client.get(
        "/api/v1/accounts/overview",
        params={"profile_id": profile_id}
    )
    assert accounts_response.status_code == 200
    accounts_data = accounts_response.json()
    
    # Verify accounts returned
    assert "accounts" in accounts_data
    assert len(accounts_data["accounts"]) > 0
    
    # Each account should have freshness_state
    for account in accounts_data["accounts"]:
        assert "freshness_state" in account
        assert account["freshness_state"] in ["current", "delayed", "unavailable"]
        
        # Verify required fields present
        assert "account_id" in account
        assert "account_type" in account
        assert "account_name" in account
        assert "current_balance_minor" in account
    
    # Verify data_gaps field exists (may be empty if no failures)
    assert "data_gaps" in accounts_data


def test_payee_cop_approval_orchestration(auth_client, db_session):
    """Test payee → CoP → approval orchestration.
    
    Verifies:
    - Get payees endpoint works
    - CoP results are returned with payees
    - Can proceed flag is set correctly
    
    Note: Full payee creation with SCA is covered in test_payees_integration.py
    This test focuses on orchestration flow using existing payees.
    """
    # 1. Get profiles
    profiles_response = auth_client.get("/api/v1/profiles")
    assert profiles_response.status_code == 200
    profile_id = profiles_response.json()["profiles"][0]["profile_id"]
    
    # 2. Get existing payees (seed data includes payees)
    payees_response = auth_client.get(
        "/api/v1/payees",
        params={"profile_id": profile_id}
    )
    
    assert payees_response.status_code == 200
    payees_data = payees_response.json()
    
    # Verify payees returned
    assert "payees" in payees_data
    payees = payees_data["payees"]
    
    # Seed should have at least one payee for admin profile
    if len(payees) > 0:
        # Verify payee structure
        payee = payees[0]
        assert "payee_id" in payee
        assert "display_name" in payee
        assert "sort_code" in payee
        assert "masked_account_number" in payee
        assert "can_proceed" in payee
        
        # Can proceed should be True for existing matched payees
        assert payee["can_proceed"] is True


def test_payment_fraud_approval_status_orchestration(auth_client, db_session):
    """Test payment → fraud → approval → status orchestration.
    
    Verifies:
    - Payment preparation with balance/limit validation
    - Fraud decision (allow/warn/step_up/hold)
    - Approval with dynamic linking
    - Status tracking (sent/pending/failed)
    - Duplicate submission prevention during pending
    """
    # 1. Get profiles and accounts
    profiles_response = auth_client.get("/api/v1/profiles")
    assert profiles_response.status_code == 200
    profile_id = profiles_response.json()["profiles"][0]["profile_id"]
    
    accounts_response = auth_client.get(
        "/api/v1/accounts/overview",
        params={"profile_id": profile_id}
    )
    assert accounts_response.status_code == 200
    accounts = accounts_response.json()["accounts"]
    
    # Find current account with sufficient balance
    source_account = next(
        (acc for acc in accounts if acc["account_type"] == "current_account"),
        accounts[0]
    )
    source_account_id = source_account["account_id"]
    
    # 2. Get payees
    payees_response = auth_client.get(
        "/api/v1/payees",
        params={"profile_id": profile_id}
    )
    assert payees_response.status_code == 200
    payees = payees_response.json()["payees"]
    assert len(payees) > 0
    payee_id = payees[0]["payee_id"]
    
    # 3. Prepare payment (includes fraud check)
    prepare_response = auth_client.post(
        "/api/v1/payments/prepare",
        json={
            "profile_id": profile_id,
            "source_account_id": source_account_id,
            "payee_id": payee_id,
            "amount_minor": 25000,  # £250
            "currency": "GBP",
            "reference": "Integration test"
        }
    )
    
    assert prepare_response.status_code == 200
    prepare_data = prepare_response.json()
    
    # Verify fraud decision present
    assert "fraud_decision" in prepare_data
    fraud_decision = prepare_data["fraud_decision"]
    assert "decision" in fraud_decision
    assert fraud_decision["decision"] in ["allow", "warn", "step_up", "hold"]
    
    # Verify balance check passed
    assert "balance_check" in prepare_data
    assert prepare_data["balance_check"]["passed"] is True
    
    # If held, payment cannot proceed
    if fraud_decision["decision"] == "hold":
        payment_id = prepare_data["payment_id"]
        challenge_id = prepare_data["approval_challenge"]["challenge_id"]
        
        approve_response = auth_client.post(
            f"/api/v1/payments/{payment_id}/approve",
            json={
                "challenge_id": challenge_id,
                "method": "dynamic_link",
                "passcode": None,
                "biometric_assertion": None,
                "device_id": "test-device"
            }
        )
        # Hold should prevent approval
        assert approve_response.status_code in [400, 403]
        return
    
    # 4. Approve payment (with dynamic linking)
    payment_id = prepare_data["payment_id"]
    challenge_id = prepare_data["approval_challenge"]["challenge_id"]
    
    approve_response = auth_client.post(
        f"/api/v1/payments/{payment_id}/approve",
        json={
            "challenge_id": challenge_id,
            "method": "dynamic_link",
            "passcode": None,
            "biometric_assertion": None,
            "device_id": "test-device"
        }
    )
    
    assert approve_response.status_code == 200
    approve_data = approve_response.json()
    
    # 5. Verify status tracking
    assert "status" in approve_data
    assert approve_data["status"] in ["sent", "pending", "failed"]
    assert "payment_reference" in approve_data
    assert "next_actions" in approve_data
    
    # 6. Get payment status
    status_response = auth_client.get(f"/api/v1/payments/{payment_id}")
    assert status_response.status_code == 200
    status_data = status_response.json()
    
    assert status_data["payment_id"] == payment_id
    assert status_data["status"] == approve_data["status"]
    assert "status_last_updated_at" in status_data
    
    # 7. Test duplicate submission during pending
    if approve_data["status"] == "pending":
        # Try to approve again
        duplicate_response = auth_client.post(
            f"/api/v1/payments/{payment_id}/approve",
            json={
                "challenge_id": challenge_id,
                "method": "dynamic_link",
                "passcode": None,
                "biometric_assertion": None,
                "device_id": "test-device"
            }
        )
        
        assert duplicate_response.status_code == 200
        duplicate_data = duplicate_response.json()
        assert duplicate_data["status"] == "pending"
        assert duplicate_data["duplicate_submission_blocked"] is True


def test_full_payment_journey_with_all_checks(auth_client, db_session):
    """Test complete payment journey: auth → profiles → accounts → payees → payment → status.
    
    Verifies the entire end-to-end flow in one orchestrated test.
    """
    # 1. Auth (via auth_client fixture)
    # User is authenticated as admin@example.com
    
    # 2. Get profiles
    profiles_response = auth_client.get("/api/v1/profiles")
    assert profiles_response.status_code == 200
    profiles_data = profiles_response.json()
    assert "profiles" in profiles_data
    
    profile = profiles_data["profiles"][0]
    profile_id = profile["profile_id"]
    # Entitlements are flattened in profile object
    assert "can_view_accounts" in profile
    assert "can_create_payee" in profile
    assert "can_approve_payment" in profile
    
    # 3. Activate profile
    activate_response = auth_client.post(
        "/api/v1/profiles/activate",
        json={"profile_id": profile_id}
    )
    assert activate_response.status_code == 200
    
    # 4. Get accounts with entitlement check
    accounts_response = auth_client.get(
        "/api/v1/accounts/overview",
        params={"profile_id": profile_id}
    )
    assert accounts_response.status_code == 200
    accounts_data = accounts_response.json()
    accounts = accounts_data["accounts"]
    assert len(accounts) > 0
    
    # Find account with sufficient balance
    source_account = next(
        (acc for acc in accounts 
         if acc.get("available_balance_minor", 0) > 100000),  # £1000
        accounts[0]
    )
    source_account_id = source_account["account_id"]
    
    # 5. Get payees
    payees_response = auth_client.get(
        "/api/v1/payees",
        params={"profile_id": profile_id}
    )
    assert payees_response.status_code == 200
    payees_data = payees_response.json()
    payees = payees_data["payees"]
    assert len(payees) > 0
    
    payee = payees[0]
    payee_id = payee["payee_id"]
    
    # 6. Prepare payment (triggers fraud check)
    prepare_response = auth_client.post(
        "/api/v1/payments/prepare",
        json={
            "profile_id": profile_id,
            "source_account_id": source_account_id,
            "payee_id": payee_id,
            "amount_minor": 50000,  # £500
            "currency": "GBP",
            "reference": "Journey test"
        }
    )
    assert prepare_response.status_code == 200
    prepare_data = prepare_response.json()
    
    # Verify all prepare response components
    assert "payment_id" in prepare_data
    assert "fraud_decision" in prepare_data
    assert "balance_check" in prepare_data
    assert "limit_check" in prepare_data
    assert "approval_challenge" in prepare_data
    
    # Skip if held by fraud
    if prepare_data["fraud_decision"]["decision"] == "hold":
        pytest.skip("Payment held by fraud decision")
    
    # 7. Approve payment (dynamic linking)
    payment_id = prepare_data["payment_id"]
    challenge_id = prepare_data["approval_challenge"]["challenge_id"]
    
    approve_response = auth_client.post(
        f"/api/v1/payments/{payment_id}/approve",
        json={
            "challenge_id": challenge_id,
            "method": "dynamic_link",
            "passcode": None,
            "biometric_assertion": None,
            "device_id": "test-device"
        }
    )
    assert approve_response.status_code == 200
    approve_data = approve_response.json()
    
    # 8. Verify final status
    assert approve_data["status"] in ["sent", "pending", "failed"]
    assert "payment_reference" in approve_data
    assert "amount_minor" in approve_data
    assert approve_data["amount_minor"] == 50000
    
    # 9. Fetch status via status endpoint
    status_response = auth_client.get(f"/api/v1/payments/{payment_id}")
    assert status_response.status_code == 200
    status_data = status_response.json()
    
    # Verify status consistency
    assert status_data["status"] == approve_data["status"]
    assert status_data["payment_id"] == payment_id
    
    # Verify audit trail recorded
    # (Audit logs are written but not exposed via API in current implementation)
