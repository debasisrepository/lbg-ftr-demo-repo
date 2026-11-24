"""Promise service."""
import uuid
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.core.context import RequestContext
from app.core.errors import NotFoundError, ConflictError, PolicyFailureError
from app.models.customers import CustomerAccount, Customer
from app.models.promises import PromiseToPay, PromiseScopeLink, IdempotencyRecord
from app.models.queue import InteractionLogEntry
from app.repositories.promise_repository import PromiseRepository
from app.repositories.idempotency_repository import IdempotencyRepository
from app.repositories.interaction_repository import InteractionRepository
from app.repositories.customer_repository import CustomerRepository
from app.services.policy_engine_service import PolicyEngineService
from app.schemas.promise_schemas import (
    PromiseCreateRequest,
    PromiseResponse,
    ScopeLinkOutput,
    PromiseListResponse,
    PromiseListItem,
)


class PromiseService:
    """Service for promise-to-pay operations."""

    def __init__(self, db: Session, clock: Clock):
        self.db = db
        self.clock = clock
        self.promise_repo = PromiseRepository(db)
        self.idempotency_repo = IdempotencyRepository(db)
        self.interaction_repo = InteractionRepository(db)
        self.customer_repo = CustomerRepository(db)
        self.policy_engine = PolicyEngineService(db, clock)

    def create_promise(
        self,
        request: PromiseCreateRequest,
        ctx: RequestContext,
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[PromiseResponse, int]:
        """Create promise with policy validation and idempotency.
        
        Returns:
            (PromiseResponse, status_code) where status_code is 201 for created or 200 for replay
        """
        now = self.clock.now()

        # Check idempotency
        existing_promise = self.promise_repo.get_by_idempotency_key(
            uuid.UUID(ctx.user_id), idempotency_key
        )

        if existing_promise:
            # Check if request fingerprint matches
            request_fingerprint = self._compute_fingerprint(request)
            existing_record = self.idempotency_repo.get_by_key(
                uuid.UUID(ctx.user_id), "promise_create", idempotency_key
            )

            if existing_record and existing_record.request_fingerprint != request_fingerprint:
                raise ConflictError(
                    "Idempotency key conflict: same key with different request body"
                )

            # Return existing promise (idempotent replay)
            return self._build_promise_response(existing_promise), 200

        # Validate customer account exists
        account = self.customer_repo.get_account_by_id(
            uuid.UUID(request.customer_account_id)
        )

        if not account:
            raise NotFoundError(
                f"Customer account {request.customer_account_id} not found"
            )

        # Handle source interaction
        source_interaction_id = None
        if request.source_interaction_id:
            source_interaction_id = uuid.UUID(request.source_interaction_id)
        elif request.source_interaction:
            # Create embedded interaction
            interaction = InteractionLogEntry(
                id=uuid.uuid4(),
                created_at=now,
                updated_at=now,
                customer_account_id=uuid.UUID(request.customer_account_id),
                interaction_type=request.source_interaction.interaction_type,
                interaction_direction=request.source_interaction.interaction_direction,
                interaction_channel=request.source_interaction.interaction_channel,
                occurred_at=request.source_interaction.occurred_at,
                recorded_by_user_id=uuid.UUID(ctx.user_id),
                summary_text=request.source_interaction.summary_text,
            )
            self.interaction_repo.create(interaction)
            source_interaction_id = interaction.id

        # Build policy context
        policy_context = {
            "promised_amount": float(request.promised_amount),
            "promised_date": request.promised_date.isoformat(),
            "scope_type": request.promise_scope_type,
            "scope_links": [
                {
                    "link_type": link.link_type,
                    "invoice_id": link.invoice_id,
                    "receivable_item_id": link.receivable_item_id,
                    "linked_amount": float(link.linked_amount),
                }
                for link in request.scope_links
            ],
            "has_source_interaction": source_interaction_id is not None,
        }

        # Evaluate policy (use a placeholder UUID for pending promises)
        pending_id = str(uuid.uuid4())
        policy_evaluation = self.policy_engine.evaluate(
            action_type="promise_create",
            context_data=policy_context,
            actor_user_id=ctx.user_id,
            actor_role_code=ctx.active_role.role_code,
            evaluation_context_type="promise_capture",
            subject_entity_type="promise_to_pay",
            subject_entity_id=pending_id,
            correlation_id=correlation_id,
        )

        if policy_evaluation.evaluation_result == "fail":
            raise PolicyFailureError(
                message="Promise validation failed",
                failed_conditions=policy_evaluation.failed_conditions_json,
                policy_evaluation_id=str(policy_evaluation.id),
            )

        # Create promise
        promise = PromiseToPay(
            id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
            customer_account_id=uuid.UUID(request.customer_account_id),
            source_interaction_log_entry_id=source_interaction_id,
            promised_amount=float(request.promised_amount),
            currency_code=request.currency_code,
            promised_date=request.promised_date,
            promise_scope_type=request.promise_scope_type,
            promise_status="captured",
            captured_by_user_id=uuid.UUID(ctx.user_id),
            captured_at=now,
            policy_evaluation_record_id=policy_evaluation.id,
            idempotency_key=idempotency_key,
        )

        self.promise_repo.create(promise)

        # Create scope links
        scope_links = []
        for link_input in request.scope_links:
            link = PromiseScopeLink(
                id=uuid.uuid4(),
                created_at=now,
                updated_at=now,
                promise_to_pay_id=promise.id,
                link_type=link_input.link_type,
                invoice_id=(
                    uuid.UUID(link_input.invoice_id) if link_input.invoice_id else None
                ),
                receivable_item_id=(
                    uuid.UUID(link_input.receivable_item_id)
                    if link_input.receivable_item_id
                    else None
                ),
                linked_amount=float(link_input.linked_amount),
            )
            self.promise_repo.create_scope_link(link)
            scope_links.append(link)

        # Create idempotency record
        request_fingerprint = self._compute_fingerprint(request)
        response_body = self._build_promise_response(promise, scope_links).model_dump_json()

        idempotency_record = IdempotencyRecord(
            id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
            user_id=uuid.UUID(ctx.user_id),
            operation="promise_create",
            idempotency_key=idempotency_key,
            request_fingerprint=request_fingerprint,
            response_status_code=201,
            response_body_json=response_body,  # Already JSON string
            resource_type="promise_to_pay",
            resource_id=promise.id,
            expires_at=now + timedelta(hours=24),
        )

        self.idempotency_repo.create(idempotency_record)
        self.db.commit()

        return self._build_promise_response(promise, scope_links), 201

    def get_promise(self, promise_id: str) -> PromiseResponse:
        """Get promise by ID."""
        promise = self.promise_repo.get_by_id(uuid.UUID(promise_id))

        if not promise:
            raise NotFoundError(f"Promise {promise_id} not found")

        return self._build_promise_response(promise)

    def list_promises(
        self,
        customer_id: Optional[str] = None,
        customer_account_id: Optional[str] = None,
        promise_status: Optional[str] = None,
        captured_by_me: bool = False,
        captured_by_user_id: Optional[str] = None,
        promised_from: Optional[datetime] = None,
        promised_to: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
        ctx: Optional[RequestContext] = None,
    ) -> PromiseListResponse:
        """List promises with filters."""
        # Apply captured_by_me filter
        if captured_by_me and ctx:
            captured_by_user_id = ctx.user_id

        promises, total = self.promise_repo.list_promises(
            customer_id=uuid.UUID(customer_id) if customer_id else None,
            customer_account_id=(
                uuid.UUID(customer_account_id) if customer_account_id else None
            ),
            promise_status=promise_status,
            captured_by_user_id=(
                uuid.UUID(captured_by_user_id) if captured_by_user_id else None
            ),
            promised_from=promised_from,
            promised_to=promised_to,
            limit=limit,
            offset=offset,
        )

        # Build response items
        items = []
        for promise in promises:
            # Get customer name
            account = self.db.scalar(
                select(CustomerAccount).where(CustomerAccount.id == promise.customer_account_id)
            )
            customer = self.db.scalar(
                select(Customer).where(Customer.id == account.customer_id)
            ) if account else None

            items.append(
                PromiseListItem(
                    promise_id=str(promise.id),
                    customer_account_id=str(promise.customer_account_id),
                    customer_name=customer.customer_name if customer else "Unknown",
                    promised_amount=str(promise.promised_amount),
                    currency_code=promise.currency_code,
                    promised_date=promise.promised_date,
                    promise_scope_type=promise.promise_scope_type,
                    promise_status=promise.promise_status,
                    captured_by_user_id=str(promise.captured_by_user_id),
                    captured_at=promise.captured_at,
                    breach_detected_at=promise.breach_detected_at,
                )
            )

        return PromiseListResponse(items=items, total=total, limit=limit, offset=offset)

    def _build_promise_response(
        self, promise: PromiseToPay, scope_links: Optional[list] = None
    ) -> PromiseResponse:
        """Build promise response."""
        if scope_links is None:
            scope_links = promise.scope_links or []

        return PromiseResponse(
            promise_id=str(promise.id),
            customer_account_id=str(promise.customer_account_id),
            promised_amount=str(promise.promised_amount),
            currency_code=promise.currency_code,
            promised_date=promise.promised_date,
            promise_scope_type=promise.promise_scope_type,
            promise_status=promise.promise_status,
            captured_by_user_id=str(promise.captured_by_user_id),
            captured_at=promise.captured_at,
            policy_evaluation_id=(
                str(promise.policy_evaluation_record_id)
                if promise.policy_evaluation_record_id
                else None
            ),
            scope_links=[
                ScopeLinkOutput(
                    link_id=str(link.id),
                    link_type=link.link_type,
                    invoice_id=str(link.invoice_id) if link.invoice_id else None,
                    receivable_item_id=(
                        str(link.receivable_item_id) if link.receivable_item_id else None
                    ),
                    linked_amount=str(link.linked_amount),
                )
                for link in scope_links
            ],
        )

    def _compute_fingerprint(self, request: PromiseCreateRequest) -> str:
        """Compute request fingerprint for idempotency check."""
        # Normalize request to canonical JSON
        payload = request.model_dump(mode="json")
        canonical = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()
