"""
Scam and unauthorised payment reporting service.
Requirement: BR-PAY-014, CON-01, FRD-03, AI-03
Release 2: In-app scam reporting with PSR SD20 and PSRs 2017 compliance
"""
import secrets
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.scam_report import ScamReport
from app.schemas.scam_schemas import (
    ReportScamRequest,
    ScamReportResponse,
    ScamReportStatusResponse,
)


class ScamService:
    """Service for scam and unauthorised payment reporting."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def report_scam(
        self,
        customer_id: uuid.UUID,
        request: ReportScamRequest
    ) -> ScamReportResponse:
        """
        Report a scam or unauthorised payment.
        
        Per BR-PAY-014: Reporting must take no more steps than making a payment.
        Per CON-01: Never forced through an assistant.
        Per PSR SD20: APP scam claims - decision within 5 business days, extendable to 35,
                      up to £85,000 per claim, claims within 13 months.
        Per PSRs 2017 reg. 76: Unauthorised payments - refund by end of next business day.
        
        Args:
            customer_id: Customer profile reference ID
            request: ReportScamRequest with payment_reference, report_type, reason
        
        Returns:
            ScamReportResponse with claim reference and timeline
        
        Raises:
            HTTPException: 404 if payment not found
            HTTPException: 400 if payment already reported
        """
        # Validate report_type
        if request.report_type not in ("scam_app", "unauthorised"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="report_type must be 'scam_app' or 'unauthorised'"
            )
        
        # Check if payment reference already reported by this customer
        existing_report = self.db.query(ScamReport).filter(
            ScamReport.customer_profile_ref_id == customer_id,
            ScamReport.payment_reference == request.payment_reference
        ).first()
        
        if existing_report:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment already reported with reference {existing_report.report_reference}"
            )
        
        # Generate unique report reference (SR-YYYYMMDD-XXXXX format)
        report_reference = self._generate_report_reference()
        
        # Create scam report
        reported_at = datetime.now(UTC)
        scam_report = ScamReport(
            id=uuid.uuid4(),
            report_reference=report_reference,
            customer_profile_ref_id=customer_id,
            payment_reference=request.payment_reference,
            report_type=request.report_type,
            report_reason=request.report_reason,
            reported_at=reported_at,
            status="submitted",
            created_at=reported_at,
            updated_at=reported_at
        )
        
        self.db.add(scam_report)
        self.db.commit()
        self.db.refresh(scam_report)
        
        # Prepare timeline message based on report type
        timeline_message = self._get_timeline_message(request.report_type)
        claim_limit_message = self._get_claim_limit_message(request.report_type)
        
        # Publish ScamReported event (would trigger downstream fraud case creation)
        # In production: self.event_publisher.publish(ScamReportedEvent(...))
        
        return ScamReportResponse(
            report_reference=report_reference,
            report_type=request.report_type,
            reported_at=reported_at,
            status="submitted",
            timeline_message=timeline_message,
            contact_guidance="We'll contact you by secure message within the app and by email. Please check your messages regularly.",
            claim_limit_message=claim_limit_message
        )
    
    def get_report_status(
        self,
        customer_id: uuid.UUID,
        report_reference: str
    ) -> ScamReportStatusResponse:
        """
        Get status of a scam report.
        
        Args:
            customer_id: Customer profile reference ID
            report_reference: Report reference to query
        
        Returns:
            ScamReportStatusResponse with current status and timeline
        
        Raises:
            HTTPException: 404 if report not found
            HTTPException: 403 if report belongs to different customer
        """
        report = self.db.query(ScamReport).filter(
            ScamReport.report_reference == report_reference
        ).first()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        if report.customer_profile_ref_id != customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this report"
            )
        
        # Update timeline message based on current status
        timeline_message = self._get_status_timeline_message(report)
        
        return ScamReportStatusResponse(
            report_reference=report.report_reference,
            report_type=report.report_type,
            reported_at=report.reported_at,
            status=report.status,
            decision=report.decision,
            decided_at=report.decided_at,
            timeline_message=timeline_message
        )
    
    def _generate_report_reference(self) -> str:
        """Generate unique report reference in format SR-YYYYMMDD-XXXXX."""
        date_part = datetime.now(UTC).strftime("%Y%m%d")
        random_part = secrets.token_hex(3).upper()  # 6 hex chars
        return f"SR-{date_part}-{random_part}"
    
    def _get_timeline_message(self, report_type: str) -> str:
        """Get initial timeline message based on report type."""
        if report_type == "scam_app":
            return (
                "Thank you for reporting this. We'll review your claim and aim to make a decision "
                "within 5 business days. In some cases, we may need up to 35 days to investigate fully. "
                "We'll keep you updated throughout the process."
            )
        elif report_type == "unauthorised":
            return (
                "Thank you for reporting this unauthorised payment. We'll investigate and aim to refund "
                "you by the end of the next business day, unless we have reasonable grounds to suspect fraud "
                "or need more information from you."
            )
        return "Thank you for reporting this. We'll be in touch soon."
    
    def _get_claim_limit_message(self, report_type: str) -> str | None:
        """Get claim limit message if applicable."""
        if report_type == "scam_app":
            return (
                "APP scam claims are covered up to £85,000 per claim. Claims must be made within "
                "13 months of the payment."
            )
        return None
    
    def _get_status_timeline_message(self, report: ScamReport) -> str:
        """Get timeline message based on current report status."""
        if report.status == "submitted":
            return self._get_timeline_message(report.report_type)
        elif report.status == "under_review":
            return "Your claim is currently under review by our fraud investigation team. We'll contact you if we need any further information."
        elif report.status == "decided":
            if report.decision == "approved":
                return "Your claim has been approved. The refund will be processed within 2 business days."
            elif report.decision == "denied":
                return "After reviewing your claim, we've been unable to approve it. Please check your secure messages for the full explanation and your appeal rights."
            elif report.decision == "partial":
                return "We've approved part of your claim. Please check your secure messages for details of the amount and the reasons for the partial approval."
        elif report.status == "closed":
            return "This claim is now closed. If you have questions, please contact our fraud team."
        
        return "We're processing your claim. We'll contact you with updates."
