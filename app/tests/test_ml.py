"""ML layer unit tests — feature extraction, prediction, and hybrid scoring."""

from unittest.mock import MagicMock, patch

import pytest

from app.ml.feature_engineering import (
    COUNTRY_LABELS,
    FEATURE_NAMES,
    MERCHANT_LABELS,
    MLFeatureVector,
    extract_features,
)
from app.ml.prediction_service import (
    FraudMLPredictor,
    MLPredictionResult,
)
from app.services.fraud_engine import (
    FraudEvaluationResult,
    apply_ml_boost,
)


# -----------------------------------------------------------------------
# Feature engineering tests
# -----------------------------------------------------------------------


class TestFeatureExtraction:
    """Verify that feature vectors are built correctly."""

    def test_basic_extraction(self) -> None:
        """Standard transaction should produce correctly encoded features."""
        result = extract_features(
            amount=1500.0,
            country="Brazil",
            device_id="NEW_DEVICE_001",
            merchant="Amazon",
            velocity_short=3,
            velocity_long=5,
            country_anomaly=True,
            spending_anomaly=False,
            rule_score=55,
        )

        assert isinstance(result, MLFeatureVector)
        assert result.features["amount"] == 1500.0
        assert result.features["country_encoded"] == float(COUNTRY_LABELS["brazil"])
        assert result.features["device_new"] == 1.0
        assert result.features["velocity_short"] == 3.0
        assert result.features["velocity_long"] == 5.0
        assert result.features["country_anomaly"] == 1.0
        assert result.features["spending_anomaly"] == 0.0
        assert result.features["merchant_encoded"] == float(MERCHANT_LABELS["amazon"])
        assert result.features["risk_score_rules"] == 55.0

    def test_unknown_country_encodes_to_zero(self) -> None:
        """Countries not in the label map should encode to 0."""
        result = extract_features(
            amount=100.0,
            country="Narnia",
            device_id="DEVICE_A",
            merchant="Amazon",
            velocity_short=0,
            velocity_long=0,
            country_anomaly=False,
            spending_anomaly=False,
            rule_score=0,
        )

        assert result.features["country_encoded"] == 0.0

    def test_unknown_merchant_encodes_to_zero(self) -> None:
        """Merchants not in the label map should encode to 0."""
        result = extract_features(
            amount=100.0,
            country="France",
            device_id="DEVICE_A",
            merchant="Unknown Shop XYZ",
            velocity_short=0,
            velocity_long=0,
            country_anomaly=False,
            spending_anomaly=False,
            rule_score=0,
        )

        assert result.features["merchant_encoded"] == 0.0

    def test_device_not_new(self) -> None:
        """Devices without the NEW prefix should set device_new to 0."""
        result = extract_features(
            amount=100.0,
            country="France",
            device_id="KNOWN_DEVICE_001",
            merchant="Amazon",
            velocity_short=0,
            velocity_long=0,
            country_anomaly=False,
            spending_anomaly=False,
            rule_score=0,
        )

        assert result.features["device_new"] == 0.0

    def test_no_history_features(self) -> None:
        """First-time user with no behavioral signals."""
        result = extract_features(
            amount=50.0,
            country="France",
            device_id="DEVICE_001",
            merchant="Grocery",
            velocity_short=0,
            velocity_long=0,
            country_anomaly=False,
            spending_anomaly=False,
            rule_score=0,
        )

        assert result.features["velocity_short"] == 0.0
        assert result.features["velocity_long"] == 0.0
        assert result.features["country_anomaly"] == 0.0
        assert result.features["spending_anomaly"] == 0.0
        assert result.features["risk_score_rules"] == 0.0

    def test_to_list_preserves_order(self) -> None:
        """to_list() must return values in FEATURE_NAMES order."""
        result = extract_features(
            amount=200.0,
            country="Germany",
            device_id="NEW_DEV",
            merchant="eBay",
            velocity_short=2,
            velocity_long=4,
            country_anomaly=True,
            spending_anomaly=True,
            rule_score=70,
        )

        ordered = result.to_list()
        assert len(ordered) == len(FEATURE_NAMES)
        for i, name in enumerate(FEATURE_NAMES):
            assert ordered[i] == result.features[name]


# -----------------------------------------------------------------------
# Prediction service tests
# -----------------------------------------------------------------------


class TestPredictionService:
    """Verify the ML prediction service."""

    def test_prediction_with_mock_model(self) -> None:
        """Predictor with a loaded model should return a valid probability."""
        import numpy as np

        mock_model = MagicMock()
        mock_model.predict_proba.return_value = np.array([[0.16, 0.84]])

        predictor = FraudMLPredictor.__new__(FraudMLPredictor)
        predictor._model = mock_model
        predictor._model_version = "v1"
        predictor._feature_names = FEATURE_NAMES
        predictor._fallback_warned = False

        feature_vector = extract_features(
            amount=1500.0,
            country="Brazil",
            device_id="NEW_DEVICE",
            merchant="Crypto Exchange",
            velocity_short=4,
            velocity_long=7,
            country_anomaly=True,
            spending_anomaly=True,
            rule_score=90,
        )

        result = predictor.predict(feature_vector)

        assert isinstance(result, MLPredictionResult)
        assert result.fraud_probability == 0.84
        assert result.model_version == "v1"
        mock_model.predict_proba.assert_called_once()

    def test_prediction_without_model_returns_zero(self) -> None:
        """Predictor without a model should return probability 0.0."""
        predictor = FraudMLPredictor.__new__(FraudMLPredictor)
        predictor._model = None
        predictor._model_version = "none"
        predictor._feature_names = FEATURE_NAMES
        predictor._fallback_warned = False

        feature_vector = extract_features(
            amount=100.0,
            country="France",
            device_id="DEVICE_A",
            merchant="Grocery",
            velocity_short=0,
            velocity_long=0,
            country_anomaly=False,
            spending_anomaly=False,
            rule_score=0,
        )

        result = predictor.predict(feature_vector)

        assert result.fraud_probability == 0.0
        assert result.model_version == "none"

    def test_ml_prediction_result_fields(self) -> None:
        """MLPredictionResult dataclass should expose correct fields."""
        result = MLPredictionResult(fraud_probability=0.72, model_version="v2")

        assert result.fraud_probability == 0.72
        assert result.model_version == "v2"


# -----------------------------------------------------------------------
# Hybrid scoring tests
# -----------------------------------------------------------------------


class TestHybridScoring:
    """Verify the apply_ml_boost function."""

    def test_basic_boost(self) -> None:
        """ML probability should add proportional points to the score."""
        evaluation = FraudEvaluationResult(
            risk_score=55,
            status="REVIEW",
            reasons=["High transaction amount", "Foreign transaction detected"],
        )

        result = apply_ml_boost(evaluation, ml_probability=0.80, ml_weight=20)

        # 55 + round(0.80 * 20) = 55 + 16 = 71
        assert result.risk_score == 71
        assert result.status == "SUSPICIOUS"
        assert "ML model flagged as suspicious (probability: 0.80)" in result.reasons

    def test_low_probability_no_reason(self) -> None:
        """ML probability below 0.5 should not add an ML reason."""
        evaluation = FraudEvaluationResult(
            risk_score=25,
            status="SAFE",
            reasons=["Foreign transaction detected"],
        )

        result = apply_ml_boost(evaluation, ml_probability=0.20, ml_weight=20)

        # 25 + round(0.20 * 20) = 25 + 4 = 29
        assert result.risk_score == 29
        assert result.status == "SAFE"
        assert not any("ML model" in r for r in result.reasons)

    def test_high_probability_adds_reason(self) -> None:
        """ML probability at or above 0.5 should add the ML reason."""
        evaluation = FraudEvaluationResult(
            risk_score=30,
            status="SAFE",
            reasons=["High transaction amount"],
        )

        result = apply_ml_boost(evaluation, ml_probability=0.50, ml_weight=20)

        # 30 + round(0.50 * 20) = 30 + 10 = 40
        assert result.risk_score == 40
        assert result.status == "REVIEW"
        assert "ML model flagged as suspicious (probability: 0.50)" in result.reasons

    def test_score_capped_at_100(self) -> None:
        """Final score must never exceed 100."""
        evaluation = FraudEvaluationResult(
            risk_score=95,
            status="SUSPICIOUS",
            reasons=["Multiple rules triggered"],
        )

        result = apply_ml_boost(evaluation, ml_probability=0.90, ml_weight=20)

        # 95 + round(0.90 * 20) = 95 + 18 = 113 → capped at 100
        assert result.risk_score == 100
        assert result.status == "SUSPICIOUS"

    def test_zero_probability_no_change(self) -> None:
        """ML probability of 0.0 should not alter the score."""
        evaluation = FraudEvaluationResult(
            risk_score=50,
            status="REVIEW",
            reasons=["Some reason"],
        )

        result = apply_ml_boost(evaluation, ml_probability=0.0, ml_weight=20)

        assert result.risk_score == 50
        assert result.status == "REVIEW"
        assert result.reasons == ["Some reason"]

    def test_preserves_original_reasons(self) -> None:
        """Original reasons should be preserved in the boosted result."""
        original_reasons = [
            "High transaction amount",
            "Foreign transaction detected",
            "High transaction velocity detected",
        ]
        evaluation = FraudEvaluationResult(
            risk_score=75,
            status="SUSPICIOUS",
            reasons=original_reasons,
        )

        result = apply_ml_boost(evaluation, ml_probability=0.70, ml_weight=20)

        for reason in original_reasons:
            assert reason in result.reasons
