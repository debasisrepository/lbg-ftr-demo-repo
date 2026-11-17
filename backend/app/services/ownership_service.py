"""Ownership service implementing FR-008 and FR-009."""
import uuid
from typing import Literal, cast

from app.core.clock import Clock
from app.core.errors import NotFoundError, ValidationError
from app.models.audit import CaseEvent
from app.models.ownership import CaseOwnership, ExpectedByCommitment
from app.repositories.case_repository import CaseRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.ownership_repository import OwnershipRepository
from app.schemas.case import (
    ExpectedByRevisionRequest,
    ExpectedByView,
    OwnerChangeRequest,
    OwnerView,
)
from app.services.audit_service import AuditService


class OwnershipService:
    """Service for ownership and expected-by management (FR-008, FR-009)."""

    def __init__(
        self,
        ownership_repo: OwnershipRepository,
        case_repo: CaseRepository,
        history_repo: HistoryRepository,
        audit_service: AuditService,
        clock: Clock
    ):
        self.ownership_repo = ownership_repo
        self.case_repo = case_repo
        self.history_repo = history_repo
        self.audit_service = audit_service
        self.clock = clock

    def change_owner(
        self,
        case_reference: str,
        request: OwnerChangeRequest,
        correlation_id: str
    ) -> OwnerView:
        """
        Change case owner (FR-008).

        Validates owner_team_code against active mappings, closes current ownership,
        inserts successor, appends OwnerChanged event, and queues continuity refresh.
        """
        # Load case
        case = self.case_repo.get_by_reference(case_reference)
        if not case:
            raise NotFoundError(f"Case {case_reference} not found")

        # Get active mapping
        mapping = self.ownership_repo.active_mapping(request.owner_team_code)
        if not mapping:
            raise ValidationError(f"Owner team code {request.owner_team_code} not found or inactive")

        # Check if owner is unchanged
        current = self.ownership_repo.current_ownership(case.id)
        if current and current.owner_team_code == request.owner_team_code:
            raise ValidationError("Owner is already set to the requested team")

        # Close current ownership
        now = self.clock.utcnow()
        if current:
            current.effective_to = now
            current.is_current = False

        # Create new ownership
        new_ownership = CaseOwnership(
            id=uuid.uuid4(),
            case_id=case.id,
            owner_team_code=mapping.owner_team_code,
            owner_semantic_label=mapping.owner_semantic_label,
            owner_display_name=mapping.owner_display_name,
            source_event_id=None,  # Will be set after event creation
            effective_from=now,
            effective_to=None,
            is_current=True,
            created_at=now
        )
        self.ownership_repo.insert_ownership(new_ownership)

        # Create OwnerChanged event
        sequence = self.history_repo.next_sequence(case.id)
        event = CaseEvent(
            id=uuid.uuid4(),
            case_id=case.id,
            sequence_number=sequence,
            event_type="OwnerChanged",
            event_timestamp=now,
            summary_text=f"Owner changed to {mapping.owner_display_name}",
            event_payload_json={
                "owner_team_code": mapping.owner_team_code,
                "owner_semantic_label": mapping.owner_semantic_label,
                "owner_display_name": mapping.owner_display_name,
                "handoff_reason_code": request.handoff_reason_code
            },
            customer_visible_flag=True,
            actor_type="colleague",
            actor_reference=None,
            basis_type="approved_manual_update",
            basis_reference=f"handoff:{request.handoff_reason_code}",
            correlation_id=correlation_id,
            created_at=now
        )
        self.history_repo.add_event(event)

        # Set source_event_id
        new_ownership.source_event_id = event.id

        # Update case.continuity_state to refresh_pending
        case.continuity_state = "refresh_pending"

        # Write audit entry
        self.audit_service.record(
            correlation_id=correlation_id,
            audit_category="case_change",
            event_type="OwnerChanged",
            actor_type="colleague",
            actor_reference=None,
            entity_type="case",
            entity_id=str(case.id),
            state_before_hash=None,
            state_after_hash=None,
            severity="info",
            metadata={
                "case_reference": case_reference,
                "new_owner": mapping.owner_team_code,
                "handoff_reason_code": request.handoff_reason_code
            }
        )

        return OwnerView(
            owner_type="team",
            owner_team_code=new_ownership.owner_team_code,
            owner_semantic_label=new_ownership.owner_semantic_label,
            owner_display_name=new_ownership.owner_display_name,
            effective_from=new_ownership.effective_from
        )

    def revise_expected_by(
        self,
        case_reference: str,
        request: ExpectedByRevisionRequest,
        correlation_id: str
    ) -> ExpectedByView:
        """
        Revise expected-by commitment (FR-009).

        Applies revision rules from LLD 4.2.4, closes current commitment,
        inserts successor, appends ExpectedByChanged event.
        """
        # Load case
        case = self.case_repo.get_by_reference(case_reference)
        if not case:
            raise NotFoundError(f"Case {case_reference} not found")

        # Get current commitment
        current = self.ownership_repo.current_expected_by(case.id)

        # Validate request based on commitment_state
        if request.commitment_state in ("committed", "revised"):
            if not request.expected_by_at:
                raise ValidationError(f"{request.commitment_state} state requires expected_by_at")
            if request.expected_by_at <= self.clock.utcnow():
                raise ValidationError("expected_by_at must be in the future")

        if request.commitment_state in ("withdrawn", "under_review"):
            if not request.customer_explanatory_text:
                raise ValidationError(f"{request.commitment_state} state requires customer_explanatory_text")

        if request.commitment_state == "withdrawn":
            if not request.withdrawn_reason_code:
                raise ValidationError("withdrawn state requires withdrawn_reason_code")

        # Check if unchanged
        if current:
            if (
                current.commitment_state == request.commitment_state
                and current.expected_by_at == request.expected_by_at
                and current.customer_explanatory_text == request.customer_explanatory_text
            ):
                raise ValidationError("Expected-by commitment is already in the requested state")

        # Close current commitment
        now = self.clock.utcnow()
        if current:
            current.effective_to = now
            current.is_current = False

        # Create new commitment
        new_commitment = ExpectedByCommitment(
            id=uuid.uuid4(),
            case_id=case.id,
            commitment_state=request.commitment_state,
            expected_by_at=request.expected_by_at,
            customer_explanatory_text=request.customer_explanatory_text,
            confidence_basis=request.confidence_basis,
            withdrawn_reason_code=request.withdrawn_reason_code,
            source_event_id=None,  # Will be set after event creation
            effective_from=now,
            effective_to=None,
            is_current=True,
            created_at=now
        )
        self.ownership_repo.insert_expected_by(new_commitment)

        # Build summary text
        if request.commitment_state in ("committed", "revised"):
            assert request.expected_by_at is not None  # Validated above
            summary_text = f"Expected by {request.expected_by_at.strftime('%Y-%m-%d')}"
        elif request.commitment_state == "withdrawn":
            summary_text = f"Expected-by withdrawn: {request.customer_explanatory_text}"
        else:
            summary_text = "Timing is under review"

        # Create ExpectedByChanged event
        sequence = self.history_repo.next_sequence(case.id)
        event = CaseEvent(
            id=uuid.uuid4(),
            case_id=case.id,
            sequence_number=sequence,
            event_type="ExpectedByChanged",
            event_timestamp=now,
            summary_text=summary_text,
            event_payload_json={
                "commitment_state": request.commitment_state,
                "expected_by_at": request.expected_by_at.isoformat() if request.expected_by_at else None,
                "customer_explanatory_text": request.customer_explanatory_text,
                "confidence_basis": request.confidence_basis,
                "withdrawn_reason_code": request.withdrawn_reason_code
            },
            customer_visible_flag=True,
            actor_type="colleague",
            actor_reference=None,
            basis_type="approved_manual_update",
            basis_reference=f"revision:{request.commitment_state}",
            correlation_id=correlation_id,
            created_at=now
        )
        self.history_repo.add_event(event)

        # Set source_event_id
        new_commitment.source_event_id = event.id

        # Update case.continuity_state to refresh_pending
        case.continuity_state = "refresh_pending"

        # Write audit entry
        self.audit_service.record(
            correlation_id=correlation_id,
            audit_category="case_change",
            event_type="ExpectedByChanged",
            actor_type="colleague",
            actor_reference=None,
            entity_type="case",
            entity_id=str(case.id),
            state_before_hash=None,
            state_after_hash=None,
            severity="info",
            metadata={
                "case_reference": case_reference,
                "commitment_state": request.commitment_state,
                "expected_by_at": request.expected_by_at.isoformat() if request.expected_by_at else None
            }
        )

        return ExpectedByView(
            commitment_state=cast(Literal["committed", "revised", "withdrawn", "under_review"], new_commitment.commitment_state),
            expected_by_at=new_commitment.expected_by_at,
            customer_explanatory_text=new_commitment.customer_explanatory_text,
            confidence_basis=new_commitment.confidence_basis,
            effective_from=new_commitment.effective_from
        )

    def current_owner(self, case_id: uuid.UUID) -> OwnerView | None:
        """Get current owner for a case."""
        ownership = self.ownership_repo.current_ownership(case_id)
        if not ownership:
            return None

        return OwnerView(
            owner_type="team",
            owner_team_code=ownership.owner_team_code,
            owner_semantic_label=ownership.owner_semantic_label,
            owner_display_name=ownership.owner_display_name,
            effective_from=ownership.effective_from
        )

    def current_expected_by(self, case_id: uuid.UUID) -> ExpectedByView | None:
        """Get current expected-by for a case."""
        commitment = self.ownership_repo.current_expected_by(case_id)
        if not commitment:
            # Return default under_review state
            return ExpectedByView(
                commitment_state="under_review",
                expected_by_at=None,
                customer_explanatory_text="Timing is under review",
                confidence_basis=None,
                effective_from=None
            )

        return ExpectedByView(
            commitment_state=cast(Literal["committed", "revised", "withdrawn", "under_review"], commitment.commitment_state),
            expected_by_at=commitment.expected_by_at,
            customer_explanatory_text=commitment.customer_explanatory_text,
            confidence_basis=commitment.confidence_basis,
            effective_from=commitment.effective_from
        )
