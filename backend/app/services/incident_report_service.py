"""Incident report service (BR-OPS-008)"""
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from ..adapters.incident_management_adapter import get_incident_management_adapter
from ..core.errors import ValidationError
from ..models.incident import IncidentReport
from ..repositories.incident_report_repository import IncidentReportRepository


class IncidentReportService:
    """Handles incident reporting for operational issues"""

    def __init__(self, db: Session):
        self.db = db
        self.incident_report_repo = IncidentReportRepository(db)
        self.incident_management_adapter = get_incident_management_adapter()

    def create_incident_report(
        self,
        customer_id: uuid.UUID,
        incident_category: str,
        incident_title: str,
        incident_description: str | None,
        severity: str,
        correlation_id: str
    ) -> IncidentReport:
        """Create a new incident report"""

        # Validate category
        valid_categories = ['technical_issue', 'service_outage', 'data_issue', 'security_concern', 'other']
        if incident_category not in valid_categories:
            raise ValidationError(f"Invalid incident category. Must be one of: {', '.join(valid_categories)}")

        # Validate severity
        valid_severities = ['low', 'medium', 'high', 'critical']
        if severity not in valid_severities:
            raise ValidationError(f"Invalid severity. Must be one of: {', '.join(valid_severities)}")

        now = datetime.now(datetime.now().astimezone().tzinfo)

        # Generate incident reference
        incident_reference = f"INC{uuid.uuid4().hex[:8].upper()}"

        # Create incident report
        incident_report = IncidentReport(
            incident_report_id=uuid.uuid4(),
            customer_id=customer_id,
            incident_reference=incident_reference,
            incident_category=incident_category,
            incident_title=incident_title,
            incident_description=incident_description,
            severity=severity,
            status="reported",
            external_incident_ref=None,
            reported_at=now,
            correlation_id=correlation_id,
            created_at=now,
            updated_at=now
        )

        incident_report = self.incident_report_repo.create(incident_report)

        # Submit to external incident management system
        external_response = self.incident_management_adapter.create_incident({
            "incident_id": str(incident_report.incident_report_id),
            "customer_id": str(customer_id),
            "category": incident_category,
            "title": incident_title,
            "description": incident_description,
            "severity": severity
        })

        if external_response.success:
            incident_report.external_incident_ref = external_response.external_incident_ref
            incident_report.status = external_response.status

        self.db.flush()

        return incident_report

    def get_incident_report(self, incident_reference: str) -> IncidentReport:
        """Get incident report by reference"""
        incident_report = self.incident_report_repo.get_by_reference(incident_reference)
        if not incident_report:
            raise ValidationError("Incident report not found")
        return incident_report

    def get_incident_report_for_customer(self, incident_reference: str, customer_id: uuid.UUID) -> IncidentReport:
        """H-003: Get incident report by reference with customer ownership check at DB level"""
        incident_report = self.incident_report_repo.get_by_reference_and_customer(incident_reference, customer_id)
        if not incident_report:
            raise ValidationError("Incident report not found")
        return incident_report

    def list_customer_incidents(self, customer_id: uuid.UUID, limit: int = 50) -> list[IncidentReport]:
        """List incident reports for a customer"""
        return self.incident_report_repo.list_by_customer(customer_id, limit)
