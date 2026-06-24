"""Train and evaluate fraud detection ML models.

Run as a module::

    python -m app.ml.train_model

Uses **Random Forest** as the primary model.  Logistic Regression is
trained as an optional comparison and its metrics are printed, but the
Random Forest is the model that gets persisted to disk.

Outputs:
  - ``app/ml/models/fraud_model.joblib``   — serialised Random Forest
  - ``app/ml/models/model_metadata.json``  — version, metrics, feature list
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from app.ml.feature_engineering import COUNTRY_LABELS, MERCHANT_LABELS, FEATURE_NAMES

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DATA_FILE = Path(__file__).resolve().parent / "data" / "fraud_dataset.csv"
MODELS_DIR = Path(__file__).resolve().parent / "models"
MODEL_FILE = MODELS_DIR / "fraud_model.joblib"
METADATA_FILE = MODELS_DIR / "model_metadata.json"

MODEL_VERSION = "v1"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _encode_country(value: str) -> int:
    return COUNTRY_LABELS.get(value.strip().casefold(), 0)


def _encode_merchant(value: str) -> int:
    return MERCHANT_LABELS.get(value.strip().casefold(), 0)


def _evaluate(name: str, y_true, y_pred) -> dict:
    """Compute and print classification metrics."""
    metrics = {
        "accuracy": round(accuracy_score(y_true, y_pred), 4),
        "precision": round(precision_score(y_true, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_true, y_pred, zero_division=0), 4),
        "f1_score": round(f1_score(y_true, y_pred, zero_division=0), 4),
    }
    print(f"\n{'=' * 50}")
    print(f"  {name}")
    print(f"{'=' * 50}")
    for metric_name, value in metrics.items():
        print(f"  {metric_name:<12}: {value:.4f}")
    return metrics


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def train() -> None:
    """Run the full training pipeline."""
    # ---- Load data --------------------------------------------------------
    if not DATA_FILE.exists():
        print(f"Dataset not found at {DATA_FILE}")
        print("Run `python -m app.ml.generate_dataset` first.")
        return

    df = pd.read_csv(DATA_FILE)
    print(f"\nDataset loaded: {len(df)} rows from {DATA_FILE}")

    # ---- Feature encoding -------------------------------------------------
    df["country_encoded"] = df["country"].apply(_encode_country)
    df["merchant_encoded"] = df["merchant"].apply(_encode_merchant)

    feature_columns = FEATURE_NAMES
    X = df[feature_columns]
    y = df["fraud_label"]

    # ---- Train / test split -----------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y,
    )
    print(f"Train set: {len(X_train)} | Test set: {len(X_test)}")

    # ---- Random Forest (primary) ------------------------------------------
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=12,
        random_state=42,
        n_jobs=-1,
    )
    rf.fit(X_train, y_train)
    rf_preds = rf.predict(X_test)
    rf_metrics = _evaluate("Random Forest (PRIMARY)", y_test, rf_preds)

    # ---- Logistic Regression (comparison) ---------------------------------
    lr = LogisticRegression(max_iter=1000, random_state=42)
    lr.fit(X_train, y_train)
    lr_preds = lr.predict(X_test)
    lr_metrics = _evaluate("Logistic Regression (comparison)", y_test, lr_preds)

    # ---- Persist primary model (Random Forest) ----------------------------
    os.makedirs(MODELS_DIR, exist_ok=True)

    joblib.dump(rf, MODEL_FILE)
    print(f"\nModel saved to {MODEL_FILE}")

    metadata = {
        "model_version": MODEL_VERSION,
        "model_type": "RandomForestClassifier",
        "feature_names": feature_columns,
        "n_estimators": 100,
        "max_depth": 12,
        "dataset_size": len(df),
        "train_size": len(X_train),
        "test_size": len(X_test),
        "metrics": {
            "random_forest": rf_metrics,
            "logistic_regression": lr_metrics,
        },
    }
    with open(METADATA_FILE, "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)
    print(f"Metadata saved to {METADATA_FILE}")

    # ---- Summary ----------------------------------------------------------
    print(f"\n{'=' * 50}")
    print("  SUMMARY")
    print(f"{'=' * 50}")
    print(f"  Primary model     : Random Forest")
    print(f"  Model version     : {MODEL_VERSION}")
    print(f"  Best F1 (RF)      : {rf_metrics['f1_score']:.4f}")
    print(f"  Comparison F1 (LR): {lr_metrics['f1_score']:.4f}")
    print(f"  Model file        : {MODEL_FILE}")
    print()


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    train()
