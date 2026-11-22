"""Incident reporting Pydantic schemas"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class IncidentReportCreateRequest(BaseModel):
    """Request to create an incident report"""
    incident_category: str = Field(max_length=64)
    incident_title: str = Field(max_length=255)
    incident_description: str | None = Field(default=None, max_length=2000)
    severity: str = Field(default='medium', max_length=16)


class IncidentReportResponse(BaseModel):
    """Incident report details"""
    incident_report_id: uuid.UUID
    customer_id: uuid.UUID
    incident_reference: str
    incident_category: str
    incident_title: str
    incident_description: str | None
    severity: str
    status: str
    external_incident_ref: str | None
    reported_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
