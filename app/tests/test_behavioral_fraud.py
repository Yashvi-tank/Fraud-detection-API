"""Behavioral fraud engine unit tests."""

import pytest

from app.services.behavioral_fraud import (
    REASON_NEW_DEVICE,
    REASON_SPENDING_ANOMALY,
    REASON_UNUSUAL_COUNTRY,
    REASON_VELOCITY,
    BehavioralTransactionInput,
    evaluate_behavioral_rules,
)
from app.services.user_history_service import UserBehaviorContext


def _context(
    *,
    prior_transaction_count: int = 0,
    recent_short_window_count: int = 0,
    recent_long_window_count: int = 0,
    historical_countries: frozenset[str] | None = None,
    known_device_ids: frozenset[str] | None = None,
    average_amount: float | None = None,
) -> UserBehaviorContext:
    """Build a user behavior context for unit tests."""
    return UserBehaviorContext(
        user_id="user123",
        prior_transaction_count=prior_transaction_count,
        recent_short_window_count=recent_short_window_count,
        recent_long_window_count=recent_long_window_count,
        historical_countries=historical_countries or frozenset(),
        known_device_ids=known_device_ids or frozenset(),
        average_amount=average_amount,
    )


def _transaction(
    *,
    amount: float = 100.0,
    country: str = "France",
    device_id: str = "DEVICE_001",
) -> BehavioralTransactionInput:
    """Build a behavioral transaction input for unit tests."""
    return BehavioralTransactionInput(
        amount=amount,
        country=country,
        device_id=device_id,
    )


def test_velocity_detection_short_window() -> None:
    """Short-window velocity should trigger when prior count reaches threshold."""
    result = evaluate_behavioral_rules(
        _transaction(),
        _context(recent_short_window_count=3),
    )

    assert REASON_VELOCITY in result.reasons
    assert result.risk_score == 20


def test_velocity_detection_long_window() -> None:
    """Long-window velocity should trigger when prior count reaches threshold."""
    result = evaluate_behavioral_rules(
        _transaction(),
        _context(recent_long_window_count=5),
    )

    assert REASON_VELOCITY in result.reasons
    assert result.risk_score == 15


def test_velocity_detection_both_windows() -> None:
    """Both velocity windows can contribute to the total score."""
    result = evaluate_behavioral_rules(
        _transaction(),
        _context(recent_short_window_count=3, recent_long_window_count=5),
    )

    assert result.reasons.count(REASON_VELOCITY) == 1
    assert result.risk_score == 35


def test_velocity_not_triggered_below_threshold() -> None:
    """Velocity should not trigger below configured thresholds."""
    result = evaluate_behavioral_rules(
        _transaction(),
        _context(recent_short_window_count=2, recent_long_window_count=4),
    )

    assert result.reasons == []
    assert result.risk_score == 0


def test_unusual_country_detection() -> None:
    """Country change should trigger when country is absent from user history."""
    result = evaluate_behavioral_rules(
        _transaction(country="Brazil", device_id="DEVICE_A"),
        _context(
            prior_transaction_count=3,
            historical_countries=frozenset({"france"}),
            known_device_ids=frozenset({"DEVICE_A"}),
        ),
    )

    assert REASON_UNUSUAL_COUNTRY in result.reasons
    assert result.risk_score == 20


def test_unusual_country_not_triggered_for_known_country() -> None:
    """Known countries should not trigger country change detection."""
    result = evaluate_behavioral_rules(
        _transaction(country="France"),
        _context(
            prior_transaction_count=3,
            historical_countries=frozenset({"france"}),
        ),
    )

    assert REASON_UNUSUAL_COUNTRY not in result.reasons


def test_unusual_country_skipped_without_history() -> None:
    """Country change should not trigger when the user has no prior transactions."""
    result = evaluate_behavioral_rules(
        _transaction(country="Brazil"),
        _context(prior_transaction_count=0),
    )

    assert result.reasons == []


def test_new_device_detection() -> None:
    """New device should trigger when device has never been seen for the user."""
    result = evaluate_behavioral_rules(
        _transaction(device_id="DEVICE_NEW", country="France"),
        _context(
            prior_transaction_count=2,
            historical_countries=frozenset({"france"}),
            known_device_ids=frozenset({"DEVICE_A", "DEVICE_B"}),
        ),
    )

    assert REASON_NEW_DEVICE in result.reasons
    assert result.risk_score == 15


def test_new_device_not_triggered_for_known_device() -> None:
    """Known devices should not trigger new device detection."""
    result = evaluate_behavioral_rules(
        _transaction(device_id="DEVICE_A"),
        _context(
            prior_transaction_count=2,
            known_device_ids=frozenset({"DEVICE_A", "DEVICE_B"}),
        ),
    )

    assert REASON_NEW_DEVICE not in result.reasons


def test_new_device_skipped_without_history() -> None:
    """New device detection should not trigger for first-time users."""
    result = evaluate_behavioral_rules(
        _transaction(device_id="DEVICE_NEW"),
        _context(prior_transaction_count=0),
    )

    assert result.reasons == []


def test_spending_anomaly_detection() -> None:
    """Spending anomaly should trigger when amount exceeds historical average."""
    result = evaluate_behavioral_rules(
        _transaction(amount=2000.0, country="France", device_id="DEVICE_A"),
        _context(
            prior_transaction_count=3,
            historical_countries=frozenset({"france"}),
            known_device_ids=frozenset({"DEVICE_A"}),
            average_amount=40.0,
        ),
    )

    assert REASON_SPENDING_ANOMALY in result.reasons
    assert result.risk_score == 25


def test_spending_anomaly_not_triggered_with_insufficient_history() -> None:
    """Spending anomaly should require a minimum prior transaction count."""
    result = evaluate_behavioral_rules(
        _transaction(amount=2000.0),
        _context(
            prior_transaction_count=2,
            average_amount=40.0,
        ),
    )

    assert REASON_SPENDING_ANOMALY not in result.reasons


def test_spending_anomaly_not_triggered_within_threshold() -> None:
    """Amounts within the multiplier threshold should not trigger."""
    result = evaluate_behavioral_rules(
        _transaction(amount=100.0),
        _context(
            prior_transaction_count=3,
            average_amount=40.0,
        ),
    )

    assert REASON_SPENDING_ANOMALY not in result.reasons


def test_multiple_behavioral_rules_trigger_together() -> None:
    """Multiple behavioral rules should aggregate score and reasons."""
    result = evaluate_behavioral_rules(
        _transaction(amount=2000.0, country="Brazil", device_id="DEVICE_NEW"),
        _context(
            prior_transaction_count=3,
            recent_short_window_count=3,
            historical_countries=frozenset({"france"}),
            known_device_ids=frozenset({"DEVICE_A"}),
            average_amount=40.0,
        ),
    )

    assert result.reasons == [
        REASON_VELOCITY,
        REASON_UNUSUAL_COUNTRY,
        REASON_NEW_DEVICE,
        REASON_SPENDING_ANOMALY,
    ]
    assert result.risk_score == 80


def test_no_behavioral_rules_with_empty_history() -> None:
    """Users with no history should not trigger behavioral rules."""
    result = evaluate_behavioral_rules(
        _transaction(amount=2000.0, country="Brazil", device_id="DEVICE_NEW"),
        _context(prior_transaction_count=0),
    )

    assert result.risk_score == 0
    assert result.reasons == []
