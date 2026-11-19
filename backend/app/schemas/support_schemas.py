"""Support/scam claim Pydantic schemas"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ScamClaimCreateRequest(BaseModel):
    """Request to create a scam claim"""
    payment_order_id: uuid.UUID | None = None
    claim_reason_code: str = Field(max_length=64)
    notes: str | None = Field(default=None, max_length=1000)


class ScamClaimResponse(BaseModel):
    """Scam claim details"""
    scam_claim_id: uuid.UUID
    claim_reference: str
    claim_status: str
    claim_reason_code: str | None
    reported_at: datetime
    support_case_reference: str | None
    fraud_case_reference: str | None
    payment_order_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
