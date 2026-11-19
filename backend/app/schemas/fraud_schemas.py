"""Fraud/scam-related Pydantic schemas"""
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class RiskAssessmentResponse(BaseModel):
    """Risk assessment result"""
    risk_assessment_id: uuid.UUID
    payment_order_id: uuid.UUID
    risk_score: Decimal | None
    decision: str
    treatment_reason_code: str | None
    warning_shown_code: str | None
    case_reference: str | None
    assessed_at: datetime

    model_config = ConfigDict(from_attributes=True)
