"""Reference data repository for SAP-synchronized entities."""
from typing import List

from sqlalchemy.orm import Session

from app.models.customers import Customer, CustomerAccount, Invoice
from app.models.receivables import ReceivableItem


class ReferenceRepository:
    """Repository for SAP reference data operations."""

    def __init__(self, db: Session):
        self.db = db

    def upsert_customer(self, customer: Customer) -> Customer:
        """Upsert customer."""
        existing = (
            self.db.query(Customer)
            .filter(Customer.sap_customer_ref == customer.sap_customer_ref)
            .first()
        )

        if existing:
            for key, value in customer.__dict__.items():
                if not key.startswith("_") and key != "id":
                    setattr(existing, key, value)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            self.db.add(customer)
            self.db.commit()
            self.db.refresh(customer)
            return customer

    def upsert_customer_account(self, account: CustomerAccount) -> CustomerAccount:
        """Upsert customer account."""
        existing = (
            self.db.query(CustomerAccount)
            .filter(
                CustomerAccount.company_code == account.company_code,
                CustomerAccount.sap_account_ref == account.sap_account_ref,
            )
            .first()
        )

        if existing:
            for key, value in account.__dict__.items():
                if not key.startswith("_") and key != "id":
                    setattr(existing, key, value)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            self.db.add(account)
            self.db.commit()
            self.db.refresh(account)
            return account

    def upsert_invoice(self, invoice: Invoice) -> Invoice:
        """Upsert invoice."""
        existing = (
            self.db.query(Invoice)
            .filter(Invoice.sap_invoice_ref == invoice.sap_invoice_ref)
            .first()
        )

        if existing:
            for key, value in invoice.__dict__.items():
                if not key.startswith("_") and key != "id":
                    setattr(existing, key, value)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            self.db.add(invoice)
            self.db.commit()
            self.db.refresh(invoice)
            return invoice

    def upsert_receivable_item(self, item: ReceivableItem) -> ReceivableItem:
        """Upsert receivable item."""
        existing = (
            self.db.query(ReceivableItem)
            .filter(ReceivableItem.sap_open_item_ref == item.sap_open_item_ref)
            .first()
        )

        if existing:
            for key, value in item.__dict__.items():
                if not key.startswith("_") and key != "id":
                    setattr(existing, key, value)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            self.db.add(item)
            self.db.commit()
            self.db.refresh(item)
            return item

    def get_receivable_items_for_customer(self, customer_account_id: str) -> List[ReceivableItem]:
        """Get all receivable items for a customer account."""
        return (
            self.db.query(ReceivableItem)
            .filter(ReceivableItem.customer_account_id == customer_account_id)
            .all()
        )
