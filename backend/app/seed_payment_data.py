"""Payment seed data functions (for seed.py)"""
import hashlib
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from .models.payment import PaymentLimit, PaymentOrder


def _seed_payment_limits(db: Session) -> None:
    """Seed payment limits for demo profile"""
    demo_profile_id = uuid.UUID("10000000-0000-0000-0000-000000000101")

    # Check if limits already exist
    limit_id = uuid.UUID("10000000-0000-0000-0000-000000000601")
    existing = db.get(PaymentLimit, limit_id)
    if existing:
        print("Payment limits already exist, skipping")
        return

    now = datetime.now(UTC)

    # Per-payment limit: £5000
    limit_per_payment = PaymentLimit(
        payment_limit_id=limit_id,
        profile_id=demo_profile_id,
        bank_account_id=None,
        limit_type="per_payment",
        payment_type="faster_payment",
        amount_limit_minor=500000,  # £5000
        currency_code="GBP",
        source_policy_ref="default_retail_policy",
        effective_from=now,
        effective_to=None,
        created_at=now,
        updated_at=now
    )
    db.add(limit_per_payment)

    # Daily limit: £10000
    limit_daily = PaymentLimit(
        payment_limit_id=uuid.UUID("10000000-0000-0000-0000-000000000602"),
        profile_id=demo_profile_id,
        bank_account_id=None,
        limit_type="daily",
        payment_type="faster_payment",
        amount_limit_minor=1000000,  # £10000
        currency_code="GBP",
        source_policy_ref="default_retail_policy",
        effective_from=now,
        effective_to=None,
        created_at=now,
        updated_at=now
    )
    db.add(limit_daily)

    print("Seeded payment limits (£5000 per payment, £10000 daily)")


def _seed_demo_payment(db: Session) -> None:
    """Seed a demo payment order"""
    demo_customer_id = uuid.UUID("10000000-0000-0000-0000-000000000001")
    demo_profile_id = uuid.UUID("10000000-0000-0000-0000-000000000101")
    payee_id = uuid.UUID("10000000-0000-0000-0000-000000000501")  # Jamie Clarke
    account_id = uuid.uuid5(uuid.NAMESPACE_DNS, "account:acc_current_001")

    # Check if demo payment already exists
    payment_id = uuid.UUID("10000000-0000-0000-0000-000000000701")
    existing = db.get(PaymentOrder, payment_id)
    if existing:
        print("Demo payment already exists, skipping")
        return

    now = datetime.now(UTC)

    # Create pending payment for demo
    payment_order = PaymentOrder(
        payment_order_id=payment_id,
        customer_id=demo_customer_id,
        profile_id=demo_profile_id,
        source_account_id=account_id,
        payee_id=payee_id,
        cop_check_id=None,
        idempotency_key=f"demo_payment_{payment_id.hex[:16]}",
        customer_payment_ref="PAYDEMO001",
        payment_reference="Thanks!",
        amount_minor=4000,  # £40.00
        currency_code="GBP",
        payment_type="faster_payment",
        dynamic_link_digest=hashlib.sha256(f"{account_id}:{payee_id}:4000:GBP:Thanks!".encode()).hexdigest(),
        external_payment_ref=None,
        current_internal_state="awaiting_sca",
        normalized_status="pending",
        latest_status_at=now,
        duplicate_suppression_until=None,
        expected_arrival_text=None,
        submitted_at=None,
        completed_at=None,
        correlation_id=f"seed_{uuid.uuid4().hex[:8]}",
        created_at=now,
        updated_at=now
    )
    db.add(payment_order)

    print("Seeded demo payment (£40.00 to Jamie Clarke, pending approval)")
