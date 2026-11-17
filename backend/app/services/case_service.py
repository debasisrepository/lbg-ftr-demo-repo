"""Case service."""
import os
import uuid

from app.adapters.customer_case_adapter import CustomerCaseAdapter
from app.core.clock import Clock
from app.core.errors import NotFoundError, ValidationError
from app.core.ids import CaseReferenceGenerator
from app.core.lifecycle_graph import LifecycleGraph
from app.models.audit import CaseEvent
from app.models.case import Case, CaseAnchorLink, CaseStatusProjection
from app.models.ownership import CaseOwnership, ExpectedByCommitment
from app.repositories.audit_repository import AuditRepository
from app.repositories.case_repository import CaseRepository
from app.repositories.config_repository import ConfigRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.ownership_repository import OwnershipRepository
from app.schemas.case import (
    CaseCreateRequest,
    CaseCreationResult,
    CaseDetail,
    CaseSummary,
    CaseTransitionRequest,
    CaseTransitionResult,
    ExpectedByView,
    HistoryEvent,
    OwnerView,
)
from app.services.audit_service import AuditService
from app.services.policy_service import PolicyService


class CaseSummaryAssembler:
    """Assembles case summaries from stored projections."""

    @staticmethod
    def assemble_summary(
        case: Case,
        projection: CaseStatusProjection,
        owner: CaseOwnership,
        expected_by: ExpectedByCommitment
    ) -> CaseSummary:
        """Assemble a case summary."""
        return CaseSummary(
            case_reference=case.case_reference,
            issue_type=case.issue_type,
            issue_title=case.issue_title,
            current_lifecycle_state=case.current_lifecycle_state,
            status_code=projection.status_code,
            status_label=projection.status_label,
            latest_meaningful_update_text=projection.customer_facing_text,
            latest_meaningful_update_at=case.latest_meaningful_update_at,
            owner=OwnerView(
                owner_team_code=owner.owner_team_code,
                owner_semantic_label=owner.owner_semantic_label,
                owner_display_name=owner.owner_display_name,
                effective_from=owner.effective_from
            ),
            expected_by=ExpectedByView(
                commitment_state=expected_by.commitment_state,
                expected_by_at=expected_by.expected_by_at,
                customer_explanatory_text=expected_by.customer_explanatory_text,
                confidence_basis=expected_by.confidence_basis,
                effective_from=expected_by.effective_from
            ),
            opened_at=case.opened_at,
            closed_at=case.closed_at,
            outcome_summary=case.outcome_summary
        )

    @staticmethod
    def assemble_detail(
        case: Case,
        projection: CaseStatusProjection,
        owner: CaseOwnership,
        expected_by: ExpectedByCommitment
    ) -> CaseDetail:
        """Assemble case detail."""
        return CaseDetail(
            case_reference=case.case_reference,
            customer_party_id=case.customer_party_id,
            brand=case.brand,  # type: ignore
            issue_type=case.issue_type,
            classification_source=case.classification_source,  # type: ignore
            issue_title=case.issue_title,
            issue_summary=case.issue_summary,
            origin_channel=case.origin_channel,
            current_lifecycle_state=case.current_lifecycle_state,
            status_code=projection.status_code,
            status_label=projection.status_label,
            status_summary_text=projection.customer_facing_text,
            latest_meaningful_update_text=projection.customer_facing_text,
            latest_meaningful_update_at=case.latest_meaningful_update_at,
            next_step_text=projection.next_step_text,
            outage_impact_banner_text=None,
            owner=OwnerView(
                owner_team_code=owner.owner_team_code,
                owner_semantic_label=owner.owner_semantic_label,
                owner_display_name=owner.owner_display_name,
                effective_from=owner.effective_from
            ),
            expected_by=ExpectedByView(
                commitment_state=expected_by.commitment_state,
                expected_by_at=expected_by.expected_by_at,
                customer_explanatory_text=expected_by.customer_explanatory_text,
                confidence_basis=expected_by.confidence_basis,
                effective_from=expected_by.effective_from
            ),
            opened_at=case.opened_at,
            closed_at=case.closed_at,
            outcome_summary=case.outcome_summary,
            continuity_state="none" if case.continuity_state == "current" else (
                "package_current" if case.continuity_state == "package_current" else "refresh_pending"
            )  # type: ignore
        )


class CaseService:
    """Service for case management."""

    def __init__(
        self,
        case_repo: CaseRepository,
        history_repo: HistoryRepository,
        ownership_repo: OwnershipRepository,
        config_repo: ConfigRepository,
        audit_repo: AuditRepository,
        policy_service: PolicyService,
        audit_service: AuditService,
        customer_case_adapter: CustomerCaseAdapter,
        clock: Clock
    ):
        self.case_repo = case_repo
        self.history_repo = history_repo
        self.ownership_repo = ownership_repo
        self.config_repo = config_repo
        self.audit_repo = audit_repo
        self.policy_service = policy_service
        self.audit_service = audit_service
        self.customer_case_adapter = customer_case_adapter
        self.clock = clock

    def create_case(
        self,
        principal_customer_party_id: str,
        principal_brand: str,
        request: CaseCreateRequest,
        correlation_id: str
    ) -> CaseCreationResult:
        """Create a new case or surface existing one.

        Implements LLD section 4.2.1 algorithm.
        """
        # Use customer's party ID unless caller is colleague with explicit override
        customer_party_id = request.customer_party_id or principal_customer_party_id
        brand = request.brand or principal_brand

        # Step 1: Check for existing open case
        existing = self.case_repo.find_open_by_issue_type(customer_party_id, request.issue_type)
        if existing:
            # Surface existing case
            projection = self.case_repo.current_projection(existing.id)
            owner = self.ownership_repo.current_ownership(existing.id)
            expected_by = self.ownership_repo.current_expected_by(existing.id)

            if projection and owner and expected_by:
                case_detail = CaseSummaryAssembler.assemble_detail(
                    existing, projection, owner, expected_by
                )
                return CaseCreationResult(
                    outcome="surfaced",
                    case=case_detail,
                    classification_source=existing.classification_source,  # type: ignore
                    continuity_available=existing.continuity_state == "package_current"
                )

        # Step 2: Policy decision (eligibility)
        policy_result = self.policy_service.decide(
            scope="eligibility",
            issue_type=request.issue_type
        )

        if policy_result.outcome == "deny":
            # Not eligible
            rule = self.config_repo.active_rule(request.issue_type)
            redirect_code = rule.redirect_journey_code if rule else os.getenv(
                "DEFAULT_REDIRECT_JOURNEY_CODE", "general_support"
            )

            return CaseCreationResult(
                outcome="not_eligible",
                redirect_journey_code=redirect_code,
                redirect_message=f"Please use the {redirect_code} journey for this type of issue."
            )

        # Step 3: Create anchor (before opening transaction)
        anchor_result = self.customer_case_adapter.create_case(
            issue_type=request.issue_type,
            customer_party_id=customer_party_id,
            issue_summary=request.issue_summary,
            origin_channel=request.origin_channel,
            correlation_id=correlation_id
        )

        # Step 4: Create case and all initial rows in one transaction
        now = self.clock.utcnow()
        case_id = uuid.uuid4()
        case_reference = CaseReferenceGenerator.generate()

        # Create case
        case = Case(
            id=case_id,
            case_reference=case_reference,
            customer_party_id=customer_party_id,
            brand=brand,
            issue_type=request.issue_type,
            classification_source="eligibility_rule",
            issue_title=request.issue_title or request.issue_type.replace("_", " ").title(),
            issue_summary=request.issue_summary,
            origin_channel=request.origin_channel,
            current_lifecycle_state="case_created",
            current_status_code="received",
            current_status_label="Received",
            continuity_state="current",
            opened_at=now,
            created_at=now,
            updated_at=now
        )
        self.case_repo.create(case)

        # Create anchor link
        anchor_link = CaseAnchorLink(
            id=uuid.uuid4(),
            case_id=case_id,
            anchor_domain=anchor_result["anchor_domain"],
            anchor_system=anchor_result["anchor_system"],
            anchor_record_type=anchor_result["anchor_record_type"],
            anchor_record_id=anchor_result["anchor_record_id"],
            anchor_reference=anchor_result["anchor_reference"],
            link_status="active",
            created_at=now
        )
        self.case_repo.create_anchor_link(anchor_link)

        # Create first status projection
        projection = CaseStatusProjection(
            id=uuid.uuid4(),
            case_id=case_id,
            status_code="received",
            status_label="Received",
            lifecycle_state="case_created",
            status_icon="in_progress",
            status_color="blue",
            customer_facing_text="Your case has been received and is being reviewed.",
            next_step_text="We're reviewing your case and will update you soon.",
            effective_from=now,
            is_current=True,
            created_at=now
        )
        self.case_repo.create_status_projection(projection)

        # Create first ownership
        default_owner_code = os.getenv("INTAKE_DEFAULT_OWNER_TEAM_CODE", "case_ops")
        owner_mapping = self.ownership_repo.active_mapping(default_owner_code)
        if not owner_mapping:
            # Fallback if mapping doesn't exist
            owner_mapping = type('obj', (object,), {
                'owner_team_code': default_owner_code,
                'owner_semantic_label': 'Operations',
                'owner_display_name': 'Case Operations Team'
            })()

        ownership = CaseOwnership(
            id=uuid.uuid4(),
            case_id=case_id,
            owner_team_code=owner_mapping.owner_team_code,
            owner_semantic_label=owner_mapping.owner_semantic_label,
            owner_display_name=owner_mapping.owner_display_name,
            effective_from=now,
            is_current=True,
            created_at=now
        )
        self.ownership_repo.insert_ownership(ownership)

        # Create first expected-by commitment
        expected_by = ExpectedByCommitment(
            id=uuid.uuid4(),
            case_id=case_id,
            commitment_state="under_review",
            customer_explanatory_text="We're reviewing the timing and will update you soon.",
            confidence_basis="initial",
            effective_from=now,
            is_current=True,
            created_at=now
        )
        self.ownership_repo.insert_expected_by(expected_by)

        # Create first event
        sequence = self.history_repo.next_sequence(case_id)
        event = CaseEvent(
            id=uuid.uuid4(),
            case_id=case_id,
            sequence_number=sequence,
            event_type="CaseCaptured",
            event_timestamp=now,
            summary_text=f"Case created for {request.issue_type}",
            customer_visible_flag=True,
            actor_type="customer",
            correlation_id=correlation_id,
            created_at=now
        )
        self.history_repo.add_event(event)

        # Create audit entry
        self.audit_service.record(
            correlation_id=correlation_id,
            audit_category="case_change",
            event_type="case_created",
            actor_type="customer",
            actor_reference=customer_party_id,
            entity_type="case",
            entity_id=str(case_id),
            severity="info",
            metadata={
                "case_reference": case_reference,
                "issue_type": request.issue_type,
                "origin_channel": request.origin_channel
            }
        )

        # Assemble response
        case_detail = CaseSummaryAssembler.assemble_detail(case, projection, ownership, expected_by)

        return CaseCreationResult(
            outcome="created",
            case=case_detail,
            classification_source="eligibility_rule",
            anchor_reference=anchor_result["anchor_reference"],
            continuity_available=False
        )

    def list_cases(
        self,
        customer_party_id: str,
        lifecycle_state: str | None = None,
        include_closed: bool = True,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[list[CaseSummary], int]:
        """List cases for a customer with pagination."""
        cases, total = self.case_repo.list_for_customer(
            customer_party_id=customer_party_id,
            lifecycle_state=lifecycle_state,
            include_closed=include_closed,
            limit=limit,
            offset=offset
        )

        summaries = []
        for case in cases:
            projection = self.case_repo.current_projection(case.id)
            owner = self.ownership_repo.current_ownership(case.id)
            expected_by = self.ownership_repo.current_expected_by(case.id)

            if projection and owner and expected_by:
                summary = CaseSummaryAssembler.assemble_summary(case, projection, owner, expected_by)
                summaries.append(summary)

        return summaries, total

    def get_case(self, customer_party_id: str, case_reference: str) -> CaseDetail:
        """Get a case by reference for a customer."""
        case = self.case_repo.get_by_reference_for_customer(case_reference, customer_party_id)
        if not case:
            raise NotFoundError(f"Case {case_reference} not found")

        projection = self.case_repo.current_projection(case.id)
        owner = self.ownership_repo.current_ownership(case.id)
        expected_by = self.ownership_repo.current_expected_by(case.id)

        if not projection or not owner or not expected_by:
            raise NotFoundError("Case projections incomplete")

        return CaseSummaryAssembler.assemble_detail(case, projection, owner, expected_by)

    def transition(
        self,
        case_reference: str,
        request: CaseTransitionRequest,
        correlation_id: str
    ) -> CaseTransitionResult:
        """
        Transition a case to a new lifecycle state.

        Implements LLD section 6.2 lifecycle transition algorithm:
        1. Validate against LifecycleGraph
        2. Write successor projection
        3. Update current fields on cases
        4. Append CaseStatusChanged event
        5. Return updated detail
        """
        # Get the case by reference only (not scoped to customer for colleague access)
        case = self.case_repo.get_by_reference(case_reference)
        if not case:
            raise NotFoundError(f"Case {case_reference} not found")

        # Validate the transition
        lifecycle_graph = LifecycleGraph(self.config_repo)

        # Check if already in target state
        if case.current_lifecycle_state == request.to_state:
            raise ValidationError(f"Case is already in state {request.to_state}")

        # Validate against lifecycle graph
        if not lifecycle_graph.is_allowed(
            case.current_lifecycle_state,
            request.to_state,
            request.basis_type
        ):
            raise ValidationError(
                f"Transition from {case.current_lifecycle_state} to {request.to_state} "
                f"with basis {request.basis_type} is not allowed"
            )

        # Validate closure requirements
        if request.to_state == "closed":
            if not request.outcome_summary:
                raise ValidationError("outcome_summary is required when closing a case")

        now = self.clock.utcnow()

        # Close current projection
        current_projection = self.case_repo.current_projection(case.id)
        if current_projection:
            current_projection.effective_to = now
            current_projection.is_current = False

        # Create successor projection
        new_projection = CaseStatusProjection(
            id=uuid.uuid4(),
            case_id=case.id,
            status_code=request.status_code,
            status_label=request.status_label,
            lifecycle_state=request.to_state,
            status_icon="in_progress",  # Could be derived from status_code
            status_color="blue",  # Could be derived from status_code
            customer_facing_text=request.status_summary_text,
            next_step_text=request.next_step_text,
            effective_from=now,
            is_current=True,
            created_at=now
        )
        self.case_repo.create_status_projection(new_projection)

        # Update current fields on case
        case.current_lifecycle_state = request.to_state
        case.current_status_code = request.status_code
        case.current_status_label = request.status_label
        case.latest_meaningful_update_at = now
        case.updated_at = now

        # Set closed_at and outcome_summary if closing
        if request.to_state == "closed":
            case.closed_at = now
            case.outcome_summary = request.outcome_summary

        # Set continuity refresh pending (will trigger refresh via event bus)
        case.continuity_state = "refresh_pending"

        # Append CaseStatusChanged event
        sequence = self.history_repo.next_sequence(case.id)
        event = CaseEvent(
            id=uuid.uuid4(),
            case_id=case.id,
            sequence_number=sequence,
            event_type="CaseStatusChanged",
            event_timestamp=now,
            summary_text=request.latest_meaningful_update_text or request.status_summary_text,
            event_payload_json={
                "lifecycle_from": current_projection.lifecycle_state if current_projection else None,
                "lifecycle_to": request.to_state,
                "status_code": request.status_code,
                "status_label": request.status_label
            },
            customer_visible_flag=True,
            actor_type="colleague",
            basis_type=request.basis_type,
            basis_reference=request.basis_reference,
            correlation_id=correlation_id,
            created_at=now
        )
        self.history_repo.add_event(event)

        # Create audit entry
        self.audit_service.record(
            correlation_id=correlation_id,
            audit_category="case_change",
            event_type="case_status_changed",
            actor_type="colleague",
            actor_reference="system",  # Would be from principal in real scenario
            entity_type="case",
            entity_id=str(case.id),
            severity="info",
            metadata={
                "case_reference": case_reference,
                "from_state": current_projection.lifecycle_state if current_projection else None,
                "to_state": request.to_state,
                "basis_type": request.basis_type,
                "basis_reference": request.basis_reference
            }
        )

        # Get updated projections
        owner = self.ownership_repo.current_ownership(case.id)
        expected_by = self.ownership_repo.current_expected_by(case.id)

        if not owner or not expected_by:
            raise NotFoundError("Case projections incomplete")

        # Assemble response
        case_detail = CaseSummaryAssembler.assemble_detail(case, new_projection, owner, expected_by)

        history_event = HistoryEvent(
            id=event.id,
            sequence_number=event.sequence_number,
            event_type=event.event_type,
            event_timestamp=event.event_timestamp,
            summary_text=event.summary_text,
            customer_visible_flag=event.customer_visible_flag,
            actor_type=event.actor_type,
            actor_reference=event.actor_reference,
            basis_type=event.basis_type,
            basis_reference=event.basis_reference,
            lifecycle_from=current_projection.lifecycle_state if current_projection else None,
            lifecycle_to=request.to_state
        )

        return CaseTransitionResult(case=case_detail, event=history_event)
