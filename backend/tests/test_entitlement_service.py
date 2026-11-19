"""Tests for entitlement service"""
import uuid
from datetime import UTC, datetime

import pytest

from app.core.errors import AuthorizationError
from app.models.customer import Entitlement, Profile
from app.services.entitlement_service import EntitlementService


def test_check_capability_with_entitlement(db_session):
    """Test capability check with valid entitlement"""
    profile_id = uuid.uuid4()
    customer_id = uuid.uuid4()

    # Create profile
    profile = Profile(
        profile_id=profile_id,
        customer_id=customer_id,
        profile_type="personal",
        external_profile_ref="test_profile",
        display_name="Test",
        status="active",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(profile)

    # Create entitlement
    entitlement = Entitlement(
        entitlement_id=uuid.uuid4(),
        profile_id=profile_id,
        entitlement_code="test_code",
        capability_type="payer",
        can_view_accounts=True,
        can_manage_payees=True,
        can_initiate_payments=False,
        source_system_ref="test_mandate",
        effective_from=datetime.now(UTC),
        effective_to=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(entitlement)
    db_session.commit()

    service = EntitlementService()

    assert service.check_capability(db_session, profile_id, "view_accounts") is True
    assert service.check_capability(db_session, profile_id, "manage_payees") is True
    assert service.check_capability(db_session, profile_id, "initiate_payments") is False


def test_check_capability_without_entitlement_fail_safe(db_session):
    """Test capability check without entitlement (fail safe mode)"""
    profile_id = uuid.uuid4()
    service = EntitlementService()

    # No entitlement exists, should return False in fail-safe mode
    assert service.check_capability(db_session, profile_id, "view_accounts", fail_safe=True) is False


def test_require_capability_raises_on_missing(db_session):
    """Test require_capability raises when capability missing"""
    profile_id = uuid.uuid4()
    service = EntitlementService()

    with pytest.raises(AuthorizationError):
        service.require_capability(db_session, profile_id, "view_accounts")
