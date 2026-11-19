"""Service for notification dispatch."""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.audit import NotificationDispatch
from app.adapters.notification_adapter import NotificationAdapter
from app.common.enums import NotificationType, DispatchState


class NotificationService:
    """Service for dispatching payment and security notifications."""

    def __init__(self, db: Session):
        self.db = db
        self.notification_adapter = NotificationAdapter()

    def send_payment_notification(
        self,
        user_identity_id: int,
        payment_instruction_id: int,
        auth_session_id: int,
        notification_type: str,
        payload: dict
    ) -> None:
        """Send payment notification to customer."""
        result = self.notification_adapter.send_notification(
            user_identity_id=user_identity_id,
            notification_type=notification_type,
            payload=payload
        )
        
        # Record notification dispatch
        now = datetime.now(timezone.utc)
        dispatch = NotificationDispatch(
            payment_instruction_id=payment_instruction_id,
            auth_session_id=auth_session_id,
            notification_type=notification_type,
            provider_reference=result["provider_reference"],
            dispatch_state=result["dispatch_state"],
            dispatched_at=result["dispatched_at"],
            created_at=now,
            updated_at=now
        )
        self.db.add(dispatch)
        self.db.commit()

    def send_security_notification(
        self,
        user_identity_id: int,
        auth_session_id: int,
        notification_type: str,
        payload: dict
    ) -> None:
        """Send security notification to customer."""
        result = self.notification_adapter.send_notification(
            user_identity_id=user_identity_id,
            notification_type=notification_type,
            payload=payload
        )
        
        # Record notification dispatch
        now = datetime.now(timezone.utc)
        dispatch = NotificationDispatch(
            payment_instruction_id=None,
            auth_session_id=auth_session_id,
            notification_type=notification_type,
            provider_reference=result["provider_reference"],
            dispatch_state=result["dispatch_state"],
            dispatched_at=result["dispatched_at"],
            created_at=now,
            updated_at=now
        )
        self.db.add(dispatch)
        self.db.commit()
