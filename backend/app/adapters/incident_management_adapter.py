"""Incident Management System adapter (stub for IT service management tool)"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from ..core.adapters import AdapterBase


@dataclass
class IncidentCreationResponse:
    """Incident management system creation response"""
    success: bool
    external_incident_ref: str | None
    status: str
    error_message: str | None


class IncidentManagementAdapter(AdapterBase, ABC):
    """Abstract incident management adapter"""

    @abstractmethod
    def create_incident(self, incident_data: dict[str, Any]) -> IncidentCreationResponse:
        """Create incident in external system"""
        pass


class StubIncidentManagementAdapter(IncidentManagementAdapter):
    """Stub implementation for incident management"""

    def __init__(self):
        super().__init__(adapter_name="incident_management_stub")

    def create_incident(self, incident_data: dict[str, Any]) -> IncidentCreationResponse:
        incident_id = incident_data.get("incident_id", "unknown")

        # Simulate external incident reference
        external_ref = f"INC{incident_id[:8].upper()}"

        return IncidentCreationResponse(
            success=True,
            external_incident_ref=external_ref,
            status="acknowledged",
            error_message=None
        )


class LiveIncidentManagementAdapter(IncidentManagementAdapter):
    """Live implementation (placeholder)"""

    def create_incident(self, incident_data: dict[str, Any]) -> IncidentCreationResponse:
        raise NotImplementedError("Live incident management adapter not implemented")


def get_incident_management_adapter() -> IncidentManagementAdapter:
    return StubIncidentManagementAdapter()
