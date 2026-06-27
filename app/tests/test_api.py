"""API integration tests."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

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

    from uuid import uuid4
    from app.core.security import get_current_user
    from app.models.user import User

    app.dependency_overrides[get_current_user] = lambda: User(
        id=uuid4(),
        username="test_user",
        hashed_password="",
    )

    from app.ml.prediction_service import MLPredictionResult
    mock_predictor = MagicMock()
    mock_predictor.predict.return_value = MLPredictionResult(
        fraud_probability=0.0,
        model_version="mock_v1",
    )

    with patch("app.main.init_db"), \
         patch("app.ml.prediction_service.get_predictor", return_value=mock_predictor), \
         TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


def _create_transaction(
    client: TestClient,
    *,
    user_id: str = "user123",
    amount: float = 1500,
    merchant: str = "Amazon",
    country: str = "Brazil",
    device_id: str = "NEW_DEVICE_001",
) -> dict:
    """Helper to create a transaction and return the response body."""
    payload = {
        "user_id": user_id,
        "amount": amount,
        "merchant": merchant,
        "country": country,
        "device_id": device_id,
    }
    response = client.post("/transactions/check", json=payload)
    assert response.status_code == 200
    return response.json()


def test_health_check(client: TestClient) -> None:
    """Health endpoint should return healthy status."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_check_transaction(client: TestClient) -> None:
    """POST /transactions/check should evaluate, store, and return a result."""
    body = _create_transaction(client)

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
    created = _create_transaction(
        client,
        user_id="user456",
        amount=50,
        merchant="Local Shop",
        country="France",
        device_id="KNOWN_DEVICE_001",
    )
    transaction_id = created["transaction_id"]

    list_response = client.get("/transactions")
    assert list_response.status_code == 200
    list_body = list_response.json()
    assert list_body["total"] == 1
    assert list_body["page"] == 1
    assert list_body["page_size"] == 10
    assert list_body["total_pages"] == 1
    assert len(list_body["items"]) == 1

    detail_response = client.get(f"/transactions/{transaction_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["user_id"] == "user456"


def test_get_transaction_by_id(client: TestClient) -> None:
    """GET /transactions/{id} should return the full transaction record."""
    created = _create_transaction(client)
    transaction_id = created["transaction_id"]

    response = client.get(f"/transactions/{transaction_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == transaction_id
    assert body["status"] == "SUSPICIOUS"
    assert body["risk_score"] == 75


def test_list_transactions_pagination(client: TestClient) -> None:
    """Pagination should limit results and expose page metadata."""
    for index in range(3):
        _create_transaction(
            client,
            user_id=f"user{index}",
            amount=100 + index,
            merchant=f"Shop{index}",
            country="France",
            device_id=f"DEVICE_{index}",
        )

    response = client.get("/transactions?page=1&page_size=2")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert body["total_pages"] == 2
    assert len(body["items"]) == 2

    page_two = client.get("/transactions?page=2&page_size=2")
    assert page_two.status_code == 200
    assert len(page_two.json()["items"]) == 1


def test_list_transactions_filter_by_status(client: TestClient) -> None:
    """Status filter should return only matching transactions."""
    _create_transaction(client, country="France", device_id="DEVICE_A")
    _create_transaction(client, country="Brazil", device_id="NEW_DEVICE")

    response = client.get("/transactions?status=SUSPICIOUS")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert all(item["status"] == "SUSPICIOUS" for item in body["items"])


def test_list_transactions_filter_by_user_id(client: TestClient) -> None:
    """User ID filter should return only matching transactions."""
    _create_transaction(client, user_id="alice")
    _create_transaction(client, user_id="bob")

    response = client.get("/transactions?user_id=alice")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["user_id"] == "alice"


def test_list_transactions_invalid_page_size(client: TestClient) -> None:
    """Page size above the maximum should be rejected."""
    response = client.get("/transactions?page_size=101")

    assert response.status_code == 422


def test_get_transaction_not_found(client: TestClient) -> None:
    """Unknown transaction IDs should return 404."""
    response = client.get(
        "/transactions/00000000-0000-0000-0000-000000000001"
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


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


def test_behavioral_velocity_detection(client: TestClient) -> None:
    """Fourth transaction within the short window should trigger velocity detection."""
    for _ in range(3):
        _create_transaction(
            client,
            user_id="velocity_user",
            amount=10,
            merchant="Coffee Shop",
            country="France",
            device_id="DEVICE_A",
        )

    response = client.post(
        "/transactions/check",
        json={
            "user_id": "velocity_user",
            "amount": 10,
            "merchant": "Coffee Shop",
            "country": "France",
            "device_id": "DEVICE_A",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "High transaction velocity detected" in body["reasons"]
    assert body["risk_score"] >= 20


def test_behavioral_unusual_country_detection(client: TestClient) -> None:
    """Country change should trigger when the user history is from another country."""
    for _ in range(3):
        _create_transaction(
            client,
            user_id="country_user",
            amount=50,
            merchant="Local Shop",
            country="France",
            device_id="DEVICE_A",
        )

    response = client.post(
        "/transactions/check",
        json={
            "user_id": "country_user",
            "amount": 50,
            "merchant": "Foreign Shop",
            "country": "Brazil",
            "device_id": "DEVICE_A",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "Transaction originated from unusual country" in body["reasons"]
    assert "Foreign transaction detected" in body["reasons"]


def test_behavioral_new_device_detection(client: TestClient) -> None:
    """Unknown device should trigger when device is absent from user history."""
    _create_transaction(
        client,
        user_id="device_user",
        amount=50,
        merchant="Local Shop",
        country="France",
        device_id="DEVICE_A",
    )
    _create_transaction(
        client,
        user_id="device_user",
        amount=50,
        merchant="Local Shop",
        country="France",
        device_id="DEVICE_A",
    )

    response = client.post(
        "/transactions/check",
        json={
            "user_id": "device_user",
            "amount": 50,
            "merchant": "Local Shop",
            "country": "France",
            "device_id": "DEVICE_B",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "New device detected" in body["reasons"]
    assert "Unrecognized device" not in body["reasons"]


def test_behavioral_spending_anomaly_detection(client: TestClient) -> None:
    """Large amount relative to user history should trigger spending anomaly."""
    for _ in range(3):
        _create_transaction(
            client,
            user_id="spending_user",
            amount=40,
            merchant="Grocery",
            country="France",
            device_id="DEVICE_A",
        )

    response = client.post(
        "/transactions/check",
        json={
            "user_id": "spending_user",
            "amount": 2000,
            "merchant": "Luxury Store",
            "country": "France",
            "device_id": "DEVICE_A",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "Transaction amount significantly exceeds user history" in body["reasons"]
    assert "High transaction amount" in body["reasons"]


def test_behavioral_multiple_rules_together(client: TestClient) -> None:
    """Multiple static and behavioral rules should aggregate in one response."""
    for _ in range(3):
        _create_transaction(
            client,
            user_id="combo_user",
            amount=40,
            merchant="Grocery",
            country="France",
            device_id="DEVICE_A",
        )

    response = client.post(
        "/transactions/check",
        json={
            "user_id": "combo_user",
            "amount": 2000,
            "merchant": "Foreign Luxury",
            "country": "Brazil",
            "device_id": "DEVICE_NEW",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "SUSPICIOUS"
    assert body["reasons"] == [
        "High transaction amount",
        "Foreign transaction detected",
        "High transaction velocity detected",
        "Transaction originated from unusual country",
        "New device detected",
        "Transaction amount significantly exceeds user history",
    ]
    assert body["risk_score"] == 100


def test_behavioral_rules_skipped_without_history(client: TestClient) -> None:
    """First transaction for a user should only apply static fraud rules."""
    response = client.post(
        "/transactions/check",
        json={
            "user_id": "first_time_user",
            "amount": 1500,
            "merchant": "Amazon",
            "country": "Brazil",
            "device_id": "NEW_DEVICE_001",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["risk_score"] == 75
    assert body["reasons"] == [
        "High transaction amount",
        "Foreign transaction detected",
        "Unrecognized device",
    ]


def test_check_transaction_includes_ml_fields(client: TestClient) -> None:
    """The response and database record should include ML-related fields when prediction is mock-enabled."""
    from app.ml.prediction_service import MLPredictionResult
    mock_predictor = MagicMock()
    mock_predictor.predict.return_value = MLPredictionResult(
        fraud_probability=0.85,
        model_version="test_model_v1"
    )

    with patch("app.ml.prediction_service.get_predictor", return_value=mock_predictor):
        response = client.post(
            "/transactions/check",
            json={
                "user_id": "ml_test_user",
                "amount": 100,
                "merchant": "Amazon",
                "country": "France",
                "device_id": "DEVICE_A",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["fraud_probability"] == 0.85
        assert body["model_version"] == "test_model_v1"
        # base score: amount <= 1000 (0), country == France (0), device not start NEW (0) -> 0
        # ml boost: round(0.85 * 20) = 17
        assert body["risk_score"] == 17
        assert "ML model flagged as suspicious (probability: 0.85)" in body["reasons"]
