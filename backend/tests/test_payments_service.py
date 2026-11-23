"""
Unit tests for PaymentOrchestrationService.
Requirement: REQ-PAY-002, REQ-PAY-003
"""
import uuid

from app.services.payment_orchestration_service import PaymentOrchestrationService


class TestPaymentOrchestrationService:
    """Unit tests for payment orchestration service."""
    
    def test_compute_review_fingerprint(self, db_session):
        """Test review fingerprint computation is consistent."""
        service = PaymentOrchestrationService(db_session)
        
        source_ref = "ACC-TEST-001"
        payee_id = uuid.uuid4()
        amount = 100000
        currency = "GBP"
        reference = "Test payment"
        version = 1
        
        fingerprint1 = service._compute_review_fingerprint(
            source_ref, payee_id, amount, currency, reference, version
        )
        fingerprint2 = service._compute_review_fingerprint(
            source_ref, payee_id, amount, currency, reference, version
        )
        
        assert fingerprint1 == fingerprint2
        assert len(fingerprint1) == 64
        assert fingerprint1.isalnum()
    
    def test_compute_review_fingerprint_changes_with_version(self, db_session):
        """Test review fingerprint changes when version changes."""
        service = PaymentOrchestrationService(db_session)
        
        source_ref = "ACC-TEST-001"
        payee_id = uuid.uuid4()
        amount = 100000
        currency = "GBP"
        reference = "Test payment"
        
        fingerprint_v1 = service._compute_review_fingerprint(
            source_ref, payee_id, amount, currency, reference, 1
        )
        fingerprint_v2 = service._compute_review_fingerprint(
            source_ref, payee_id, amount, currency, reference, 2
        )
        
        assert fingerprint_v1 != fingerprint_v2
    
    def test_get_status_message_review_ready(self, db_session):
        """Test status message for review_ready state."""
        service = PaymentOrchestrationService(db_session)
        
        message = service._get_status_message("review_ready", False)
        assert "not sent yet" in message.lower()
        assert "review and approve" in message.lower()
    
    def test_get_status_message_held(self, db_session):
        """Test status message for held_for_review state."""
        service = PaymentOrchestrationService(db_session)
        
        message = service._get_status_message("held_for_review", True)
        assert "checking" in message.lower()
        assert "don't send this payment again" in message.lower()
    
    def test_get_next_action_review_ready(self, db_session):
        """Test next action for review_ready state."""
        service = PaymentOrchestrationService(db_session)
        
        action = service._get_next_action("review_ready")
        assert action == "review_and_approve"
    
    def test_get_next_action_held(self, db_session):
        """Test next action for held state."""
        service = PaymentOrchestrationService(db_session)
        
        action = service._get_next_action("held_for_review")
        assert action == "check_status"
    
    def test_is_submitted_state_draft(self, db_session):
        """Test draft is not submitted."""
        service = PaymentOrchestrationService(db_session)
        
        assert service._is_submitted_state("draft") is False
        assert service._is_submitted_state("review_ready") is False
    
    def test_is_submitted_state_held(self, db_session):
        """Test held is submitted."""
        service = PaymentOrchestrationService(db_session)
        
        assert service._is_submitted_state("held_for_review") is True
        assert service._is_submitted_state("completed") is True
