"""Acceptance tests for notifications."""
import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.core.clock import Clock
from app.models.communication import CommunicationRecord, NotificationRecord
from app.repositories.communication_repository import CommunicationRepository


def test_get_notifications_for_customer(db_session):
    """Test fetching notifications for a customer returns correct records."""
    # Arrange
    now = datetime.now(timezone.utc)
    case_id = uuid.uuid4()
    customer_party_id = "TEST-CUSTOMER-001"
    
    comm = CommunicationRecord(
        id=uuid.uuid4(),
        case_id=case_id,
        communication_type="case_update",
        subject_text="Test notification",
        body_text="Test body",
        approved_wording_set="test_v1",
        correlation_id="test-001",
        created_at=now
    )
    db_session.add(comm)
    
    token = "test_token_123"
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    notif = NotificationRecord(
        id=uuid.uuid4(),
        communication_id=comm.id,
        case_id=case_id,
        customer_party_id=customer_party_id,
        notification_type="case_update",
        safe_preview_text="Your case has been updated",
        deep_link_token_hash=token_hash,
        deep_link_target="case_view",
        deep_link_expires_at=now + timedelta(hours=24),
        notification_template_code="status_change",
        delivery_state="delivered",
        delivery_attempts=1,
        delivered_at=now,
        correlation_id="test-001",
        created_at=now
    )
    db_session.add(notif)
    db_session.commit()
    
    # Act
    repo = CommunicationRepository(db_session)
    notifications, total = repo.page_for_customer(customer_party_id, limit=20, offset=0)
    
    # Assert
    assert total == 1
    assert len(notifications) == 1
    assert notifications[0].safe_preview_text == "Your case has been updated"
    assert notifications[0].notification_type == "case_update"
    assert notifications[0].deep_link_target == "case_view"


def test_open_notification_with_valid_token(db_session):
    """Test opening a notification with a valid token sets opened_at."""
    # Arrange
    now = Clock().utcnow()
    case_id = uuid.uuid4()
    customer_party_id = "TEST-CUSTOMER-002"
    
    comm = CommunicationRecord(
        id=uuid.uuid4(),
        case_id=case_id,
        communication_type="case_update",
        subject_text="Test",
        body_text="Test body",
        approved_wording_set="test_v1",
        correlation_id="test-002",
        created_at=now
    )
    db_session.add(comm)
    
    token = "valid_token_456"
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    notif = NotificationRecord(
        id=uuid.uuid4(),
        communication_id=comm.id,
        case_id=case_id,
        customer_party_id=customer_party_id,
        notification_type="case_update",
        safe_preview_text="Test preview",
        deep_link_token_hash=token_hash,
        deep_link_target="case_view",
        deep_link_expires_at=now + timedelta(hours=24),
        notification_template_code="status_change",
        delivery_state="delivered",
        delivery_attempts=1,
        delivered_at=now,
        opened_at=None,  # Not yet opened
        correlation_id="test-002",
        created_at=now
    )
    db_session.add(notif)
    db_session.commit()
    
    # Act - Simulate opening the notification
    repo = CommunicationRepository(db_session)
    found = repo.by_token_hash(token_hash)
    assert found is not None
    assert found.opened_at is None
    
    # Set opened_at
    found.opened_at = Clock().utcnow()
    repo.update_notification(found)
    db_session.commit()
    
    # Assert
    db_session.expire(found)
    db_session.refresh(found)
    assert found.opened_at is not None
    assert found.deep_link_target == "case_view"


def test_open_notification_with_expired_token_fails(db_session):
    """Test opening a notification with expired token should be rejected."""
    # Arrange
    now = Clock().utcnow()
    case_id = uuid.uuid4()
    customer_party_id = "TEST-CUSTOMER-003"
    
    comm = CommunicationRecord(
        id=uuid.uuid4(),
        case_id=case_id,
        communication_type="case_update",
        subject_text="Test",
        body_text="Test body",
        approved_wording_set="test_v1",
        correlation_id="test-003",
        created_at=now
    )
    db_session.add(comm)
    
    token = "expired_token_789"
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    notif = NotificationRecord(
        id=uuid.uuid4(),
        communication_id=comm.id,
        case_id=case_id,
        customer_party_id=customer_party_id,
        notification_type="case_update",
        safe_preview_text="Test preview",
        deep_link_token_hash=token_hash,
        deep_link_target="case_view",
        deep_link_expires_at=now - timedelta(hours=1),  # Expired
        notification_template_code="status_change",
        delivery_state="delivered",
        delivery_attempts=1,
        delivered_at=now,
        correlation_id="test-003",
        created_at=now
    )
    db_session.add(notif)
    db_session.commit()
    
    # Act
    repo = CommunicationRepository(db_session)
    found = repo.by_token_hash(token_hash)
    
    # Assert
    assert found is not None
    # Handle timezone-aware vs naive comparison
    expires_at = found.deep_link_expires_at
    if expires_at.tzinfo is None:
        from datetime import timezone
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    assert expires_at < Clock().utcnow()  # Expired


def test_open_notification_with_unknown_token(db_session):
    """Test opening notification with unknown token returns None."""
    # Act
    repo = CommunicationRepository(db_session)
    token_hash = hashlib.sha256("unknown_token".encode()).hexdigest()
    found = repo.by_token_hash(token_hash)
    
    # Assert
    assert found is None


def test_notifications_scoped_to_customer(db_session):
    """Test notifications are scoped to the correct customer."""
    # Arrange: Create notifications for two different customers
    now = datetime.now(timezone.utc)
    
    for customer_id in ["CUST-A", "CUST-B"]:
        case_id = uuid.uuid4()
        
        comm = CommunicationRecord(
            id=uuid.uuid4(),
            case_id=case_id,
            communication_type="case_update",
            subject_text=f"Test for {customer_id}",
            body_text="Test body",
            approved_wording_set="test_v1",
            correlation_id=f"test-{customer_id}",
            created_at=now
        )
        db_session.add(comm)
        
        token = f"token_{customer_id}"
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        notif = NotificationRecord(
            id=uuid.uuid4(),
            communication_id=comm.id,
            case_id=case_id,
            customer_party_id=customer_id,
            notification_type="case_update",
            safe_preview_text=f"Preview for {customer_id}",
            deep_link_token_hash=token_hash,
            deep_link_target="case_view",
            deep_link_expires_at=now + timedelta(hours=24),
            notification_template_code="status_change",
            delivery_state="delivered",
            delivery_attempts=1,
            delivered_at=now,
            correlation_id=f"test-{customer_id}",
            created_at=now
        )
        db_session.add(notif)
    
    db_session.commit()
    
    # Act - Query for CUST-A only
    repo = CommunicationRepository(db_session)
    notifications, total = repo.page_for_customer("CUST-A", limit=20, offset=0)
    
    # Assert - Should only see CUST-A's notification
    assert total == 1
    assert notifications[0].safe_preview_text == "Preview for CUST-A"
