"""Pydantic schemas for promise endpoints."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# Scope links
class ScopeLinkInput(BaseModel):
    """Promise scope link input."""
    link_type: str  # "invoice" or "receivable_item"
    invoice_id: Optional[str] = None
    receivable_item_id: Optional[str] = None
    linked_amount: str  # Decimal as string


class ScopeLinkOutput(BaseModel):
    """Promise scope link output."""
    link_id: str
    link_type: str
    invoice_id: Optional[str] = None
    receivable_item_id: Optional[str] = None
    linked_amount: str


# Source interaction
class SourceInteractionInput(BaseModel):
    """Source interaction input (embedded)."""
    interaction_type: str
    interaction_direction: str
    interaction_channel: str
    occurred_at: datetime
    summary_text: Optional[str] = None


# Promise create
class PromiseCreateRequest(BaseModel):
    """Promise create request."""
    customer_account_id: str
    promised_amount: str  # Decimal as string
    currency_code: str
    promised_date: datetime
    promise_scope_type: str  # "invoice", "account_balance", "partial"
    scope_links: List[ScopeLinkInput] = Field(default_factory=list)
    source_interaction_id: Optional[str] = None
    source_interaction: Optional[SourceInteractionInput] = None
    note: Optional[str] = None


# Promise response
class PromiseResponse(BaseModel):
    """Promise response."""
    promise_id: str
    customer_account_id: str
    promised_amount: str
    currency_code: str
    promised_date: datetime
    promise_scope_type: str
    promise_status: str
    captured_by_user_id: str
    captured_at: datetime
    policy_evaluation_id: Optional[str] = None
    scope_links: List[ScopeLinkOutput] = Field(default_factory=list)


# Promise list
class PromiseListItem(BaseModel):
    """Promise list item."""
    promise_id: str
    customer_account_id: str
    customer_name: str
    promised_amount: str
    currency_code: str
    promised_date: datetime
    promise_scope_type: str
    promise_status: str
    captured_by_user_id: str
    captured_at: datetime
    breach_detected_at: Optional[datetime] = None


class PromiseListResponse(BaseModel):
    """Promise list response."""
    items: List[PromiseListItem]
    total: int
    limit: int
    offset: int
