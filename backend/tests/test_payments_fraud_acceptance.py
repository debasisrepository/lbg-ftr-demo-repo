"""
Acceptance tests for FR-PAY-009 and FR-PAY-010 acceptance criteria.
Requirement: REQ-PAY-006, REQ-PAY-007
"""
import uuid

from app.models.scam_check_outcome import ScamCheckOutcome


def test_fr_pay_009_ac1_payment_journey_can_present_risk_warning(auth_client, db_session):
    """
    FR-PAY-009 AC1: A payment journey can present a risk warning before execution
    when scam or fraud controls require it.
    """
    # Get actual account and payee from seed data
    from app.models.account_read_model import AccountReadModel
    from app.models.payee import Payee
    
    account = db_session.query(AccountReadModel).first()
    payee = db_session.query(Payee).first()
    
    # Create and submit payment that triggers warning
    create_response = auth_client.post(
        "/api/v1/payments",
        json={
            "source_account_id": str(account.id),
            "payee_id": str(payee.id),
            "amount_minor": 600000,  # Triggers warning
            "currency": "GBP",
            "payment_reference": "AC1 test"
        },
        headers={"Idempotency-Key": f"ac1-{uuid.uuid4()}"}
    )
    payment_id = create_response.json()["payment_id"]
    
    submit_response = auth_client.post(
        f"/api/v1/payments/{payment_id}/submit",
        json={
            "review_version": 1,
            "review_fingerprint": create_response.json()["review_fingerprint"],
            "approval": {"method": "passcode", "passcode": "Pass1234"}
        },
        headers={"Idempotency-Key": f"ac1-submit-{uuid.uuid4()}"}
    )
    
    result = submit_response.json()
    
    # Verify warning presented before execution
    assert result["current_state"] == "warning_presented"
    assert result["is_submitted"] is False  # Not executed yet
    assert result["warning"] is not None


def test_fr_pay_009_ac2_warning_content_makes_clear_payment_may_be_unsafe(auth_client, db_session):
    """
    FR-PAY-009 AC2: Warning content makes clear that the payment may be unsafe
    and requires a conscious customer decision or stop action under governed flow rules.
    """
    # Get actual account and payee from seed data
    from app.models.account_read_model import AccountReadModel
    from app.models.payee import Payee
    
    account = db_session.query(AccountReadModel).first()
    payee = db_session.query(Payee).first()
    
    # Create and submit payment that triggers warning
    create_response = auth_client.post(
        "/api/v1/payments",
        json={
            "source_account_id": str(account.id),
            "payee_id": str(payee.id),
            "amount_minor": 600000,
            "currency": "GBP",
            "payment_reference": "AC2 test"
        },
        headers={"Idempotency-Key": f"ac2-{uuid.uuid4()}"}
    )
    payment_id = create_response.json()["payment_id"]
    
    submit_response = auth_client.post(
        f"/api/v1/payments/{payment_id}/submit",
        json={
            "review_version": 1,
            "review_fingerprint": create_response.json()["review_fingerprint"],
            "approval": {"method": "passcode", "passcode": "Pass1234"}
        },
        headers={"Idempotency-Key": f"ac2-submit-{uuid.uuid4()}"}
    )
    
    warning = submit_response.json()["warning"]
    
    # Verify warning content is clear
    assert warning["heading"] is not None
    assert "unsafe" in warning["heading"].lower() or "unsafe" in warning["body"].lower()
    assert len(warning["body"]) > 0
    assert len(warning["allowed_actions"]) > 0
    assert "stop" in warning["allowed_actions"]  # Stop is always allowed


def test_fr_pay_009_ac3_payment_does_not_bypass_mandatory_warning(auth_client, db_session):
    """
    FR-PAY-009 AC3: A payment does not silently bypass mandatory warning presentation
    when the risk service indicates customer friction is required.
    """
    # Get actual account and payee from seed data
    from app.models.account_read_model import AccountReadModel
    from app.models.payee import Payee
    
    account = db_session.query(AccountReadModel).first()
    payee = db_session.query(Payee).first()
    
    # Create and submit payment that triggers warning
    create_response = auth_client.post(
        "/api/v1/payments",
        json={
            "source_account_id": str(account.id),
            "payee_id": str(payee.id),
            "amount_minor": 600000,  # Must trigger warning
            "currency": "GBP",
            "payment_reference": "AC3 test"
        },
        headers={"Idempotency-Key": f"ac3-{uuid.uuid4()}"}
    )
    payment_id = create_response.json()["payment_id"]
    
    submit_response = auth_client.post(
        f"/api/v1/payments/{payment_id}/submit",
        json={
            "review_version": 1,
            "review_fingerprint": create_response.json()["review_fingerprint"],
            "approval": {"method": "passcode", "passcode": "Pass1234"}
        },
        headers={"Idempotency-Key": f"ac3-submit-{uuid.uuid4()}"}
    )
    
    # Verify payment is NOT in submission or completed state
    # It must be in warning_presented state
    assert submit_response.json()["current_state"] == "warning_presented"
    assert submit_response.json()["is_submitted"] is False
    
    # Verify no way to bypass - must use E-12 to proceed
    # Cannot GET /api/v1/payments/{id}/submit again to skip warning


def test_fr_pay_009_ac4_warning_presentation_remains_accessible(auth_client, db_session):
    """
    FR-PAY-009 AC4: Warning presentation remains accessible and understandable.
    """
    # Get actual account and payee from seed data
    from app.models.account_read_model import AccountReadModel
    from app.models.payee import Payee
    
    account = db_session.query(AccountReadModel).first()
    payee = db_session.query(Payee).first()
    
    # Create and submit payment that triggers warning
    create_response = auth_client.post(
        "/api/v1/payments",
        json={
            "source_account_id": str(account.id),
            "payee_id": str(payee.id),
            "amount_minor": 600000,
            "currency": "GBP",
            "payment_reference": "AC4 test"
        },
        headers={"Idempotency-Key": f"ac4-{uuid.uuid4()}"}
    )
    payment_id = create_response.json()["payment_id"]
    
    submit_response = auth_client.post(
        f"/api/v1/payments/{payment_id}/submit",
        json={
            "review_version": 1,
            "review_fingerprint": create_response.json()["review_fingerprint"],
            "approval": {"method": "passcode", "passcode": "Pass1234"}
        },
        headers={"Idempotency-Key": f"ac4-submit-{uuid.uuid4()}"}
    )
    
    warning = submit_response.json()["warning"]
    
    # Verify warning is accessible (all required fields present)
    assert "heading" in warning
    assert "body" in warning
    assert "allowed_actions" in warning
    assert "policy_allows_continue" in warning
    
    # Verify understandable (plain language, not technical)
    assert len(warning["heading"]) > 0
    assert len(warning["body"]) > 10  # Meaningful message


def test_fr_pay_010_ac1_customer_shown_available_next_steps(auth_client, db_session):
    """
    FR-PAY-010 AC1: After a warning is presented, the customer is shown
    the available next steps defined by the governed warning outcome.
    """
    # Get actual account and payee from seed data
    from app.models.account_read_model import AccountReadModel
    from app.models.payee import Payee
    
    account = db_session.query(AccountReadModel).first()
    payee = db_session.query(Payee).first()
    
    # Create and submit payment that triggers warning
    create_response = auth_client.post(
        "/api/v1/payments",
        json={
            "source_account_id": str(account.id),
            "payee_id": str(payee.id),
            "amount_minor": 600000,
            "currency": "GBP",
            "payment_reference": "AC1 test"
        },
        headers={"Idempotency-Key": f"010-ac1-{uuid.uuid4()}"}
    )
    payment_id = create_response.json()["payment_id"]
    
    submit_response = auth_client.post(
        f"/api/v1/payments/{payment_id}/submit",
        json={
            "review_version": 1,
            "review_fingerprint": create_response.json()["review_fingerprint"],
            "approval": {"method": "passcode", "passcode": "Pass1234"}
        },
        headers={"Idempotency-Key": f"010-ac1-submit-{uuid.uuid4()}"}
    )
    
    result = submit_response.json()
    
    # Verify next_action is set
    assert result["next_action"] == "acknowledge_warning"
    
    # Verify allowed_actions list shows what customer can do
    assert "stop" in result["warning"]["allowed_actions"]
    
    # Verify policy_allows_continue tells customer if continue is option
    assert isinstance(result["warning"]["policy_allows_continue"], bool)


def test_fr_pay_010_ac2_choosing_not_to_continue_leaves_unexecuted(auth_client, db_session):
    """
    FR-PAY-010 AC2: Choosing not to continue leaves the payment unexecuted.
    """
    # Get actual account and payee from seed data
    from app.models.account_read_model import AccountReadModel
    from app.models.payee import Payee
    
    account = db_session.query(AccountReadModel).first()
    payee = db_session.query(Payee).first()
    
    # Create and submit payment that triggers warning
    create_response = auth_client.post(
        "/api/v1/payments",
        json={
            "source_account_id": str(account.id),
            "payee_id": str(payee.id),
            "amount_minor": 600000,
            "currency": "GBP",
            "payment_reference": "AC2 test"
        },
        headers={"Idempotency-Key": f"010-ac2-{uuid.uuid4()}"}
    )
    payment_id = create_response.json()["payment_id"]
    
    auth_client.post(
        f"/api/v1/payments/{payment_id}/submit",
        json={
            "review_version": 1,
            "review_fingerprint": create_response.json()["review_fingerprint"],
            "approval": {"method": "passcode", "passcode": "Pass1234"}
        },
        headers={"Idempotency-Key": f"010-ac2-submit-{uuid.uuid4()}"}
    )
    
    # Choose to stop
    decision_response = auth_client.post(
        f"/api/v1/payments/{payment_id}/warning-decision",
        json={"review_version": 1, "decision": "stop"}
    )
    
    result = decision_response.json()
    
    # Verify payment unexecuted
    assert result["is_submitted"] is False
    assert result["current_state"] == "stopped_after_warning"
    assert "not sent" in result["status_message"].lower()


def test_fr_pay_010_ac3_continuation_records_warning_traversal(auth_client, db_session):
    """
    FR-PAY-010 AC3: Where customer continuation is allowed, the journey records
    that the warning path was traversed before execution continues.
    """
    # Get actual account and payee from seed data
    from app.models.account_read_model import AccountReadModel
    from app.models.payee import Payee
    
    account = db_session.query(AccountReadModel).first()
    payee = db_session.query(Payee).first()
    
    # Create and submit payment that triggers warning with continue allowed
    create_response = auth_client.post(
        "/api/v1/payments",
        json={
            "source_account_id": str(account.id),
            "payee_id": str(payee.id),
            "amount_minor": 600000,  # Triggers warning with continue allowed
            "currency": "GBP",
            "payment_reference": "AC3 test"
        },
        headers={"Idempotency-Key": f"010-ac3-{uuid.uuid4()}"}
    )
    payment_id = create_response.json()["payment_id"]
    
    auth_client.post(
        f"/api/v1/payments/{payment_id}/submit",
        json={
            "review_version": 1,
            "review_fingerprint": create_response.json()["review_fingerprint"],
            "approval": {"method": "passcode", "passcode": "Pass1234"}
        },
        headers={"Idempotency-Key": f"010-ac3-submit-{uuid.uuid4()}"}
    )
    
    # Choose to continue
    decision_response = auth_client.post(
        f"/api/v1/payments/{payment_id}/warning-decision",
        json={"review_version": 1, "decision": "continue"}
    )
    
    result = decision_response.json()
    
    # Verify execution continued
    assert result["current_state"] == "submission_in_progress"
    assert result["is_submitted"] is True
    
    # Verify warning traversal recorded in scam_check_outcome
    scam_outcome = db_session.query(ScamCheckOutcome).filter_by(
        payment_intent_id=uuid.UUID(payment_id),
        review_version=1
    ).first()
    assert scam_outcome.customer_decision == "continued"
    assert scam_outcome.customer_decision_at is not None


def test_fr_pay_010_ac4_stopped_warned_payment_not_shown_as_sent(auth_client, db_session):
    """
    FR-PAY-010 AC4: The app does not give the impression that a stopped
    warned payment was sent.
    """
    # Get actual account and payee from seed data
    from app.models.account_read_model import AccountReadModel
    from app.models.payee import Payee
    
    account = db_session.query(AccountReadModel).first()
    payee = db_session.query(Payee).first()
    
    # Create and submit payment that triggers warning
    create_response = auth_client.post(
        "/api/v1/payments",
        json={
            "source_account_id": str(account.id),
            "payee_id": str(payee.id),
            "amount_minor": 600000,
            "currency": "GBP",
            "payment_reference": "AC4 test"
        },
        headers={"Idempotency-Key": f"010-ac4-{uuid.uuid4()}"}
    )
    payment_id = create_response.json()["payment_id"]
    
    auth_client.post(
        f"/api/v1/payments/{payment_id}/submit",
        json={
            "review_version": 1,
            "review_fingerprint": create_response.json()["review_fingerprint"],
            "approval": {"method": "passcode", "passcode": "Pass1234"}
        },
        headers={"Idempotency-Key": f"010-ac4-submit-{uuid.uuid4()}"}
    )
    
    # Choose to stop
    decision_response = auth_client.post(
        f"/api/v1/payments/{payment_id}/warning-decision",
        json={"review_version": 1, "decision": "stop"}
    )
    
    result = decision_response.json()
    
    # Verify NOT shown as sent
    assert result["customer_visible_status"] is None  # Not Sent, Pending, or Failed
    assert result["is_submitted"] is False
    assert "not sent" in result["status_message"].lower()
    
    # Double-check by getting payment status
    get_response = auth_client.get(f"/api/v1/payments/{payment_id}")
    get_result = get_response.json()
    assert get_result["customer_visible_status"] is None
    assert get_result["is_submitted"] is False
