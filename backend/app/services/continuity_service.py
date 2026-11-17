"""Continuity service."""
import uuid
from pathlib import Path
from typing import Any
from uuid import UUID

import yaml

from app.core.clock import Clock
from app.core.errors import NotFoundError
from app.models.audit import CaseEvent
from app.models.case import Case
from app.models.continuity import ChannelHandoff, ContinuityContext
from app.models.ownership import CaseOwnership, ExpectedByCommitment
from app.repositories.audit_repository import AuditRepository
from app.repositories.case_repository import CaseRepository
from app.repositories.continuity_repository import ContinuityRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.ownership_repository import OwnershipRepository
from app.services.audit_service import AuditService


class ContinuityPackageBuilder:
    """Pure function builder for continuity packages with allow-list filtering."""

    def __init__(self, allow_list_path: str | None = None):
        """Initialize with allow-list configuration."""
        if allow_list_path is None:
            config_dir = Path(__file__).parent.parent / "config"
            allow_list_path = str(config_dir / "continuity_allow_list.yaml")

        with open(allow_list_path, "r") as f:
            self.allow_lists = yaml.safe_load(f)

    def build(
        self,
        case: Case,
        owner: CaseOwnership,
        expected_by: ExpectedByCommitment,
        recent_events: list[CaseEvent],
        handoffs: list[ChannelHandoff],
        context_version: int
    ) -> dict[str, Any]:
        """Build full continuity package."""
        # Build structured context
        structured_context = self._build_structured_context(
            case, owner, expected_by, recent_events, handoffs
        )

        # Build filtered payloads
        colleague_payload = self._filter_by_allow_list(
            structured_context, self.allow_lists["colleague_payload"]
        )
        llm_safe_payload = self._filter_by_allow_list(
            structured_context, self.allow_lists["llm_safe_payload"]
        )

        # Build channel history
        channel_history = [
            {
                "from_channel": h.from_channel,
                "to_channel": h.to_channel,
                "handoff_timestamp": h.handoff_timestamp.isoformat(),
                "context_presented_flag": h.context_presented_flag
            }
            for h in handoffs
        ]

        # Build recent updates
        recent_updates = [
            {
                "event_type": e.event_type,
                "summary_text": e.summary_text,
                "event_timestamp": e.event_timestamp.isoformat(),
                "customer_visible_flag": e.customer_visible_flag
            }
            for e in recent_events
        ]

        return {
            "context_version": context_version,
            "customer_issue_summary": case.issue_summary,
            "structured_context": structured_context,
            "shared_field_names": self.allow_lists["structured_context"],
            "current_state": case.current_lifecycle_state,
            "recent_updates": recent_updates,
            "channel_history": channel_history,
            "colleague_payload": colleague_payload,
            "llm_safe_payload": llm_safe_payload
        }

    def colleague_view(
        self,
        case: Case,
        owner: CaseOwnership,
        expected_by: ExpectedByCommitment,
        recent_events: list[CaseEvent],
        handoffs: list[ChannelHandoff],
        context_version: int
    ) -> dict[str, Any]:
        """Build colleague-filtered continuity view."""
        # Build structured context
        structured_context = self._build_structured_context(
            case, owner, expected_by, recent_events, handoffs
        )

        # Filter to colleague-allowed fields
        colleague_payload = self._filter_by_allow_list(
            structured_context, self.allow_lists["colleague_payload"]
        )

        # Build channel history
        channel_history = [
            {
                "from_channel": h.from_channel,
                "to_channel": h.to_channel,
                "handoff_timestamp": h.handoff_timestamp.isoformat(),
                "context_presented_flag": h.context_presented_flag
            }
            for h in handoffs
        ]

        # Build recent updates (customer-visible only for colleagues)
        recent_updates = [
            {
                "event_type": e.event_type,
                "summary_text": e.summary_text,
                "event_timestamp": e.event_timestamp.isoformat()
            }
            for e in recent_events if e.customer_visible_flag
        ]

        return {
            "context_version": context_version,
            "case_reference": case.case_reference,
            "customer_party_id": case.customer_party_id,
            "issue_type": case.issue_type,
            "issue_title": case.issue_title,
            "issue_summary": case.issue_summary,
            "current_state": case.current_lifecycle_state,
            "current_status": colleague_payload.get("current_status_code"),
            "owner": colleague_payload.get("owner_display_name"),
            "expected_by_at": colleague_payload.get("expected_by_at"),
            "recent_updates": recent_updates,
            "channel_history": channel_history
        }

    def _build_structured_context(
        self,
        case: Case,
        owner: CaseOwnership,
        expected_by: ExpectedByCommitment,
        recent_events: list[CaseEvent],
        handoffs: list[ChannelHandoff]
    ) -> dict[str, Any]:
        """Build full structured context before filtering."""
        # Get latest update text from most recent event
        latest_update_text = None
        if recent_events:
            latest_update_text = recent_events[0].summary_text

        return {
            "case_reference": case.case_reference,
            "customer_party_id": case.customer_party_id,
            "issue_type": case.issue_type,
            "issue_title": case.issue_title,
            "issue_summary": case.issue_summary,
            "current_lifecycle_state": case.current_lifecycle_state,
            "current_status_code": case.current_status_code,
            "current_status_label": case.current_status_label,
            "owner_team_code": owner.owner_team_code,
            "owner_display_name": owner.owner_display_name,
            "expected_by_at": expected_by.expected_by_at.isoformat() if expected_by.expected_by_at else None,
            "expected_by_text": expected_by.customer_explanatory_text,
            "latest_update_text": latest_update_text,
            "latest_update_at": case.latest_meaningful_update_at.isoformat() if case.latest_meaningful_update_at else None,
            "channel_history": [h.to_channel for h in handoffs],
            "recent_events": [e.event_type for e in recent_events]
        }

    def _filter_by_allow_list(self, data: dict[str, Any], allow_list: list[str]) -> dict[str, Any]:
        """Filter data by allow-list."""
        return {key: data[key] for key in allow_list if key in data}


class ContinuityService:
    """Service for cross-channel continuity."""

    def __init__(
        self,
        continuity_repo: ContinuityRepository,
        case_repo: CaseRepository,
        ownership_repo: OwnershipRepository,
        history_repo: HistoryRepository,
        audit_repo: AuditRepository,
        audit_service: AuditService,
        clock: Clock
    ):
        self.continuity_repo = continuity_repo
        self.case_repo = case_repo
        self.ownership_repo = ownership_repo
        self.history_repo = history_repo
        self.audit_repo = audit_repo
        self.audit_service = audit_service
        self.clock = clock
        self.builder = ContinuityPackageBuilder()

    def get_package(
        self,
        case_reference: str,
        customer_party_id: str
    ) -> dict[str, Any]:
        """Get continuity package for a case (customer-scoped)."""
        # Get case
        case = self.case_repo.get_by_reference_for_customer(case_reference, customer_party_id)
        if not case:
            raise NotFoundError(f"Case {case_reference} not found")

        # Get current context
        context = self.continuity_repo.current_package(case.id)
        if context:
            # Return persisted package
            return {
                "context_version": context.package_version,
                "customer_issue_summary": case.issue_summary,
                "structured_context": context.structured_context_json,
                "shared_field_names": self.builder.allow_lists["structured_context"],
                "current_state": case.current_lifecycle_state,
                "recent_updates": context.structured_context_json.get("recent_updates", []),
                "channel_history": context.structured_context_json.get("channel_history", [])
            }

        # Build on-demand if no persisted package
        owner = self.ownership_repo.current_ownership(case.id)
        expected_by = self.ownership_repo.current_expected_by(case.id)
        recent_events, _ = self.history_repo.page_for_case(case.id, limit=10, offset=0, customer_visible_only=True)
        handoffs = self.continuity_repo.handoffs_for_case(case.id, limit=10)

        if not owner or not expected_by:
            raise NotFoundError("Case ownership or expected-by not found")

        return self.builder.build(
            case, owner, expected_by, recent_events, handoffs, context_version=1
        )

    def record_handoff(
        self,
        case_reference: str,
        customer_party_id: str,
        from_channel: str,
        to_channel: str,
        context_presented_flag: bool,
        correlation_id: str
    ) -> None:
        """Record a channel handoff."""
        # Get case
        case = self.case_repo.get_by_reference_for_customer(case_reference, customer_party_id)
        if not case:
            raise NotFoundError(f"Case {case_reference} not found")

        now = self.clock.utcnow()

        # Insert handoff record
        handoff = ChannelHandoff(
            id=uuid.uuid4(),
            case_id=case.id,
            from_channel=from_channel,
            to_channel=to_channel,
            context_presented_flag=context_presented_flag,
            handoff_timestamp=now,
            correlation_id=correlation_id,
            created_at=now
        )
        self.continuity_repo.insert_handoff(handoff)

        # Set continuity state to refresh_pending
        case.continuity_state = "refresh_pending"

        # Audit
        self.audit_service.record(
            correlation_id=correlation_id,
            audit_category="case_change",
            event_type="channel_handoff",
            actor_type="system",
            actor_reference="continuity_service",
            entity_type="case",
            entity_id=str(case.id),
            severity="info",
            metadata={
                "case_reference": case_reference,
                "from_channel": from_channel,
                "to_channel": to_channel,
                "context_presented_flag": context_presented_flag
            }
        )

    def colleague_retrieve(
        self,
        case_reference: str,
        colleague_reference: str,
        correlation_id: str
    ) -> dict[str, Any]:
        """Retrieve case continuity for colleague (entitlement-checked)."""
        # Get case (no customer scoping for colleague)
        case = self.case_repo.get_by_reference(case_reference)
        if not case:
            raise NotFoundError(f"Case {case_reference} not found")

        # Policy decision for colleague entitlement
        # For now, allow all colleagues - in real implementation, check against customer_party_id entitlement

        # Get current context
        owner = self.ownership_repo.current_ownership(case.id)
        expected_by = self.ownership_repo.current_expected_by(case.id)
        recent_events, _ = self.history_repo.page_for_case(case.id, limit=10, offset=0, customer_visible_only=True)
        handoffs = self.continuity_repo.handoffs_for_case(case.id, limit=10)

        if not owner or not expected_by:
            raise NotFoundError("Case ownership or expected-by not found")

        # Build colleague view
        context = self.continuity_repo.current_package(case.id)
        context_version = context.package_version if context else 1

        # Audit colleague access
        self.audit_service.record(
            correlation_id=correlation_id,
            audit_category="access",
            event_type="continuity_retrieval",
            actor_type="colleague",
            actor_reference=colleague_reference,
            entity_type="case",
            entity_id=str(case.id),
            severity="info",
            metadata={
                "case_reference": case_reference,
                "access_type": "continuity_package"
            }
        )

        return self.builder.colleague_view(
            case, owner, expected_by, recent_events, handoffs, context_version
        )

    def list_colleague_cases(
        self,
        customer_party_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[list[dict[str, Any]], int]:
        """List cases for a customer (colleague scope)."""
        # Get cases for customer
        cases, total = self.case_repo.list_for_customer(
            customer_party_id,
            include_closed=False,
            limit=limit,
            offset=offset
        )

        # Build summary list
        summaries = []
        for case in cases:
            summaries.append({
                "case_reference": case.case_reference,
                "issue_type": case.issue_type,
                "issue_title": case.issue_title,
                "current_lifecycle_state": case.current_lifecycle_state,
                "current_status_label": case.current_status_label,
                "opened_at": case.opened_at.isoformat()
            })

        return summaries, total

    def refresh_if_pending(self, case_id: UUID) -> None:
        """Refresh continuity package if state is refresh_pending."""
        # Get case
        case = self.case_repo.session.get(Case, case_id)
        if not case or case.continuity_state != "refresh_pending":
            return

        # Get required data
        owner = self.ownership_repo.current_ownership(case.id)
        expected_by = self.ownership_repo.current_expected_by(case.id)
        recent_events, _ = self.history_repo.page_for_case(case.id, limit=10, offset=0, customer_visible_only=True)
        handoffs = self.continuity_repo.handoffs_for_case(case.id, limit=10)

        if not owner or not expected_by:
            return

        now = self.clock.utcnow()

        # Close current context if exists
        self.continuity_repo.close_current_context(case.id, now)

        # Get next version
        current_context = self.continuity_repo.current_package(case.id)
        next_version = (current_context.package_version + 1) if current_context else 1

        # Build new package
        package = self.builder.build(
            case, owner, expected_by, recent_events, handoffs, next_version
        )

        # Insert new context
        new_context = ContinuityContext(
            id=uuid.uuid4(),
            case_id=case.id,
            package_version=next_version,
            structured_context_json=package["structured_context"],
            llm_safe_payload_json=package["llm_safe_payload"],
            colleague_payload_json=package["colleague_payload"],
            restricted_fields_excluded_flag=True,
            last_channel=handoffs[0].to_channel if handoffs else None,
            last_presented_at=now,
            effective_from=now,
            is_current=True,
            created_at=now
        )
        self.continuity_repo.insert_context(new_context)

        # Update case state
        case.continuity_state = "current"

    def restore_return_visit(
        self,
        case_reference: str,
        return_session_token: str,
        channel: str = "mobile_app",
        correlation_id: str | None = None
    ) -> dict[str, Any]:
        """Restore continuity for return visit after re-authentication.

        Args:
            case_reference: Case reference to restore
            return_session_token: Return session token from identity system
            channel: Channel for return visit (default: mobile_app)
            correlation_id: Correlation ID for audit

        Returns:
            dict with case, recent_updates, context_version, return_visit_restored_at

        Raises:
            NotFoundError: Case not found
            ValueError: Invalid return session token
        """
        from app.adapters.identity_adapter import IdentityAdapter

        # Authenticate return session token
        identity_adapter = IdentityAdapter()
        identity_result = identity_adapter.authenticate_customer(return_session_token)
        customer_party_id = identity_result["customer_party_id"]

        # Get case with customer scoping
        case = self.case_repo.get_by_reference_for_customer(case_reference, customer_party_id)
        if not case:
            raise NotFoundError(f"Case {case_reference} not found")

        now = self.clock.utcnow()

        # Get current continuity context
        context = self.continuity_repo.current_package(case.id)
        context_version = context.package_version if context else 1

        # Get recent customer-visible events
        recent_events, _ = self.history_repo.page_for_case(
            case.id,
            limit=10,
            offset=0,
            customer_visible_only=True
        )

        # Build recent updates
        recent_updates = [
            {
                "event_type": e.event_type,
                "summary_text": e.summary_text,
                "event_timestamp": e.event_timestamp.isoformat(),
                "customer_visible_flag": e.customer_visible_flag
            }
            for e in recent_events
        ]

        # Get case detail
        from app.schemas.case import CaseDetail, ExpectedByView, OwnerView

        owner = self.ownership_repo.current_ownership(case.id)
        expected_by = self.ownership_repo.current_expected_by(case.id)

        # Build owner view
        owner_view = OwnerView(
            owner_type="team",
            owner_semantic_label=owner.owner_semantic_label,
            owner_team_code=owner.owner_team_code,
            owner_display_name=owner.owner_display_name,
            effective_from=owner.effective_from
        ) if owner else OwnerView(
            owner_type="team",
            owner_semantic_label="Unassigned",
            owner_team_code="UNASSIGNED",
            owner_display_name="Unassigned",
            effective_from=now
        )

        # Build expected-by view
        expected_by_view = ExpectedByView(
            commitment_state=expected_by.commitment_state,
            expected_by_at=expected_by.expected_by_at,
            customer_explanatory_text=expected_by.customer_explanatory_text,
            effective_from=expected_by.effective_from
        ) if expected_by else ExpectedByView(
            commitment_state="under_review",
            customer_explanatory_text="We're reviewing your case",
            effective_from=now
        )

        # Get latest meaningful update text from most recent event
        latest_update_text = recent_events[0].summary_text if recent_events else None

        # Map continuity_state from model to schema (model uses 'current', schema expects 'package_current')
        continuity_state_map = {
            "current": "package_current",
            "refresh_pending": "refresh_pending",
            "refreshing": "refresh_pending"  # Map refreshing to refresh_pending for schema
        }
        continuity_state_for_schema = continuity_state_map.get(case.continuity_state, "none")

        case_detail = CaseDetail(
            case_reference=case.case_reference,
            customer_party_id=case.customer_party_id,
            brand=case.brand,
            issue_type=case.issue_type,
            classification_source=case.classification_source,
            issue_title=case.issue_title,
            issue_summary=case.issue_summary,
            origin_channel=case.origin_channel,
            current_lifecycle_state=case.current_lifecycle_state,
            status_code=case.current_status_code,
            status_label=case.current_status_label,
            status_summary_text=None,
            latest_meaningful_update_text=latest_update_text,
            latest_meaningful_update_at=case.latest_meaningful_update_at,
            next_step_text=None,
            outage_impact_banner_text=None,
            owner=owner_view,
            expected_by=expected_by_view,
            opened_at=case.opened_at,
            closed_at=case.closed_at,
            outcome_summary=case.outcome_summary,
            continuity_state=continuity_state_for_schema
        )

        # Audit the return visit restoration
        if correlation_id:
            self.audit_service.record(
                correlation_id=correlation_id,
                audit_category="access",
                event_type="return_visit_restored",
                actor_type="customer",
                actor_reference=customer_party_id,
                entity_type="case",
                entity_id=str(case.id),
                severity="info",
                metadata={
                    "case_reference": case_reference,
                    "channel": channel,
                    "context_version": context_version
                }
            )

        return {
            "case": case_detail,
            "recent_updates": recent_updates,
            "context_version": context_version,
            "return_visit_restored_at": now.isoformat()
        }
