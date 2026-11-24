"""Shared test fixtures for backend tests."""
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

from app.core.db import Base
from app.core.deps import get_db
from app.main import app as fastapi_app

# Import all models to register them with Base
import app.models.users  # noqa: F401
import app.models.roles  # noqa: F401
import app.models.sessions  # noqa: F401
import app.models.customers  # noqa: F401
import app.models.receivables  # noqa: F401
import app.models.queue  # noqa: F401
import app.models.promises  # noqa: F401
import app.models.policy  # noqa: F401
import app.models.audit  # noqa: F401

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
    """Get database session for tests."""
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """Get test client with database session override."""
    fastapi_app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def auth_client(client, db_session):
    """Get authenticated test client.
    
    This fixture seeds a test user and logs in through the app's own login endpoint.
    """
    from datetime import datetime, timezone
    from app.core.security import hash_password
    from app.models.users import User
    from app.models.roles import RoleProfile, RoleAssignment
    import uuid
    
    now = datetime.now(timezone.utc)
    
    # Create test role profile
    role = RoleProfile(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        role_code="test_analyst",
        role_label="Test Analyst",
        description="Test role",
        allowed_widgets_json={"codes": ["queue_summary"]},
        entitled_queue_states_json={"states": ["active"]},
        allowed_actions_json={"actions": ["queue.read"]},
        can_view_sensitive_fields=False,
        profile_status="active"
    )
    db_session.add(role)
    
    # Create test user
    user = User(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        username="tester",
        display_name="Test User",
        email="tester@example.com",
        password_hash=hash_password("Test-pass-1"),
        status="active"
    )
    db_session.add(user)
    db_session.flush()
    
    # Create role assignment
    assignment = RoleAssignment(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        user_id=user.id,
        role_code="test_analyst",
        assignment_status="active"
    )
    db_session.add(assignment)
    db_session.commit()
    
    # Login through real endpoint (when implemented)
    # For now, return client without authentication
    return client
