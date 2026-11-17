"""Notifications router."""
import hashlib
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.database import get_db
from app.deps import require_scope
from app.repositories.communication_repository import CommunicationRepository
from app.schemas.case import Page

router = APIRouter()


class NotificationItem(BaseModel):
    """Notification item for list view."""
    id: str
    case_id: str
    case_reference: str | None = None
    notification_type: str
    safe_preview_text: str
    deep_link_target: str
    opened_at: datetime | None
    created_at: datetime


class OpenNotificationRequest(BaseModel):
    """Request to open a notification via deep link token."""
    deep_link_token: str


class OpenNotificationResponse(BaseModel):
    """Response after opening a notification."""
    deep_link_target: str
    case_reference: str | None = None


@router.get("/notifications", response_model=Page[NotificationItem])
def list_notifications(
    limit: int = 20,
    offset: int = 0,
    principal = Depends(require_scope("customer")),
    db: Session = Depends(get_db)
):
    """List notifications for a customer."""
    # Validate limit
    if limit < 1 or limit > 100:
        limit = 20
    if offset < 0:
        offset = 0

    repo = CommunicationRepository(db)
    notifications, total = repo.page_for_customer(
        customer_party_id=principal.customer_party_id,
        limit=limit,
        offset=offset
    )

    # Build notification items
    items = []
    for notif in notifications:
        items.append(NotificationItem(
            id=str(notif.id),
            case_id=str(notif.case_id),
            case_reference=None,  # Case reference lookup would require join
            notification_type=notif.notification_type,
            safe_preview_text=notif.safe_preview_text,
            deep_link_target=notif.deep_link_target,
            opened_at=notif.opened_at,
            created_at=notif.created_at
        ))

    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("/notifications/open", response_model=OpenNotificationResponse)
def open_notification(
    request: OpenNotificationRequest,
    principal = Depends(require_scope("customer")),
    db: Session = Depends(get_db)
):
    """Open a notification via deep link token.

    Validates token, checks expiry, sets opened_at, returns deep link target.
    """
    # Hash the token
    token_hash = hashlib.sha256(request.deep_link_token.encode()).hexdigest()

    # Find notification by token hash
    repo = CommunicationRepository(db)
    notification = repo.by_token_hash(token_hash)

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    # Check expiry
    now = Clock().utcnow()
    if notification.deep_link_expires_at < now:
        raise HTTPException(status_code=410, detail="Notification link has expired")

    # Verify notification belongs to this customer
    if notification.customer_party_id != principal.customer_party_id:
        raise HTTPException(status_code=404, detail="Notification not found")

    # Set opened_at if not already opened
    if notification.opened_at is None:
        notification.opened_at = now
        repo.update_notification(notification)
        db.commit()

    # Return deep link target
    # Note: case_reference lookup would require joining with cases table
    return OpenNotificationResponse(
        deep_link_target=notification.deep_link_target,
        case_reference=None
    )
