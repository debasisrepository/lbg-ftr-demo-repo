"""Customer case adapter."""
import hashlib
import os
import httpx
from datetime import datetime, timezone
from typing import Any

from app.adapters.base import Adapter, AdapterHealth
from app.core.errors import DependencyUnavailable


class CustomerCaseAdapter(Adapter):
    """Adapter for creating customer cases in external systems."""
    
    def __init__(self):
        super().__init__()
        self.mode = os.getenv("ADAPTER_MODE", "sandbox")
        self.gateway_base_url = os.getenv("GATEWAY_BASE_URL", "")
    
    def create_case(
        self,
        issue_type: str,
        customer_party_id: str,
        issue_summary: str,
        origin_channel: str,
        correlation_id: str
    ) -> dict[str, Any]:
        """Create a case in the external system.
        
        Returns:
            {
                "anchor_domain": str,
                "anchor_system": str,
                "anchor_record_type": str,
                "anchor_record_id": str,
                "anchor_reference": str
            }
        """
        if not self.circuit_breaker.can_attempt():
            raise DependencyUnavailable("CustomerCaseAdapter circuit breaker is open")
        
        try:
            if self.mode == "sandbox":
                # Sandbox mode: return realistic mock anchor with idempotency
                idempotency_key = self._generate_idempotency_key(
                    customer_party_id, issue_type, correlation_id
                )
                anchor_id = f"MOCK-{idempotency_key[:8]}"
                
                result = {
                    "anchor_domain": "customer_case",
                    "anchor_system": "case_management",
                    "anchor_record_type": "case",
                    "anchor_record_id": anchor_id,
                    "anchor_reference": f"CC-{anchor_id}"
                }
                
                self.circuit_breaker.record_success()
                return result
            else:
                # Live mode: make actual API call through gateway
                if not self.gateway_base_url:
                    raise DependencyUnavailable("GATEWAY_BASE_URL not configured for live mode")

                with httpx.Client(timeout=10.0) as client:
                    response = client.post(
                        f"{self.gateway_base_url}/case-management/v1/cases",
                        json={
                            "issue_type": issue_type,
                            "customer_party_id": customer_party_id,
                            "issue_summary": issue_summary,
                            "origin_channel": origin_channel,
                            "correlation_id": correlation_id
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
            raise DependencyUnavailable(f"Failed to create customer case: {str(e)}")
    
    def _generate_idempotency_key(
        self,
        customer_party_id: str,
        issue_type: str,
        correlation_id: str
    ) -> str:
        """Generate an idempotency key for deduplication."""
        combined = f"{customer_party_id}:{issue_type}:{correlation_id}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def health(self) -> AdapterHealth:
        """Check adapter health."""
        if self.mode == "sandbox":
            return AdapterHealth(
                available=True,
                message="Sandbox mode active",
                last_check=datetime.now(timezone.utc)
            )
        else:
            # Live mode: check actual connectivity
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
                        message="Case management gateway accessible",
                        last_check=datetime.now(timezone.utc)
                    )
            except Exception as e:
                return AdapterHealth(
                    available=False,
                    message=f"Gateway health check failed: {str(e)}",
                    last_check=datetime.now(timezone.utc)
                )
