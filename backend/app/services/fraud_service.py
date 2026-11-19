"""Fraud assessment service"""
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from ..adapters.fraud_decision_adapter import get_fraud_decision_adapter
from ..models.payment import RiskAssessment
from ..repositories.risk_assessment_repository import RiskAssessmentRepository


class FraudService:
    """Handles fraud/scam risk assessment"""

    def __init__(self, db: Session):
        self.db = db
        self.risk_assessment_repo = RiskAssessmentRepository(db)
        self.fraud_adapter = get_fraud_decision_adapter()

    def assess_payment(
        self,
        payment_order_id: uuid.UUID,
        customer_id: uuid.UUID,
        amount_minor: int,
        payee_id: uuid.UUID,
        correlation_id: str
    ) -> RiskAssessment:
        """Assess payment for fraud risk"""

        # Call fraud decision adapter
        fraud_response = self.fraud_adapter.assess_payment({
            "payment_order_id": str(payment_order_id),
            "customer_id": str(customer_id),
            "amount_minor": amount_minor,
            "payee_id": str(payee_id)
        })

        # Create risk assessment record
        now = datetime.now(datetime.now().astimezone().tzinfo)

        risk_assessment = RiskAssessment(
            risk_assessment_id=uuid.uuid4(),
            payment_order_id=payment_order_id,
            risk_engine_reference=f"risk_{payment_order_id.hex[:8]}",
            risk_score=fraud_response.risk_score,
            decision=fraud_response.decision,
            treatment_reason_code=fraud_response.treatment_reason_code,
            warning_shown_code=None,
            purpose_answer_code=None,
            customer_acknowledged_at=None,
            case_reference=fraud_response.case_reference,
            assessed_at=now,
            correlation_id=correlation_id,
            created_at=now
        )

        return self.risk_assessment_repo.create(risk_assessment)

    def acknowledge_risk_warning(
        self,
        risk_assessment: RiskAssessment,
        purpose_answer_code: str | None = None
    ) -> RiskAssessment:
        """Record customer acknowledgment of risk warning"""

        now = datetime.now(datetime.now().astimezone().tzinfo)
        risk_assessment.customer_acknowledged_at = now
        risk_assessment.purpose_answer_code = purpose_answer_code
        self.db.flush()

        return risk_assessment
