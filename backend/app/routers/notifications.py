"""Notification endpoints"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..core.auth_middleware import get_current_customer_id
from ..database import get_db
from ..schemas.notification_schemas import (
    NotificationListResponse,
    NotificationResponse,
    ServiceStatusListResponse,
    ServiceStatusResponse,
)
from ..services.notification_service import NotificationService
from ..services.service_status_service import ServiceStatusService

router = APIRouter()


@router.get("", response_model=NotificationListResponse, status_code=200)
def list_notifications(
    limit: int = 50,
    offset: int = 0,
    customer_id: uuid.UUID = Depends(get_current_customer_id),
    db: Session = Depends(get_db)
):
    """Get customer notifications"""

    notification_service = NotificationService(db)
    notifications, total, unread_count = notification_service.get_customer_notifications(
        customer_id,
        limit,
        offset
    )

    return NotificationListResponse(
        items=[
            NotificationResponse(
                customer_notification_id=n.customer_notification_id,
                notification_type=n.notification_type,
                channel=n.channel,
                template_code=n.template_code,
                title=n.title,
                body_summary=n.body_summary,
                delivery_state=n.delivery_state,
                read_at=n.read_at,
                dispatched_at=n.dispatched_at,
                payment_order_id=n.payment_order_id,
                created_at=n.created_at
            )
            for n in notifications
        ],
        total=total,
        unread_count=unread_count
    )


@router.get("/service-status", response_model=ServiceStatusListResponse, status_code=200)
def get_service_status(
    db: Session = Depends(get_db)
):
    """Get active service status notices"""
    service_status_service = ServiceStatusService(db)
    notices = service_status_service.get_active_notices()

    return ServiceStatusListResponse(
        items=[
            ServiceStatusResponse(
                service_status_notice_id=n.service_status_notice_id,
                capability=n.capability,
                severity=n.severity,
                headline=n.headline,
                customer_message=n.customer_message,
                still_available_text=n.still_available_text,
                next_step_text=n.next_step_text,
                next_update_at=n.next_update_at,
                starts_at=n.starts_at,
                ends_at=n.ends_at
            )
            for n in notices
        ],
        total=len(notices)
    )
