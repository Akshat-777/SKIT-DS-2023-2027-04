import pytest
import jwt
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone

from app.main import app
from app.core.config import settings
from app.db.database import Base, engine, SessionLocal
from app.db.repositories import UserRepository
from app.db.seed import seed_database

@pytest.fixture(scope="session", autouse=True)
def prepare_db():
    """Create all tables and seed once for the entire test session."""
    Base.metadata.create_all(bind=engine)
    seed_database()
    yield
    # Teardown: drop everything after the session
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def valid_auth_headers():
    """JWT for the legacy US1 conftest user (no exp – works with the existing auth_dep)."""
    payload = {
        "sub": "user_test_123",
        "email": "testuser@example.com",
        "name": "Test User",
        "role": "user"
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def invalid_auth_headers():
    return {"Authorization": "Bearer invalid.jwt.token"}
