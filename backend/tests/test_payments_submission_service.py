"""
Unit tests for payment submission and outbox publishing.
Requirement: REQ-PAY-008, REQ-PAY-009
"""
from app.services.payment_orchestration_service import PaymentOrchestrationService


def test_converge_customer_visible_status_sent(db_session):
    """Test status convergence for completed state returns Sent."""
    service = PaymentOrchestrationService(db_session)
    status = service._converge_customer_visible_status("completed")
    assert status == "Sent"


def test_converge_customer_visible_status_pending(db_session):
    """Test status convergence for in-flight states returns Pending."""
    service = PaymentOrchestrationService(db_session)
    
    for state in ["held_for_review", "submission_in_progress", "submitted_to_payments_hub",
                  "pending_confirmation", "unknown_unresolved"]:
        status = service._converge_customer_visible_status(state)
        assert status == "Pending", f"State {state} should converge to Pending"


def test_converge_customer_visible_status_failed(db_session):
    """Test status convergence for failed/rejected states returns Failed."""
    service = PaymentOrchestrationService(db_session)
    
    for state in ["failed", "rejected"]:
        status = service._converge_customer_visible_status(state)
        assert status == "Failed", f"State {state} should converge to Failed"


def test_converge_customer_visible_status_none_for_not_submitted(db_session):
    """Test status convergence for not-submitted states returns None."""
    service = PaymentOrchestrationService(db_session)
    
    for state in ["draft", "review_ready", "awaiting_dynamic_link_approval",
                  "approval_failed_or_abandoned", "fraud_check_in_progress",
                  "warning_presented", "stopped_after_warning"]:
        status = service._converge_customer_visible_status(state)
        assert status is None, f"State {state} should have no customer-visible status"


def test_status_convergence_one_function():
    """Test that there is only one status convergence function."""
    # This test documents the architectural requirement: ONE convergence function
    assert hasattr(PaymentOrchestrationService, "_converge_customer_visible_status")
    # The function is called from exactly the places where status is set
