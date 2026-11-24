"""Queue items router."""
from typing import Optional

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.core.context import RequestContext
from app.core.deps import get_clock, get_correlation_id, get_db, get_request_context, require_action
from app.repositories.queue_repository import QueueRepository
from app.repositories.sync_run_repository import SyncRunRepository
from app.schemas.queue_schemas import (
    QueueGroupSchema,
    QueueItemSchema,
    QueueListResponse,
    QueueRefreshRequest,
    RefreshRunResponse,
)
from app.services.queue_service import QueueService

router = APIRouter()


@router.get("", response_model=QueueListResponse)
def list_queue_items(
    request: Request,
    queue_state: Optional[str] = None,
    non_standard: Optional[bool] = None,
    non_standard_reason: Optional[str] = None,
    customer_id: Optional[str] = None,
    assigned_to_me: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
    ctx: RequestContext = require_action("queue.read"),
):
    """List queue items."""
    queue_repo = QueueRepository(db)

    assigned_user_id = ctx.user_id if assigned_to_me else None

    items, total = queue_repo.list_items(
        queue_state=queue_state,
        non_standard=non_standard,
        non_standard_reason=non_standard_reason,
        customer_id=customer_id,
        assigned_user_id=assigned_user_id,
        limit=limit,
        offset=offset,
    )

    groups = queue_repo.get_groups()
    data_freshness = queue_repo.get_data_freshness()

    # Map to schema
    from app.models.customers import CustomerAccount
    item_schemas = []
    for item in items:
        # Get customer name
        account = db.query(CustomerAccount).filter(CustomerAccount.id == item.customer_account_id).first()
        customer_name = account.customer.customer_name if account and account.customer else "Unknown"

        # Get receivable item for amounts
        receivable = item.receivable_item

        item_schemas.append(
            QueueItemSchema(
                queue_item_id=str(item.id),
                receivable_item_id=str(item.receivable_item_id),
                customer_account_id=str(item.customer_account_id),
                customer_name=customer_name,
                queue_state=item.queue_state,
                is_non_standard=item.is_non_standard,
                non_standard_reason=item.non_standard_reason,
                priority_rank=item.current_rank,
                priority_score=item.current_priority_score,
                open_amount=receivable.open_amount if receivable else 0,
                currency_code=receivable.currency_code if receivable else "GBP",
                days_past_due=receivable.days_past_due if receivable else 0,
                aging_bucket=receivable.aging_bucket if receivable else "unknown",
                promise_indicator=receivable.promise_indicator if receivable else False,
                dispute_indicator=receivable.dispute_indicator if receivable else False,
                entered_queue_at=item.entered_queue_at,
                last_refreshed_at=item.last_refreshed_at,
            )
        )

    return QueueListResponse(
        items=item_schemas,
        total=total,
        limit=limit,
        offset=offset,
        groups=[
            QueueGroupSchema(
                queue_state=g["queue_state"],
                count=g["count"],
                total_amount=g["total_amount"],
            )
            for g in groups
        ],
        data_freshness=data_freshness or clock.now(),
    )


@router.post("/refresh", response_model=RefreshRunResponse, status_code=status.HTTP_202_ACCEPTED)
def trigger_queue_refresh(
    request: Request,
    body: QueueRefreshRequest,
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
    correlation_id: str = Depends(get_correlation_id),
    ctx: RequestContext = require_action("queue.refresh"),
):
    """Trigger queue refresh."""
    queue_service = QueueService(db, clock)

    sync_run = queue_service.execute_refresh(
        scope=body.scope,
        trigger_type="manual",
        triggered_by_user_id=ctx.user_id,
        customer_id=body.customer_id,
        correlation_id=correlation_id,
    )

    return RefreshRunResponse(
        run_id=str(sync_run.id),
        run_status=sync_run.run_status,
        trigger_type=sync_run.trigger_type,
        started_at=sync_run.started_at,
        status_url=f"/api/v1/queue-items/refresh-runs/{sync_run.id}",
        completed_at=sync_run.completed_at,
        records_read=sync_run.records_read,
        records_upserted=sync_run.records_upserted,
    )


@router.get("/refresh-runs/{run_id}", response_model=RefreshRunResponse)
def get_refresh_run(
    run_id: str,
    db: Session = Depends(get_db),
    ctx: RequestContext = require_action("queue.read"),
):
    """Get refresh run status."""
    sync_run_repo = SyncRunRepository(db)

    sync_run = sync_run_repo.get_by_id(run_id)
    if not sync_run:
        from app.core.errors import NotFoundError
        raise NotFoundError("Refresh run not found", code="refresh_run_not_found")

    return RefreshRunResponse(
        run_id=str(sync_run.id),
        run_status=sync_run.run_status,
        trigger_type=sync_run.trigger_type,
        started_at=sync_run.started_at,
        status_url=f"/api/v1/queue-items/refresh-runs/{sync_run.id}",
        completed_at=sync_run.completed_at,
        records_read=sync_run.records_read,
        records_upserted=sync_run.records_upserted,
        error_summary=sync_run.error_summary,
    )
