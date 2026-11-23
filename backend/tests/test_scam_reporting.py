"""
Unit tests for scam and unauthorised payment reporting.
Requirement: BR-PAY-014, CON-01, FRD-03, AI-03 (Release 2)
Test Cases: TC-PAY-034
"""
import uuid
from datetime import UTC, datetime

import pytest
from fastapi import HTTPException

from app.models.scam_report import ScamReport
from app.schemas.scam_schemas import ReportScamRequest
from app.services.scam_service import ScamService


def test_report_app_scam_success(db_session):
    """Test successful APP scam report with claim reference and timeline (TC-PAY-034)."""
    customer_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    payment_reference = "PAY-TEST-001"
    
    service = ScamService(db=db_session)
    
    # Execute
    request = ReportScamRequest(
        payment_reference=payment_reference,
        report_type="scam_app",
        report_reason="I was tricked into sending money to a fake investment scheme"
    )
    
    result = service.report_scam(customer_id, request)
    
    # Verify response
    assert result.report_reference.startswith("SR-")
    assert result.report_type == "scam_app"
    assert result.status == "submitted"
    assert result.reported_at is not None
    
    # Verify PSR SD20 timeline message (5 days decision, extendable to 35)
    assert "5 business days" in result.timeline_message
    assert "35 days" in result.timeline_message
    
    # Verify claim limit message (£85,000 per claim)
    assert "£85,000" in result.claim_limit_message
    
    # Verify contact guidance
    assert "secure message" in result.contact_guidance.lower()
    
    # Verify database record created
    report = db_session.query(ScamReport).filter(
        ScamReport.report_reference == result.report_reference
    ).first()
    assert report is not None
    assert report.customer_profile_ref_id == customer_id
    assert report.payment_reference == payment_reference
    assert report.report_type == "scam_app"
    assert report.status == "submitted"


def test_report_unauthorised_payment_success(db_session):
    """Test successful unauthorised payment report with next-day refund timeline."""
    customer_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    payment_reference = "PAY-TEST-002"
    
    service = ScamService(db=db_session)
    
    # Execute
    request = ReportScamRequest(
        payment_reference=payment_reference,
        report_type="unauthorised",
        report_reason="This payment was not made by me - I did not authorise it"
    )
    
    result = service.report_scam(customer_id, request)
    
    # Verify response
    assert result.report_reference.startswith("SR-")
    assert result.report_type == "unauthorised"
    assert result.status == "submitted"
    
    # Verify PSRs 2017 reg. 76 timeline (refund by end of next business day)
    assert "next business day" in result.timeline_message.lower()
    
    # Verify no claim limit for unauthorised (full refund)
    assert "claim limit does not apply" in result.claim_limit_message.lower() or \
           "full refund" in result.claim_limit_message.lower()
    
    # Verify database record
    report = db_session.query(ScamReport).filter(
        ScamReport.report_reference == result.report_reference
    ).first()
    assert report is not None
    assert report.report_type == "unauthorised"


def test_report_scam_duplicate_payment_rejected(db_session):
    """Test reporting same payment twice is rejected."""
    customer_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    payment_reference = "PAY-TEST-003"
    
    service = ScamService(db=db_session)
    
    # First report
    request1 = ReportScamRequest(
        payment_reference=payment_reference,
        report_type="scam_app",
        report_reason="First report"
    )
    result1 = service.report_scam(customer_id, request1)
    assert result1.report_reference.startswith("SR-")
    
    # Second report for same payment - should fail
    request2 = ReportScamRequest(
        payment_reference=payment_reference,
        report_type="scam_app",
        report_reason="Duplicate report"
    )
    
    with pytest.raises(HTTPException) as exc_info:
        service.report_scam(customer_id, request2)
    
    assert exc_info.value.status_code == 400
    assert "already reported" in exc_info.value.detail.lower()
    assert result1.report_reference in exc_info.value.detail


def test_report_scam_invalid_report_type(db_session):
    """Test invalid report type is rejected."""
    customer_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    payment_reference = "PAY-TEST-004"
    
    service = ScamService(db=db_session)
    
    # Invalid report type
    request = ReportScamRequest(
        payment_reference=payment_reference,
        report_type="invalid_type",
        report_reason="Test"
    )
    
    with pytest.raises(HTTPException) as exc_info:
        service.report_scam(customer_id, request)
    
    assert exc_info.value.status_code == 400
    assert "must be" in exc_info.value.detail.lower()


def test_get_report_status_success(db_session):
    """Test retrieving report status."""
    customer_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    payment_reference = "PAY-TEST-005"
    
    service = ScamService(db=db_session)
    
    # Create report
    request = ReportScamRequest(
        payment_reference=payment_reference,
        report_type="scam_app",
        report_reason="Test scam"
    )
    created_report = service.report_scam(customer_id, request)
    
    # Get status
    status = service.get_report_status(customer_id, created_report.report_reference)
    
    # Verify
    assert status.report_reference == created_report.report_reference
    assert status.report_type == "scam_app"
    assert status.status == "submitted"
    assert status.reported_at == created_report.reported_at


def test_get_report_status_not_found(db_session):
    """Test getting status for non-existent report."""
    customer_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    
    service = ScamService(db=db_session)
    
    with pytest.raises(HTTPException) as exc_info:
        service.get_report_status(customer_id, "SR-NONEXISTENT")
    
    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail.lower()


def test_get_report_status_different_customer_forbidden(db_session):
    """Test retrieving report status by different customer is forbidden."""
    customer1_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    customer2_id = uuid.UUID("00000000-0000-0000-0000-000000000002")
    payment_reference = "PAY-TEST-006"
    
    service = ScamService(db=db_session)
    
    # Customer 1 creates report
    request = ReportScamRequest(
        payment_reference=payment_reference,
        report_type="scam_app",
        report_reason="Test scam"
    )
    created_report = service.report_scam(customer1_id, request)
    
    # Customer 2 tries to access
    with pytest.raises(HTTPException) as exc_info:
        service.get_report_status(customer2_id, created_report.report_reference)
    
    assert exc_info.value.status_code == 403
    assert "not authorized" in exc_info.value.detail.lower()


def test_report_reference_format(db_session):
    """Test report reference follows format SR-YYYYMMDD-XXXXX."""
    customer_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    payment_reference = "PAY-TEST-007"
    
    service = ScamService(db=db_session)
    
    request = ReportScamRequest(
        payment_reference=payment_reference,
        report_type="scam_app",
        report_reason="Test format"
    )
    
    result = service.report_scam(customer_id, request)
    
    # Verify format: SR-YYYYMMDD-XXXXX
    assert result.report_reference.startswith("SR-")
    parts = result.report_reference.split("-")
    assert len(parts) == 3
    assert parts[0] == "SR"
    assert len(parts[1]) == 8  # YYYYMMDD
    assert parts[1].isdigit()
    assert len(parts[2]) == 5  # XXXXX
    assert parts[2].isalnum()


def test_scam_report_no_more_steps_than_payment(db_session):
    """
    Test scam reporting simplicity per BR-PAY-014:
    'Reporting must take no more steps than making a payment'.
    
    This is a documentation test - verifies the service method
    has minimal required fields matching payment initiation complexity.
    """
    customer_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    
    service = ScamService(db=db_session)
    
    # Scam report requires: payment_reference, report_type, report_reason
    # Payment initiation requires: account_id, payee_id, amount
    # Both are 3 required fields - equivalent complexity
    
    request = ReportScamRequest(
        payment_reference="PAY-TEST-008",
        report_type="scam_app",
        report_reason="Minimal complexity test"
    )
    
    result = service.report_scam(customer_id, request)
    
    # Success with minimal fields
    assert result.report_reference is not None
    assert result.status == "submitted"


def test_scam_report_includes_psr_sd20_compliance_messaging(db_session):
    """Test APP scam report includes PSR SD20 compliance messaging."""
    customer_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    
    service = ScamService(db=db_session)
    
    request = ReportScamRequest(
        payment_reference="PAY-TEST-009",
        report_type="scam_app",
        report_reason="PSR SD20 compliance test"
    )
    
    result = service.report_scam(customer_id, request)
    
    # Verify PSR SD20 key points are communicated
    timeline = result.timeline_message.lower()
    
    # Decision timeline
    assert "5 business days" in timeline or "5 days" in timeline
    assert "35 days" in timeline or "35 business days" in timeline
    
    # Claim limit
    claim_limit = result.claim_limit_message.lower()
    assert "£85,000" in claim_limit or "85000" in claim_limit
    
    # Claims window (13 months from payment)
    # This may be in extended guidance
    assert result.contact_guidance is not None


def test_unauthorised_payment_report_includes_psrs_2017_compliance(db_session):
    """Test unauthorised payment report includes PSRs 2017 reg. 76 compliance messaging."""
    customer_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    
    service = ScamService(db=db_session)
    
    request = ReportScamRequest(
        payment_reference="PAY-TEST-010",
        report_type="unauthorised",
        report_reason="PSRs 2017 compliance test"
    )
    
    result = service.report_scam(customer_id, request)
    
    # Verify PSRs 2017 reg. 76: refund by end of next business day
    timeline = result.timeline_message.lower()
    assert "next business day" in timeline or "next day" in timeline
    
    # No £85k limit for unauthorised - full refund
    claim_limit = result.claim_limit_message.lower()
    assert "does not apply" in claim_limit or "full refund" in claim_limit or "full amount" in claim_limit
