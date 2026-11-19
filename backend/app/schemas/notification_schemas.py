"""Notification-related Pydantic schemas"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    """Customer notification"""
    customer_notification_id: uuid.UUID
    notification_type: str
    channel: str
    template_code: str
    title: str
    body_summary: str
    delivery_state: str
    read_at: datetime | None
    dispatched_at: datetime | None
    payment_order_id: uuid.UUID | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    """List of customer notifications"""
    items: list[NotificationResponse]
    total: int
    unread_count: int


class ServiceStatusResponse(BaseModel):
    """Service status notice"""
    service_status_notice_id: uuid.UUID
    capability: str
    severity: str
    headline: str
    customer_message: str
    still_available_text: str | None
    next_step_text: str | None
    next_update_at: datetime | None
    starts_at: datetime
    ends_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ServiceStatusListResponse(BaseModel):
    """List of active service statuses"""
    items: list[ServiceStatusResponse]
    total: int
