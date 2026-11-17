"""Action repository for protected actions."""
import uuid
from sqlalchemy.orm import Session
from app.models.actions import ProtectedActionRequest


class ActionRepository:
    """Repository for protected actions."""

    def __init__(self, session: Session):
        self.session = session

    def open_request_for(
        self,
        case_id: uuid.UUID,
        customer_party_id: str,
        action_type: str,
        action_domain: str,
        action_payload: dict,
        correlation_id: str,
        created_at
    ) -> ProtectedActionRequest:
        """Open a new protected action request."""
        action_request = ProtectedActionRequest(
            id=uuid.uuid4(),
            case_id=case_id,
            customer_party_id=customer_party_id,
            action_type=action_type,
            action_domain=action_domain,
            action_payload_json=action_payload,
            request_status="pending_sca",
            requires_sca_flag=True,
            sca_outcome="not_invoked",
            correlation_id=correlation_id,
            created_at=created_at
        )
        self.session.add(action_request)
        self.session.flush()
        return action_request

    def get_for_case(
        self,
        action_id: uuid.UUID,
        customer_party_id: str
    ) -> ProtectedActionRequest | None:
        """Get an action request by ID for a specific customer."""
        return self.session.query(ProtectedActionRequest).filter(
            ProtectedActionRequest.id == action_id,
            ProtectedActionRequest.customer_party_id == customer_party_id
        ).first()

    def update(self, action_request: ProtectedActionRequest) -> None:
        """Update an action request (already attached to session)."""
        self.session.flush()
