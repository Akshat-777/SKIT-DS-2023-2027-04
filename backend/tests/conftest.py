import pytest
import jwt
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def valid_auth_headers():
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
