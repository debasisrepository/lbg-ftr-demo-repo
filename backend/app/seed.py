"""Seed data for local development."""
import hashlib
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.security import hash_password
from app.database import SessionLocal
from app.models.audit import CaseEvent
from app.models.auth import UserAccount
from app.models.case import Case, CaseAnchorLink, CaseStatusProjection
from app.models.communication import CommunicationRecord, NotificationRecord
from app.models.config import (
    CaseLifecycleTransition,
    IssueEligibilityRule,
    KillSwitchSetting,
    OwnerTeamMapping,
)
from app.models.continuity import ChannelHandoff, ContinuityContext
from app.models.incident import LifelineGuidance, ServiceIncident, ServiceStatusPublication
from app.models.ownership import CaseOwnership, ExpectedByCommitment
from app.models.actions import ProtectedActionRequest


def seed_data():
    """Seed database with initial data (idempotent)."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        # Seed users
        admin_user = db.scalar(select(UserAccount).where(UserAccount.username == "admin@example.com"))
        if not admin_user:
            admin_user = UserAccount(
                id=uuid.UUID(int=1),
                username="admin@example.com",
                hashed_password=hash_password("admin123"),
                email="admin@example.com",
                display_name="Admin User",
                scope="customer",
                customer_party_id="CUST-001",
                brand="lloyds",
                is_active=True,
                failed_login_count=0,
                created_at=now,
                updated_at=now,
            )
            db.add(admin_user)
            print("✓ Created admin user")

        colleague_user = db.scalar(select(UserAccount).where(UserAccount.username == "colleague@example.com"))
        if not colleague_user:
            colleague_user = UserAccount(
                id=uuid.UUID(int=2),
                username="colleague@example.com",
                hashed_password=hash_password("colleague123"),
                email="colleague@example.com",
                display_name="Colleague User",
                scope="colleague",
                colleague_reference="COLL-001",
                brand="lloyds",
                is_active=True,
                failed_login_count=0,
                created_at=now,
                updated_at=now,
            )
            db.add(colleague_user)
            print("✓ Created colleague user")

        # Seed user1 through user4
        test_users = [
            ("user1@example.com", "CUST-002", "User One"),
            ("user2@example.com", "CUST-003", "User Two"),
            ("user3@example.com", "CUST-004", "User Three"),
            ("user4@example.com", "CUST-005", "User Four"),
        ]
        for idx, (email, party_id, display) in enumerate(test_users, start=3):
            user = db.scalar(select(UserAccount).where(UserAccount.username == email))
            if not user:
                user = UserAccount(
                    id=uuid.UUID(int=idx),
                    username=email,
                    hashed_password=hash_password("user123"),
                    email=email,
                    display_name=display,
                    scope="customer",
                    customer_party_id=party_id,
                    brand="lloyds",
                    is_active=True,
                    failed_login_count=0,
                    created_at=now,
                    updated_at=now,
                )
                db.add(user)
                print(f"✓ Created user: {email}")

        # Seed issue eligibility rules
        eligibility_rules = [
            ("card_declined", True, None, 100),
            ("payment_missing", True, None, 90),
            ("general_query", False, "existing_support", 50),
        ]
        for issue_type, is_eligible, redirect, priority in eligibility_rules:
            exists = db.scalar(
                select(IssueEligibilityRule).where(IssueEligibilityRule.issue_type == issue_type)
            )
            if not exists:
                rule = IssueEligibilityRule(
                    id=uuid.uuid4(),
                    issue_type=issue_type,
                    is_eligible=is_eligible,
                    redirect_journey_code=redirect,
                    priority_weight=priority,
                    created_at=now,
                )
                db.add(rule)
                print(f"✓ Created eligibility rule: {issue_type}")

        # Seed lifecycle transitions (15 transitions)
        lifecycle_transitions = [
            ("captured", "under_review", "customer_submission", True),
            ("under_review", "awaiting_customer", "information_requested", True),
            ("under_review", "in_progress", "colleague_accepted", True),
            ("awaiting_customer", "in_progress", "customer_responded", True),
            ("awaiting_customer", "abandoned", "customer_timeout", True),
            ("in_progress", "awaiting_customer", "information_requested", True),
            ("in_progress", "escalated", "specialist_required", True),
            ("in_progress", "resolved", "issue_resolved", True),
            ("escalated", "in_progress", "specialist_completed", True),
            ("escalated", "resolved", "issue_resolved", True),
            ("resolved", "reopened", "customer_disagreed", True),
            ("reopened", "in_progress", "colleague_accepted", True),
            ("reopened", "resolved", "issue_resolved", True),
            ("resolved", "closed", "retention_expired", True),
            ("abandoned", "closed", "retention_expired", True),
        ]
        for from_state, to_state, basis, is_active in lifecycle_transitions:
            exists = db.scalar(
                select(CaseLifecycleTransition).where(
                    CaseLifecycleTransition.from_state == from_state,
                    CaseLifecycleTransition.to_state == to_state,
                    CaseLifecycleTransition.basis_type == basis,
                )
            )
            if not exists:
                transition = CaseLifecycleTransition(
                    id=uuid.uuid4(),
                    from_state=from_state,
                    to_state=to_state,
                    basis_type=basis,
                    is_active=is_active,
                    created_at=now,
                )
                db.add(transition)

        print("✓ Created lifecycle transitions")

        # Seed owner team mappings (5 including INTAKE_DEFAULT)
        owner_mappings = [
            ("INTAKE_DEFAULT", "Intake Team", "Intake & Triage"),
            ("CARDS_DISPUTES", "Card Disputes Team", "Card Disputes"),
            ("PAYMENTS_SUPPORT", "Payments Support Team", "Payments Support"),
            ("FRAUD_TEAM", "Fraud Investigation Team", "Fraud Investigation"),
            ("COMPLAINTS_TEAM", "Complaints Team", "Customer Complaints"),
        ]
        for code, semantic, display in owner_mappings:
            exists = db.scalar(
                select(OwnerTeamMapping).where(OwnerTeamMapping.owner_team_code == code)
            )
            if not exists:
                mapping = OwnerTeamMapping(
                    id=uuid.uuid4(),
                    owner_team_code=code,
                    owner_semantic_label=semantic,
                    owner_display_name=display,
                    is_active=True,
                    created_at=now,
                )
                db.add(mapping)
                print(f"✓ Created owner mapping: {code}")

        # Seed kill switch settings (2 per agent/tool as placeholder)
        kill_switches = [
            ("agent", "intake_agent", True, "active"),
            ("agent", "case_owner_agent", True, "recommend_only"),
            ("tool", "create_case", True, "active"),
            ("tool", "update_case", True, "active"),
        ]
        for component_type, component_name, is_enabled, execution_mode in kill_switches:
            exists = db.scalar(
                select(KillSwitchSetting).where(KillSwitchSetting.component_name == component_name)
            )
            if not exists:
                switch = KillSwitchSetting(
                    id=uuid.uuid4(),
                    component_type=component_type,
                    component_name=component_name,
                    is_enabled=is_enabled,
                    execution_mode=execution_mode,
                    created_at=now,
                    updated_at=now,
                )
                db.add(switch)
                print(f"✓ Created kill switch: {component_name}")

        # Seed existing case for user1 (card_declined issue)
        case_id = uuid.UUID(int=1001)
        existing_case = db.scalar(select(Case).where(Case.case_reference == "CP-MOCK1"))
        if not existing_case:
            existing_case = Case(
                id=case_id,
                case_reference="CP-MOCK1",
                customer_party_id="CUST-002",  # user1
                brand="lloyds",
                issue_type="card_declined",
                classification_source="eligibility_rule",
                issue_title="Card Declined",
                issue_summary="My card was declined at a store",
                origin_channel="mobile_app",
                current_lifecycle_state="case_created",
                current_status_code="received",
                current_status_label="Received",
                opened_at=now,
                created_at=now,
                updated_at=now
            )
            db.add(existing_case)
            
            # Add anchor link
            anchor_link = CaseAnchorLink(
                id=uuid.UUID(int=2001),
                case_id=case_id,
                anchor_domain="customer_case",
                anchor_system="case_management",
                anchor_record_type="case",
                anchor_record_id="MOCK-001",
                anchor_reference="CC-MOCK-001",
                link_status="active",
                created_at=now
            )
            db.add(anchor_link)
            
            # Add status projection
            projection = CaseStatusProjection(
                id=uuid.UUID(int=3001),
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
            db.add(projection)
            
            # Add ownership
            ownership = CaseOwnership(
                id=uuid.UUID(int=4001),
                case_id=case_id,
                owner_team_code="INTAKE_DEFAULT",
                owner_semantic_label="Intake Team",
                owner_display_name="Intake & Triage",
                effective_from=now,
                is_current=True,
                created_at=now
            )
            db.add(ownership)
            
            # Add expected-by
            expected_by = ExpectedByCommitment(
                id=uuid.UUID(int=5001),
                case_id=case_id,
                commitment_state="under_review",
                customer_explanatory_text="We're reviewing the timing and will update you soon.",
                confidence_basis="initial",
                effective_from=now,
                is_current=True,
                created_at=now
            )
            db.add(expected_by)
            
            # Add first event
            event = CaseEvent(
                id=uuid.UUID(int=6001),
                case_id=case_id,
                sequence_number=1,
                event_type="CaseCaptured",
                event_timestamp=now,
                summary_text="Case created for card_declined",
                customer_visible_flag=True,
                actor_type="customer",
                correlation_id="seed-001",
                created_at=now
            )
            db.add(event)
            
            print("✓ Created existing case for user1: CP-MOCK1")
            
            # Add 3 owner changes for CP-MOCK1
            # Owner change 1: INTAKE_DEFAULT → CARDS_DISPUTES (1 hour ago)
            event2 = CaseEvent(
                id=uuid.UUID(int=6002),
                case_id=case_id,
                sequence_number=2,
                event_type="OwnerChanged",
                event_timestamp=now - timedelta(hours=1),
                summary_text="Owner changed to Card Disputes",
                event_payload_json={"owner_team_code": "CARDS_DISPUTES"},
                customer_visible_flag=True,
                actor_type="colleague",
                basis_type="approved_manual_update",
                basis_reference="handoff:case_type_match",
                correlation_id="seed-002",
                created_at=now - timedelta(hours=1)
            )
            db.add(event2)
            
            # Close initial ownership, create second ownership
            ownership.effective_to = now - timedelta(hours=1)
            ownership.is_current = False
            
            ownership2 = CaseOwnership(
                id=uuid.UUID(int=4002),
                case_id=case_id,
                owner_team_code="CARDS_DISPUTES",
                owner_semantic_label="Card Disputes Team",
                owner_display_name="Card Disputes",
                source_event_id=uuid.UUID(int=6002),
                effective_from=now - timedelta(hours=1),
                is_current=False,
                created_at=now - timedelta(hours=1)
            )
            db.add(ownership2)
            
            # Owner change 2: CARDS_DISPUTES → FRAUD_TEAM (30 minutes ago)
            event3 = CaseEvent(
                id=uuid.UUID(int=6003),
                case_id=case_id,
                sequence_number=3,
                event_type="OwnerChanged",
                event_timestamp=now - timedelta(minutes=30),
                summary_text="Owner changed to Fraud Investigation",
                event_payload_json={"owner_team_code": "FRAUD_TEAM"},
                customer_visible_flag=True,
                actor_type="colleague",
                basis_type="approved_manual_update",
                basis_reference="handoff:suspected_fraud",
                correlation_id="seed-003",
                created_at=now - timedelta(minutes=30)
            )
            db.add(event3)
            
            # Close second ownership, create third ownership
            ownership2.effective_to = now - timedelta(minutes=30)
            
            ownership3 = CaseOwnership(
                id=uuid.UUID(int=4003),
                case_id=case_id,
                owner_team_code="FRAUD_TEAM",
                owner_semantic_label="Fraud Investigation Team",
                owner_display_name="Fraud Investigation",
                source_event_id=uuid.UUID(int=6003),
                effective_from=now - timedelta(minutes=30),
                is_current=False,
                created_at=now - timedelta(minutes=30)
            )
            db.add(ownership3)
            
            # Owner change 3: FRAUD_TEAM → CARDS_DISPUTES (current - 10 minutes ago)
            event4 = CaseEvent(
                id=uuid.UUID(int=6004),
                case_id=case_id,
                sequence_number=4,
                event_type="OwnerChanged",
                event_timestamp=now - timedelta(minutes=10),
                summary_text="Owner changed to Card Disputes",
                event_payload_json={"owner_team_code": "CARDS_DISPUTES"},
                customer_visible_flag=True,
                actor_type="colleague",
                basis_type="approved_manual_update",
                basis_reference="handoff:fraud_cleared",
                correlation_id="seed-004",
                created_at=now - timedelta(minutes=10)
            )
            db.add(event4)
            
            # Close third ownership, create fourth (current) ownership
            ownership3.effective_to = now - timedelta(minutes=10)
            
            ownership4 = CaseOwnership(
                id=uuid.UUID(int=4004),
                case_id=case_id,
                owner_team_code="CARDS_DISPUTES",
                owner_semantic_label="Card Disputes Team",
                owner_display_name="Card Disputes",
                source_event_id=uuid.UUID(int=6004),
                effective_from=now - timedelta(minutes=10),
                is_current=True,
                created_at=now - timedelta(minutes=10)
            )
            db.add(ownership4)
            
            # Add 2 expected-by revisions
            # Revision 1: under_review → committed (2 hours ago)
            event5 = CaseEvent(
                id=uuid.UUID(int=6005),
                case_id=case_id,
                sequence_number=5,
                event_type="ExpectedByChanged",
                event_timestamp=now - timedelta(hours=2),
                summary_text="Expected by " + (now + timedelta(days=3)).strftime('%Y-%m-%d'),
                event_payload_json={
                    "commitment_state": "committed",
                    "expected_by_at": (now + timedelta(days=3)).isoformat()
                },
                customer_visible_flag=True,
                actor_type="colleague",
                basis_type="approved_manual_update",
                basis_reference="revision:committed",
                correlation_id="seed-005",
                created_at=now - timedelta(hours=2)
            )
            db.add(event5)
            
            # Close initial expected-by, create second
            expected_by.effective_to = now - timedelta(hours=2)
            expected_by.is_current = False
            
            expected_by2 = ExpectedByCommitment(
                id=uuid.UUID(int=5002),
                case_id=case_id,
                commitment_state="committed",
                expected_by_at=now + timedelta(days=3),
                customer_explanatory_text=None,
                confidence_basis="team_capacity",
                source_event_id=uuid.UUID(int=6005),
                effective_from=now - timedelta(hours=2),
                is_current=False,
                created_at=now - timedelta(hours=2)
            )
            db.add(expected_by2)
            
            # Revision 2: committed → revised (current - 1 hour ago, pushed date out by 2 days)
            event6 = CaseEvent(
                id=uuid.UUID(int=6006),
                case_id=case_id,
                sequence_number=6,
                event_type="ExpectedByChanged",
                event_timestamp=now - timedelta(hours=1),
                summary_text="Expected by " + (now + timedelta(days=5)).strftime('%Y-%m-%d'),
                event_payload_json={
                    "commitment_state": "revised",
                    "expected_by_at": (now + timedelta(days=5)).isoformat()
                },
                customer_visible_flag=True,
                actor_type="colleague",
                basis_type="approved_manual_update",
                basis_reference="revision:revised",
                correlation_id="seed-006",
                created_at=now - timedelta(hours=1)
            )
            db.add(event6)
            
            # Close second expected-by, create third (current)
            expected_by2.effective_to = now - timedelta(hours=1)
            
            expected_by3 = ExpectedByCommitment(
                id=uuid.UUID(int=5003),
                case_id=case_id,
                commitment_state="revised",
                expected_by_at=now + timedelta(days=5),
                customer_explanatory_text=None,
                confidence_basis="specialist_review",
                source_event_id=uuid.UUID(int=6006),
                effective_from=now - timedelta(hours=1),
                is_current=True,
                created_at=now - timedelta(hours=1)
            )
            db.add(expected_by3)
            
            print("✓ Added 3 owner changes and 2 expected-by revisions for CP-MOCK1")
        
        # Seed communication and notification records for user1's case
        # Two CaseStatusChanged events: one opened, one new
        comm1 = db.scalar(select(CommunicationRecord).where(CommunicationRecord.id == uuid.UUID(int=7001)))
        if not comm1:
            comm1 = CommunicationRecord(
                id=uuid.UUID(int=7001),
                case_id=case_id,
                communication_type="case_update",
                subject_text="Case status update",
                body_text="The status of your case has been updated. Sign in to view the details.",
                approved_wording_set="status_change_v1",
                source_event_id=uuid.UUID(int=6001),
                correlation_id="seed-002",
                created_at=now
            )
            db.add(comm1)
            
            # Generate a token hash for the notification
            token1 = "seed_token_opened_123"
            token_hash1 = hashlib.sha256(token1.encode()).hexdigest()
            
            notif1 = NotificationRecord(
                id=uuid.UUID(int=8001),
                communication_id=comm1.id,
                case_id=case_id,
                customer_party_id="CUST-002",
                notification_type="case_update",
                safe_preview_text="Your case has been updated",
                deep_link_token_hash=token_hash1,
                deep_link_target="case_view",
                deep_link_expires_at=now + timedelta(hours=24),
                notification_template_code="status_change",
                delivery_state="delivered",
                delivery_attempts=1,
                delivered_at=now,
                opened_at=now,  # Already opened
                correlation_id="seed-002",
                created_at=now
            )
            db.add(notif1)
            print("✓ Created notification 1 (opened)")
        
        comm2 = db.scalar(select(CommunicationRecord).where(CommunicationRecord.id == uuid.UUID(int=7002)))
        if not comm2:
            comm2 = CommunicationRecord(
                id=uuid.UUID(int=7002),
                case_id=case_id,
                communication_type="case_update",
                subject_text="Case status update",
                body_text="The status of your case has been updated. Sign in to view the details.",
                approved_wording_set="status_change_v1",
                source_event_id=uuid.UUID(int=6001),
                correlation_id="seed-003",
                created_at=now
            )
            db.add(comm2)
            
            # Generate a token hash for the notification
            token2 = "seed_token_new_456"
            token_hash2 = hashlib.sha256(token2.encode()).hexdigest()
            
            notif2 = NotificationRecord(
                id=uuid.UUID(int=8002),
                communication_id=comm2.id,
                case_id=case_id,
                customer_party_id="CUST-002",
                notification_type="case_update",
                safe_preview_text="Your case has been updated",
                deep_link_token_hash=token_hash2,
                deep_link_target="case_view",
                deep_link_expires_at=now + timedelta(hours=24),
                notification_template_code="status_change",
                delivery_state="delivered",
                delivery_attempts=1,
                delivered_at=now,
                opened_at=None,  # Not yet opened (new)
                correlation_id="seed-003",
                created_at=now
            )
            db.add(notif2)
            print("✓ Created notification 2 (new)")

        # Seed service incidents (2 active incidents)
        incident1 = db.scalar(
            select(ServiceIncident).where(ServiceIncident.incident_reference == "INC-2024-CARD-001")
        )
        if not incident1:
            incident1 = ServiceIncident(
                id=uuid.UUID(int=9001),
                incident_reference="INC-2024-CARD-001",
                incident_state="declared",
                affected_service_code="card_payments",
                customer_impact_summary="Some card payments may be declined. We're working to resolve this.",
                started_at=now - timedelta(hours=2),
                created_at=now,
                updated_at=now,
            )
            db.add(incident1)
            print("✓ Created service incident: INC-2024-CARD-001")

        incident2 = db.scalar(
            select(ServiceIncident).where(ServiceIncident.incident_reference == "INC-2024-MOBILE-002")
        )
        if not incident2:
            incident2 = ServiceIncident(
                id=uuid.UUID(int=9002),
                incident_reference="INC-2024-MOBILE-002",
                incident_state="monitoring",
                affected_service_code="mobile_banking",
                customer_impact_summary="Mobile app login may be slower than usual. Service is being monitored.",
                started_at=now - timedelta(hours=1),
                created_at=now,
                updated_at=now,
            )
            db.add(incident2)
            print("✓ Created service incident: INC-2024-MOBILE-002")

        # Seed service status publications (2 publications, 1 per incident)
        pub1 = db.scalar(
            select(ServiceStatusPublication).where(ServiceStatusPublication.id == uuid.UUID(int=10001))
        )
        if not pub1:
            pub1 = ServiceStatusPublication(
                id=uuid.UUID(int=10001),
                incident_id=uuid.UUID(int=9001),
                publication_state="active",
                headline_text="Card payment issues",
                summary_text="We're experiencing issues with card payments. Some transactions may be declined.",
                affected_journeys_json=["card_payment", "atm_withdrawal"],
                content_version=1,
                published_at=now - timedelta(hours=2),
                created_at=now,
            )
            db.add(pub1)
            print("✓ Created status publication for INC-2024-CARD-001")

        pub2 = db.scalar(
            select(ServiceStatusPublication).where(ServiceStatusPublication.id == uuid.UUID(int=10002))
        )
        if not pub2:
            pub2 = ServiceStatusPublication(
                id=uuid.UUID(int=10002),
                incident_id=uuid.UUID(int=9002),
                publication_state="active",
                headline_text="Mobile app slower than usual",
                summary_text="Mobile banking app login is taking longer than normal. We're monitoring the situation.",
                affected_journeys_json=["mobile_login", "mobile_banking"],
                content_version=1,
                published_at=now - timedelta(hours=1),
                created_at=now,
            )
            db.add(pub2)
            print("✓ Created status publication for INC-2024-MOBILE-002")

        # Seed lifeline guidance (2 items, 1 per incident)
        lifeline1 = db.scalar(select(LifelineGuidance).where(LifelineGuidance.id == uuid.UUID(int=11001)))
        if not lifeline1:
            lifeline1 = LifelineGuidance(
                id=uuid.UUID(int=11001),
                incident_id=uuid.UUID(int=9001),
                guidance_title="Alternative payment methods",
                guidance_content=(
                    "If your card is declined, try: "
                    "1) Use a different card if you have one. "
                    "2) Use cash or another payment method. "
                    "3) Try again in a few minutes."
                ),
                guidance_type="fallback",
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            db.add(lifeline1)
            print("✓ Created lifeline guidance for INC-2024-CARD-001")

        lifeline2 = db.scalar(select(LifelineGuidance).where(LifelineGuidance.id == uuid.UUID(int=11002)))
        if not lifeline2:
            lifeline2 = LifelineGuidance(
                id=uuid.UUID(int=11002),
                incident_id=uuid.UUID(int=9002),
                guidance_title="Mobile app access tips",
                guidance_content=(
                    "While we resolve the slow login issue: "
                    "1) Be patient - login may take longer than usual. "
                    "2) Try using online banking instead. "
                    "3) Call us if you need urgent assistance."
                ),
                guidance_type="fallback",
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            db.add(lifeline2)
            print("✓ Created lifeline guidance for INC-2024-MOBILE-002")

        # Seed continuity context for user1's case (CP-MOCK1)
        continuity_ctx = db.scalar(
            select(ContinuityContext).where(ContinuityContext.id == uuid.UUID(int=12001))
        )
        if not continuity_ctx:
            continuity_ctx = ContinuityContext(
                id=uuid.UUID(int=12001),
                case_id=case_id,
                package_version=1,
                structured_context_json={
                    "case_reference": "CP-MOCK1",
                    "customer_party_id": "CUST-002",
                    "issue_type": "card_declined",
                    "issue_title": "Card Declined",
                    "issue_summary": "My card was declined at a store",
                    "current_lifecycle_state": "case_created",
                    "current_status_code": "received",
                    "current_status_label": "Received",
                    "owner_team_code": "CARDS_DISPUTES",
                    "owner_display_name": "Card Disputes",
                    "expected_by_at": (now + timedelta(days=5)).isoformat(),
                    "expected_by_text": None,
                    "latest_update_text": "Your case has been received and is being reviewed.",
                    "latest_update_at": now.isoformat(),
                    "channel_history": ["mobile_app", "chat", "phone"],
                    "recent_events": ["CaseCaptured", "OwnerChanged", "OwnerChanged", "OwnerChanged", "ExpectedByChanged", "ExpectedByChanged"]
                },
                llm_safe_payload_json={
                    "case_reference": "CP-MOCK1",
                    "issue_type": "card_declined",
                    "issue_title": "Card Declined",
                    "current_lifecycle_state": "case_created",
                    "current_status_code": "received",
                    "owner_team_code": "CARDS_DISPUTES",
                    "expected_by_at": (now + timedelta(days=5)).isoformat(),
                    "latest_update_text": "Your case has been received and is being reviewed.",
                    "latest_update_at": now.isoformat()
                },
                colleague_payload_json={
                    "case_reference": "CP-MOCK1",
                    "customer_party_id": "CUST-002",
                    "issue_type": "card_declined",
                    "issue_title": "Card Declined",
                    "issue_summary": "My card was declined at a store",
                    "current_lifecycle_state": "case_created",
                    "current_status_code": "received",
                    "owner_team_code": "CARDS_DISPUTES",
                    "owner_display_name": "Card Disputes",
                    "expected_by_at": (now + timedelta(days=5)).isoformat(),
                    "latest_update_text": "Your case has been received and is being reviewed.",
                    "latest_update_at": now.isoformat(),
                    "channel_history": ["mobile_app", "chat", "phone"]
                },
                restricted_fields_excluded_flag=True,
                last_channel="phone",
                last_presented_at=now - timedelta(minutes=5),
                effective_from=now - timedelta(minutes=5),
                is_current=True,
                created_at=now - timedelta(minutes=5)
            )
            db.add(continuity_ctx)
            print("✓ Created continuity context for CP-MOCK1")

        # Seed 2 channel handoffs for user1's case
        handoff1 = db.scalar(
            select(ChannelHandoff).where(ChannelHandoff.id == uuid.UUID(int=13001))
        )
        if not handoff1:
            handoff1 = ChannelHandoff(
                id=uuid.UUID(int=13001),
                case_id=case_id,
                from_channel="mobile_app",
                to_channel="chat",
                context_presented_flag=True,
                handoff_timestamp=now - timedelta(hours=1),
                correlation_id="seed-handoff-001",
                created_at=now - timedelta(hours=1)
            )
            db.add(handoff1)
            print("✓ Created handoff 1: mobile_app → chat")

        handoff2 = db.scalar(
            select(ChannelHandoff).where(ChannelHandoff.id == uuid.UUID(int=13002))
        )
        if not handoff2:
            handoff2 = ChannelHandoff(
                id=uuid.UUID(int=13002),
                case_id=case_id,
                from_channel="chat",
                to_channel="phone",
                context_presented_flag=True,
                handoff_timestamp=now - timedelta(minutes=30),
                correlation_id="seed-handoff-002",
                created_at=now - timedelta(minutes=30)
            )
            db.add(handoff2)
            print("✓ Created handoff 2: chat → phone")

        # Seed 1 protected action request (pending_sca) for user1's case
        action1 = db.scalar(
            select(ProtectedActionRequest).where(ProtectedActionRequest.id == uuid.UUID(int=14001))
        )
        if not action1:
            action1 = ProtectedActionRequest(
                id=uuid.UUID(int=14001),
                case_id=case_id,
                customer_party_id="CUST-002",
                action_type="stop_card",
                action_domain="card",
                action_payload_json={"card_last_four": "1234", "reason": "lost"},
                request_status="pending_sca",
                requires_sca_flag=True,
                sca_outcome="not_invoked",
                sca_invoked_at=now - timedelta(minutes=5),
                correlation_id="seed-action-001",
                created_at=now - timedelta(minutes=5)
            )
            db.add(action1)
            print("✓ Created protected action request (pending_sca)")

        # Seed 10 case events for user1's case (complete event history)
        # Events already created: 6 (CaseCaptured, OwnerChanged x3, ExpectedByChanged x2)
        # Add 4 more events to reach 10
        
        event7 = db.scalar(select(CaseEvent).where(CaseEvent.id == uuid.UUID(int=6007)))
        if not event7:
            # CaseStatusChanged event
            event7 = CaseEvent(
                id=uuid.UUID(int=6007),
                case_id=case_id,
                sequence_number=7,
                event_type="CaseStatusChanged",
                event_timestamp=now - timedelta(minutes=50),
                summary_text="Status changed to Under Review",
                event_payload_json={
                    "lifecycle_from": "case_created",
                    "lifecycle_to": "under_review",
                    "status_code": "under_review",
                    "status_label": "Under Review"
                },
                customer_visible_flag=True,
                actor_type="colleague",
                basis_type="operational_event",
                basis_reference="colleague_accepted",
                correlation_id="seed-007",
                created_at=now - timedelta(minutes=50)
            )
            db.add(event7)
            
        event8 = db.scalar(select(CaseEvent).where(CaseEvent.id == uuid.UUID(int=6008)))
        if not event8:
            # CaseStatusChanged event
            event8 = CaseEvent(
                id=uuid.UUID(int=6008),
                case_id=case_id,
                sequence_number=8,
                event_type="CaseStatusChanged",
                event_timestamp=now - timedelta(minutes=40),
                summary_text="Status changed to Awaiting Customer",
                event_payload_json={
                    "lifecycle_from": "under_review",
                    "lifecycle_to": "awaiting_customer",
                    "status_code": "awaiting_customer",
                    "status_label": "Awaiting Customer"
                },
                customer_visible_flag=True,
                actor_type="colleague",
                basis_type="operational_event",
                basis_reference="information_requested",
                correlation_id="seed-008",
                created_at=now - timedelta(minutes=40)
            )
            db.add(event8)
            
        event9 = db.scalar(select(CaseEvent).where(CaseEvent.id == uuid.UUID(int=6009)))
        if not event9:
            # CaseStatusChanged event
            event9 = CaseEvent(
                id=uuid.UUID(int=6009),
                case_id=case_id,
                sequence_number=9,
                event_type="CaseStatusChanged",
                event_timestamp=now - timedelta(minutes=20),
                summary_text="Status changed to In Progress",
                event_payload_json={
                    "lifecycle_from": "awaiting_customer",
                    "lifecycle_to": "in_progress",
                    "status_code": "in_progress",
                    "status_label": "In Progress"
                },
                customer_visible_flag=True,
                actor_type="colleague",
                basis_type="operational_event",
                basis_reference="customer_responded",
                correlation_id="seed-009",
                created_at=now - timedelta(minutes=20)
            )
            db.add(event9)
            
        event10 = db.scalar(select(CaseEvent).where(CaseEvent.id == uuid.UUID(int=6010)))
        if not event10:
            # ChannelHandoffRecorded event
            event10 = CaseEvent(
                id=uuid.UUID(int=6010),
                case_id=case_id,
                sequence_number=10,
                event_type="ChannelHandoffRecorded",
                event_timestamp=now - timedelta(minutes=10),
                summary_text="Channel handoff: mobile_app → chat",
                event_payload_json={
                    "from_channel": "mobile_app",
                    "to_channel": "chat",
                    "context_presented_flag": True
                },
                customer_visible_flag=True,
                actor_type="customer",
                correlation_id="seed-010",
                created_at=now - timedelta(minutes=10)
            )
            db.add(event10)
            
        event11 = db.scalar(select(CaseEvent).where(CaseEvent.id == uuid.UUID(int=6011)))
        if not event11:
            # ProtectedActionRequested event
            event11 = CaseEvent(
                id=uuid.UUID(int=6011),
                case_id=case_id,
                sequence_number=11,
                event_type="ProtectedActionRequested",
                event_timestamp=now - timedelta(minutes=5),
                summary_text="Protected action requested: stop_card",
                event_payload_json={
                    "action_id": str(uuid.UUID(int=14001)),
                    "action_type": "stop_card",
                    "action_domain": "card",
                    "sca_invoked": True
                },
                customer_visible_flag=True,
                actor_type="customer",
                actor_reference="CUST-002",
                correlation_id="seed-action-001",
                created_at=now - timedelta(minutes=5)
            )
            db.add(event11)
            print("✓ Created 5 additional case events (total 11)")

        db.commit()
        print("\n✅ Seed data created successfully")
        print("\nDefault credentials:")
        print("  Customer: admin@example.com / admin123")
        print("  Colleague: colleague@example.com / colleague123")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error seeding data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
