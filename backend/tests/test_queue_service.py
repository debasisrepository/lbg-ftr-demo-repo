"""Queue service unit tests."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from app.core.clock import FixedClock
from app.services.queue_service import QueueService
from app.models.customers import Customer, CustomerAccount, Invoice
from app.models.receivables import ReceivableItem


def test_execute_refresh(db_session):
    """Test queue refresh execution."""
    now = datetime.now(timezone.utc)
    clock = FixedClock(now)
    
    # Create test data
    customer = Customer(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        sap_customer_ref="CUST001",
        customer_name="Test Customer",
        last_sync_at=now,
    )
    db_session.add(customer)
    db_session.flush()
    
    account = CustomerAccount(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        customer_id=customer.id,
        sap_account_ref="ACCT001",
        company_code="1000",
        currency_code="GBP",
        last_sync_at=now,
    )
    db_session.add(account)
    db_session.flush()
    
    invoice = Invoice(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        customer_account_id=account.id,
        sap_invoice_ref="INV001",
        invoice_number="9000001",
        document_date=now,
        due_date=now,
        invoice_amount=Decimal("1000.00"),
        open_amount=Decimal("1000.00"),
        currency_code="GBP",
        last_sync_at=now,
    )
    db_session.add(invoice)
    db_session.flush()
    
    receivable = ReceivableItem(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        invoice_id=invoice.id,
        customer_account_id=account.id,
        sap_open_item_ref="ITEM001",
        aging_bucket="31-60",
        days_past_due=45,
        open_amount=Decimal("1000.00"),
        currency_code="GBP",
        dispute_indicator=False,
        unapplied_cash_indicator=False,
        last_sync_at=now,
    )
    db_session.add(receivable)
    db_session.commit()
    
    # Execute refresh
    queue_service = QueueService(db_session, clock)
    sync_run = queue_service.execute_refresh(
        scope="full",
        trigger_type="manual",
        triggered_by_user_id=None,
        customer_id=None,
        correlation_id="test-123",
    )
    
    assert sync_run.run_status == "succeeded"
    assert sync_run.records_read >= 0


def test_rank_queue_items_deterministic(db_session):
    """Test deterministic ranking."""
    now = datetime.now(timezone.utc)
    clock = FixedClock(now)
    
    # Create items with known DPD
    customer = Customer(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        sap_customer_ref="CUST001",
        customer_name="Test Customer",
        last_sync_at=now,
    )
    db_session.add(customer)
    db_session.flush()
    
    account = CustomerAccount(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        customer_id=customer.id,
        sap_account_ref="ACCT001",
        company_code="1000",
        currency_code="GBP",
        last_sync_at=now,
    )
    db_session.add(account)
    db_session.flush()
    
    for i, dpd in enumerate([90, 30, 60]):
        invoice = Invoice(
            id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
            customer_account_id=account.id,
            sap_invoice_ref=f"INV{i:03d}",
            invoice_number=f"900000{i}",
            document_date=now,
            due_date=now,
            invoice_amount=Decimal("1000.00"),
            open_amount=Decimal("1000.00"),
            currency_code="GBP",
            last_sync_at=now,
        )
        db_session.add(invoice)
        db_session.flush()
        
        receivable = ReceivableItem(
            id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
            invoice_id=invoice.id,
            customer_account_id=account.id,
            sap_open_item_ref=f"ITEM{i:03d}",
            aging_bucket="31-60",
            days_past_due=dpd,
            open_amount=Decimal("1000.00"),
            currency_code="GBP",
            dispute_indicator=False,
            unapplied_cash_indicator=False,
            last_sync_at=now,
        )
        db_session.add(receivable)
    
    db_session.commit()
    
    # Execute refresh
    queue_service = QueueService(db_session, clock)
    sync_run = queue_service.execute_refresh(
        scope="full",
        trigger_type="manual",
        triggered_by_user_id=None,
        customer_id=None,
        correlation_id="test-123",
    )
    
    # Verify ranking: should be ordered by DPD desc (90, 60, 30)
    queue_repo = queue_service.queue_repo
    items, _ = queue_repo.list_items(limit=10, offset=0)
    
    assert len(items) >= 3
    # Items should be ranked by DPD descending
    ranks = [(item.current_rank, item.receivable_item.days_past_due) for item in items]
    dpd_values = [dpd for _, dpd in sorted(ranks)]
    assert dpd_values == sorted(dpd_values, reverse=True)
