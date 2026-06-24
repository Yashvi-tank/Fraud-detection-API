"""Reusable feature extraction for the ML fraud model.

Converts raw transaction data and user behavioral context into a numeric
feature vector suitable for scikit-learn models.  This module has **no**
dependency on FastAPI, SQLAlchemy, or any web-layer code.
"""

from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Country and merchant label maps — must match the training dataset encoding.
# New/unknown values map to 0 (the "other" bucket).
# ---------------------------------------------------------------------------

COUNTRY_LABELS: dict[str, int] = {
    "france": 1,
    "germany": 2,
    "brazil": 3,
    "usa": 4,
    "uk": 5,
    "nigeria": 6,
    "china": 7,
    "india": 8,
    "russia": 9,
    "japan": 10,
}

MERCHANT_LABELS: dict[str, int] = {
    "amazon": 1,
    "walmart": 2,
    "ebay": 3,
    "target": 4,
    "best buy": 5,
    "apple store": 6,
    "luxury goods": 7,
    "crypto exchange": 8,
    "wire transfer": 9,
    "gambling site": 10,
    "grocery": 11,
    "gas station": 12,
    "restaurant": 13,
    "travel agency": 14,
    "electronics store": 15,
}

# Feature names expected by the trained model (order matters).
FEATURE_NAMES: list[str] = [
    "amount",
    "country_encoded",
    "device_new",
    "velocity_short",
    "velocity_long",
    "country_anomaly",
    "spending_anomaly",
    "merchant_encoded",
    "risk_score_rules",
]


@dataclass(frozen=True)
class MLFeatureVector:
    """Typed container for a single ML feature vector."""

    features: dict[str, float]

    def to_list(self) -> list[float]:
        """Return features as an ordered list matching ``FEATURE_NAMES``."""
        return [self.features[name] for name in FEATURE_NAMES]


def extract_features(
    *,
    amount: float,
    country: str,
    device_id: str,
    merchant: str,
    velocity_short: int,
    velocity_long: int,
    country_anomaly: bool,
    spending_anomaly: bool,
    rule_score: int,
) -> MLFeatureVector:
    """Build an ML feature vector from transaction and behavioral signals.

    Parameters
    ----------
    amount:
        Transaction amount.
    country:
        Transaction country (will be label-encoded).
    device_id:
        Raw device identifier — ``device_new`` is derived from this.
    merchant:
        Merchant name (will be label-encoded).
    velocity_short:
        Number of transactions in the short velocity window.
    velocity_long:
        Number of transactions in the long velocity window.
    country_anomaly:
        Whether the country is absent from user history.
    spending_anomaly:
        Whether the amount exceeds the user's historical average.
    rule_score:
        Combined static + behavioral rule score (before ML boost).
    """
    normalized_country = country.strip().casefold()
    normalized_merchant = merchant.strip().casefold()
    normalized_device = device_id.strip().upper()

    features: dict[str, float] = {
        "amount": float(amount),
        "country_encoded": float(COUNTRY_LABELS.get(normalized_country, 0)),
        "device_new": 1.0 if normalized_device.startswith("NEW") else 0.0,
        "velocity_short": float(velocity_short),
        "velocity_long": float(velocity_long),
        "country_anomaly": 1.0 if country_anomaly else 0.0,
        "spending_anomaly": 1.0 if spending_anomaly else 0.0,
        "merchant_encoded": float(MERCHANT_LABELS.get(normalized_merchant, 0)),
        "risk_score_rules": float(rule_score),
    }

    return MLFeatureVector(features=features)
