"""Generate a synthetic fraud detection training dataset.

Run as a module::

    python -m app.ml.generate_dataset

Produces ``app/ml/data/fraud_dataset.csv`` with 5 000+ labelled samples.
"""

from __future__ import annotations

import csv
import os
import random
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUT_DIR = Path(__file__).resolve().parent / "data"
OUTPUT_FILE = OUTPUT_DIR / "fraud_dataset.csv"

SAMPLE_COUNT = 5_500  # Generate a comfortable margin above the 5 000 minimum.

COUNTRIES = [
    "France", "Germany", "Brazil", "USA", "UK",
    "Nigeria", "China", "India", "Russia", "Japan",
]

# Higher-weight countries appear more often in legitimate transactions.
LEGITIMATE_COUNTRY_WEIGHTS = [30, 15, 10, 10, 8, 3, 5, 7, 4, 8]

MERCHANTS = [
    "Amazon", "Walmart", "eBay", "Target", "Best Buy",
    "Apple Store", "Luxury Goods", "Crypto Exchange", "Wire Transfer",
    "Gambling Site", "Grocery", "Gas Station", "Restaurant",
    "Travel Agency", "Electronics Store",
]

HIGH_RISK_MERCHANTS = {"Crypto Exchange", "Wire Transfer", "Gambling Site", "Luxury Goods"}

FIELDNAMES = [
    "amount",
    "country",
    "device_new",
    "velocity_short",
    "velocity_long",
    "country_anomaly",
    "spending_anomaly",
    "merchant",
    "risk_score_rules",
    "fraud_label",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _generate_legitimate() -> dict:
    """Generate a single legitimate transaction row."""
    country = random.choices(COUNTRIES, weights=LEGITIMATE_COUNTRY_WEIGHTS, k=1)[0]
    merchant = random.choice(MERCHANTS)
    amount = round(random.uniform(5, 800), 2)
    device_new = 1 if random.random() < 0.08 else 0
    velocity_short = random.choices(range(5), weights=[60, 25, 10, 3, 2], k=1)[0]
    velocity_long = velocity_short + random.choices(range(5), weights=[50, 25, 15, 7, 3], k=1)[0]
    country_anomaly = 1 if random.random() < 0.05 else 0
    spending_anomaly = 1 if random.random() < 0.04 else 0

    # Simulate rule score
    risk_score = 0
    if amount > 1000:
        risk_score += 30
    if country != "France":
        risk_score += 25
    if device_new:
        risk_score += 20
    if velocity_short >= 3:
        risk_score += 20
    if velocity_long >= 5:
        risk_score += 15
    if country_anomaly:
        risk_score += 20
    if spending_anomaly:
        risk_score += 25

    return {
        "amount": amount,
        "country": country,
        "device_new": device_new,
        "velocity_short": velocity_short,
        "velocity_long": velocity_long,
        "country_anomaly": country_anomaly,
        "spending_anomaly": spending_anomaly,
        "merchant": merchant,
        "risk_score_rules": risk_score,
        "fraud_label": 0,
    }


def _generate_fraud() -> dict:
    """Generate a single fraudulent transaction row."""
    # Fraud transactions skew towards foreign, high-amount, new devices.
    country = random.choices(
        COUNTRIES,
        weights=[5, 8, 20, 10, 8, 20, 10, 8, 8, 3],
        k=1,
    )[0]
    merchant = random.choices(
        MERCHANTS,
        weights=[5, 3, 5, 3, 3, 3, 15, 20, 18, 15, 2, 2, 2, 2, 2],
        k=1,
    )[0]
    amount = round(random.uniform(300, 10_000), 2)
    device_new = 1 if random.random() < 0.55 else 0
    velocity_short = random.choices(range(9), weights=[10, 10, 15, 20, 15, 12, 8, 6, 4], k=1)[0]
    velocity_long = velocity_short + random.choices(range(8), weights=[10, 10, 15, 20, 15, 12, 10, 8], k=1)[0]
    country_anomaly = 1 if random.random() < 0.60 else 0
    spending_anomaly = 1 if random.random() < 0.55 else 0

    # Simulate rule score
    risk_score = 0
    if amount > 1000:
        risk_score += 30
    if country != "France":
        risk_score += 25
    if device_new:
        risk_score += 20
    if velocity_short >= 3:
        risk_score += 20
    if velocity_long >= 5:
        risk_score += 15
    if country_anomaly:
        risk_score += 20
    if spending_anomaly:
        risk_score += 25

    return {
        "amount": amount,
        "country": country,
        "device_new": device_new,
        "velocity_short": velocity_short,
        "velocity_long": velocity_long,
        "country_anomaly": country_anomaly,
        "spending_anomaly": spending_anomaly,
        "merchant": merchant,
        "risk_score_rules": risk_score,
        "fraud_label": 1,
    }


def generate_dataset(
    n_samples: int = SAMPLE_COUNT,
    fraud_ratio: float = 0.10,
) -> Path:
    """Write a CSV dataset to ``OUTPUT_FILE`` and return its path.

    Parameters
    ----------
    n_samples:
        Total number of rows to generate.
    fraud_ratio:
        Fraction of rows that are fraudulent (default 10 %).
    """
    n_fraud = int(n_samples * fraud_ratio)
    n_legit = n_samples - n_fraud

    rows: list[dict] = []
    for _ in range(n_legit):
        rows.append(_generate_legitimate())
    for _ in range(n_fraud):
        rows.append(_generate_fraud())

    random.shuffle(rows)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Dataset generated: {OUTPUT_FILE}")
    print(f"  Total samples : {len(rows)}")
    print(f"  Fraud samples : {n_fraud} ({fraud_ratio * 100:.0f}%)")
    print(f"  Legit samples : {n_legit} ({(1 - fraud_ratio) * 100:.0f}%)")

    return OUTPUT_FILE


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    generate_dataset()
