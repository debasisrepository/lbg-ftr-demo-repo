"""IncidentReport repository"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.incident import IncidentReport


class IncidentReportRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, incident_report: IncidentReport) -> IncidentReport:
        self.db.add(incident_report)
        self.db.flush()
        return incident_report

    def get_by_reference(self, incident_reference: str) -> IncidentReport | None:
        result = self.db.execute(
            select(IncidentReport).where(IncidentReport.incident_reference == incident_reference)
        )
        return result.scalar_one_or_none()

    def get_by_reference_and_customer(self, incident_reference: str, customer_id: uuid.UUID) -> IncidentReport | None:
        """H-003: Get by reference with customer ownership check at query level"""
        result = self.db.execute(
            select(IncidentReport).where(
                IncidentReport.incident_reference == incident_reference,
                IncidentReport.customer_id == customer_id
            )
        )
        return result.scalar_one_or_none()

    def get_by_id(self, incident_report_id: uuid.UUID) -> IncidentReport | None:
        result = self.db.execute(
            select(IncidentReport).where(IncidentReport.incident_report_id == incident_report_id)
        )
        return result.scalar_one_or_none()

    def list_by_customer(self, customer_id: uuid.UUID, limit: int = 50) -> list[IncidentReport]:
        result = self.db.execute(
            select(IncidentReport)
            .where(IncidentReport.customer_id == customer_id)
            .order_by(IncidentReport.reported_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
