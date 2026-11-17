"""Unit tests for communication service."""
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest

from app.adapters.correspondence_adapter import CorrespondenceAdapter
from app.core.clock import Clock
from app.models.communication import CommunicationRecord, NotificationRecord
from app.repositories.communication_repository import CommunicationRepository
from app.services.communication_service import (
    CommunicationService,
    NotificationDispatcher,
)


class TestCommunicationService:
    """Test communication service."""

    def test_handle_event_approved_update_type(self):
        """Test handling an approved event type generates notification."""
        # Arrange
        repo = Mock(spec=CommunicationRepository)
        dispatcher = Mock(spec=NotificationDispatcher)
        clock = Mock(spec=Clock)
        now = datetime.now(timezone.utc)
        clock.utcnow.return_value = now
        
        dispatcher.dispatch.return_value = {"delivery_id": "test-123", "delivery_state": "sent"}
        
        service = CommunicationService(repo, dispatcher, clock)
        
        event_data = {
            "event_type": "CaseStatusChanged",
            "case_id": str(uuid.uuid4()),
            "case_reference": "CP-TEST1",
            "customer_party_id": "CUST-001",
            "event_id": str(uuid.uuid4()),
            "correlation_id": "corr-001"
        }
        
        # Act
        service.handle_event(event_data)
        
        # Assert
        assert repo.create_communication.called
        assert repo.create_notification.called
        assert dispatcher.dispatch.called
        
        # Verify communication record
        comm_call = repo.create_communication.call_args[0][0]
        assert isinstance(comm_call, CommunicationRecord)
        assert comm_call.communication_type == "case_update"
        assert comm_call.subject_text == "Case status update"
        
        # Verify notification record
        notif_call = repo.create_notification.call_args[0][0]
        assert isinstance(notif_call, NotificationRecord)
        assert notif_call.safe_preview_text == "Your case has been updated"
        assert notif_call.deep_link_target == "case_view"
        assert notif_call.notification_template_code == "status_change"

    def test_handle_event_non_approved_type_skipped(self):
        """Test non-approved event types do not generate notifications."""
        # Arrange
        repo = Mock(spec=CommunicationRepository)
        dispatcher = Mock(spec=NotificationDispatcher)
        clock = Mock(spec=Clock)
        
        service = CommunicationService(repo, dispatcher, clock)
        
        event_data = {
            "event_type": "SomeOtherEvent",
            "case_id": str(uuid.uuid4()),
            "customer_party_id": "CUST-001"
        }
        
        # Act
        service.handle_event(event_data)
        
        # Assert
        assert not repo.create_communication.called
        assert not repo.create_notification.called
        assert not dispatcher.dispatch.called

    def test_handle_event_missing_required_data(self):
        """Test event with missing required data is skipped."""
        # Arrange
        repo = Mock(spec=CommunicationRepository)
        dispatcher = Mock(spec=NotificationDispatcher)
        clock = Mock(spec=Clock)
        
        service = CommunicationService(repo, dispatcher, clock)
        
        # Missing customer_party_id
        event_data = {
            "event_type": "CaseStatusChanged",
            "case_id": str(uuid.uuid4()),
            "case_reference": "CP-TEST1"
        }
        
        # Act
        service.handle_event(event_data)
        
        # Assert
        assert not repo.create_communication.called

    def test_dispatcher_uses_correspondence_adapter(self):
        """Test dispatcher calls correspondence adapter."""
        # Arrange
        adapter = Mock(spec=CorrespondenceAdapter)
        adapter.send_push_notification.return_value = {
            "delivery_id": "test-456",
            "delivery_state": "sent"
        }
        
        dispatcher = NotificationDispatcher(adapter)
        
        # Act
        result = dispatcher.dispatch(
            customer_party_id="CUST-001",
            safe_preview_text="Test notification",
            deep_link_token="token123"
        )
        
        # Assert
        assert adapter.send_push_notification.called
        assert result["delivery_id"] == "test-456"
        assert result["delivery_state"] == "sent"
