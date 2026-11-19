"""Payment service tests"""
import uuid

from app.services.payment_service import PaymentService


def test_prepare_payment_creates_order(db_session, seeded_data):
    """Test preparing a new payment"""
    payment_service = PaymentService(db_session)

    customer_id = uuid.UUID("10000000-0000-0000-0000-000000000001")
    profile_id = uuid.UUID("10000000-0000-0000-0000-000000000101")
    source_account_id = uuid.uuid5(uuid.NAMESPACE_DNS, "account:acc_current_001")
    payee_id = uuid.UUID("10000000-0000-0000-0000-000000000501")

    result = payment_service.prepare_payment(
        customer_id=customer_id,
        profile_id=profile_id,
        source_account_id=source_account_id,
        payee_id=payee_id,
        amount_minor=5000,
        currency_code="GBP",
        payment_reference="Test payment",
        idempotency_key=f"test_{uuid.uuid4().hex}",
        correlation_id=f"corr_{uuid.uuid4().hex}"
    )

    assert result is not None
    assert "payment_order" in result
    payment_order = result["payment_order"]
    assert payment_order.payment_order_id is not None
    assert payment_order.amount_minor == 5000
    assert payment_order.normalized_status == "pending"


def test_approve_payment_updates_status(db_session, seeded_data):
    """Test approving a payment"""
    payment_service = PaymentService(db_session)

    # First create a payment
    customer_id = uuid.UUID("10000000-0000-0000-0000-000000000001")
    profile_id = uuid.UUID("10000000-0000-0000-0000-000000000101")
    source_account_id = uuid.uuid5(uuid.NAMESPACE_DNS, "account:acc_current_001")
    payee_id = uuid.UUID("10000000-0000-0000-0000-000000000501")
    device_id = uuid.UUID("10000000-0000-0000-0000-000000000201")

    result = payment_service.prepare_payment(
        customer_id=customer_id,
        profile_id=profile_id,
        source_account_id=source_account_id,
        payee_id=payee_id,
        amount_minor=5000,
        currency_code="GBP",
        payment_reference="Test payment",
        idempotency_key=f"test_{uuid.uuid4().hex}",
        correlation_id=f"corr_{uuid.uuid4().hex}"
    )
    payment_order = result["payment_order"]

    # Approve it
    approved_payment = payment_service.approve_payment(
        payment_order_id=payment_order.payment_order_id,
        device_id=device_id,
        customer_id=customer_id,
        correlation_id=f"corr_{uuid.uuid4().hex}"
    )

    assert approved_payment is not None
    assert approved_payment.current_internal_state == "awaiting_sca"


def test_submit_payment_updates_status(db_session, seeded_data):
    """Test submitting a payment"""
    payment_service = PaymentService(db_session)

    # Create and approve a payment
    customer_id = uuid.UUID("10000000-0000-0000-0000-000000000001")
    profile_id = uuid.UUID("10000000-0000-0000-0000-000000000101")
    source_account_id = uuid.uuid5(uuid.NAMESPACE_DNS, "account:acc_current_001")
    payee_id = uuid.UUID("10000000-0000-0000-0000-000000000501")
    device_id = uuid.UUID("10000000-0000-0000-0000-000000000201")

    result = payment_service.prepare_payment(
        customer_id=customer_id,
        profile_id=profile_id,
        source_account_id=source_account_id,
        payee_id=payee_id,
        amount_minor=5000,
        currency_code="GBP",
        payment_reference="Test payment",
        idempotency_key=f"test_{uuid.uuid4().hex}",
        correlation_id=f"corr_{uuid.uuid4().hex}"
    )
    payment_order = result["payment_order"]

    payment_service.approve_payment(
        payment_order_id=payment_order.payment_order_id,
        device_id=device_id,
        customer_id=customer_id,
        correlation_id=f"corr_{uuid.uuid4().hex}"
    )

    # Submit it
    submitted_payment = payment_service.submit_payment(
        payment_order_id=payment_order.payment_order_id,
        customer_id=customer_id,
        correlation_id=f"corr_{uuid.uuid4().hex}"
    )

    assert submitted_payment is not None
    assert submitted_payment.current_internal_state == "submitted"
    assert submitted_payment.external_payment_ref is not None
