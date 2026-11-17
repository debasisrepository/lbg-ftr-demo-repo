"""Action service for protected actions with SCA."""
import uuid
from pathlib import Path
from typing import Any

import yaml

from app.adapters.identity_adapter import IdentityAdapter
from app.adapters.management_api_adapter import ManagementApiAdapter
from app.core.clock import Clock
from app.core.errors import NotFoundError, ValidationError
from app.models.audit import CaseEvent
from app.repositories.action_repository import ActionRepository
from app.repositories.case_repository import CaseRepository
from app.repositories.history_repository import HistoryRepository
from app.services.audit_service import AuditService


class ActionService:
    """Service for protected actions with SCA state machine.

    Implements LLD 6.4 state machine:
    - pending_sca → released (on SCA success)
    - pending_sca → not_executed (on SCA failure/abandoned)
    """

    def __init__(
        self,
        action_repo: ActionRepository,
        case_repo: CaseRepository,
        history_repo: HistoryRepository,
        audit_service: AuditService,
        identity_adapter: IdentityAdapter,
        management_api_adapter: ManagementApiAdapter,
        clock: Clock
    ):
        self.action_repo = action_repo
        self.case_repo = case_repo
        self.history_repo = history_repo
        self.audit_service = audit_service
        self.identity_adapter = identity_adapter
        self.management_api_adapter = management_api_adapter
        self.clock = clock
        self._load_fallback_guidance()

    def _load_fallback_guidance(self) -> None:
        """Load fallback guidance catalogue from config."""
        config_path = Path(__file__).parent.parent / "config" / "protected_actions.yaml"
        if not config_path.exists():
            self.fallback_guidance = {}
            return

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            self.fallback_guidance = config.get("fallback_guidance", {})

    def _get_fallback_guidance(self, action_type: str, action_domain: str) -> str:
        """Get fallback guidance for an action type and domain."""
        key = f"{action_domain}_{action_type}"
        return self.fallback_guidance.get(
            key,
            "We were unable to complete this action. Please try again later or contact us for assistance."
        )

    def start(
        self,
        customer_party_id: str,
        case_reference: str,
        action_type: str,
        action_domain: str,
        action_payload: dict[str, Any],
        correlation_id: str
    ) -> dict[str, Any]:
        """Start a protected action with SCA.

        Implements LLD 6.4 algorithm:
        1. Validate case ownership
        2. Create action request
        3. Invoke SCA
        4. Return action_id and challenge_reference

        Returns:
            dict with action_id and sca_challenge_reference
        """
        # Get case and validate ownership
        case = self.case_repo.get_by_reference_for_customer(case_reference, customer_party_id)
        if not case:
            raise NotFoundError(f"Case {case_reference} not found")

        now = self.clock.utcnow()

        # Create action request
        action_request = self.action_repo.open_request_for(
            case_id=case.id,
            customer_party_id=customer_party_id,
            action_type=action_type,
            action_domain=action_domain,
            action_payload=action_payload,
            correlation_id=correlation_id,
            created_at=now
        )

        # Invoke SCA
        try:
            sca_result = self.identity_adapter.start_sca(
                customer_party_id=customer_party_id,
                action_type=action_type
            )

            # Record SCA invocation
            action_request.sca_invoked_at = now

            # Create ProtectedActionRequested event
            sequence = self.history_repo.next_sequence(case.id)
            event = CaseEvent(
                id=uuid.uuid4(),
                case_id=case.id,
                sequence_number=sequence,
                event_type="ProtectedActionRequested",
                event_timestamp=now,
                summary_text=f"Protected action requested: {action_type}",
                event_payload_json={
                    "action_id": str(action_request.id),
                    "action_type": action_type,
                    "action_domain": action_domain,
                    "sca_invoked": True
                },
                customer_visible_flag=True,
                actor_type="customer",
                actor_reference=customer_party_id,
                correlation_id=correlation_id,
                created_at=now
            )
            self.history_repo.add_event(event)

            # Audit
            self.audit_service.record(
                correlation_id=correlation_id,
                audit_category="action",
                event_type="protected_action_requested",
                actor_type="customer",
                actor_reference=customer_party_id,
                entity_type="protected_action_request",
                entity_id=str(action_request.id),
                severity="info",
                metadata={
                    "case_reference": case_reference,
                    "action_type": action_type,
                    "action_domain": action_domain,
                    "sca_invoked": True
                }
            )

            return {
                "action_id": str(action_request.id),
                "sca_challenge_reference": sca_result["challenge_reference"]
            }

        except Exception as e:
            # SCA start failed - mark action as not executed
            action_request.request_status = "not_executed"
            action_request.fallback_guidance_text = self._get_fallback_guidance(action_type, action_domain)
            action_request.completed_at = now

            # Audit failure
            self.audit_service.record(
                correlation_id=correlation_id,
                audit_category="action",
                event_type="protected_action_sca_failed",
                actor_type="customer",
                actor_reference=customer_party_id,
                entity_type="protected_action_request",
                entity_id=str(action_request.id),
                severity="warning",
                metadata={
                    "case_reference": case_reference,
                    "action_type": action_type,
                    "error": str(e)
                }
            )

            # Re-raise to let caller handle
            raise

    def report_outcome(
        self,
        customer_party_id: str,
        case_reference: str,
        action_id: uuid.UUID,
        sca_outcome: str,
        sca_verification_token: str,
        correlation_id: str
    ) -> dict[str, Any]:
        """Report SCA outcome and execute or abort action.

        Implements LLD 6.4 state machine:
        - success → execute via ManagementApiAdapter → released
        - failed/abandoned → not_executed with fallback guidance

        Idempotent: repeat calls return stored state
        """
        # Get action and validate
        action_request = self.action_repo.get_for_case(action_id, customer_party_id)
        if not action_request:
            raise NotFoundError(f"Action {action_id} not found")

        # Get case for events
        case = self.case_repo.get_by_reference_for_customer(case_reference, customer_party_id)
        if not case:
            raise NotFoundError(f"Case {case_reference} not found")

        # Check if already finalized (idempotency)
        if action_request.request_status in ("released", "not_executed"):
            # If same outcome, return existing state (idempotent)
            if action_request.sca_outcome == sca_outcome:
                return {
                    "action_id": str(action_request.id),
                    "request_status": action_request.request_status,
                    "sca_outcome": action_request.sca_outcome,
                    "management_api_reference": action_request.management_api_reference,
                    "fallback_guidance_text": action_request.fallback_guidance_text,
                    "completed_at": action_request.completed_at.isoformat() if action_request.completed_at else None
                }
            else:
                # Different outcome after finalized - not allowed
                raise ValidationError(
                    f"Action {action_id} already finalized with outcome {action_request.sca_outcome}"
                )

        # Validate state
        if action_request.request_status != "pending_sca":
            raise ValidationError(f"Action {action_id} is not in pending_sca state")

        now = self.clock.utcnow()

        # Update SCA outcome
        action_request.sca_outcome = sca_outcome
        action_request.sca_completed_at = now

        if sca_outcome == "success":
            # Execute protected action
            try:
                management_result = self.management_api_adapter.execute_protected_action(
                    action_type=action_request.action_type,
                    action_domain=action_request.action_domain,
                    action_payload=action_request.action_payload_json,
                    customer_party_id=customer_party_id,
                    correlation_id=correlation_id
                )

                # Mark as released
                action_request.request_status = "released"
                action_request.management_api_reference = management_result.get("reference")
                action_request.completed_at = now

                # Create ProtectedActionOutcome event (success)
                sequence = self.history_repo.next_sequence(case.id)
                event = CaseEvent(
                    id=uuid.uuid4(),
                    case_id=case.id,
                    sequence_number=sequence,
                    event_type="ProtectedActionOutcome",
                    event_timestamp=now,
                    summary_text=f"Protected action completed: {action_request.action_type}",
                    event_payload_json={
                        "action_id": str(action_request.id),
                        "action_type": action_request.action_type,
                        "sca_outcome": sca_outcome,
                        "request_status": "released",
                        "management_api_reference": action_request.management_api_reference
                    },
                    customer_visible_flag=True,
                    actor_type="customer",
                    actor_reference=customer_party_id,
                    correlation_id=correlation_id,
                    created_at=now
                )
                self.history_repo.add_event(event)

                # Audit
                self.audit_service.record(
                    correlation_id=correlation_id,
                    audit_category="action",
                    event_type="protected_action_released",
                    actor_type="customer",
                    actor_reference=customer_party_id,
                    entity_type="protected_action_request",
                    entity_id=str(action_request.id),
                    severity="info",
                    metadata={
                        "case_reference": case_reference,
                        "action_type": action_request.action_type,
                        "sca_outcome": sca_outcome,
                        "management_api_reference": action_request.management_api_reference
                    }
                )

            except Exception as e:
                # Execution failed after SCA success - still mark as not_executed
                action_request.request_status = "not_executed"
                action_request.fallback_guidance_text = self._get_fallback_guidance(
                    action_request.action_type,
                    action_request.action_domain
                )
                action_request.completed_at = now

                # Audit
                self.audit_service.record(
                    correlation_id=correlation_id,
                    audit_category="action",
                    event_type="protected_action_execution_failed",
                    actor_type="customer",
                    actor_reference=customer_party_id,
                    entity_type="protected_action_request",
                    entity_id=str(action_request.id),
                    severity="error",
                    metadata={
                        "case_reference": case_reference,
                        "action_type": action_request.action_type,
                        "error": str(e)
                    }
                )

        else:
            # SCA failed or abandoned - do not execute
            action_request.request_status = "not_executed"
            action_request.fallback_guidance_text = self._get_fallback_guidance(
                action_request.action_type,
                action_request.action_domain
            )
            action_request.completed_at = now

            # Create ProtectedActionOutcome event (failure)
            sequence = self.history_repo.next_sequence(case.id)
            event = CaseEvent(
                id=uuid.uuid4(),
                case_id=case.id,
                sequence_number=sequence,
                event_type="ProtectedActionOutcome",
                event_timestamp=now,
                summary_text=f"Protected action not completed: {action_request.action_type}",
                event_payload_json={
                    "action_id": str(action_request.id),
                    "action_type": action_request.action_type,
                    "sca_outcome": sca_outcome,
                    "request_status": "not_executed"
                },
                customer_visible_flag=True,
                actor_type="customer",
                actor_reference=customer_party_id,
                correlation_id=correlation_id,
                created_at=now
            )
            self.history_repo.add_event(event)

            # Audit
            self.audit_service.record(
                correlation_id=correlation_id,
                audit_category="action",
                event_type="protected_action_not_executed",
                actor_type="customer",
                actor_reference=customer_party_id,
                entity_type="protected_action_request",
                entity_id=str(action_request.id),
                severity="info",
                metadata={
                    "case_reference": case_reference,
                    "action_type": action_request.action_type,
                    "sca_outcome": sca_outcome
                }
            )

        # Update the action request
        self.action_repo.update(action_request)

        return {
            "action_id": str(action_request.id),
            "request_status": action_request.request_status,
            "sca_outcome": action_request.sca_outcome,
            "management_api_reference": action_request.management_api_reference,
            "fallback_guidance_text": action_request.fallback_guidance_text,
            "completed_at": action_request.completed_at.isoformat() if action_request.completed_at else None
        }
