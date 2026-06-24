"""User history service integration tests."""

from collections.abc import Generator

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.models.transaction import Transaction
from app.services.user_history_service import UserHistoryService


@pytest.fixture(name="session")
def session_fixture() -> Generator[Session, None, None]:
    """Provide an in-memory SQLite session for history service tests."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


def _add_transaction(
    session: Session,
    *,
    user_id: str = "user123",
    amount: float = 40.0,
    country: str = "France",
    device_id: str = "DEVICE_A",
) -> Transaction:
    """Persist a transaction record for history service tests."""
    transaction = Transaction(
        user_id=user_id,
        amount=amount,
        merchant="Test Shop",
        country=country,
        device_id=device_id,
        risk_score=0,
        status="SAFE",
        reasons=[],
    )
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return transaction


def test_build_context_with_no_history(session: Session) -> None:
    """Context for a new user should contain empty behavioral signals."""
    service = UserHistoryService(session)
    context = service.build_context("new_user")

    assert context.prior_transaction_count == 0
    assert context.recent_short_window_count == 0
    assert context.recent_long_window_count == 0
    assert context.historical_countries == frozenset()
    assert context.known_device_ids == frozenset()
    assert context.average_amount is None


def test_build_context_aggregates_history(session: Session) -> None:
    """Context should aggregate countries, devices, and average amount."""
    _add_transaction(session, amount=40.0, country="France", device_id="DEVICE_A")
    _add_transaction(session, amount=60.0, country="France", device_id="DEVICE_B")
    _add_transaction(session, amount=80.0, country="Germany", device_id="DEVICE_A")

    service = UserHistoryService(session)
    context = service.build_context("user123")

    assert context.prior_transaction_count == 3
    assert context.historical_countries == frozenset({"france", "germany"})
    assert context.known_device_ids == frozenset({"DEVICE_A", "DEVICE_B"})
    assert context.average_amount == pytest.approx(60.0)


def test_build_context_counts_recent_transactions(session: Session) -> None:
    """Recent transaction counts should include all transactions in the window."""
    for _ in range(3):
        _add_transaction(session)

    service = UserHistoryService(session)
    context = service.build_context("user123")

    assert context.recent_short_window_count == 3
    assert context.recent_long_window_count == 3
