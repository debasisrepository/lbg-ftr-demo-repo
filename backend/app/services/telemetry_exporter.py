"""Telemetry exporter service"""
from ..adapters.observability_adapter import get_observability_adapter


class TelemetryExporter:
    """Exports telemetry to observability platform"""

    def __init__(self):
        self.observability_adapter = get_observability_adapter()

    def emit_payment_metric(
        self,
        metric_name: str,
        value: float,
        payment_type: str | None = None
    ) -> None:
        """Emit payment-related metric"""
        tags = {}
        if payment_type:
            tags["payment_type"] = payment_type

        self.observability_adapter.emit_metric(metric_name, value, tags)

    def emit_payment_event(
        self,
        event_type: str,
        payment_id: str,
        status: str
    ) -> None:
        """Emit payment event"""
        self.observability_adapter.emit_event(event_type, {
            "payment_id": payment_id,
            "status": status
        })
