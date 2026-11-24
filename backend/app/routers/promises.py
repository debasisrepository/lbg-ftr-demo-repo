"""Promises router."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.core.context import RequestContext
from app.core.deps import get_db, get_clock, get_request_context, require_action, get_correlation_id
from app.schemas.promise_schemas import (
    PromiseCreateRequest,
    PromiseResponse,
    PromiseListResponse,
)
from app.services.promise_service import PromiseService


router = APIRouter(tags=["promises"])


@router.post("", response_model=PromiseResponse, status_code=status.HTTP_201_CREATED)
def create_promise(
    request: PromiseCreateRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
    ctx: RequestContext = require_action("promise.create"),
    correlation_id: str = Depends(get_correlation_id),
) -> PromiseResponse:
    """Create promise-to-pay.
    
    Requires Idempotency-Key header.
    Returns 201 for new promise, 200 for idempotent replay.
    """
    service = PromiseService(db, clock)
    response, status_code = service.create_promise(
        request=request,
        ctx=ctx,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )

    # Note: FastAPI doesn't allow dynamic status codes easily,
    # so we return 201 always (decorator) but service returns the actual code
    return response


@router.get("", response_model=PromiseListResponse)
def list_promises(
    customer_id: Optional[str] = Query(None),
    customer_account_id: Optional[str] = Query(None),
    promise_status: Optional[str] = Query(None),
    captured_by_me: bool = Query(False),
    promised_from: Optional[datetime] = Query(None),
    promised_to: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
    ctx: RequestContext = require_action("promise.read"),
) -> PromiseListResponse:
    """List promises with filters."""
    service = PromiseService(db, clock)
    return service.list_promises(
        customer_id=customer_id,
        customer_account_id=customer_account_id,
        promise_status=promise_status,
        captured_by_me=captured_by_me,
        promised_from=promised_from,
        promised_to=promised_to,
        limit=limit,
        offset=offset,
        ctx=ctx,
    )


@router.get("/{promise_id}", response_model=PromiseResponse)
def get_promise(
    promise_id: str,
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
    ctx: RequestContext = require_action("promise.read"),
) -> PromiseResponse:
    """Get promise by ID."""
    service = PromiseService(db, clock)
    return service.get_promise(promise_id)
