"""Incident adapter for external incident management system."""
from datetime import datetime, timedelta
from typing import Any

from app.adapters.base import Adapter, AdapterHealth
from app.config import settings
from app.core.clock import Clock


class IncidentAdapter(Adapter):
    """Adapter for incident management system integration.
    
    In sandbox mode, returns synthetic incident data.
    """

    def __init__(self):
        super().__init__()
        self.mode = settings.adapter_mode

    def get_incidents(self) -> list[dict[str, Any]]:
        """Fetch current incidents from external system.
        
        Returns:
            List of incident dictionaries with structure matching ServiceIncident model.
        """
        if not self.circuit_breaker.can_attempt():
            return []

        try:
            if self.mode == "sandbox":
                incidents = self._get_sandbox_incidents()
            else:
                # In live mode, would call external API
                incidents = []

            self.circuit_breaker.record_success()
            return incidents

        except Exception:
            self.circuit_breaker.record_failure()
            return []

    def _get_sandbox_incidents(self) -> list[dict[str, Any]]:
        """Return synthetic incidents for sandbox mode.
        
        Returns 2 active incidents as specified in task requirements.
        """
        now = Clock.utcnow()
        
        return [
            {
                "incident_reference": "INC-2024-CARD-001",
                "incident_state": "declared",
                "affected_service_code": "card_payments",
                "customer_impact_summary": "Some card payments may be declined. We're working to resolve this.",
                "started_at": now - timedelta(hours=2),
                "resolved_at": None,
            },
            {
                "incident_reference": "INC-2024-MOBILE-002",
                "incident_state": "monitoring",
                "affected_service_code": "mobile_banking",
                "customer_impact_summary": "Mobile app login may be slower than usual. Service is being monitored.",
                "started_at": now - timedelta(hours=1),
                "resolved_at": None,
            },
        ]

    def health(self) -> AdapterHealth:
        """Check adapter health."""
        now = Clock.utcnow()
        
        if self.mode == "sandbox":
            return AdapterHealth(
                available=True,
                message="Sandbox mode operational",
                last_check=now,
            )
        
        # In live mode, would check actual connectivity
        return AdapterHealth(
            available=self.circuit_breaker.can_attempt(),
            message="Live mode - circuit breaker status",
            last_check=now,
        )
