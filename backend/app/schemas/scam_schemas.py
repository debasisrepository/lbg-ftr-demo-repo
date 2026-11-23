"""
Scam and unauthorised payment reporting schemas.
Requirement: BR-PAY-014, CON-01, FRD-03, AI-03
Release 2: In-app scam reporting with PSR SD20 and PSRs 2017 compliance
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReportScamRequest(BaseModel):
    """Request to report a scam or unauthorised payment."""
    payment_reference: str = Field(..., max_length=32, description="Payment reference to report")
    report_type: str = Field(..., description="scam_app or unauthorised")
    report_reason: str | None = Field(None, max_length=500, description="Optional customer description")
    
    model_config = ConfigDict(from_attributes=True)


class ScamReportResponse(BaseModel):
    """
    Response after reporting scam or unauthorised payment.
    Provides claim reference, timeline and next steps per PSR SD20 and PSRs 2017 reg. 76.
    """
    report_reference: str = Field(..., max_length=32, description="Unique claim reference")
    report_type: str = Field(..., description="scam_app or unauthorised")
    reported_at: datetime = Field(..., description="When report was submitted")
    status: str = Field(..., description="submitted, under_review, decided, closed")
    timeline_message: str = Field(..., description="Expected timeline and next steps")
    contact_guidance: str = Field(..., description="How customer will be contacted")
    claim_limit_message: str | None = Field(None, description="Claim limits (APP scam: up to £85,000)")
    
    model_config = ConfigDict(from_attributes=True)


class ScamReportStatusResponse(BaseModel):
    """Status of an existing scam report."""
    report_reference: str = Field(..., max_length=32, description="Unique claim reference")
    report_type: str = Field(..., description="scam_app or unauthorised")
    reported_at: datetime = Field(..., description="When report was submitted")
    status: str = Field(..., description="submitted, under_review, decided, closed")
    decision: str | None = Field(None, description="approved, denied, partial (if decided)")
    decided_at: datetime | None = Field(None, description="When decision was made")
    timeline_message: str = Field(..., description="Current status and next steps")
    
    model_config = ConfigDict(from_attributes=True)
