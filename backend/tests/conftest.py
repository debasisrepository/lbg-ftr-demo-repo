"""Shared test fixtures for backend tests"""
import os
import tempfile
from pathlib import Path

# 1. Configuration BEFORE anything imports the app
_BACKEND = Path(__file__).resolve().parents[1]
for _seed in ("dev.env", ".env.example"):
    if (_BACKEND / _seed).is_file():
        for _line in (_BACKEND / _seed).read_text().splitlines():
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _value = _line.removeprefix("export ").split("=", 1)
                os.environ.setdefault(_key.strip(), _value.strip().strip("\"'"))
        break

_DB_FILE = Path(tempfile.mkdtemp()) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_FILE.as_posix()}"
os.environ["RATE_LIMIT_ENABLED"] = "false"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401 - registers every model on Base before create_all

# Import the app after models are registered
from app import main
from app.database import Base, get_db

engine = create_engine(os.environ["DATABASE_URL"], connect_args={"check_same_thread": False})
TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture(autouse=True)
def _fresh_schema():
    """Create fresh schema before each test"""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session() -> Session:
    """Test database session"""
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """Test client with overridden database session"""
    main.app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(main.app) as test_client:
        yield test_client
    main.app.dependency_overrides.clear()


@pytest.fixture
def seeded_data(db_session):
    """Run seed data for tests that need it"""
    from app.seed import seed_database
    seed_database()
    return True


@pytest.fixture
def demo_customer(db_session):
    """Get or create demo customer with device and profile"""
    import uuid
    from datetime import UTC, datetime

    from app.models.customer import Customer, Device, Profile

    # Check if already exists (seeded by app lifespan or seeded_data fixture)
    customer_id = uuid.UUID("10000000-0000-0000-0000-000000000001")
    customer = db_session.get(Customer, customer_id)

    if not customer:
        customer = Customer(
            customer_id=customer_id,
            external_identity_ref="ciam_sasha_001",
            customer_type="retail",
            first_name="Sasha",
            primary_contact_ref="sasha.patel@gmail.com",
            status="active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        db_session.add(customer)

        profile = Profile(
            profile_id=uuid.UUID("10000000-0000-0000-0000-000000000101"),
            customer_id=customer.customer_id,
            profile_type="personal",
            external_profile_ref="profile_sasha_personal",
            display_name="Personal",
            status="active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        db_session.add(profile)

        device = Device(
            device_id=uuid.UUID("10000000-0000-0000-0000-000000000201"),
            customer_id=customer.customer_id,
            device_public_key_ref="device_key_sasha_001",
            platform_type="ios",
            platform_device_ref="ios_device_sasha_001",
            device_label="Sasha's iPhone",
            trust_state="trusted",
            integrity_state="ok",
            biometric_enabled=True,
            passcode_failed_count=0,
            registered_at=datetime.now(UTC),
            last_seen_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        db_session.add(device)

        db_session.commit()
    else:
        profile = db_session.get(Profile, uuid.UUID("10000000-0000-0000-0000-000000000101"))
        device = db_session.get(Device, uuid.UUID("10000000-0000-0000-0000-000000000201"))

    return customer, profile, device


@pytest.fixture
def auth_client(client, db_session, demo_customer):
    """Authenticated test client (logged in through real auth endpoint)"""
    customer, profile, device = demo_customer

    # Sign in with demo credentials
    response = client.post(
        "/api/v1/auth/sign-in",
        json={
            "username": "sasha.patel@gmail.com",
            "password": "Demo1234!",
            "device_id": str(device.device_id)
        }
    )
    assert response.status_code == 200, f"Sign-in failed: {response.text}"
    sign_in_data = response.json()
    session_id = sign_in_data.get("session_id")
    assert session_id, "No session_id received from sign-in"

    # Submit proof (passcode)
    response = client.post(
        "/api/v1/auth/proof",
        json={
            "session_id": session_id,
            "proof_type": "passcode",
            "proof_value": "123456",
            "device_id": str(device.device_id)
        }
    )
    assert response.status_code == 200, f"Proof failed: {response.text}"

    # Extract token and set auth header
    proof_data = response.json()
    token = proof_data.get("access_token")
    assert token, f"No access_token received from proof: {proof_data}"

    client.headers["Authorization"] = f"Bearer {token}"
    return client
