from sqlalchemy.orm import Session
from sqlalchemy import select
from app.auth.models import AppUser
from app.services.orchestrator.models import AgentRegistry
from app.services.policy.models import ActionControl
from app.auth.passwords import PasswordHasher
from app.core.logging import logger


def seed_all(db: Session) -> None:
    logger.info("Starting seed data creation...")

    seed_users(db)
    seed_agent_registry(db)
    seed_action_control(db)

    logger.info("Seed data creation complete")


def seed_users(db: Session) -> None:
    admin_email = "admin@example.com"
    result = db.execute(select(AppUser).where(AppUser.email == admin_email))
    if result.scalar_one_or_none():
        logger.info(f"User {admin_email} already exists, skipping")
        return

    admin = AppUser(
        email=admin_email,
        hashed_password=PasswordHasher.hash_password("admin123"),
        is_active=True,
        is_colleague=False,
        customer_reference="CUST-001",
        brand="lloyds",
        failed_login_count=0,
    )
    db.add(admin)

    colleague = AppUser(
        email="colleague@example.com",
        hashed_password=PasswordHasher.hash_password("colleague123"),
        is_active=True,
        is_colleague=True,
        customer_reference=None,
        brand=None,
        failed_login_count=0,
    )
    db.add(colleague)

    db.commit()
    logger.info("Seeded 2 users: admin@example.com, colleague@example.com")


def seed_agent_registry(db: Session) -> None:
    result = db.execute(select(AgentRegistry))
    if result.scalars().first():
        logger.info("Agent registry already seeded, skipping")
        return

    agents = [
        AgentRegistry(
            agent_code="intake_triage_agent",
            agent_role="intake_triage",
            max_autonomy_level=1,
            shadow_mode_default=True,
            kill_switch_active=False,
        ),
        AgentRegistry(
            agent_code="case_owner_agent",
            agent_role="case_owner",
            max_autonomy_level=1,
            shadow_mode_default=True,
            kill_switch_active=False,
        ),
        AgentRegistry(
            agent_code="guardrail_supervisor_agent",
            agent_role="guardrail_supervisor",
            max_autonomy_level=0,
            shadow_mode_default=True,
            kill_switch_active=False,
        ),
        AgentRegistry(
            agent_code="colleague_copilot_agent",
            agent_role="colleague_copilot",
            max_autonomy_level=0,
            shadow_mode_default=True,
            kill_switch_active=False,
        ),
    ]

    for agent in agents:
        db.add(agent)

    db.commit()
    logger.info("Seeded 4 agents")


def seed_action_control(db: Session) -> None:
    result = db.execute(select(ActionControl))
    if result.scalars().first():
        logger.info("Action control already seeded, skipping")
        return

    actions = [
        ActionControl(
            action_code="get_transactions",
            action_type="tool",
            max_autonomy_level=1,
            sca_required=False,
            changes_card_or_money=False,
            shadow_mode=True,
            kill_switch_active=False,
        ),
        ActionControl(
            action_code="request_document",
            action_type="tool",
            max_autonomy_level=1,
            sca_required=False,
            changes_card_or_money=False,
            shadow_mode=True,
            kill_switch_active=False,
        ),
        ActionControl(
            action_code="schedule_callback",
            action_type="tool",
            max_autonomy_level=1,
            sca_required=False,
            changes_card_or_money=False,
            shadow_mode=True,
            kill_switch_active=False,
        ),
        ActionControl(
            action_code="card_controls",
            action_type="tool",
            max_autonomy_level=1,
            sca_required=True,
            changes_card_or_money=True,
            shadow_mode=True,
            kill_switch_active=False,
        ),
        ActionControl(
            action_code="retry_payment",
            action_type="tool",
            max_autonomy_level=1,
            sca_required=True,
            changes_card_or_money=True,
            shadow_mode=True,
            kill_switch_active=False,
        ),
        ActionControl(
            action_code="create_case",
            action_type="tool",
            max_autonomy_level=2,
            sca_required=False,
            changes_card_or_money=False,
            shadow_mode=True,
            kill_switch_active=False,
        ),
        ActionControl(
            action_code="update_case",
            action_type="tool",
            max_autonomy_level=2,
            sca_required=False,
            changes_card_or_money=False,
            shadow_mode=True,
            kill_switch_active=False,
        ),
        ActionControl(
            action_code="route_to_queue",
            action_type="tool",
            max_autonomy_level=2,
            sca_required=False,
            changes_card_or_money=False,
            shadow_mode=True,
            kill_switch_active=False,
        ),
        ActionControl(
            action_code="provide_information",
            action_type="information",
            max_autonomy_level=0,
            sca_required=False,
            changes_card_or_money=False,
            shadow_mode=True,
            kill_switch_active=False,
        ),
    ]

    for action in actions:
        db.add(action)

    db.commit()
    logger.info("Seeded 9 action controls")


if __name__ == "__main__":
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()
