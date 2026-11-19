"""Integration tests for payments API."""
import pytest
from app.common.security import create_access_token


def test_prepare_payment_validates_balance(auth_client, db_session):
    """Test POST /api/v1/payments/prepare validates balance."""
    # auth_client uses admin@example.com with admin_profile (profile_id: 1)
    # admin_current account has £5,000 balance
    response = auth_client.post(
        "/api/v1/payments/prepare",
        json={
            "profile_id": 1,  # admin_profile from seed
            "source_account_id": 1,  # admin_current from seed (£5,000.00)
            "payee_id": 1,  # Test Supplier Ltd from seed
            "amount_minor": 1000000,  # £10,000 - exceeds balance
            "currency": "GBP",
            "reference": "Test payment"
        }
    )
    
    assert response.status_code == 400  # ValidationError returns 400
    assert "validation failed" in response.json()["detail"].lower()


def test_prepare_payment_returns_fraud_decision(auth_client, db_session):
    """Test POST /api/v1/payments/prepare returns fraud decision."""
    response = auth_client.post(
        "/api/v1/payments/prepare",
        json={
            "profile_id": 1,  # admin_profile from seed
            "source_account_id": 1,  # admin_current from seed (£5,000.00)
            "payee_id": 1,  # Test Supplier Ltd (admin profile payee from seed)
            "amount_minor": 50000,  # £500
            "currency": "GBP",
            "reference": "Test payment"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "fraud_decision" in data
    assert data["fraud_decision"]["decision"] in ["allow", "warn", "step_up", "hold"]
    assert "balance_check" in data
    assert data["balance_check"]["passed"] is True
    assert "approval_challenge" in data


def test_approve_payment_with_valid_approval(auth_client, db_session):
    """Test POST /api/v1/payments/{id}/approve with valid approval returns status."""
    # First prepare a payment
    prepare_response = auth_client.post(
        "/api/v1/payments/prepare",
        json={
            "profile_id": 1,  # admin_profile from seed
            "source_account_id": 1,  # admin_current from seed
            "payee_id": 1,  # Test Supplier Ltd from seed
            "amount_minor": 30000,  # £300
            "currency": "GBP",
            "reference": "Test payment"
        }
    )
    
    assert prepare_response.status_code == 200
    prepare_data = prepare_response.json()
    
    # Skip if held by fraud
    if prepare_data["fraud_decision"]["decision"] == "hold":
        pytest.skip("Payment held by fraud decision")
    
    payment_id = prepare_data["payment_id"]
    challenge_id = prepare_data["approval_challenge"]["challenge_id"]
    
    # Approve the payment
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
    assert approve_data["status"] in ["sent", "pending", "failed"]
    assert approve_data["payment_reference"] is not None
    assert "next_actions" in approve_data


def test_duplicate_submission_during_pending(auth_client, db_session):
    """Test duplicate submission during pending returns existing pending status."""
    # First prepare a payment
    prepare_response = auth_client.post(
        "/api/v1/payments/prepare",
        json={
            "profile_id": 1,
            "source_account_id": 1,
            "payee_id": 1,
            "amount_minor": 20000,  # £200
            "currency": "GBP",
            "reference": "Test duplicate"
        }
    )
    
    assert prepare_response.status_code == 200
    prepare_data = prepare_response.json()
    
    # Skip if held
    if prepare_data["fraud_decision"]["decision"] == "hold":
        pytest.skip("Payment held by fraud decision")
    
    payment_id = prepare_data["payment_id"]
    challenge_id = prepare_data["approval_challenge"]["challenge_id"]
    
    # Approve the payment
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
    first_approve = approve_response.json()
    
    # If status is pending, try to approve again
    if first_approve["status"] == "pending":
        second_approve_response = auth_client.post(
            f"/api/v1/payments/{payment_id}/approve",
            json={
                "challenge_id": challenge_id,
                "method": "dynamic_link",
                "passcode": None,
                "biometric_assertion": None,
                "device_id": "test-device"
            }
        )
        
        assert second_approve_response.status_code == 200
        second_approve = second_approve_response.json()
        assert second_approve["status"] == "pending"
        assert second_approve["duplicate_submission_blocked"] is True


def test_get_payment_status(auth_client, db_session):
    """Test GET /api/v1/payments/{id} returns payment status."""
    # Prepare and approve a payment
    prepare_response = auth_client.post(
        "/api/v1/payments/prepare",
        json={
            "profile_id": 1,
            "source_account_id": 1,
            "payee_id": 1,
            "amount_minor": 15000,  # £150
            "currency": "GBP",
            "reference": "Status test"
        }
    )
    
    assert prepare_response.status_code == 200
    prepare_data = prepare_response.json()
    
    # Skip if held
    if prepare_data["fraud_decision"]["decision"] == "hold":
        pytest.skip("Payment held by fraud decision")
    
    payment_id = prepare_data["payment_id"]
    challenge_id = prepare_data["approval_challenge"]["challenge_id"]
    
    # Approve
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
    
    # Get status
    status_response = auth_client.get(f"/api/v1/payments/{payment_id}")
    
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["payment_id"] == payment_id
    assert status_data["status"] in ["sent", "pending", "failed"]
    assert status_data["amount_minor"] == 15000
    assert "status_last_updated_at" in status_data
