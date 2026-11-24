"""SAP reference synchronizer."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict

from sqlalchemy.orm import Session

from app.adapters.sap import SapReceivablesReader
from app.core.errors import SapUnavailableError
from app.core.logging import get_logger
from app.models.customers import Customer, CustomerAccount, Invoice
from app.models.receivables import ReceivableItem
from app.repositories.reference_repository import ReferenceRepository

logger = get_logger(__name__)


class SapReferenceSynchronizer:
    """Synchronizes SAP reference data into local tables."""

    def __init__(self, db: Session, sap_reader: SapReceivablesReader):
        self.db = db
        self.sap_reader = sap_reader
        self.repo = ReferenceRepository(db)

    def sync_open_items(self, company_code: str, customer_account_ref: str = None) -> Dict[str, int]:
        """Sync open items from SAP.
        
        Returns:
            Dictionary with counts: records_read, records_upserted
        """
        try:
            items_data = self.sap_reader.read_open_items(company_code, customer_account_ref)
        except Exception as exc:
            logger.error("sap_read_failed", error=str(exc))
            raise SapUnavailableError("Failed to read from SAP", code="sap_read_failed")

        now = datetime.now(timezone.utc)
        records_read = len(items_data)
        records_upserted = 0

        for item_data in items_data:
            # Upsert customer
            customer = Customer(
                id=uuid.uuid4(),
                created_at=now,
                updated_at=now,
                sap_customer_ref=item_data["sap_customer_ref"],
                customer_name=item_data["customer_name"],
                last_sync_at=now,
            )
            customer = self.repo.upsert_customer(customer)

            # Upsert customer account
            account = CustomerAccount(
                id=uuid.uuid4(),
                created_at=now,
                updated_at=now,
                customer_id=customer.id,
                sap_account_ref=item_data["sap_account_ref"],
                company_code=item_data["company_code"],
                currency_code=item_data["currency_code"],
                last_sync_at=now,
            )
            account = self.repo.upsert_customer_account(account)

            # Upsert invoice
            invoice = Invoice(
                id=uuid.uuid4(),
                created_at=now,
                updated_at=now,
                customer_account_id=account.id,
                sap_invoice_ref=item_data["sap_invoice_ref"],
                invoice_number=item_data["invoice_number"],
                document_date=datetime.fromisoformat(item_data["document_date"]),
                due_date=datetime.fromisoformat(item_data["due_date"]),
                invoice_amount=Decimal(item_data["invoice_amount"]),
                open_amount=Decimal(item_data["open_amount"]),
                currency_code=item_data["currency_code"],
                last_sync_at=now,
            )
            invoice = self.repo.upsert_invoice(invoice)

            # Upsert receivable item
            receivable = ReceivableItem(
                id=uuid.uuid4(),
                created_at=now,
                updated_at=now,
                invoice_id=invoice.id,
                customer_account_id=account.id,
                sap_open_item_ref=item_data["sap_open_item_ref"],
                aging_bucket=item_data["aging_bucket"],
                days_past_due=item_data["days_past_due"],
                open_amount=Decimal(item_data["open_amount"]),
                currency_code=item_data["currency_code"],
                dispute_indicator=item_data["dispute_indicator"],
                unapplied_cash_indicator=item_data["unapplied_cash_indicator"],
                last_sync_at=now,
            )
            receivable = self.repo.upsert_receivable_item(receivable)
            records_upserted += 1

        return {
            "records_read": records_read,
            "records_upserted": records_upserted,
        }
