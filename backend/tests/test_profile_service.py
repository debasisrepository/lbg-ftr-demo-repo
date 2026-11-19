"""Tests for profile service"""
import uuid
from datetime import UTC, datetime

import pytest

from app.core.errors import AuthorizationError
from app.models.customer import Profile
from app.models.session import Session as SessionModel
from app.services.profile_service import ProfileService


def test_get_profiles_for_customer(db_session):
    """Test getting profiles for a customer"""
    customer_id = uuid.uuid4()

    # Create profiles
    profile1 = Profile(
        profile_id=uuid.uuid4(),
        customer_id=customer_id,
        profile_type="personal",
        external_profile_ref="prof1",
        display_name="Personal",
        status="active",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    profile2 = Profile(
        profile_id=uuid.uuid4(),
        customer_id=customer_id,
        profile_type="business",
        external_profile_ref="prof2",
        display_name="Business",
        status="active",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add_all([profile1, profile2])
    db_session.commit()

    service = ProfileService()
    profiles = service.get_profiles_for_customer(db_session, customer_id)

    assert len(profiles) == 2
    assert {p.profile_type for p in profiles} == {"personal", "business"}


def test_set_active_profile(db_session):
    """Test setting active profile for session"""
    customer_id = uuid.uuid4()
    session_id = uuid.uuid4()
    profile_id = uuid.uuid4()

    # Create profile
    profile = Profile(
        profile_id=profile_id,
        customer_id=customer_id,
        profile_type="personal",
        external_profile_ref="prof1",
        display_name="Personal",
        status="active",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(profile)

    # Create session
    session = SessionModel(
        session_id=session_id,
        customer_id=customer_id,
        device_id=uuid.uuid4(),
        session_token_hash="test_hash",
        auth_level="proven",
        started_at=datetime.now(UTC),
        last_activity_at=datetime.now(UTC),
        expires_at=datetime.now(UTC),
        inactivity_timeout_seconds=300,
        correlation_id="test_corr_id",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(session)
    db_session.commit()

    service = ProfileService()
    service.set_active_profile(db_session, session_id, customer_id, profile_id)
    db_session.commit()

    # Verify profile was set
    updated_session = db_session.get(SessionModel, session_id)
    assert updated_session.active_profile_id == profile_id


def test_set_active_profile_wrong_customer(db_session):
    """Test setting active profile with wrong customer raises error"""
    customer_id = uuid.uuid4()
    wrong_customer_id = uuid.uuid4()
    session_id = uuid.uuid4()
    profile_id = uuid.uuid4()

    # Create profile for different customer
    profile = Profile(
        profile_id=profile_id,
        customer_id=wrong_customer_id,
        profile_type="personal",
        external_profile_ref="prof1",
        display_name="Personal",
        status="active",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(profile)

    # Create session
    session = SessionModel(
        session_id=session_id,
        customer_id=customer_id,
        device_id=uuid.uuid4(),
        session_token_hash="test_hash",
        auth_level="proven",
        started_at=datetime.now(UTC),
        last_activity_at=datetime.now(UTC),
        expires_at=datetime.now(UTC),
        inactivity_timeout_seconds=300,
        correlation_id="test_corr_id_2",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(session)
    db_session.commit()

    service = ProfileService()
    with pytest.raises(AuthorizationError):
        service.set_active_profile(db_session, session_id, customer_id, profile_id)
