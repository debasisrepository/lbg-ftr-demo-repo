"""Capability health registry"""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class HealthStatus:
    """Health status for a capability"""
    capability: str
    status: str
    message: str | None = None
    last_check: datetime | None = None


class CapabilityHealthRegistry:
    """Registry for capability health status"""

    def __init__(self):
        self._health_statuses: dict[str, HealthStatus] = {}

    def register_capability(self, capability: str, status: str, message: str | None = None) -> None:
        """Register or update capability health status"""
        self._health_statuses[capability] = HealthStatus(
            capability=capability,
            status=status,
            message=message,
            last_check=datetime.now(datetime.now().astimezone().tzinfo)
        )

    def get_capability_status(self, capability: str) -> HealthStatus | None:
        """Get health status for a capability"""
        return self._health_statuses.get(capability)

    def get_all_statuses(self) -> list[HealthStatus]:
        """Get all capability health statuses"""
        return list(self._health_statuses.values())

    def is_healthy(self) -> bool:
        """Check if all capabilities are healthy"""
        return all(status.status == "ok" for status in self._health_statuses.values())


# Global registry instance
health_registry = CapabilityHealthRegistry()
