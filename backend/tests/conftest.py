"""Test fixtures."""
import os
import tempfile
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.clock import Clock
from app.core.security import hash_password
from app.database import Base, get_db
from app.main import app as fastapi_app
from app.models.auth import UserAccount

# Load dev.env for tests
_BACKEND = Path(__file__).resolve().parents[1]
for _seed in ("dev.env", ".env.example"):
    if (_BACKEND / _seed).is_file():
        for _line in (_BACKEND / _seed).read_text().splitlines():
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _value = _line.removeprefix("export ").split("=", 1)
                os.environ.setdefault(_key.strip(), _value.strip().strip("\"'"))
        break

# Test database
_DB_FILE = Path(tempfile.mkdtemp()) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_FILE.as_posix()}"
os.environ["RATE_LIMIT_ENABLED"] = "false"

# Import all models to ensure they're registered
import app.models.actions  # noqa: F401
import app.models.audit  # noqa: F401
import app.models.auth  # noqa: F401
import app.models.case  # noqa: F401
import app.models.communication  # noqa: F401
import app.models.config  # noqa: F401
import app.models.continuity  # noqa: F401
import app.models.governance  # noqa: F401
import app.models.incident  # noqa: F401
import app.models.ownership  # noqa: F401

engine = create_engine(os.environ["DATABASE_URL"], connect_args={"check_same_thread": False})
TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=True)


@pytest.fixture(autouse=True)
def _fresh_schema():
    """Create fresh schema for each test."""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session() -> Session:
    """Database session fixture."""
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """Test client fixture."""
    fastapi_app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()


def login_helper(client: TestClient, username: str = "tester@example.com", password: str = "Test-pass-1") -> tuple[TestClient, str]:
    """Login helper to get authenticated client and session_id."""
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    data = response.json()
    session_id = data.get("session_id")
    return client, session_id


@pytest.fixture
def auth_client(db_session):
    """Authenticated client fixture with proper auth headers."""
    from app.models.config import IssueEligibilityRule, OwnerTeamMapping
    
    # Create test user
    now = Clock.utcnow()
    test_user = UserAccount(
        id=uuid.UUID(int=100),
        username="tester@example.com",
        hashed_password=hash_password("Test-pass-1"),
        email="tester@example.com",
        display_name="Test User",
        scope="customer",
        customer_party_id="TEST-001",
        brand="lloyds",
        is_active=True,
        failed_login_count=0,
        created_at=now,
        updated_at=now,
    )
    db_session.add(test_user)
    
    # Create user1 for cross-customer tests
    user1 = UserAccount(
        id=uuid.UUID(int=101),
        username="user1@example.com",
        hashed_password=hash_password("user123"),
        email="user1@example.com",
        display_name="User One",
        scope="customer",
        customer_party_id="CUST-002",
        brand="lloyds",
        is_active=True,
        failed_login_count=0,
        created_at=now,
        updated_at=now,
    )
    db_session.add(user1)
    
    # Seed eligibility rules
    rules = [
        IssueEligibilityRule(
            id=uuid.uuid4(),
            issue_type="card_declined",
            is_eligible=True,
            priority_weight=100,
            created_at=now
        ),
        IssueEligibilityRule(
            id=uuid.uuid4(),
            issue_type="payment_missing",
            is_eligible=True,
            priority_weight=90,
            created_at=now
        ),
        IssueEligibilityRule(
            id=uuid.uuid4(),
            issue_type="general_query",
            is_eligible=False,
            redirect_journey_code="existing_support",
            priority_weight=50,
            created_at=now
        ),
    ]
    for rule in rules:
        db_session.add(rule)
    
    # Seed owner mappings (5 teams)
    owner_mappings = [
        ("INTAKE_DEFAULT", "Intake Team", "Intake & Triage"),
        ("CARDS_DISPUTES", "Card Disputes Team", "Card Disputes"),
        ("PAYMENTS_SUPPORT", "Payments Support Team", "Payments Support"),
        ("FRAUD_TEAM", "Fraud Investigation Team", "Fraud Investigation"),
        ("COMPLAINTS_TEAM", "Complaints Team", "Customer Complaints"),
    ]
    for code, semantic, display in owner_mappings:
        mapping = OwnerTeamMapping(
            id=uuid.uuid4(),
            owner_team_code=code,
            owner_semantic_label=semantic,
            owner_display_name=display,
            is_active=True,
            created_at=now
        )
        db_session.add(mapping)
    
    # Create colleague user for ownership tests
    colleague_user = UserAccount(
        id=uuid.UUID(int=102),
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
    db_session.add(colleague_user)
    
    db_session.commit()
    
    # Create a temp client to login
    fastapi_app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(fastapi_app) as temp_client:
        response = temp_client.post("/api/v1/auth/login", json={"username": "tester@example.com", "password": "Test-pass-1"})
        assert response.status_code == 200, response.text
        data = response.json()
        token = data.get("access_token")
        session_id = data.get("session_id")
    
    # Now create the auth client with the token as default header
    with TestClient(fastapi_app, headers={"Authorization": f"Bearer {token}"}) as auth_test_client:
        auth_test_client._session_id = session_id
        yield auth_test_client
    
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def colleague_client(client, db_session):
    """Authenticated colleague client fixture for ownership tests."""
    # Import required models for seeding
    from app.models.config import OwnerTeamMapping
    
    # Seed colleague user and mappings (needed for ownership tests)
    now = Clock.utcnow()
    
    # Create colleague user
    colleague_user = UserAccount(
        id=uuid.UUID(int=102),
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
    db_session.add(colleague_user)
    
    # Seed owner mappings (5 teams)
    owner_mappings = [
        ("INTAKE_DEFAULT", "Intake Team", "Intake & Triage"),
        ("CARDS_DISPUTES", "Card Disputes Team", "Card Disputes"),
        ("PAYMENTS_SUPPORT", "Payments Support Team", "Payments Support"),
        ("FRAUD_TEAM", "Fraud Investigation Team", "Fraud Investigation"),
        ("COMPLAINTS_TEAM", "Complaints Team", "Customer Complaints"),
    ]
    for code, semantic, display in owner_mappings:
        mapping = OwnerTeamMapping(
            id=uuid.uuid4(),
            owner_team_code=code,
            owner_semantic_label=semantic,
            owner_display_name=display,
            is_active=True,
            created_at=now
        )
        db_session.add(mapping)
    
    db_session.commit()
    
    # Login as colleague
    client_coll, session_id = login_helper(client, "colleague@example.com", "colleague123")
    client_coll._session_id = session_id
    return client_coll


@pytest.fixture
def auth_client_colleague(colleague_client):
    """Alias for colleague_client for continuity tests."""
    return colleague_client
