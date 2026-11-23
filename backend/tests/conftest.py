"""
Shared test fixtures for all tests.
"""
import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Configuration BEFORE importing the app
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

from datetime import UTC

import app.models  # noqa: F401
from app.database import Base, get_db
from app.main import app as fastapi_app

engine = create_engine(os.environ["DATABASE_URL"], connect_args={"check_same_thread": False})
TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture(autouse=True)
def _fresh_schema():
    """Create fresh schema for each test."""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session() -> Session:
    """Provide a database session for tests."""
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """Provide a test client with database session override."""
    # Seed database for integration tests
    from app.seed import seed_database
    seed_database(db_session)
    
    fastapi_app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def test_customer(db_session):
    """Create a test customer with credentials and devices."""
    import uuid
    from datetime import datetime, timedelta

    import bcrypt

    from app.models.customer_profile_ref import CustomerProfileRef
    from app.models.device_registration import DeviceRegistration
    from app.models.sandbox_credential import SandboxCredential
    
    customer_id = uuid.uuid4()
    customer = CustomerProfileRef(
        id=customer_id,
        customer_party_id="TEST-CUST-001",
        ciam_subject_reference="ciam-test-001",
        display_name="Test User",
        profile_type="personal",
        release_scope_status="in_scope",
        is_active=True,
    )
    db_session.add(customer)
    
    # Add credential
    passcode = "Test1234"
    passcode_hash = bcrypt.hashpw(passcode.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
    credential = SandboxCredential(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer_id,
        passcode_hash=passcode_hash,
        failed_attempt_count=0,
    )
    db_session.add(credential)
    
    # Add device
    device = DeviceRegistration(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer_id,
        device_identifier_hash="test-device-hash",
        mobile_platform="iOS",
        registration_status="active",
        ciam_subject_reference="ciam-test-001",
        registered_at=datetime.now(UTC) - timedelta(days=1),
    )
    db_session.add(device)
    
    db_session.commit()
    db_session.refresh(customer)
    
    return {
        "customer": customer,
        "passcode": passcode,
        "device_hash": "test-device-hash",
    }


@pytest.fixture
def auth_client(client):
    """Provide an authenticated test client using seeded customer."""
    # Login with seeded customer (Alex Taylor from seed.py)
    login_response = client.post("/api/v1/auth/login", json={
        "device_identifier": "device-CUST-SYNTH-001-iOS",
        "mobile_platform": "iOS",
        "passcode": "Pass1234"
    })
    
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    token = login_response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client
