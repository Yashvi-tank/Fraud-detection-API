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
