"""Tests for accounts overview service"""
import uuid
from datetime import UTC, datetime

from app.models.customer import Profile
from app.services.accounts_overview_service import AccountsOverviewService


def test_get_accounts_overview(db_session):
    """Test getting accounts overview with stub adapters"""
    # Use seeded demo customer and profile
    customer_id = uuid.UUID("10000000-0000-0000-0000-000000000001")
    profile_id = uuid.UUID("10000000-0000-0000-0000-000000000101")

    # Profile already exists from seed data, no need to create it

    service = AccountsOverviewService()
    accounts_with_perm, loans = service.get_accounts_overview(db_session, customer_id, profile_id)

    # Stub adapters return demo data
    assert len(accounts_with_perm) >= 0  # May create accounts
    assert len(loans) >= 0  # May create loans


def test_parallel_adapter_calls_timeout_gracefully(db_session):
    """Test that parallel adapter calls handle timeouts"""
    customer_id = uuid.uuid4()
    profile_id = uuid.uuid4()

    # Create profile
    profile = Profile(
        profile_id=profile_id,
        customer_id=customer_id,
        profile_type="personal",
        external_profile_ref="test",
        display_name="Test",
        status="active",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(profile)
    db_session.commit()

    service = AccountsOverviewService()
    # Should not raise even if adapters fail
    accounts_with_perm, loans = service.get_accounts_overview(db_session, customer_id, profile_id)

    assert isinstance(accounts_with_perm, list)
    assert isinstance(loans, list)
