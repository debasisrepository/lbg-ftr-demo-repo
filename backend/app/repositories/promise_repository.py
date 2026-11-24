"""Repository for promises to pay."""
import uuid
from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session, joinedload

from app.models.promises import PromiseToPay, PromiseScopeLink
from app.models.customers import CustomerAccount


class PromiseRepository:
    """Repository for promises to pay."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, promise: PromiseToPay) -> PromiseToPay:
        """Create promise."""
        self.db.add(promise)
        self.db.flush()
        self.db.refresh(promise)
        return promise

    def create_scope_link(self, link: PromiseScopeLink) -> PromiseScopeLink:
        """Create scope link."""
        self.db.add(link)
        self.db.flush()
        self.db.refresh(link)
        return link

    def get_by_id(self, promise_id: uuid.UUID) -> Optional[PromiseToPay]:
        """Get promise by ID."""
        stmt = (
            select(PromiseToPay)
            .where(PromiseToPay.id == promise_id)
            .options(joinedload(PromiseToPay.scope_links))
        )
        return self.db.scalar(stmt)

    def get_by_idempotency_key(
        self, user_id: uuid.UUID, idempotency_key: str
    ) -> Optional[PromiseToPay]:
        """Get promise by user and idempotency key."""
        stmt = (
            select(PromiseToPay)
            .where(
                and_(
                    PromiseToPay.captured_by_user_id == user_id,
                    PromiseToPay.idempotency_key == idempotency_key,
                )
            )
            .options(joinedload(PromiseToPay.scope_links))
        )
        return self.db.scalar(stmt)

    def list_promises(
        self,
        customer_id: Optional[uuid.UUID] = None,
        customer_account_id: Optional[uuid.UUID] = None,
        promise_status: Optional[str] = None,
        captured_by_user_id: Optional[uuid.UUID] = None,
        promised_from: Optional[datetime] = None,
        promised_to: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[List[PromiseToPay], int]:
        """List promises with filters."""
        # Build base query
        stmt = select(PromiseToPay).join(
            CustomerAccount, PromiseToPay.customer_account_id == CustomerAccount.id
        )

        # Apply filters
        conditions = []
        if customer_id:
            conditions.append(CustomerAccount.customer_id == customer_id)
        if customer_account_id:
            conditions.append(PromiseToPay.customer_account_id == customer_account_id)
        if promise_status:
            conditions.append(PromiseToPay.promise_status == promise_status)
        if captured_by_user_id:
            conditions.append(PromiseToPay.captured_by_user_id == captured_by_user_id)
        if promised_from:
            conditions.append(PromiseToPay.promised_date >= promised_from)
        if promised_to:
            conditions.append(PromiseToPay.promised_date <= promised_to)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt) or 0

        # Apply pagination and fetch
        stmt = stmt.order_by(PromiseToPay.captured_at.desc()).limit(limit).offset(offset)
        promises = list(self.db.scalars(stmt).all())

        return promises, total

    def get_for_customer_account(
        self, customer_account_id: uuid.UUID, limit: int = 100
    ) -> List[PromiseToPay]:
        """Get promises for customer account."""
        stmt = (
            select(PromiseToPay)
            .where(PromiseToPay.customer_account_id == customer_account_id)
            .order_by(PromiseToPay.captured_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())
