import os
import tempfile
from pathlib import Path

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
import app.auth.models
import app.services.case.models
import app.services.orchestrator.models
import app.services.policy.models
import app.events.models
import app.services.notification.models
import app.services.audit.models

engine = create_engine(os.environ["DATABASE_URL"], connect_args={"check_same_thread": False})
TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture(autouse=True)
def _fresh_schema():
    Base.metadata.create_all(engine)
    # Seed required data
    session = TestingSession()
    try:
        from app.seed import seed_agent_registry, seed_action_control
        seed_agent_registry(session)
        seed_action_control(session)
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
    from app.auth.models import AppUser
    from app.auth.passwords import PasswordHasher

    db_session.add(AppUser(
        email="tester@example.com",
        hashed_password=PasswordHasher.hash_password("Test-pass-1"),
        is_active=True,
        is_colleague=False,
        customer_reference="CUST-TEST",
        brand="lloyds",
    ))
    db_session.commit()
    response = client.post("/api/v1/auth/login", json={"email": "tester@example.com", "password": "Test-pass-1"})
    assert response.status_code == 200, response.text
    token = response.json().get("access_token")
    if token:
        client.headers["Authorization"] = f"Bearer {token}"
    return client
