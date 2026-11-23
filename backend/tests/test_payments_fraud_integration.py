"""
Integration tests for fraud checks and warning handling.
Requirement: REQ-PAY-006, REQ-PAY-007
"""
import uuid

from app.models.audit_event import AuditEvent
from app.models.scam_check_outcome import ScamCheckOutcome


def test_e11_fraud_allow_moves_to_submission(auth_client, db_session):
    """Test E-11: fraud allow decision moves payment to submission_in_progress."""
    # Get actual account and payee from seed data
    from app.models.account_read_model import AccountReadModel
    from app.models.payee import Payee
    
    account = db_session.query(AccountReadModel).first()
    payee = db_session.query(Payee).first()
    
    # Create a payment review (E-07)
    create_response = auth_client.post(
        "/api/v1/payments",
        json={
            "source_account_id": str(account.id),
            "payee_id": str(payee.id),
            "amount_minor": 50000,  # £500 - will trigger 'allow'
            "currency": "GBP",
            "payment_reference": "Test ref allow"
        },
        headers={"Idempotency-Key": f"test-allow-{uuid.uuid4()}"}
    )
    assert create_response.status_code == 201
    payment_id = create_response.json()["payment_id"]
    
    # Submit payment (E-11)
    submit_response = auth_client.post(
        f"/api/v1/payments/{payment_id}/submit",
        json={
            "review_version": 1,
            "review_fingerprint": create_response.json()["review_fingerprint"],
            "approval": {
                "method": "passcode",
                "passcode": "Pass1234"  # Seed passcode
            }
        },
        headers={"Idempotency-Key": f"test-submit-allow-{uuid.uuid4()}"}
    )
    
    assert submit_response.status_code == 200
    result = submit_response.json()
    
    # Verify payment moved to submission_in_progress (allow path)
    assert result["current_state"] == "submission_in_progress"
    assert result["is_submitted"] is True
    assert result["customer_visible_status"] == "Pending"
    assert result["do_not_resubmit"] is True
    
    # Verify scam_check_outcome created with allow
    scam_outcome = db_session.query(ScamCheckOutcome).filter_by(
        payment_intent_id=uuid.UUID(payment_id),
        review_version=1
    ).first()
    assert scam_outcome is not None
    assert scam_outcome.risk_outcome == "allow"
    assert scam_outcome.customer_warning_required is False


def test_e11_fraud_warn_presents_warning(auth_client, db_session):
    """Test E-11: fraud warn decision presents warning to customer."""
    # Get actual account and payee from seed data
    from app.models.account_read_model import AccountReadModel
    from app.models.payee import Payee
    
    account = db_session.query(AccountReadModel).first()
    payee = db_session.query(Payee).first()
    
    # Create payment review
    create_response = auth_client.post(
        "/api/v1/payments",
        json={
            "source_account_id": str(account.id),
            "payee_id": str(payee.id),
            "amount_minor": 600000,  # £6000 - will trigger 'warn' with continue allowed
            "currency": "GBP",
            "payment_reference": "Test ref warn"
        },
        headers={"Idempotency-Key": f"test-warn-{uuid.uuid4()}"}
    )
    assert create_response.status_code == 201
    payment_id = create_response.json()["payment_id"]
    
    # Submit payment
    submit_response = auth_client.post(
        f"/api/v1/payments/{payment_id}/submit",
        json={
            "review_version": 1,
            "review_fingerprint": create_response.json()["review_fingerprint"],
            "approval": {
                "method": "passcode",
                "passcode": "Pass1234"
            }
        },
        headers={"Idempotency-Key": f"test-submit-warn-{uuid.uuid4()}"}
    )
    
    assert submit_response.status_code == 200
    result = submit_response.json()
    
    # Verify payment in warning_presented state
    assert result["current_state"] == "warning_presented"
    assert result["next_action"] == "acknowledge_warning"
    assert result["is_submitted"] is False
    
    # Verify warning details present
    assert result["warning"] is not None
    assert result["warning"]["heading"] == "Warning: This payment may be unsafe"
    assert "stop" in result["warning"]["allowed_actions"]
    assert "continue" in result["warning"]["allowed_actions"]
    assert result["warning"]["policy_allows_continue"] is True
    
    # Verify scam_check_outcome created
    scam_outcome = db_session.query(ScamCheckOutcome).filter_by(
        payment_intent_id=uuid.UUID(payment_id),
        review_version=1
    ).first()
    assert scam_outcome is not None
    assert scam_outcome.risk_outcome == "warn"
    assert scam_outcome.customer_warning_required is True
    assert scam_outcome.policy_allows_continue is True
    assert scam_outcome.customer_decision == "pending"
    assert scam_outcome.customer_warning_presented_at is not None


def test_e11_fraud_hold_moves_to_held_state(auth_client, db_session):
    """Test E-11: fraud hold decision moves payment to held_for_review."""
    # Get actual account and payee from seed data
    from app.models.account_read_model import AccountReadModel
    from app.models.payee import Payee
    
    account = db_session.query(AccountReadModel).first()
    payee = db_session.query(Payee).first()
    
    # Create payment review
    create_response = auth_client.post(
        "/api/v1/payments",
        json={
            "source_account_id": str(account.id),
            "payee_id": str(payee.id),
            "amount_minor": 1500000,  # £15,000 - will trigger 'hold'
            "currency": "GBP",
            "payment_reference": "Test ref hold"
        },
        headers={"Idempotency-Key": f"test-hold-{uuid.uuid4()}"}
    )
    assert create_response.status_code == 201
    payment_id = create_response.json()["payment_id"]
    
    # Submit payment
    submit_response = auth_client.post(
        f"/api/v1/payments/{payment_id}/submit",
        json={
            "review_version": 1,
            "review_fingerprint": create_response.json()["review_fingerprint"],
            "approval": {
                "method": "passcode",
                "passcode": "Pass1234"
            }
        },
        headers={"Idempotency-Key": f"test-submit-hold-{uuid.uuid4()}"}
    )
    
    assert submit_response.status_code == 200
    result = submit_response.json()
    
    # Verify payment in held_for_review state
    assert result["current_state"] == "held_for_review"
    assert result["customer_visible_status"] == "Pending"
    assert result["do_not_resubmit"] is True
    assert result["is_submitted"] is True
    assert result["hold_latest_decision_at"] is not None
    
    # Verify scam_check_outcome created with hold
    scam_outcome = db_session.query(ScamCheckOutcome).filter_by(
        payment_intent_id=uuid.UUID(payment_id),
        review_version=1
    ).first()
    assert scam_outcome is not None
    assert scam_outcome.risk_outcome == "hold"
    assert scam_outcome.hold_latest_decision_at is not None


def test_e12_warning_decision_stop_leaves_unexecuted(auth_client, db_session):
    """Test E-12: stop warning decision leaves payment unexecuted."""
    # Get actual account and payee from seed data
    from app.models.account_read_model import AccountReadModel
    from app.models.payee import Payee
    
    account = db_session.query(AccountReadModel).first()
    payee = db_session.query(Payee).first()
    
    # Create and submit payment to get warning
    create_response = auth_client.post(
        "/api/v1/payments",
        json={
            "source_account_id": str(account.id),
            "payee_id": str(payee.id),
            "amount_minor": 600000,  # Triggers warning
            "currency": "GBP",
            "payment_reference": "Test stop"
        },
        headers={"Idempotency-Key": f"test-stop-{uuid.uuid4()}"}
    )
    payment_id = create_response.json()["payment_id"]
    
    auth_client.post(
        f"/api/v1/payments/{payment_id}/submit",
        json={
            "review_version": 1,
            "review_fingerprint": create_response.json()["review_fingerprint"],
            "approval": {"method": "passcode", "passcode": "Pass1234"}
        },
        headers={"Idempotency-Key": f"test-submit-stop-{uuid.uuid4()}"}
    )
    
    # Record stop decision (E-12)
    decision_response = auth_client.post(
        f"/api/v1/payments/{payment_id}/warning-decision",
        json={
            "review_version": 1,
            "decision": "stop"
        }
    )
    
    assert decision_response.status_code == 200
    result = decision_response.json()
    
    # Verify payment stopped
    assert result["current_state"] == "stopped_after_warning"
    assert result["is_submitted"] is False
    assert "not sent" in result["status_message"].lower()
    
    # Verify scam_check_outcome updated
    scam_outcome = db_session.query(ScamCheckOutcome).filter_by(
        payment_intent_id=uuid.UUID(payment_id),
        review_version=1
    ).first()
    assert scam_outcome.customer_decision == "stopped"
    assert scam_outcome.customer_decision_at is not None


def test_e12_warning_decision_continue_moves_to_submission(auth_client, db_session):
    """Test E-12: continue warning decision (when allowed) moves to submission."""
    # Get actual account and payee from seed data
    from app.models.account_read_model import AccountReadModel
    from app.models.payee import Payee
    
    account = db_session.query(AccountReadModel).first()
    payee = db_session.query(Payee).first()
    
    # Create and submit payment to get warning
    create_response = auth_client.post(
        "/api/v1/payments",
        json={
            "source_account_id": str(account.id),
            "payee_id": str(payee.id),
            "amount_minor": 600000,  # Triggers warning with continue allowed
            "currency": "GBP",
            "payment_reference": "Test continue"
        },
        headers={"Idempotency-Key": f"test-continue-{uuid.uuid4()}"}
    )
    payment_id = create_response.json()["payment_id"]
    
    auth_client.post(
        f"/api/v1/payments/{payment_id}/submit",
        json={
            "review_version": 1,
            "review_fingerprint": create_response.json()["review_fingerprint"],
            "approval": {"method": "passcode", "passcode": "Pass1234"}
        },
        headers={"Idempotency-Key": f"test-submit-continue-{uuid.uuid4()}"}
    )
    
    # Record continue decision (E-12)
    decision_response = auth_client.post(
        f"/api/v1/payments/{payment_id}/warning-decision",
        json={
            "review_version": 1,
            "decision": "continue"
        }
    )
    
    assert decision_response.status_code == 200
    result = decision_response.json()
    
    # Verify payment moved to submission
    assert result["current_state"] == "submission_in_progress"
    assert result["is_submitted"] is True
    assert result["customer_visible_status"] == "Pending"
    
    # Verify scam_check_outcome updated
    scam_outcome = db_session.query(ScamCheckOutcome).filter_by(
        payment_intent_id=uuid.UUID(payment_id),
        review_version=1
    ).first()
    assert scam_outcome.customer_decision == "continued"
    assert scam_outcome.customer_decision_at is not None
    
    # Verify audit event written for warning traversal
    audit_event = db_session.query(AuditEvent).filter_by(
        event_type="payment.warning_traversed",
        resource_reference=str(payment_id)
    ).first()
    assert audit_event is not None
    assert audit_event.action_detail == "warning_continued"


def test_e12_warning_decision_continue_not_allowed_returns_403(auth_client, db_session):
    """Test E-12: continue when not allowed returns 403."""
    # This would need a scenario where policy_allows_continue is False
    # For now, this is a placeholder test showing the expected behavior


def test_e12_warning_decision_wrong_state_returns_400(auth_client, db_session):
    """Test E-12: warning decision in wrong state returns 400."""
    # Get actual account and payee from seed data
    from app.models.account_read_model import AccountReadModel
    from app.models.payee import Payee
    
    account = db_session.query(AccountReadModel).first()
    payee = db_session.query(Payee).first()
    
    # Create payment in review_ready state
    create_response = auth_client.post(
        "/api/v1/payments",
        json={
            "source_account_id": str(account.id),
            "payee_id": str(payee.id),
            "amount_minor": 50000,
            "currency": "GBP",
            "payment_reference": "Test wrong state"
        },
        headers={"Idempotency-Key": f"test-wrong-state-{uuid.uuid4()}"}
    )
    payment_id = create_response.json()["payment_id"]
    
    # Try to record warning decision without being in warning_presented state
    decision_response = auth_client.post(
        f"/api/v1/payments/{payment_id}/warning-decision",
        json={
            "review_version": 1,
            "decision": "stop"
        }
    )
    
    assert decision_response.status_code == 400
    assert "not valid for current payment state" in decision_response.json()["detail"].lower()
