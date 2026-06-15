"""API integration tests."""

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


def test_health_check(client: TestClient) -> None:
    """Health endpoint should return healthy status."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_check_transaction(client: TestClient) -> None:
    """POST /transactions/check should evaluate, store, and return a result."""
    payload = {
        "user_id": "user123",
        "amount": 1500,
        "merchant": "Amazon",
        "country": "Brazil",
        "device_id": "NEW_DEVICE_001",
    }

    response = client.post("/transactions/check", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["risk_score"] == 75
    assert body["status"] == "SUSPICIOUS"
    assert body["reasons"] == [
        "High transaction amount",
        "Foreign transaction detected",
        "Unrecognized device",
    ]
    assert "transaction_id" in body


def test_list_and_get_transactions(client: TestClient) -> None:
    """Stored transactions should be retrievable via list and detail endpoints."""
    payload = {
        "user_id": "user456",
        "amount": 50,
        "merchant": "Local Shop",
        "country": "France",
        "device_id": "KNOWN_DEVICE_001",
    }
    create_response = client.post("/transactions/check", json=payload)
    transaction_id = create_response.json()["transaction_id"]

    list_response = client.get("/transactions")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    detail_response = client.get(f"/transactions/{transaction_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["user_id"] == "user456"


def test_get_transaction_not_found(client: TestClient) -> None:
    """Unknown transaction IDs should return 404."""
    response = client.get(
        "/transactions/00000000-0000-0000-0000-000000000001"
    )

    assert response.status_code == 404


def test_validation_rejects_invalid_amount(client: TestClient) -> None:
    """Amount must be greater than zero."""
    payload = {
        "user_id": "user123",
        "amount": 0,
        "merchant": "Amazon",
        "country": "France",
        "device_id": "DEVICE_001",
    }

    response = client.post("/transactions/check", json=payload)

    assert response.status_code == 422
