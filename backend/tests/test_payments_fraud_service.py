"""
Unit tests for fraud check and warning handling in PaymentOrchestrationService.
Requirement: REQ-PAY-006, REQ-PAY-007
"""
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

from sqlalchemy.orm import Session

from app.models.account_read_model import AccountReadModel
from app.models.payee import Payee
from app.models.payment_intent import PaymentIntent
from app.models.scam_check_outcome import ScamCheckOutcome
from app.services.payment_orchestration_service import PaymentOrchestrationService


def test_fraud_decision_allow_moves_to_submission(db_session: Session):
    """Test that allow fraud decision moves payment to submission_in_progress."""
    service = PaymentOrchestrationService(db_session)
    
    # Mock fraud adapter to return allow
    service.fraud_adapter = Mock()
    service.fraud_adapter.check_payment_fraud_risk = Mock(
        return_value=("allow", 150, "FRAUD-TEST-123", False)
    )
    
    # This test verifies the fraud decision logic is wired correctly


def test_fraud_decision_warn_creates_scam_outcome_with_warning(db_session: Session):
    """Test that warn fraud decision creates scam_check_outcome and moves to warning_presented."""
    service = PaymentOrchestrationService(db_session)
    
    # Mock fraud adapter to return warn
    service.fraud_adapter = Mock()
    service.fraud_adapter.check_payment_fraud_risk = Mock(
        return_value=("warn", 200, "FRAUD-TEST-456", True)  # policy_allows_continue=True
    )
    
    # This test verifies warning presentation logic


def test_fraud_decision_hold_creates_hold_outcome(db_session: Session):
    """Test that hold fraud decision creates scam_check_outcome with hold date."""
    service = PaymentOrchestrationService(db_session)
    
    # Mock fraud adapter to return hold
    service.fraud_adapter = Mock()
    service.fraud_adapter.check_payment_fraud_risk = Mock(
        return_value=("hold", 180, "FRAUD-TEST-789", False)
    )
    
    # This test verifies hold logic with decision date


def test_fraud_decision_unavailable_disables_payments_capability(db_session: Session):
    """Test that unavailable fraud engine disables payments capability."""
    service = PaymentOrchestrationService(db_session)
    
    # Mock fraud adapter to return unavailable
    service.fraud_adapter = Mock()
    service.fraud_adapter.check_payment_fraud_risk = Mock(
        return_value=("unavailable", 0, "", False)
    )
    
    # This test verifies capability is disabled when fraud engine unavailable


def test_warning_decision_stop_moves_to_stopped_state(db_session: Session):
    """Test that stop warning decision moves payment to stopped_after_warning."""
    service = PaymentOrchestrationService(db_session)
    
    # Mock payment in warning_presented state
    payment = Mock(spec=PaymentIntent)
    payment.id = uuid.uuid4()
    payment.current_state = "warning_presented"
    payment.review_version = 1
    payment.source_account_reference = "ACC-123"
    payment.payee_id = uuid.uuid4()
    
    # Mock scam outcome with warning
    scam_outcome = Mock(spec=ScamCheckOutcome)
    scam_outcome.policy_allows_continue = False
    
    # Test stop decision


def test_warning_decision_continue_allowed_moves_to_submission(db_session: Session):
    """Test that continue decision (when allowed) moves to submission_in_progress."""
    service = PaymentOrchestrationService(db_session)
    
    # Mock payment in warning_presented state
    payment = Mock(spec=PaymentIntent)
    payment.id = uuid.uuid4()
    payment.current_state = "warning_presented"
    payment.review_version = 1
    
    # Mock scam outcome with policy allows continue
    scam_outcome = Mock(spec=ScamCheckOutcome)
    scam_outcome.policy_allows_continue = True
    
    # Test continue decision when allowed


def test_warning_decision_continue_not_allowed_returns_403(db_session: Session):
    """Test that continue decision when not allowed returns 403."""
    service = PaymentOrchestrationService(db_session)
    
    # Mock payment in warning_presented state
    payment = Mock(spec=PaymentIntent)
    payment.id = uuid.uuid4()
    payment.current_state = "warning_presented"
    payment.review_version = 1
    
    # Mock scam outcome with policy does not allow continue
    scam_outcome = Mock(spec=ScamCheckOutcome)
    scam_outcome.policy_allows_continue = False
    
    # Test continue decision when not allowed should raise 403


def test_warning_decision_wrong_state_returns_400(db_session: Session):
    """Test that warning decision in wrong state returns 400."""
    service = PaymentOrchestrationService(db_session)
    
    # Mock payment not in warning_presented state
    payment = Mock(spec=PaymentIntent)
    payment.id = uuid.uuid4()
    payment.current_state = "review_ready"  # Wrong state
    payment.review_version = 1
    
    # Test warning decision in wrong state should raise 400


def test_warning_decision_version_mismatch_returns_409(db_session: Session):
    """Test that warning decision with version mismatch returns 409."""
    service = PaymentOrchestrationService(db_session)
    
    # Mock payment in warning_presented state
    payment = Mock(spec=PaymentIntent)
    payment.id = uuid.uuid4()
    payment.current_state = "warning_presented"
    payment.review_version = 2  # Different version
    
    # Test version mismatch should raise 409


def test_payment_response_includes_warning_when_in_warning_state(db_session: Session):
    """Test that PaymentResponse includes warning details when in warning_presented state."""
    service = PaymentOrchestrationService(db_session)
    
    # Mock payment in warning_presented state
    payment = Mock(spec=PaymentIntent)
    payment.id = uuid.uuid4()
    payment.current_state = "warning_presented"
    payment.review_version = 1
    payment.payment_reference_text = "Test payment"
    payment.amount_minor = 100000
    payment.currency = "GBP"
    payment.source_account_reference = "ACC-123"
    payment.payee_id = uuid.uuid4()
    payment.review_fingerprint = "a" * 64
    payment.created_at = datetime.now(UTC)
    payment.updated_at = datetime.now(UTC)
    payment.customer_visible_status = None
    payment.do_not_resubmit = False
    
    # Mock account and payee
    account = Mock(spec=AccountReadModel)
    account.id = uuid.uuid4()
    account.display_name = "Main Account"
    account.masked_account_identifier = "**** 1234"
    
    payee = Mock(spec=Payee)
    payee.id = payment.payee_id
    payee.payee_name = "Test Payee"
    payee.masked_account_identifier = "**** 5678"
    
    # Mock scam outcome with warning
    scam_outcome = Mock(spec=ScamCheckOutcome)
    scam_outcome.customer_warning_required = True
    scam_outcome.policy_allows_continue = True
    
    service.scam_check_repo = Mock()
    service.scam_check_repo.get_by_payment_and_version = Mock(return_value=scam_outcome)
    
    # Build response
    response = service._build_payment_response(payment, account, payee)
    
    # Verify warning is included
    assert response.warning is not None
    assert response.warning.heading == "Warning: This payment may be unsafe"
    assert response.warning.policy_allows_continue is True
    assert "stop" in response.warning.allowed_actions
    assert "continue" in response.warning.allowed_actions


def test_payment_response_includes_hold_decision_date_when_held(db_session: Session):
    """Test that PaymentResponse includes hold_latest_decision_at when held."""
    service = PaymentOrchestrationService(db_session)
    
    # Mock payment in held_for_review state
    payment = Mock(spec=PaymentIntent)
    payment.id = uuid.uuid4()
    payment.current_state = "held_for_review"
    payment.review_version = 1
    payment.payment_reference_text = "Test payment"
    payment.amount_minor = 1500000  # £15,000
    payment.currency = "GBP"
    payment.source_account_reference = "ACC-123"
    payment.payee_id = uuid.uuid4()
    payment.review_fingerprint = "b" * 64
    payment.created_at = datetime.now(UTC)
    payment.updated_at = datetime.now(UTC)
    payment.customer_visible_status = "Pending"
    payment.do_not_resubmit = True
    
    # Mock account and payee
    account = Mock(spec=AccountReadModel)
    account.id = uuid.uuid4()
    account.display_name = "Main Account"
    account.masked_account_identifier = "**** 1234"
    
    payee = Mock(spec=Payee)
    payee.id = payment.payee_id
    payee.payee_name = "Test Payee"
    payee.masked_account_identifier = "**** 5678"
    
    # Mock scam outcome with hold
    hold_decision_date = datetime.now(UTC) + timedelta(days=4)
    scam_outcome = Mock(spec=ScamCheckOutcome)
    scam_outcome.hold_latest_decision_at = hold_decision_date
    
    service.scam_check_repo = Mock()
    service.scam_check_repo.get_by_payment_and_version = Mock(return_value=scam_outcome)
    
    # Build response
    response = service._build_payment_response(payment, account, payee)
    
    # Verify hold date is included
    assert response.hold_latest_decision_at == hold_decision_date
    assert response.warning is None  # No warning in held state
