"""CLI commands for database seeding and management."""
import sys
import uuid
from datetime import timedelta

from app.core.clock import SystemClock
from app.core.config import settings
from app.core.db import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.audit import AuditEvent
from app.models.policy import PolicyRuleSetVersion
from app.models.roles import RoleAssignment, RoleProfile
from app.models.users import User
from app.policy.rules_seed import seed_policy_rules


def seed():
    """Seed database with initial data."""
    # Import all models to ensure they're registered
    import app.models.audit  # noqa: F401
    import app.models.customers  # noqa: F401
    import app.models.policy  # noqa: F401
    import app.models.promises  # noqa: F401
    import app.models.queue  # noqa: F401
    import app.models.receivables  # noqa: F401
    import app.models.roles  # noqa: F401
    import app.models.sessions  # noqa: F401
    import app.models.users  # noqa: F401

    # Create tables if they don't exist (for SQLite only)
    if settings.database_url.startswith("sqlite") or settings.load_seed_data:
        print("Creating tables...")
        Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    clock = SystemClock()
    now = clock.now()

    try:
        # Check if already seeded
        existing_user = db.query(User).filter(User.username == "analyst1").first()
        if existing_user:
            print("Database already seeded. Skipping.")
            return

        print("Seeding database...")

        # Seed role profiles
        role_profiles = [
            RoleProfile(
                id=uuid.uuid4(),
                created_at=now,
                updated_at=now,
                role_code="collections_analyst",
                role_label="Collections Analyst",
                description="Standard collections analyst role",
                allowed_widgets_json={"codes": ["queue_summary", "open_promises"]},
                entitled_queue_states_json={"states": ["active", "awaiting_follow_up"]},
                allowed_actions_json={"actions": ["queue.read", "queue.refresh", "customer.view", "promise.create", "promise.read", "policy.read", "audit.read"]},
                can_view_sensitive_fields=False,
                profile_status="active"
            ),
            RoleProfile(
                id=uuid.uuid4(),
                created_at=now,
                updated_at=now,
                role_code="collections_reviewer",
                role_label="Collections Reviewer",
                description="Collections reviewer with elevated permissions",
                allowed_widgets_json={"codes": ["queue_summary", "open_promises", "audit_trail"]},
                entitled_queue_states_json={"states": ["active", "awaiting_follow_up", "blocked"]},
                allowed_actions_json={"actions": ["queue.read", "queue.refresh", "customer.view", "promise.create", "promise.read", "policy.read", "audit.read"]},
                can_view_sensitive_fields=True,
                profile_status="active"
            ),
        ]

        for profile in role_profiles:
            db.add(profile)

        db.flush()

        # Seed users
        users = [
            User(
                id=uuid.uuid4(),
                created_at=now,
                updated_at=now,
                username="analyst1",
                display_name="Alice Analyst",
                email="alice.analyst@example.com",
                password_hash=hash_password("analyst123"),
                status="active",
                primary_region="US",
            ),
            User(
                id=uuid.uuid4(),
                created_at=now,
                updated_at=now,
                username="reviewer1",
                display_name="Bob Reviewer",
                email="bob.reviewer@example.com",
                password_hash=hash_password("reviewer123"),
                status="active",
                primary_region="US",
            ),
        ]

        for user in users:
            db.add(user)

        db.flush()

        # Seed role assignments
        assignments = [
            RoleAssignment(
                id=uuid.uuid4(),
                created_at=now,
                updated_at=now,
                user_id=users[0].id,
                role_code="collections_analyst",
                assignment_status="active",
            ),
            RoleAssignment(
                id=uuid.uuid4(),
                created_at=now,
                updated_at=now,
                user_id=users[1].id,
                role_code="collections_reviewer",
                assignment_status="active",
            ),
        ]

        for assignment in assignments:
            db.add(assignment)

        # Seed sample customers and accounts for E2E tests
        from app.models.customers import Customer, CustomerAccount, Invoice
        from app.models.queue import InteractionLogEntry
        
        # Create sample customer with known UUID for E2E tests
        customer1_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        customer1 = Customer(
            id=customer1_id,
            created_at=now,
            updated_at=now,
            sap_customer_ref="CUST001",
            customer_name="ABC Grocers Ltd",
            regional_business_unit="UK",
            credit_status_indicator="normal",
            master_data_source="SAP",
            last_sync_at=now,
        )
        db.add(customer1)
        
        # Create customer account with known UUID
        account1_id = uuid.UUID("00000000-0000-0000-0000-000000000002")
        account1 = CustomerAccount(
            id=account1_id,
            created_at=now,
            updated_at=now,
            customer_id=customer1_id,
            sap_account_ref="ACCT001",
            company_code="1000",
            currency_code="GBP",
            account_status="active",
            risk_segment="medium",
            portfolio_ref="PORT_UK",
            collector_owner_user_id=users[0].id,
            last_sync_at=now,
        )
        db.add(account1)
        
        # Create sample invoice
        invoice1 = Invoice(
            id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
            customer_account_id=account1_id,
            sap_invoice_ref="INV001",
            invoice_number="9000001",
            document_date=now - timedelta(days=90),
            due_date=now - timedelta(days=60),
            invoice_amount=15000.00,
            open_amount=15000.00,
            currency_code="GBP",
            invoice_status="open",
            last_sync_at=now,
        )
        db.add(invoice1)
        
        # Create sample interaction
        interaction1 = InteractionLogEntry(
            id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
            customer_account_id=account1_id,
            interaction_type="call",
            interaction_direction="outbound",
            interaction_channel="phone",
            occurred_at=now - timedelta(days=1),
            recorded_by_user_id=users[0].id,
            summary_text="Discussed overdue balance with customer",
        )
        db.add(interaction1)
        
        db.flush()

        # Seed policy rules
        seed_policy_rules(db, clock)

        db.commit()
        print("Database seeded successfully!")
        print("\nDefault credentials:")
        print("  Analyst: analyst1 / analyst123")
        print("  Reviewer: reviewer1 / reviewer123")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


def activate_rule_set(version: int, approver: str):
    """Activate a policy rule set version.
    
    Args:
        version: Version number to activate
        approver: Username of approver
    """
    db = SessionLocal()
    clock = SystemClock()
    now = clock.now()

    try:
        # Find rule set by version number
        rule_set = db.query(PolicyRuleSetVersion).filter(
            PolicyRuleSetVersion.version_number == version
        ).first()

        if not rule_set:
            print(f"Error: Rule set version {version} not found")
            sys.exit(1)

        # Find approver user
        approver_user = db.query(User).filter(User.username == approver).first()
        if not approver_user:
            print(f"Error: User '{approver}' not found")
            sys.exit(1)

        # Deactivate any currently active rule sets for the same region
        active_sets = db.query(PolicyRuleSetVersion).filter(
            PolicyRuleSetVersion.rule_set_status == "active",
            PolicyRuleSetVersion.region_code == rule_set.region_code
        ).all()

        for active_set in active_sets:
            active_set.rule_set_status = "superseded"
            active_set.updated_at = now
            active_set.effective_to = now

        # Activate the target rule set
        rule_set.rule_set_status = "active"
        rule_set.approved_by_user_id = approver_user.id
        rule_set.approved_at = now
        rule_set.effective_from = now
        rule_set.updated_at = now

        db.commit()

        print(f"Successfully activated rule set version {version}")
        print(f"  Region: {rule_set.region_code}")
        print(f"  Label: {rule_set.version_label}")
        print(f"  Approved by: {approver}")
        print(f"  Effective from: {now}")

        if active_sets:
            print(f"  Superseded {len(active_sets)} previous rule set(s)")

    except Exception as e:
        db.rollback()
        print(f"Error activating rule set: {e}")
        raise
    finally:
        db.close()


def purge_audit_events(retention_days: int = 90):
    """Purge old audit events beyond retention period.
    
    Args:
        retention_days: Number of days to retain (default 90)
    """
    db = SessionLocal()
    clock = SystemClock()
    now = clock.now()
    cutoff_date = now - timedelta(days=retention_days)

    try:
        # Count events to be purged
        count = db.query(AuditEvent).filter(
            AuditEvent.event_timestamp < cutoff_date
        ).count()

        if count == 0:
            print(f"No audit events older than {retention_days} days found")
            return

        print(f"Purging {count} audit events older than {cutoff_date.date()}...")

        # Delete old events
        db.query(AuditEvent).filter(
            AuditEvent.event_timestamp < cutoff_date
        ).delete(synchronize_session=False)

        db.commit()
        print(f"Successfully purged {count} audit events")

    except Exception as e:
        db.rollback()
        print(f"Error purging audit events: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python app/cli.py seed")
        print("  python app/cli.py activate-rule-set --version N --approver USERNAME")
        print("  python app/cli.py purge --retention-days N")
        sys.exit(1)

    command = sys.argv[1]

    if command == "seed":
        seed()
    elif command == "activate-rule-set":
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--version", type=int, required=True)
        parser.add_argument("--approver", type=str, required=True)
        args = parser.parse_args(sys.argv[2:])
        activate_rule_set(args.version, args.approver)
    elif command == "purge":
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--retention-days", type=int, default=90)
        args = parser.parse_args(sys.argv[2:])
        purge_audit_events(args.retention_days)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
