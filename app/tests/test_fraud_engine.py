"""Fraud engine unit tests."""

import pytest

from app.services.fraud_engine import (
    STATUS_REVIEW,
    STATUS_SAFE,
    STATUS_SUSPICIOUS,
    evaluate_transaction,
)


@pytest.mark.parametrize(
    ("amount", "country", "device_id", "expected_score", "expected_status", "expected_reasons"),
    [
        (
            100.0,
            "France",
            "KNOWN_DEVICE_001",
            0,
            STATUS_SAFE,
            [],
        ),
        (
            1500.0,
            "France",
            "KNOWN_DEVICE_001",
            30,
            STATUS_SAFE,
            ["High transaction amount"],
        ),
        (
            500.0,
            "Brazil",
            "KNOWN_DEVICE_001",
            25,
            STATUS_SAFE,
            ["Foreign transaction detected"],
        ),
        (
            500.0,
            "France",
            "NEW_DEVICE_001",
            20,
            STATUS_SAFE,
            ["Unrecognized device"],
        ),
        (
            1500.0,
            "Brazil",
            "KNOWN_DEVICE_001",
            55,
            STATUS_REVIEW,
            [
                "High transaction amount",
                "Foreign transaction detected",
            ],
        ),
        (
            1500.0,
            "Brazil",
            "NEW_DEVICE_001",
            75,
            STATUS_SUSPICIOUS,
            [
                "High transaction amount",
                "Foreign transaction detected",
                "Unrecognized device",
            ],
        ),
        (
            500.0,
            "france",
            "new_device_001",
            20,
            STATUS_SAFE,
            ["Unrecognized device"],
        ),
    ],
)
def test_evaluate_transaction(
    amount: float,
    country: str,
    device_id: str,
    expected_score: int,
    expected_status: str,
    expected_reasons: list[str],
) -> None:
    """Verify fraud rules and risk classification."""
    result = evaluate_transaction(amount=amount, country=country, device_id=device_id)

    assert result.risk_score == expected_score
    assert result.status == expected_status
    assert result.reasons == expected_reasons


def test_aggregate_fraud_evaluations_combines_scores_and_reasons() -> None:
    """Aggregated evaluations should sum scores and preserve reason order."""
    from app.services.fraud_engine import FraudEvaluationResult, aggregate_fraud_evaluations

    static = FraudEvaluationResult(
        risk_score=30,
        status="SAFE",
        reasons=["High transaction amount"],
    )
    behavioral = FraudEvaluationResult(
        risk_score=35,
        status="",
        reasons=["High transaction velocity detected", "New device detected"],
    )

    result = aggregate_fraud_evaluations(static, behavioral)

    assert result.risk_score == 65
    assert result.status == "SUSPICIOUS"
    assert result.reasons == [
        "High transaction amount",
        "High transaction velocity detected",
        "New device detected",
    ]


def test_aggregate_fraud_evaluations_deduplicates_reasons() -> None:
    """Duplicate reasons should not appear twice in the aggregated result."""
    from app.services.fraud_engine import FraudEvaluationResult, aggregate_fraud_evaluations

    first = FraudEvaluationResult(
        risk_score=10,
        status="SAFE",
        reasons=["Duplicate reason"],
    )
    second = FraudEvaluationResult(
        risk_score=10,
        status="SAFE",
        reasons=["Duplicate reason", "Unique reason"],
    )

    result = aggregate_fraud_evaluations(first, second)

    assert result.reasons == ["Duplicate reason", "Unique reason"]
