"""Fraud service tests"""
import uuid

from app.services.fraud_service import FraudService


def test_assess_payment_creates_risk_assessment(db_session):
    """Test fraud assessment creation"""
    fraud_service = FraudService(db_session)

    payment_order_id = uuid.uuid4()
    customer_id = uuid.UUID("10000000-0000-0000-0000-000000000001")
    payee_id = uuid.UUID("10000000-0000-0000-0000-000000000501")

    risk_assessment = fraud_service.assess_payment(
        payment_order_id=payment_order_id,
        customer_id=customer_id,
        amount_minor=5000,
        payee_id=payee_id,
        correlation_id=f"corr_{uuid.uuid4().hex}"
    )

    assert risk_assessment is not None
    assert risk_assessment.decision in ("allow", "warn", "challenge", "hold", "block")
    assert risk_assessment.payment_order_id == payment_order_id


def test_high_amount_triggers_warning(db_session):
    """Test that high amounts trigger fraud warning"""
    fraud_service = FraudService(db_session)

    payment_order_id = uuid.uuid4()
    customer_id = uuid.UUID("10000000-0000-0000-0000-000000000001")
    payee_id = uuid.UUID("10000000-0000-0000-0000-000000000501")

    risk_assessment = fraud_service.assess_payment(
        payment_order_id=payment_order_id,
        customer_id=customer_id,
        amount_minor=600000,  # £6000
        payee_id=payee_id,
        correlation_id=f"corr_{uuid.uuid4().hex}"
    )

    assert risk_assessment.decision == "warn"
