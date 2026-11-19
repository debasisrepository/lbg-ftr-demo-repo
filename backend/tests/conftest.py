# backend/tests/conftest.py - shared by every test file. Extend it; never add a second database setup.
import os
import tempfile
from pathlib import Path

# 1. Configuration BEFORE anything imports the app: the committed dev.env, then test overrides.
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

from app.database import Base, get_db
from app.main import app as fastapi_app
import app.models.auth  # noqa: F401
import app.models.sca  # noqa: F401
import app.models.profiles  # noqa: F401
import app.models.accounts  # noqa: F401
import app.models.payees  # noqa: F401
import app.models.payments  # noqa: F401
import app.models.audit  # noqa: F401
import app.models.telemetry  # noqa: F401

engine = create_engine(os.environ["DATABASE_URL"], connect_args={"check_same_thread": False})
TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture(autouse=True)
def _fresh_schema():
    Base.metadata.create_all(engine)
    # Load seed data for tests
    from app.seed import seed_database
    session = TestingSession()
    try:
        seed_database(session)
    finally:
        session.close()
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session() -> Session:
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    fastapi_app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def auth_client(client, db_session):
    """Logged in through the app's own login as admin@example.com from seed data."""
    # Use the real login endpoint with seed admin credentials
    response = client.post("/api/v1/auth/login", json={"username": "admin@example.com", "password": "admin123"})
    assert response.status_code == 200, response.text
    token = response.json().get("access_token")
    if token:
        client.headers["Authorization"] = f"Bearer {token}"
    
    return client
