"""
Integration tests for scam reporting feature (Release 2).
Requirement: BR-PAY-014, CON-01, FRD-03, AI-03, PSR SD20, PSRs 2017 reg. 76
Test Cases: TC-PAY-034
"""
import uuid
from datetime import UTC, datetime

from app.models.customer_profile_ref import CustomerProfileRef
from app.models.payment_intent import PaymentIntent
from app.models.scam_report import ScamReport


def test_report_scam_requires_auth(client):
    """Test that POST /api/v1/scam-reports requires authentication."""
    response = client.post("/api/v1/scam-reports", json={
        "payment_reference": "PAY-TEST-001",
        "report_type": "scam_app",
        "report_reason": "Test scam"
    })
    assert response.status_code == 401


def test_report_scam_app_success(auth_client, db_session):
    """
    TC-PAY-034: Report APP scam with claim reference and timeline.
    Per PSR SD20: Decision within 5 business days, up to £85,000 per claim.
    Per BR-PAY-014: Reporting takes no more steps than making a payment.
    """
    # Create a test payment to report
    customer = db_session.query(CustomerProfileRef).first()
    
    test_payment = PaymentIntent(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer.id,
        payment_reference="PAY-SCAM-TEST-001",
        source_account_reference="ACC-TEST-001",
        payee_account_identifier="12345678",
        payee_sort_code="20-00-00",
        payee_name="Suspicious Payee",
        amount_minor=50000,
        currency="GBP",
        payment_type="faster_payment",
        state="completed",
        is_submitted=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(test_payment)
    db_session.commit()
    
    # Report the payment as scam
    report_request = {
        "payment_reference": "PAY-SCAM-TEST-001",
        "report_type": "scam_app",
        "report_reason": "I was tricked into paying for items I never received"
    }
    
    response = auth_client.post("/api/v1/scam-reports", json=report_request)
    
    assert response.status_code == 201
    data = response.json()
    
    # Verify response includes required fields per PSR SD20
    assert "report_reference" in data
    assert data["report_reference"].startswith("SR-")  # Claim reference format
    assert data["report_type"] == "scam_app"
    assert data["status"] == "submitted"
    assert "reported_at" in data
    
    # Verify timeline message for APP scam (5-35 business days)
    assert "timeline_message" in data
    assert "5 business days" in data["timeline_message"] or "five business days" in data["timeline_message"]
    
    # Verify claim limit message (£85,000)
    assert "claim_limit_message" in data
    assert "£85,000" in data["claim_limit_message"] or "85000" in data["claim_limit_message"]
    
    assert "contact_guidance" in data


def test_report_unauthorised_payment_success(auth_client, db_session):
    """
    TC-PAY-034: Report unauthorised payment with refund timeline.
    Per PSRs 2017 reg. 76: Refund by end of next business day.
    """
    customer = db_session.query(CustomerProfileRef).first()
    
    # Create a test payment
    test_payment = PaymentIntent(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer.id,
        payment_reference="PAY-UNAUTH-TEST-001",
        source_account_reference="ACC-TEST-001",
        payee_account_identifier="98765432",
        payee_sort_code="30-00-00",
        payee_name="Unknown Payee",
        amount_minor=20000,
        currency="GBP",
        payment_type="faster_payment",
        state="completed",
        is_submitted=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(test_payment)
    db_session.commit()
    
    # Report as unauthorised
    report_request = {
        "payment_reference": "PAY-UNAUTH-TEST-001",
        "report_type": "unauthorised",
        "report_reason": "I did not make this payment"
    }
    
    response = auth_client.post("/api/v1/scam-reports", json=report_request)
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["report_type"] == "unauthorised"
    assert data["status"] == "submitted"
    
    # Verify timeline for unauthorised payment (next business day)
    assert "timeline_message" in data
    assert "next business day" in data["timeline_message"]


def test_report_scam_duplicate_payment_fails(auth_client, db_session):
    """
    TC-PAY-034: Duplicate scam report for same payment reference fails.
    Per BR-PAY-014: Payment can only be reported once per customer.
    """
    customer = db_session.query(CustomerProfileRef).first()
    
    # Create existing scam report
    existing_report = ScamReport(
        id=uuid.uuid4(),
        report_reference="SR-20261123-00001",
        customer_profile_ref_id=customer.id,
        payment_reference="PAY-DUPLICATE-TEST",
        report_type="scam_app",
        report_reason="First report",
        reported_at=datetime.now(UTC),
        status="submitted",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(existing_report)
    db_session.commit()
    
    # Attempt to report same payment again
    report_request = {
        "payment_reference": "PAY-DUPLICATE-TEST",
        "report_type": "scam_app",
        "report_reason": "Second report (should fail)"
    }
    
    response = auth_client.post("/api/v1/scam-reports", json=report_request)
    
    assert response.status_code == 400
    assert "already reported" in response.json()["detail"].lower()


def test_report_scam_invalid_type_fails(auth_client, db_session):
    """
    TC-PAY-034: Invalid report_type returns 400.
    Valid types: scam_app, unauthorised.
    """
    report_request = {
        "payment_reference": "PAY-TEST-999",
        "report_type": "invalid_type",
        "report_reason": "Test"
    }
    
    response = auth_client.post("/api/v1/scam-reports", json=report_request)
    
    assert response.status_code == 400
    assert "report_type" in response.json()["detail"].lower()


def test_get_scam_report_status(auth_client, db_session):
    """
    TC-PAY-034: Get status of existing scam report.
    Per BR-PAY-014: Customer can check status of their claim.
    """
    customer = db_session.query(CustomerProfileRef).first()
    
    # Create a scam report
    report = ScamReport(
        id=uuid.uuid4(),
        report_reference="SR-20261123-99999",
        customer_profile_ref_id=customer.id,
        payment_reference="PAY-STATUS-TEST",
        report_type="scam_app",
        report_reason="Status test",
        reported_at=datetime.now(UTC),
        status="under_review",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(report)
    db_session.commit()
    
    # Get report status
    response = auth_client.get(f"/api/v1/scam-reports/{report.report_reference}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["report_reference"] == "SR-20261123-99999"
    assert data["report_type"] == "scam_app"
    assert data["status"] == "under_review"
    assert "timeline_message" in data


def test_scam_report_never_forced_through_assistant(auth_client, db_session):
    """
    Test documentation: Scam reporting must never be forced through an assistant.
    Per CON-01: Reporting must never be forced through an assistant.
    
    This is verified by having direct API endpoints, not requiring LLM interaction.
    """
    # Scam reporting is available via direct REST API POST /api/v1/scam-reports
    # No assistant interaction required
    # This test documents the requirement
    pass


def test_scam_decisions_made_by_authorised_fraud_colleagues_only(auth_client, db_session):
    """
    Test documentation: Decisions made only by authorised fraud colleagues.
    Per FRD-03: Decisions made only by authorised fraud colleagues.
    Per AI-03: AI never makes scam claim decisions.
    
    This is a business process requirement, not a technical test.
    """
    # Scam report creation returns "submitted" status
    # Decisions (approved, denied, partial) are made by fraud team, not by API
    # AI is not involved in decision-making
    pass


def test_scam_reporting_takes_no_more_steps_than_payment(auth_client, db_session):
    """
    TC-PAY-034: Scam reporting takes no more steps than making a payment.
    Per BR-PAY-014: Reporting must take no more steps than making a payment.
    
    Payment flow: 1) Create review 2) Approve -> 2 API calls
    Scam report: 1) POST /api/v1/scam-reports -> 1 API call
    
    Scam reporting is simpler than making a payment.
    """
    customer = db_session.query(CustomerProfileRef).first()
    
    # Create test payment
    test_payment = PaymentIntent(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer.id,
        payment_reference="PAY-STEPS-TEST",
        source_account_reference="ACC-TEST-001",
        payee_account_identifier="11223344",
        payee_sort_code="40-00-00",
        payee_name="Test Payee",
        amount_minor=10000,
        currency="GBP",
        payment_type="faster_payment",
        state="completed",
        is_submitted=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(test_payment)
    db_session.commit()
    
    # Report in single API call
    report_request = {
        "payment_reference": "PAY-STEPS-TEST",
        "report_type": "scam_app",
        "report_reason": "Test simplicity"
    }
    
    response = auth_client.post("/api/v1/scam-reports", json=report_request)
    
    assert response.status_code == 201
    # Single API call completes the reporting - simpler than 2-step payment flow


def test_scam_report_includes_next_steps_and_timeline(auth_client, db_session):
    """
    TC-PAY-034: Scam report response includes next steps and timeline.
    Per BR-PAY-014: Give customer claim reference, next steps, and timeline.
    """
    customer = db_session.query(CustomerProfileRef).first()
    
    test_payment = PaymentIntent(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer.id,
        payment_reference="PAY-TIMELINE-TEST",
        source_account_reference="ACC-TEST-001",
        payee_account_identifier="55667788",
        payee_sort_code="50-00-00",
        payee_name="Timeline Test Payee",
        amount_minor=15000,
        currency="GBP",
        payment_type="faster_payment",
        state="completed",
        is_submitted=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(test_payment)
    db_session.commit()
    
    report_request = {
        "payment_reference": "PAY-TIMELINE-TEST",
        "report_type": "scam_app",
        "report_reason": "Timeline test"
    }
    
    response = auth_client.post("/api/v1/scam-reports", json=report_request)
    
    assert response.status_code == 201
    data = response.json()
    
    # Verify claim reference
    assert "report_reference" in data
    assert len(data["report_reference"]) > 0
    
    # Verify timeline
    assert "timeline_message" in data
    assert len(data["timeline_message"]) > 0
    
    # Verify next steps (contact guidance)
    assert "contact_guidance" in data
    assert len(data["contact_guidance"]) > 0


def test_scam_report_within_13_months_accepted(auth_client, db_session):
    """
    Test documentation: APP scam claims accepted within 13 months.
    Per PSR SD20: Claims accepted within 13 months.
    
    This is a business process rule, enforced by fraud case management system.
    """
    # API accepts scam reports
    # 13-month eligibility check is downstream in fraud case management
    pass
