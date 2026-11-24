"""Customers router."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.core.context import RequestContext
from app.core.deps import get_db, get_clock, get_request_context, require_action
from app.schemas.customer_schemas import CustomerListResponse, Customer360Response
from app.services.customer360_service import Customer360Service


router = APIRouter(tags=["customers"])


@router.get("", response_model=CustomerListResponse)
def list_customers(
    q: Optional[str] = Query(None, description="Search query"),
    portfolio_ref: Optional[str] = Query(None, description="Portfolio reference"),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
    ctx: RequestContext = require_action("customer.view"),
) -> CustomerListResponse:
    """List/search customers."""
    service = Customer360Service(db, clock)
    return service.search_customers(q=q, portfolio_ref=portfolio_ref, limit=limit, offset=offset)


@router.get("/{customer_id}/view", response_model=Customer360Response)
def get_customer_view(
    customer_id: str,
    account_id: Optional[str] = Query(None, description="Focus on specific account"),
    invoice_limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
    ctx: RequestContext = require_action("customer.view"),
) -> Customer360Response:
    """Get customer 360 view."""
    service = Customer360Service(db, clock)
    return service.get_customer_view(
        customer_id=customer_id,
        ctx=ctx,
        account_id=account_id,
        invoice_limit=invoice_limit,
    )
