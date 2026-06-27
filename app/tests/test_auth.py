"""Authentication unit and integration tests."""

from collections.abc import Generator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.core.database import get_session
from app.main import app


@pytest.fixture(name="client")
def client_fixture() -> Generator[TestClient, None, None]:
    """Provide a test client backed by an in-memory SQLite database."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def get_test_session() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session

    with patch("app.main.init_db"), TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


def test_register_user(client: TestClient) -> None:
    """Registering a new user should hash the password and return user details."""
    response = client.post(
        "/auth/register",
        json={"username": "newuser", "password": "securepassword"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "newuser"
    assert "id" in body
    assert "hashed_password" not in body  # Sensitive details should not leak


def test_register_duplicate_username(client: TestClient) -> None:
    """Registering a duplicate username should return 400 Bad Request."""
    client.post(
        "/auth/register",
        json={"username": "duplicateuser", "password": "password123"},
    )
    response = client.post(
        "/auth/register",
        json={"username": "duplicateuser", "password": "password456"},
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login_successful(client: TestClient) -> None:
    """Logging in with correct credentials should return a signed JWT token."""
    client.post(
        "/auth/register",
        json={"username": "loginuser", "password": "password123"},
    )
    response = client.post(
        "/auth/login",
        json={"username": "loginuser", "password": "password123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_incorrect_credentials(client: TestClient) -> None:
    """Logging in with incorrect credentials should return 401 Unauthorized."""
    client.post(
        "/auth/register",
        json={"username": "wronguser", "password": "correctpassword"},
    )
    response = client.post(
        "/auth/login",
        json={"username": "wronguser", "password": "incorrectpassword"},
    )
    assert response.status_code == 401
    assert "incorrect username" in response.json()["detail"].lower()


def test_get_current_user_profile(client: TestClient) -> None:
    """Retrieving profile details should work when passing a valid token."""
    client.post(
        "/auth/register",
        json={"username": "profileuser", "password": "password123"},
    )
    login_response = client.post(
        "/auth/login",
        json={"username": "profileuser", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "profileuser"


def test_profile_unauthorized_access(client: TestClient) -> None:
    """Retrieving profile without authorization headers should return 401."""
    response = client.get("/auth/me")
    assert response.status_code == 401
