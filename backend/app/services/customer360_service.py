"""Customer 360 service."""
import uuid
from typing import List, Optional

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session, joinedload

from app.core.clock import Clock
from app.core.context import RequestContext
from app.core.errors import NotFoundError
from app.models.customers import Customer, CustomerAccount, Invoice
from app.models.receivables import ReceivableItem, UnappliedCashReference
from app.repositories.promise_repository import PromiseRepository
from app.repositories.interaction_repository import InteractionRepository
from app.repositories.customer_repository import CustomerRepository
from app.adapters.sap.configured import get_sap_customer_context_reader
from app.adapters.sap.synchronizer import SapReferenceSynchronizer
from app.schemas.customer_schemas import (
    CustomerListItem,
    CustomerListResponse,
    Customer360Response,
    Section,
    ProfileData,
    AccountData,
    InvoiceData,
    ReceivableItemData,
    UnappliedCashData,
    PromiseData,
    InteractionData,
)


class Customer360Service:
    """Service for customer 360 view."""

    def __init__(self, db: Session, clock: Clock):
        self.db = db
        self.clock = clock
        self.promise_repo = PromiseRepository(db)
        self.interaction_repo = InteractionRepository(db)
        self.customer_repo = CustomerRepository(db)

    def search_customers(
        self,
        q: Optional[str] = None,
        portfolio_ref: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> CustomerListResponse:
        """Search customers."""
        # Build query
        stmt = select(Customer)
        conditions = []

        if q:
            conditions.append(
                (Customer.customer_name.ilike(f"%{q}%"))
                | (Customer.sap_customer_ref.ilike(f"%{q}%"))
            )

        if portfolio_ref:
            # Join to customer accounts to filter by portfolio
            stmt = stmt.join(CustomerAccount)
            conditions.append(CustomerAccount.portfolio_ref == portfolio_ref)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt) or 0

        # Fetch page
        stmt = stmt.order_by(Customer.customer_name).limit(limit).offset(offset)
        customers = list(self.db.scalars(stmt).all())

        # Build response items
        items = []
        for customer in customers:
            # Count accounts for this customer
            account_count = self.customer_repo.get_account_count(customer.id)

            items.append(
                CustomerListItem(
                    customer_id=str(customer.id),
                    customer_name=customer.customer_name,
                    sap_customer_ref=customer.sap_customer_ref,
                    regional_business_unit=customer.regional_business_unit,
                    credit_status_indicator=customer.credit_status_indicator,
                    account_count=account_count,
                )
            )

        return CustomerListResponse(items=items, total=total, limit=limit, offset=offset)

    def get_customer_view(
        self,
        customer_id: str,
        ctx: RequestContext,
        account_id: Optional[str] = None,
        invoice_limit: int = 50,
    ) -> Customer360Response:
        """Get customer 360 view.
        
        Args:
            customer_id: Customer ID
            ctx: Request context (for role checking)
            account_id: Optional account ID to focus on
            invoice_limit: Limit for invoices section
            
        Returns:
            Customer360Response with sections
        """
        now = self.clock.now()

        # Get customer
        customer_uuid = uuid.UUID(customer_id)
        stmt = select(Customer).where(Customer.id == customer_uuid)
        customer = self.db.scalar(stmt)

        if not customer:
            raise NotFoundError(f"Customer {customer_id} not found")

        # Optionally sync from SAP (trigger adapter)
        try:
            sap_reader = get_sap_customer_context_reader()
            sap_data = sap_reader.read_customer_context(customer.sap_customer_ref)
            # Could upsert here if needed, but for MVP we just use existing data
        except Exception:
            # SAP unavailable - continue with local data
            pass

        # Build sections
        profile_section = self._build_profile_section(customer, ctx)
        accounts_section = self._build_accounts_section(customer_uuid, account_id)
        invoices_section = self._build_invoices_section(customer_uuid, account_id, invoice_limit)
        receivables_section = self._build_receivables_section(customer_uuid, account_id)
        unapplied_section = self._build_unapplied_section(customer_uuid, account_id)
        promises_section = self._build_promises_section(customer_uuid, account_id)
        interactions_section = self._build_interactions_section(customer_uuid, account_id)

        return Customer360Response(
            customer_id=customer_id,
            generated_at=now,
            data_freshness=customer.last_sync_at or customer.updated_at,
            profile=profile_section,
            accounts=accounts_section,
            invoices=invoices_section,
            receivable_items=receivables_section,
            unapplied_cash=unapplied_section,
            promises=promises_section,
            source_interactions=interactions_section,
        )

    def _build_profile_section(self, customer: Customer, ctx: RequestContext) -> Section:
        """Build profile section with masking."""
        profile_data = ProfileData(
            customer_id=str(customer.id),
            customer_name=customer.customer_name,
            sap_customer_ref=customer.sap_customer_ref,
            regional_business_unit=customer.regional_business_unit,
            credit_status_indicator=(
                customer.credit_status_indicator
                if ctx.active_role.can_view_sensitive_fields
                else None
            ),
            master_data_source=customer.master_data_source,
        )

        status = "masked" if not ctx.active_role.can_view_sensitive_fields else "available"

        return Section(status=status, as_of=customer.updated_at, data=profile_data.model_dump())

    def _build_accounts_section(
        self, customer_id: uuid.UUID, account_id: Optional[str]
    ) -> Section:
        """Build accounts section."""
        stmt = select(CustomerAccount).where(CustomerAccount.customer_id == customer_id)
        if account_id:
            stmt = stmt.where(CustomerAccount.id == uuid.UUID(account_id))

        accounts = list(self.db.scalars(stmt).all())

        if not accounts:
            return Section(status="unavailable", reason="No accounts found")

        accounts_data = []
        for account in accounts:
            # Calculate open balance
            balance = self.customer_repo.get_account_open_balance(account.id)

            accounts_data.append(
                AccountData(
                    customer_account_id=str(account.id),
                    sap_account_ref=account.sap_account_ref,
                    company_code=account.company_code,
                    currency_code=account.currency_code,
                    account_status=account.account_status,
                    risk_segment=account.risk_segment,
                    portfolio_ref=account.portfolio_ref,
                    collector_owner_user_id=(
                        str(account.collector_owner_user_id)
                        if account.collector_owner_user_id
                        else None
                    ),
                    open_balance=str(balance),
                ).model_dump()
            )

        return Section(
            status="available", as_of=accounts[0].updated_at, data=accounts_data
        )

    def _build_invoices_section(
        self, customer_id: uuid.UUID, account_id: Optional[str], limit: int
    ) -> Section:
        """Build invoices section."""
        stmt = select(Invoice).join(CustomerAccount)
        stmt = stmt.where(CustomerAccount.customer_id == customer_id)

        if account_id:
            stmt = stmt.where(Invoice.customer_account_id == uuid.UUID(account_id))

        stmt = stmt.order_by(Invoice.due_date.desc()).limit(limit)
        invoices = list(self.db.scalars(stmt).all())

        if not invoices:
            return Section(status="unavailable", reason="No invoices found")

        invoices_data = [
            InvoiceData(
                invoice_id=str(inv.id),
                sap_invoice_ref=inv.sap_invoice_ref,
                invoice_number=inv.invoice_number,
                document_date=inv.document_date,
                due_date=inv.due_date,
                invoice_amount=str(inv.invoice_amount),
                open_amount=str(inv.open_amount),
                currency_code=inv.currency_code,
                invoice_status=inv.invoice_status,
            ).model_dump()
            for inv in invoices
        ]

        return Section(status="available", as_of=invoices[0].updated_at, data=invoices_data)

    def _build_receivables_section(
        self, customer_id: uuid.UUID, account_id: Optional[str]
    ) -> Section:
        """Build receivables section."""
        stmt = select(ReceivableItem).where(
            ReceivableItem.customer_account_id.in_(
                select(CustomerAccount.id).where(CustomerAccount.customer_id == customer_id)
            )
        )

        if account_id:
            stmt = stmt.where(ReceivableItem.customer_account_id == uuid.UUID(account_id))

        stmt = stmt.order_by(ReceivableItem.days_past_due.desc()).limit(100)
        items = list(self.db.scalars(stmt).all())

        if not items:
            return Section(status="unavailable", reason="No receivable items found")

        items_data = [
            ReceivableItemData(
                receivable_item_id=str(item.id),
                sap_open_item_ref=item.sap_open_item_ref,
                aging_bucket=item.aging_bucket,
                days_past_due=item.days_past_due,
                open_amount=str(item.open_amount),
                currency_code=item.currency_code,
                dispute_indicator=item.dispute_indicator,
                deduction_indicator=item.deduction_indicator,
                promise_indicator=item.promise_indicator,
            ).model_dump()
            for item in items
        ]

        return Section(status="available", as_of=items[0].updated_at, data=items_data)

    def _build_unapplied_section(
        self, customer_id: uuid.UUID, account_id: Optional[str]
    ) -> Section:
        """Build unapplied cash section."""
        stmt = select(UnappliedCashReference).where(
            UnappliedCashReference.customer_account_id.in_(
                select(CustomerAccount.id).where(CustomerAccount.customer_id == customer_id)
            )
        )

        if account_id:
            stmt = stmt.where(
                UnappliedCashReference.customer_account_id == uuid.UUID(account_id)
            )

        stmt = stmt.order_by(UnappliedCashReference.receipt_date.desc()).limit(50)
        items = list(self.db.scalars(stmt).all())

        if not items:
            return Section(status="unavailable", reason="No unapplied cash found")

        cash_data = [
            UnappliedCashData(
                unapplied_cash_id=str(item.id),
                sap_cash_item_ref=item.sap_cash_item_ref,
                bank_or_lockbox_reference=item.bank_or_lockbox_reference,
                receipt_date=item.receipt_date,
                unapplied_amount=str(item.unapplied_amount),
                currency_code=item.currency_code,
                classification_status=item.classification_status,
                aging_days=item.aging_days,
            ).model_dump()
            for item in items
        ]

        return Section(status="available", as_of=items[0].updated_at, data=cash_data)

    def _build_promises_section(
        self, customer_id: uuid.UUID, account_id: Optional[str]
    ) -> Section:
        """Build promises section."""
        # Get promises
        if account_id:
            promises = self.promise_repo.get_for_customer_account(uuid.UUID(account_id))
        else:
            # Get all promises for all accounts of this customer
            account_ids = self.db.scalars(
                select(CustomerAccount.id).where(CustomerAccount.customer_id == customer_id)
            ).all()

            promises = []
            for acc_id in account_ids:
                promises.extend(self.promise_repo.get_for_customer_account(acc_id))

        if not promises:
            return Section(status="unavailable", reason="No promises found")

        promises_data = [
            PromiseData(
                promise_id=str(p.id),
                promised_amount=str(p.promised_amount),
                currency_code=p.currency_code,
                promised_date=p.promised_date,
                promise_scope_type=p.promise_scope_type,
                promise_status=p.promise_status,
                captured_by_user_id=str(p.captured_by_user_id),
                captured_at=p.captured_at,
            ).model_dump()
            for p in promises
        ]

        return Section(status="available", as_of=promises[0].updated_at, data=promises_data)

    def _build_interactions_section(
        self, customer_id: uuid.UUID, account_id: Optional[str]
    ) -> Section:
        """Build interactions section."""
        # Get interactions
        if account_id:
            interactions = self.interaction_repo.get_for_customer_account(
                uuid.UUID(account_id)
            )
        else:
            # Get all interactions for all accounts of this customer
            account_ids = self.db.scalars(
                select(CustomerAccount.id).where(CustomerAccount.customer_id == customer_id)
            ).all()

            interactions = []
            for acc_id in account_ids:
                interactions.extend(self.interaction_repo.get_for_customer_account(acc_id))

        if not interactions:
            return Section(status="unavailable", reason="No interactions found")

        interactions_data = [
            InteractionData(
                interaction_id=str(i.id),
                interaction_type=i.interaction_type,
                interaction_direction=i.interaction_direction,
                interaction_channel=i.interaction_channel,
                occurred_at=i.occurred_at,
                recorded_by_user_id=str(i.recorded_by_user_id),
                summary_text=i.summary_text,
            ).model_dump()
            for i in sorted(interactions, key=lambda x: x.occurred_at, reverse=True)[:50]
        ]

        return Section(
            status="available", as_of=interactions[0].updated_at, data=interactions_data
        )
