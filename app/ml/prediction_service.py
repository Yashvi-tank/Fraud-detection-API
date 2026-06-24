"""ML prediction service for fraud probability scoring.

Loads a trained scikit-learn model from disk and returns a fraud
probability for a given feature vector.  Degrades gracefully when no
model file is available (returns probability 0.0).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from app.core.config import settings
from app.ml.feature_engineering import FEATURE_NAMES, MLFeatureVector

logger = logging.getLogger("fraud_detection")

_DEFAULT_MODEL_VERSION = "none"


@dataclass(frozen=True)
class MLPredictionResult:
    """Output of the ML fraud prediction service."""

    fraud_probability: float
    model_version: str


class FraudMLPredictor:
    """Load a persisted model and produce fraud probability predictions.

    If the model file does not exist on disk the predictor enters
    *fallback mode* — ``predict()`` always returns probability ``0.0``
    and logs a warning on first use.
    """

    def __init__(self) -> None:
        self._model = None
        self._model_version: str = _DEFAULT_MODEL_VERSION
        self._feature_names: list[str] = FEATURE_NAMES
        self._fallback_warned = False

        self._load_model()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def predict(self, feature_vector: MLFeatureVector) -> MLPredictionResult:
        """Return the fraud probability for a single transaction.

        Parameters
        ----------
        feature_vector:
            An ``MLFeatureVector`` produced by the feature engineering
            module.

        Returns
        -------
        MLPredictionResult
            Contains ``fraud_probability`` in [0, 1] and ``model_version``.
        """
        if self._model is None:
            if not self._fallback_warned:
                logger.warning(
                    "ML model not loaded — returning default probability 0.0. "
                    "Train a model with `python -m app.ml.train_model`."
                )
                self._fallback_warned = True
            return MLPredictionResult(
                fraud_probability=0.0,
                model_version=_DEFAULT_MODEL_VERSION,
            )

        ordered_features = feature_vector.to_list()
        features_df = pd.DataFrame([ordered_features], columns=self._feature_names)

        # predict_proba returns [[p_class_0, p_class_1]]
        probabilities = self._model.predict_proba(features_df)
        fraud_prob = float(probabilities[0][1])

        return MLPredictionResult(
            fraud_probability=round(fraud_prob, 4),
            model_version=self._model_version,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_model(self) -> None:
        """Attempt to load the model and metadata from disk."""
        model_path = Path(settings.ML_MODEL_PATH)
        metadata_path = Path(settings.ML_MODEL_METADATA_PATH)

        if not model_path.exists():
            logger.info(
                "ML model file not found at %s — prediction disabled.",
                model_path,
            )
            return

        try:
            self._model = joblib.load(model_path)
            logger.info("ML model loaded from %s", model_path)
        except Exception:
            logger.exception("Failed to load ML model from %s", model_path)
            return

        if metadata_path.exists():
            try:
                with open(metadata_path, encoding="utf-8") as fh:
                    metadata = json.load(fh)
                self._model_version = metadata.get("model_version", _DEFAULT_MODEL_VERSION)
                self._feature_names = metadata.get("feature_names", FEATURE_NAMES)
                logger.info(
                    "ML model metadata loaded: version=%s", self._model_version
                )
            except Exception:
                logger.exception("Failed to read ML model metadata from %s", metadata_path)


# ---------------------------------------------------------------------------
# Module-level singleton — instantiated once when first imported.
# ---------------------------------------------------------------------------

_predictor: FraudMLPredictor | None = None


def get_predictor() -> FraudMLPredictor:
    """Return (or create) the module-level predictor singleton."""
    global _predictor  # noqa: PLW0603
    if _predictor is None:
        _predictor = FraudMLPredictor()
    return _predictor
