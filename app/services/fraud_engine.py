"""Rule-based fraud detection engine."""

from dataclasses import dataclass

# Risk thresholds for classification
SAFE_MAX_SCORE = 30
REVIEW_MAX_SCORE = 60

# Rule scoring constants
HIGH_AMOUNT_THRESHOLD = 1000
HIGH_AMOUNT_SCORE = 30
FOREIGN_COUNTRY_SCORE = 25
UNRECOGNIZED_DEVICE_SCORE = 20

# Expected domestic country for Rule 2
DOMESTIC_COUNTRY = "France"

# Status labels
STATUS_SAFE = "SAFE"
STATUS_REVIEW = "REVIEW"
STATUS_SUSPICIOUS = "SUSPICIOUS"


@dataclass(frozen=True)
class FraudEvaluationResult:
    """Output of the fraud rule engine."""

    risk_score: int
    status: str
    reasons: list[str]


def _classify_risk(risk_score: int) -> str:
    """Map a numeric risk score to a status label."""
    if risk_score <= SAFE_MAX_SCORE:
        return STATUS_SAFE
    if risk_score <= REVIEW_MAX_SCORE:
        return STATUS_REVIEW
    return STATUS_SUSPICIOUS


def evaluate_transaction(
    amount: float,
    country: str,
    device_id: str,
) -> FraudEvaluationResult:
    """
    Evaluate a transaction against configured fraud rules.

    Rules:
      1. Amount > 1000          -> +30  "High transaction amount"
      2. Country != France      -> +25  "Foreign transaction detected"
      3. device_id starts NEW   -> +20  "Unrecognized device"

    Classification:
      0-30   -> SAFE
      31-60  -> REVIEW
      61+    -> SUSPICIOUS
    """
    normalized_country = country.strip().casefold()
    normalized_domestic_country = DOMESTIC_COUNTRY.casefold()
    normalized_device_id = device_id.strip().upper()

    risk_score = 0
    reasons: list[str] = []

    if amount > HIGH_AMOUNT_THRESHOLD:
        risk_score += HIGH_AMOUNT_SCORE
        reasons.append("High transaction amount")

    if normalized_country != normalized_domestic_country:
        risk_score += FOREIGN_COUNTRY_SCORE
        reasons.append("Foreign transaction detected")

    if normalized_device_id.startswith("NEW"):
        risk_score += UNRECOGNIZED_DEVICE_SCORE
        reasons.append("Unrecognized device")

    status = _classify_risk(risk_score)

    return FraudEvaluationResult(
        risk_score=risk_score,
        status=status,
        reasons=reasons,
    )


def aggregate_fraud_evaluations(
    *evaluations: FraudEvaluationResult,
) -> FraudEvaluationResult:
    """Combine multiple fraud evaluation results into a single assessment."""
    total_score = sum(evaluation.risk_score for evaluation in evaluations)
    reasons: list[str] = []
    seen_reasons: set[str] = set()

    for evaluation in evaluations:
        for reason in evaluation.reasons:
            if reason not in seen_reasons:
                seen_reasons.add(reason)
                reasons.append(reason)

    return FraudEvaluationResult(
        risk_score=total_score,
        status=_classify_risk(total_score),
        reasons=reasons,
    )


def apply_ml_boost(
    evaluation: FraudEvaluationResult,
    ml_probability: float,
    ml_weight: int = 20,
) -> FraudEvaluationResult:
    """Add ML fraud probability contribution to the risk score.

    Formula::

        final_score = min(100, rule_score + round(ml_probability * ml_weight))

    The total risk score is **capped at 100**.

    Parameters
    ----------
    evaluation:
        The aggregated static + behavioral evaluation result.
    ml_probability:
        Fraud probability from the ML model (0.0 – 1.0).
    ml_weight:
        Maximum points the ML layer can contribute (default 20).
    """
    ml_score = round(ml_probability * ml_weight)
    new_score = min(100, evaluation.risk_score + ml_score)
    reasons = list(evaluation.reasons)

    if ml_probability >= 0.5:
        reasons.append(
            f"ML model flagged as suspicious (probability: {ml_probability:.2f})"
        )

    return FraudEvaluationResult(
        risk_score=new_score,
        status=_classify_risk(new_score),
        reasons=reasons,
    )
