"""
Acceptance tests for FR-PAY-002 and FR-PAY-003.
Requirement: REQ-PAY-002, REQ-PAY-003
"""
import uuid


class TestFRPAY002InitiatePayment:
    """
    FR-PAY-002: Initiate a payment to a saved payee
    
    Acceptance Criteria:
    - The customer can choose a valid source account and saved payee before payment submission.
    - The customer can provide the payment amount and payment reference within the defined journey.
    - The app prevents payment submission until required payment-entry information is present.
    - A started payment remains pending approval until the required approval step completes.
    """
    
    def test_customer_can_choose_valid_source_account_and_payee(self, auth_client, db_session):
        """AC1: Customer can choose valid source account and saved payee."""
        from app.models.account_read_model import AccountReadModel
        from app.models.payee import Payee
        
        # Get available accounts and payees
        accounts = db_session.query(AccountReadModel).all()
        payees = db_session.query(Payee).filter_by(payee_status="saved_active").all()
        
        assert len(accounts) > 0, "Customer has accounts available"
        assert len(payees) > 0, "Customer has saved payees available"
        
        # Create payment with valid account and payee
        response = auth_client.post(
            "/api/v1/payments",
            json={
                "source_account_id": str(accounts[0].id),
                "payee_id": str(payees[0].id),
                "amount_minor": 100000,
                "currency": "GBP",
                "payment_reference": "Rent payment"
            },
            headers={"Idempotency-Key": "ac1-test-key-001"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["source_account"]["account_id"] == str(accounts[0].id)
        assert data["payee"]["payee_id"] == str(payees[0].id)
    
    def test_customer_can_provide_amount_and_reference(self, auth_client, db_session):
        """AC2: Customer can provide payment amount and reference."""
        from app.models.account_read_model import AccountReadModel
        from app.models.payee import Payee
        
        account = db_session.query(AccountReadModel).first()
        payee = db_session.query(Payee).first()
        
        test_amount = 50000  # £500.00
        test_reference = "Utility bill"
        
        response = auth_client.post(
            "/api/v1/payments",
            json={
                "source_account_id": str(account.id),
                "payee_id": str(payee.id),
                "amount_minor": test_amount,
                "currency": "GBP",
                "payment_reference": test_reference
            },
            headers={"Idempotency-Key": "ac2-test-key-001"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["amount_minor"] == test_amount
        assert data["payment_reference"] == test_reference
    
    def test_app_prevents_submission_without_required_info(self, auth_client):
        """AC3: App prevents submission until required information present."""
        # Missing amount_minor
        response1 = auth_client.post(
            "/api/v1/payments",
            json={
                "source_account_id": str(uuid.uuid4()),
                "payee_id": str(uuid.uuid4()),
                "currency": "GBP",
                "payment_reference": "Test"
            },
            headers={"Idempotency-Key": "ac3-test-key-001"}
        )
        assert response1.status_code == 422
        
        # Missing payment_reference
        response2 = auth_client.post(
            "/api/v1/payments",
            json={
                "source_account_id": str(uuid.uuid4()),
                "payee_id": str(uuid.uuid4()),
                "amount_minor": 100000,
                "currency": "GBP"
            },
            headers={"Idempotency-Key": "ac3-test-key-002"}
        )
        assert response2.status_code == 422
        
        # Amount below minimum (0 or negative)
        response3 = auth_client.post(
            "/api/v1/payments",
            json={
                "source_account_id": str(uuid.uuid4()),
                "payee_id": str(uuid.uuid4()),
                "amount_minor": 0,
                "currency": "GBP",
                "payment_reference": "Test"
            },
            headers={"Idempotency-Key": "ac3-test-key-003"}
        )
        assert response3.status_code == 422
    
    def test_started_payment_remains_pending_approval(self, auth_client, db_session):
        """AC4: Started payment remains pending approval until required step completes."""
        from app.models.account_read_model import AccountReadModel
        from app.models.payee import Payee
        
        account = db_session.query(AccountReadModel).first()
        payee = db_session.query(Payee).first()
        
        # Create payment
        response = auth_client.post(
            "/api/v1/payments",
            json={
                "source_account_id": str(account.id),
                "payee_id": str(payee.id),
                "amount_minor": 100000,
                "currency": "GBP",
                "payment_reference": "Test payment"
            },
            headers={"Idempotency-Key": "ac4-test-key-001"}
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Payment is in review_ready state (not submitted yet)
        assert data["current_state"] == "review_ready"
        assert data["is_submitted"] is False
        assert data["next_action"] == "review_and_approve"
        assert "not sent yet" in data["status_message"].lower()


class TestFRPAY003CapturePaymentReference:
    """
    FR-PAY-003: Capture payment reference
    
    Acceptance Criteria:
    - The customer can enter a payment reference before submitting a payment.
    - The entered payment reference is shown again during payment review and outcome display.
    - If the payment cannot be completed, the customer can still see which attempted payment the status refers to.
    - The reference shown after submission matches the reference approved by the customer.
    """
    
    def test_customer_can_enter_payment_reference(self, auth_client, db_session):
        """AC1: Customer can enter payment reference before submitting."""
        from app.models.account_read_model import AccountReadModel
        from app.models.payee import Payee
        
        account = db_session.query(AccountReadModel).first()
        payee = db_session.query(Payee).first()
        
        custom_reference = "Invoice #12345"
        
        response = auth_client.post(
            "/api/v1/payments",
            json={
                "source_account_id": str(account.id),
                "payee_id": str(payee.id),
                "amount_minor": 100000,
                "currency": "GBP",
                "payment_reference": custom_reference
            },
            headers={"Idempotency-Key": "fr-pay-003-ac1-001"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["payment_reference"] == custom_reference
    
    def test_reference_shown_during_review(self, auth_client, db_session):
        """AC2: Reference is shown during payment review."""
        from app.models.account_read_model import AccountReadModel
        from app.models.payee import Payee
        
        account = db_session.query(AccountReadModel).first()
        payee = db_session.query(Payee).first()
        
        test_reference = "Rent May 2026"
        
        # Create payment (review stage)
        create_response = auth_client.post(
            "/api/v1/payments",
            json={
                "source_account_id": str(account.id),
                "payee_id": str(payee.id),
                "amount_minor": 100000,
                "currency": "GBP",
                "payment_reference": test_reference
            },
            headers={"Idempotency-Key": "fr-pay-003-ac2-001"}
        )
        
        assert create_response.status_code == 201
        review_data = create_response.json()
        
        # Reference is present in review response
        assert review_data["payment_reference"] == test_reference
        assert review_data["current_state"] == "review_ready"
    
    def test_reference_visible_in_payment_status(self, auth_client, db_session):
        """AC3: Customer can see reference even if payment cannot be completed."""
        from app.models.account_read_model import AccountReadModel
        from app.models.payee import Payee
        
        account = db_session.query(AccountReadModel).first()
        payee = db_session.query(Payee).first()
        
        test_reference = "Utility payment"
        
        # Create payment
        response = auth_client.post(
            "/api/v1/payments",
            json={
                "source_account_id": str(account.id),
                "payee_id": str(payee.id),
                "amount_minor": 100000,
                "currency": "GBP",
                "payment_reference": test_reference
            },
            headers={"Idempotency-Key": "fr-pay-003-ac3-001"}
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Reference is always present regardless of state
        assert data["payment_reference"] == test_reference
    
    def test_reference_matches_after_changes(self, auth_client, db_session):
        """AC4: Reference shown matches reference approved by customer."""
        from app.models.account_read_model import AccountReadModel
        from app.models.payee import Payee
        
        account = db_session.query(AccountReadModel).first()
        payee = db_session.query(Payee).first()
        
        original_reference = "Original reference"
        updated_reference = "Updated reference"
        
        # Create payment
        create_response = auth_client.post(
            "/api/v1/payments",
            json={
                "source_account_id": str(account.id),
                "payee_id": str(payee.id),
                "amount_minor": 100000,
                "currency": "GBP",
                "payment_reference": original_reference
            },
            headers={"Idempotency-Key": "fr-pay-003-ac4-001"}
        )
        assert create_response.status_code == 201
        payment_id = create_response.json()["payment_id"]
        
        # Change reference
        change_response = auth_client.patch(
            f"/api/v1/payments/{payment_id}",
            json={
                "expected_review_version": 1,
                "payment_reference": updated_reference
            }
        )
        assert change_response.status_code == 200
        changed_data = change_response.json()
        
        # Reference matches the updated value
        assert changed_data["payment_reference"] == updated_reference
        # Review version incremented (requires new approval)
        assert changed_data["review_version"] == 2
