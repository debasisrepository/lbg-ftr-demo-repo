"""
Tests for payment outcome details (FR-PAY-013).
Requirement: REQ-PAY-010, REQ-PAY-011

Covers:
- Outcome details include payment reference (always present)
- Expected arrival time shown only when supplied by payments hub (never estimated)
- Payee display name included in outcome
- Outcome details remain visible for Sent, Pending, Failed states
"""
import uuid
from datetime import UTC, datetime, timedelta

from app.models.account_read_model import AccountReadModel
from app.models.payee import Payee
from app.models.payment_intent import PaymentIntent


def test_outcome_details_include_payment_reference(client, db_session, auth_client):
    """
    AC: The outcome view includes the payment reference for the relevant payment.
    
    Test that PaymentResponse includes payment_reference in all states.
    """
    # Get seeded account and payee using query
    account = db_session.query(AccountReadModel).first()
    payee = db_session.query(Payee).filter_by(payee_status="saved_active").first()
    
    assert account is not None, "No seeded account found"
    assert payee is not None, "No seeded payee found"
    
    # Create payment with specific reference
    response = auth_client.post(
        "/api/v1/payments",
        json={
            "source_account_id": str(account.id),
            "payee_id": str(payee.id),
            "amount_minor": 5000,
            "currency": "GBP",
            "payment_reference": "Invoice 12345"
        },
        headers={"Idempotency-Key": str(uuid.uuid4())}
    )
    assert response.status_code in [200, 201], f"Failed to create payment: {response.text}"
    
    data = response.json()
    
    # Verify payment reference is present
    assert "payment_reference" in data, "payment_reference missing from response"
    assert data["payment_reference"] == "Invoice 12345", "payment_reference doesn't match"
    
    # Also verify in GET endpoint
    payment_id = data["payment_id"]
    get_response = auth_client.get(f"/api/v1/payments/{payment_id}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["payment_reference"] == "Invoice 12345", "payment_reference missing in GET response"


def test_expected_arrival_time_only_when_supplied(client, db_session, auth_client):
    """
    AC: When an expected arrival time is available from the trusted payment-status flow,
    it is shown with the outcome. If unavailable, the app does not invent or guess one.
    
    Test that expected_arrival_time is None when not supplied by payments hub.
    """
    # Get seeded account and payee
    account = db_session.query(AccountReadModel).first()
    payee = db_session.query(Payee).filter_by(payee_status="saved_active").first()
    
    assert account is not None
    assert payee is not None
    
    # Create payment in review_ready state
    response = auth_client.post(
        "/api/v1/payments",
        json={
            "source_account_id": str(account.id),
            "payee_id": str(payee.id),
            "amount_minor": 10000,
            "currency": "GBP",
            "payment_reference": "Test payment"
        },
        headers={"Idempotency-Key": str(uuid.uuid4())}
    )
    assert response.status_code in [200, 201]
    
    data = response.json()
    
    # Verify expected_arrival_time is None when not supplied
    assert data["expected_arrival_time"] is None, "expected_arrival_time should be None when not supplied"
    
    # Create a completed payment with expected_arrival_time manually set
    # (In real flow, this would come from payments hub response)
    payment_id = uuid.UUID(data["payment_id"])
    payment = db_session.query(PaymentIntent).filter_by(id=payment_id).first()
    
    expected_arrival = datetime.now(UTC) + timedelta(hours=2)
    payment.expected_arrival_time = expected_arrival
    payment.current_state = "completed"
    payment.customer_visible_status = "Sent"
    db_session.commit()
    
    # Verify expected_arrival_time is present when supplied
    get_response = auth_client.get(f"/api/v1/payments/{payment_id}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    
    assert get_data["expected_arrival_time"] is not None, "expected_arrival_time should be present"
    # Parse and compare datetimes (allow small tolerance for serialization)
    response_time = datetime.fromisoformat(get_data["expected_arrival_time"].replace('Z', '+00:00'))
    assert abs((response_time - expected_arrival).total_seconds()) < 2, "expected_arrival_time doesn't match"


def test_payee_display_name_in_outcome(client, db_session, auth_client):
    """
    Test that payee_display_name is included in payment response (outcome details).
    """
    # Get seeded account and payee
    account = db_session.query(AccountReadModel).first()
    payee = db_session.query(Payee).filter_by(payee_status="saved_active").first()
    
    assert account is not None
    assert payee is not None
    
    # Create payment
    response = auth_client.post(
        "/api/v1/payments",
        json={
            "source_account_id": str(account.id),
            "payee_id": str(payee.id),
            "amount_minor": 7500,
            "currency": "GBP",
            "payment_reference": "Test ref"
        },
        headers={"Idempotency-Key": str(uuid.uuid4())}
    )
    assert response.status_code in [200, 201]
    
    data = response.json()
    
    # Verify payee_display_name is present
    assert "payee_display_name" in data, "payee_display_name missing from response"
    assert data["payee_display_name"] == payee.payee_name, "payee_display_name doesn't match payee name"


def test_outcome_details_for_sent_state(client, db_session, auth_client):
    """
    AC: Outcome details remain visible for Sent, Pending, and Failed states where applicable.
    
    Test Sent state includes outcome details (reference, expected_arrival_time, payee_display_name).
    """
    # Get seeded account and payee
    account = db_session.query(AccountReadModel).first()
    payee = db_session.query(Payee).filter_by(payee_status="saved_active").first()
    
    assert account is not None
    assert payee is not None
    
    # Create payment and set to completed (Sent)
    response = auth_client.post(
        "/api/v1/payments",
        json={
            "source_account_id": str(account.id),
            "payee_id": str(payee.id),
            "amount_minor": 15000,
            "currency": "GBP",
            "payment_reference": "Completed payment"
        },
        headers={"Idempotency-Key": str(uuid.uuid4())}
    )
    assert response.status_code in [200, 201]
    
    data = response.json()
    payment_id = uuid.UUID(data["payment_id"])
    
    # Manually set to completed with expected_arrival_time
    payment = db_session.query(PaymentIntent).filter_by(id=payment_id).first()
    
    payment.current_state = "completed"
    payment.customer_visible_status = "Sent"
    payment.expected_arrival_time = datetime.now(UTC) + timedelta(hours=4)
    db_session.commit()
    
    # Get payment and verify outcome details
    get_response = auth_client.get(f"/api/v1/payments/{payment_id}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    
    assert get_data["customer_visible_status"] == "Sent"
    assert get_data["payment_reference"] == "Completed payment"
    assert get_data["expected_arrival_time"] is not None
    assert get_data["payee_display_name"] == payee.payee_name


def test_outcome_details_for_pending_state(client, db_session, auth_client):
    """
    AC: Outcome details remain visible for Sent, Pending, and Failed states where applicable.
    
    Test Pending state includes outcome details.
    """
    # Get seeded account and payee
    account = db_session.query(AccountReadModel).first()
    payee = db_session.query(Payee).filter_by(payee_status="saved_active").first()
    
    assert account is not None
    assert payee is not None
    
    # Create payment and set to pending_confirmation (Pending)
    response = auth_client.post(
        "/api/v1/payments",
        json={
            "source_account_id": str(account.id),
            "payee_id": str(payee.id),
            "amount_minor": 25000,
            "currency": "GBP",
            "payment_reference": "Pending payment"
        },
        headers={"Idempotency-Key": str(uuid.uuid4())}
    )
    assert response.status_code in [200, 201]
    
    data = response.json()
    payment_id = uuid.UUID(data["payment_id"])
    
    # Manually set to pending_confirmation
    payment = db_session.query(PaymentIntent).filter_by(id=payment_id).first()
    
    payment.current_state = "pending_confirmation"
    payment.customer_visible_status = "Pending"
    payment.do_not_resubmit = True
    db_session.commit()
    
    # Get payment and verify outcome details
    get_response = auth_client.get(f"/api/v1/payments/{payment_id}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    
    assert get_data["customer_visible_status"] == "Pending"
    assert get_data["payment_reference"] == "Pending payment"
    assert get_data["payee_display_name"] == payee.payee_name
    assert get_data["do_not_resubmit"] is True


def test_outcome_details_for_failed_state(client, db_session, auth_client):
    """
    AC: Outcome details remain visible for Sent, Pending, and Failed states where applicable.
    
    Test Failed state includes outcome details.
    """
    # Get seeded account and payee
    account = db_session.query(AccountReadModel).first()
    payee = db_session.query(Payee).filter_by(payee_status="saved_active").first()
    
    assert account is not None
    assert payee is not None
    
    # Create payment and set to rejected (Failed)
    response = auth_client.post(
        "/api/v1/payments",
        json={
            "source_account_id": str(account.id),
            "payee_id": str(payee.id),
            "amount_minor": 35000,
            "currency": "GBP",
            "payment_reference": "Failed payment"
        },
        headers={"Idempotency-Key": str(uuid.uuid4())}
    )
    assert response.status_code in [200, 201]
    
    data = response.json()
    payment_id = uuid.UUID(data["payment_id"])
    
    # Manually set to rejected
    payment = db_session.query(PaymentIntent).filter_by(id=payment_id).first()
    
    payment.current_state = "rejected"
    payment.customer_visible_status = "Failed"
    db_session.commit()
    
    # Get payment and verify outcome details
    get_response = auth_client.get(f"/api/v1/payments/{payment_id}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    
    assert get_data["customer_visible_status"] == "Failed"
    assert get_data["payment_reference"] == "Failed payment"
    assert get_data["payee_display_name"] == payee.payee_name
