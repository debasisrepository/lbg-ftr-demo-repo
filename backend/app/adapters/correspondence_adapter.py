"""Correspondence adapter for notifications."""
import os
import uuid
import httpx
from datetime import datetime, timezone

from app.adapters.base import Adapter, AdapterHealth
from app.core.errors import DependencyUnavailable


class CorrespondenceAdapter(Adapter):
    """Adapter for sending push notifications through correspondence system."""

    def __init__(self):
        self.mode = os.getenv("ADAPTER_MODE", "sandbox")
        self.gateway_base_url = os.getenv("GATEWAY_BASE_URL", "")

    def send_push_notification(
        self,
        customer_party_id: str,
        safe_preview_text: str,
        deep_link_token: str
    ) -> dict:
        """Send a push notification with safe preview text and deep link token.

        Args:
            customer_party_id: Customer identifier
            safe_preview_text: Safe preview text (no sensitive data)
            deep_link_token: One-time deep link token

        Returns:
            dict with delivery_id and delivery_state
        """
        if not self.circuit_breaker.can_attempt():
            raise DependencyUnavailable("CorrespondenceAdapter circuit breaker is open")

        try:
            if self.mode == "sandbox":
                delivery_id = str(uuid.uuid4())
                result = {
                    "delivery_id": delivery_id,
                    "delivery_state": "sent"
                }
                self.circuit_breaker.record_success()
                return result
            else:
                # Live mode: integrate with actual correspondence system via gateway
                if not self.gateway_base_url:
                    raise DependencyUnavailable("GATEWAY_BASE_URL not configured for live mode")

                with httpx.Client(timeout=10.0) as client:
                    response = client.post(
                        f"{self.gateway_base_url}/correspondence/v1/push-notifications",
                        json={
                            "customer_party_id": customer_party_id,
                            "safe_preview_text": safe_preview_text,
                            "deep_link_token": deep_link_token
                        }
                    )
                    response.raise_for_status()
                    result = response.json()
                    self.circuit_breaker.record_success()
                    return result

        except Exception as e:
            self.circuit_breaker.record_failure()
            if isinstance(e, DependencyUnavailable):
                raise
            raise DependencyUnavailable(f"Failed to send push notification: {str(e)}")

    def health(self) -> AdapterHealth:
        """Check adapter health."""
        if self.mode == "sandbox":
            return AdapterHealth(
                available=True,
                message="Correspondence adapter operational in sandbox mode",
                last_check=datetime.now(timezone.utc)
            )
        else:
            # Live mode: check actual gateway connectivity
            try:
                if not self.gateway_base_url:
                    return AdapterHealth(
                        available=False,
                        message="GATEWAY_BASE_URL not configured",
                        last_check=datetime.now(timezone.utc)
                    )

                with httpx.Client(timeout=5.0) as client:
                    response = client.get(f"{self.gateway_base_url}/health")
                    response.raise_for_status()
                    return AdapterHealth(
                        available=True,
                        message="Correspondence gateway accessible",
                        last_check=datetime.now(timezone.utc)
                    )
            except Exception as e:
                return AdapterHealth(
                    available=False,
                    message=f"Gateway health check failed: {str(e)}",
                    last_check=datetime.now(timezone.utc)
                )
