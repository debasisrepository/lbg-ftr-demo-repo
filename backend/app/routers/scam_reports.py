"""
Scam reporting router for in-app scam and unauthorised payment reporting.
Requirement: BR-PAY-014, CON-01, FRD-03, AI-03
Release 2: Scam reporting with PSR SD20 and PSRs 2017 compliance
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.middleware.correlation_middleware import get_correlation_id
from app.models.customer_profile_ref import CustomerProfileRef
from app.schemas.scam_schemas import (
    ReportScamRequest,
    ScamReportResponse,
    ScamReportStatusResponse,
)
from app.services.scam_service import ScamService

router = APIRouter()


@router.post("/", response_model=ScamReportResponse)
def report_scam(
    request: ReportScamRequest,
    db: Session = Depends(get_db),
    current_user: CustomerProfileRef = Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id)
) -> ScamReportResponse:
    """
    POST /api/v1/scam-reports - Report a scam or unauthorised payment.
    
    Per BR-PAY-014: Reporting must take no more steps than making a payment.
    Per CON-01: Never forced through an assistant.
    Per FRD-03, AI-03: Decisions made only by authorised fraud colleagues (not AI).
    
    Per PSR SD20 (APP scams):
    - Decision normally within 5 business days, extendable to 35 with reason
    - Up to £85,000 per claim
    - Claims accepted within 13 months
    
    Per PSRs 2017 reg. 76 (Unauthorised):
    - Refund by end of next business day
    
    Request body:
        {
          "payment_reference": "string",
          "report_type": "scam_app" | "unauthorised",
          "report_reason": "optional customer description"
        }
    
    Returns:
        ScamReportResponse with claim reference and timeline
    
    Raises:
        401: Invalid or expired session
        400: Invalid report_type or payment already reported
        404: Payment not found
    """
    scam_service = ScamService(db)
    
    return scam_service.report_scam(
        customer_id=current_user.id,
        request=request
    )


@router.get("/{report_reference}", response_model=ScamReportStatusResponse)
def get_report_status(
    report_reference: Annotated[str, Path(max_length=32)],
    db: Session = Depends(get_db),
    current_user: CustomerProfileRef = Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id)
) -> ScamReportStatusResponse:
    """
    GET /api/v1/scam-reports/{report_reference} - Get scam report status.
    
    Returns current status, decision (if made), and timeline message.
    
    Returns:
        ScamReportStatusResponse with status and timeline
    
    Raises:
        401: Invalid or expired session
        403: Report belongs to different customer
        404: Report not found
    """
    scam_service = ScamService(db)
    
    return scam_service.get_report_status(
        customer_id=current_user.id,
        report_reference=report_reference
    )
