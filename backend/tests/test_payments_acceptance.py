"""Payments router acceptance tests"""
import uuid


def test_prepare_payment(client, seeded_data):
    """Test preparing a new payment"""
    source_account_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, "account:acc_current_001"))
    payee_id = "10000000-0000-0000-0000-000000000501"

    response = client.post("/api/v1/payments/prepare", json={
        "source_account_id": source_account_id,
        "payee_id": payee_id,
        "amount_minor": 5000,
        "currency_code": "GBP",
        "payment_reference": "Test payment",
        "idempotency_key": f"test_{uuid.uuid4().hex}"
    })

    assert response.status_code == 200
    data = response.json()
    assert "payment_order_id" in data
    assert data["amount_minor"] == 5000
    assert data["currency_code"] == "GBP"


def test_get_payment(client, seeded_data):
    """Test retrieving payment details"""
    # First create a payment
    source_account_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, "account:acc_current_001"))
    payee_id = "10000000-0000-0000-0000-000000000501"

    create_response = client.post("/api/v1/payments/prepare", json={
        "source_account_id": source_account_id,
        "payee_id": payee_id,
        "amount_minor": 5000,
        "currency_code": "GBP",
        "payment_reference": "Test",
        "idempotency_key": f"test_{uuid.uuid4().hex}"
    })

    payment_order_id = create_response.json()["payment_order_id"]

    # Now retrieve it
    response = client.get(f"/api/v1/payments/{payment_order_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["payment_order_id"] == payment_order_id
    assert data["amount_minor"] == 5000


def test_get_payment_receipt(client, seeded_data):
    """Test retrieving payment receipt"""
    # Use the seeded demo payment
    payment_order_id = "10000000-0000-0000-0000-000000000701"

    response = client.get(f"/api/v1/payments/{payment_order_id}/receipt")

    assert response.status_code == 200
    data = response.json()
    assert data["payment_order_id"] == payment_order_id
    assert "payee_name" in data
    assert "source_account_name" in data


def test_approve_payment(client, seeded_data):
    """Test approving a payment"""
    # Create a payment first
    source_account_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, "account:acc_current_001"))
    payee_id = "10000000-0000-0000-0000-000000000501"

    create_response = client.post("/api/v1/payments/prepare", json={
        "source_account_id": source_account_id,
        "payee_id": payee_id,
        "amount_minor": 5000,
        "currency_code": "GBP",
        "payment_reference": "Test",
        "idempotency_key": f"test_{uuid.uuid4().hex}"
    })

    payment_order_id = create_response.json()["payment_order_id"]

    # Approve it
    response = client.post(f"/api/v1/payments/{payment_order_id}/approve", json={})

    assert response.status_code == 200
    data = response.json()
    assert data["approval_result"] == "approved"


def test_submit_payment(client, seeded_data):
    """Test submitting a payment"""
    # Create and approve a payment first
    source_account_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, "account:acc_current_001"))
    payee_id = "10000000-0000-0000-0000-000000000501"

    create_response = client.post("/api/v1/payments/prepare", json={
        "source_account_id": source_account_id,
        "payee_id": payee_id,
        "amount_minor": 5000,
        "currency_code": "GBP",
        "payment_reference": "Test",
        "idempotency_key": f"test_{uuid.uuid4().hex}"
    })

    payment_order_id = create_response.json()["payment_order_id"]

    client.post(f"/api/v1/payments/{payment_order_id}/approve", json={})

    # Submit it
    response = client.post(f"/api/v1/payments/{payment_order_id}/submit", json={})

    assert response.status_code == 200
    data = response.json()
    assert data["normalized_status"] == "sent"
    assert data["external_payment_ref"] is not None
