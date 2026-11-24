"""Queue endpoint schemas."""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class QueueItemSchema(BaseModel):
    """Queue item schema."""
    queue_item_id: str
    receivable_item_id: str
    customer_account_id: str
    customer_name: str
    queue_state: str
    is_non_standard: bool
    non_standard_reason: Optional[str] = None
    priority_rank: int
    priority_score: Decimal
    open_amount: Decimal
    currency_code: str
    days_past_due: int
    aging_bucket: str
    promise_indicator: bool
    dispute_indicator: bool
    entered_queue_at: datetime
    last_refreshed_at: datetime


class QueueGroupSchema(BaseModel):
    """Queue group schema."""
    queue_state: str
    count: int
    total_amount: Decimal


class QueueListResponse(BaseModel):
    """Queue items list response."""
    items: List[QueueItemSchema]
    total: int
    limit: int
    offset: int
    groups: List[QueueGroupSchema]
    data_freshness: datetime


class QueueRefreshRequest(BaseModel):
    """Queue refresh request."""
    scope: str  # "full" or "customer"
    customer_id: Optional[str] = None


class RefreshRunResponse(BaseModel):
    """Refresh run response."""
    run_id: str
    run_status: str  # "running", "succeeded", "failed", "partial"
    trigger_type: str  # "scheduled", "user_refresh", "manual"
    started_at: datetime
    status_url: str
    completed_at: Optional[datetime] = None
    records_read: Optional[int] = None
    records_upserted: Optional[int] = None
    items_ranked: Optional[int] = None
    items_flagged_non_standard: Optional[int] = None
    error_summary: Optional[str] = None
