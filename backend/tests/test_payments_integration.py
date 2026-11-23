"""
Integration tests for payments endpoints E-07 and E-10.
Requirement: REQ-PAY-002, REQ-PAY-003
"""
import uuid


class TestPaymentsIntegration:
    """Integration tests for payments API."""
    
    def test_create_payment_review_success(self, auth_client, db_session):
        """Test E-07: Create payment review successfully."""
        # Get first account and payee for the test customer
        from app.models.account_read_model import AccountReadModel
        from app.models.payee import Payee
        
        account = db_session.query(AccountReadModel).first()
        payee = db_session.query(Payee).first()
        
        assert account is not None
        assert payee is not None
        
        response = auth_client.post(
            "/api/v1/payments",
            json={
                "source_account_id": str(account.id),
                "payee_id": str(payee.id),
                "amount_minor": 100000,
                "currency": "GBP",
                "payment_reference": "Test payment"
            },
            headers={"Idempotency-Key": "test-key-001"}
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert "payment_id" in data
        assert data["current_state"] == "review_ready"
        assert data["next_action"] == "review_and_approve"
        assert data["customer_visible_status"] is None
        assert data["is_submitted"] is False
        assert data["do_not_resubmit"] is False
        assert data["payment_reference"] == "Test payment"
        assert data["amount_minor"] == 100000
        assert data["currency"] == "GBP"
        assert data["review_version"] == 1
        assert len(data["review_fingerprint"]) == 64
        assert "source_account" in data
        assert "payee" in data
    
    def test_create_payment_review_idempotent_replay(self, auth_client, db_session):
        """Test E-07: Idempotent replay returns same payment."""
        from app.models.account_read_model import AccountReadModel
        from app.models.payee import Payee
        
        account = db_session.query(AccountReadModel).first()
        payee = db_session.query(Payee).first()
        
        payload = {
            "source_account_id": str(account.id),
            "payee_id": str(payee.id),
            "amount_minor": 50000,
            "currency": "GBP",
            "payment_reference": "Idempotent test"
        }
        
        # First call
        response1 = auth_client.post(
            "/api/v1/payments",
            json=payload,
            headers={"Idempotency-Key": "test-key-replay-001"}
        )
        assert response1.status_code == 201
        payment_id1 = response1.json()["payment_id"]
        
        # Second call with same key and body
        response2 = auth_client.post(
            "/api/v1/payments",
            json=payload,
            headers={"Idempotency-Key": "test-key-replay-001"}
        )
        assert response2.status_code == 201
        payment_id2 = response2.json()["payment_id"]
        
        # Should return same payment
        assert payment_id1 == payment_id2
    
    def test_create_payment_review_idempotency_key_reuse(self, auth_client, db_session):
        """Test E-07: Same key with different body returns 422."""
        from app.models.account_read_model import AccountReadModel
        from app.models.payee import Payee
        
        account = db_session.query(AccountReadModel).first()
        payee = db_session.query(Payee).first()
        
        # First call
        response1 = auth_client.post(
            "/api/v1/payments",
            json={
                "source_account_id": str(account.id),
                "payee_id": str(payee.id),
                "amount_minor": 100000,
                "currency": "GBP",
                "payment_reference": "First reference"
            },
            headers={"Idempotency-Key": "test-key-reuse-001"}
        )
        assert response1.status_code == 201
        
        # Second call with same key but different body
        response2 = auth_client.post(
            "/api/v1/payments",
            json={
                "source_account_id": str(account.id),
                "payee_id": str(payee.id),
                "amount_minor": 200000,  # Different amount
                "currency": "GBP",
                "payment_reference": "Second reference"  # Different reference
            },
            headers={"Idempotency-Key": "test-key-reuse-001"}
        )
        assert response2.status_code == 422
        error = response2.json()
        assert "idempotency" in error["detail"].lower()
    
    def test_create_payment_review_account_not_found(self, auth_client):
        """Test E-07: 404 when account not found."""
        response = auth_client.post(
            "/api/v1/payments",
            json={
                "source_account_id": str(uuid.uuid4()),
                "payee_id": str(uuid.uuid4()),
                "amount_minor": 100000,
                "currency": "GBP",
                "payment_reference": "Test"
            },
            headers={"Idempotency-Key": "test-key-not-found-001"}
        )
        
        assert response.status_code == 404
    
    def test_change_payment_review_success(self, auth_client, db_session):
        """Test E-10: Change payment review successfully."""
        from app.models.account_read_model import AccountReadModel
        from app.models.payee import Payee
        
        account = db_session.query(AccountReadModel).first()
        payee = db_session.query(Payee).first()
        
        # Create payment
        create_response = auth_client.post(
            "/api/v1/payments",
            json={
                "source_account_id": str(account.id),
                "payee_id": str(payee.id),
                "amount_minor": 100000,
                "currency": "GBP",
                "payment_reference": "Original reference"
            },
            headers={"Idempotency-Key": "test-key-change-001"}
        )
        assert create_response.status_code == 201
        payment_id = create_response.json()["payment_id"]
        
        # Change payment
        change_response = auth_client.patch(
            f"/api/v1/payments/{payment_id}",
            json={
                "expected_review_version": 1,
                "amount_minor": 150000,
                "payment_reference": "Updated reference"
            }
        )
        assert change_response.status_code == 200
        changed = change_response.json()
        
        assert changed["payment_id"] == payment_id
        assert changed["amount_minor"] == 150000
        assert changed["payment_reference"] == "Updated reference"
        assert changed["review_version"] == 2
        assert changed["current_state"] == "review_ready"
    
    def test_change_payment_review_version_mismatch(self, auth_client, db_session):
        """Test E-10: 409 when expected version doesn't match."""
        from app.models.account_read_model import AccountReadModel
        from app.models.payee import Payee
        
        account = db_session.query(AccountReadModel).first()
        payee = db_session.query(Payee).first()
        
        # Create payment
        create_response = auth_client.post(
            "/api/v1/payments",
            json={
                "source_account_id": str(account.id),
                "payee_id": str(payee.id),
                "amount_minor": 100000,
                "currency": "GBP",
                "payment_reference": "Test"
            },
            headers={"Idempotency-Key": "test-key-mismatch-001"}
        )
        assert create_response.status_code == 201
        payment_id = create_response.json()["payment_id"]
        
        # Try to change with wrong version
        change_response = auth_client.patch(
            f"/api/v1/payments/{payment_id}",
            json={
                "expected_review_version": 99,  # Wrong version
                "amount_minor": 150000
            }
        )
        assert change_response.status_code == 409
        error = change_response.json()
        assert "changed" in error["detail"].lower()
    
    def test_change_payment_review_payment_not_found(self, auth_client):
        """Test E-10: 404 when payment not found."""
        response = auth_client.patch(
            f"/api/v1/payments/{uuid.uuid4()}",
            json={
                "expected_review_version": 1,
                "amount_minor": 150000
            }
        )
        
        assert response.status_code == 404
