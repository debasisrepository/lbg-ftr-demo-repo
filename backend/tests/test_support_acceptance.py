"""Support router acceptance tests"""
import uuid


def test_create_scam_claim(client):
    """Test creating a scam claim"""
    response = client.post("/api/v1/support/scam-claims", json={
        "payment_order_id": str(uuid.uuid4()),
        "claim_reason_code": "unauthorized_payment",
        "notes": "I did not authorize this payment"
    })

    assert response.status_code == 201
    data = response.json()
    assert "claim_reference" in data
    assert data["claim_reference"].startswith("SCM")
    assert data["claim_status"] == "reported"
    assert "support_case_reference" in data


def test_get_scam_claim(client):
    """Test retrieving a scam claim"""
    # Create a claim first
    create_response = client.post("/api/v1/support/scam-claims", json={
        "payment_order_id": str(uuid.uuid4()),
        "claim_reason_code": "suspected_fraud",
        "notes": "Suspicious payment"
    })

    claim_reference = create_response.json()["claim_reference"]

    # Retrieve it
    response = client.get(f"/api/v1/support/scam-claims/{claim_reference}")

    assert response.status_code == 200
    data = response.json()
    assert data["claim_reference"] == claim_reference
    assert data["claim_status"] == "reported"
