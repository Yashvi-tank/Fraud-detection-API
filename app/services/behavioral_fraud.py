"""Behavioral fraud detection rules based on user transaction history."""

from dataclasses import dataclass

from app.core.config import settings
from app.services.fraud_engine import FraudEvaluationResult
from app.services.user_history_service import UserBehaviorContext, normalize_country

REASON_VELOCITY = "High transaction velocity detected"
REASON_UNUSUAL_COUNTRY = "Transaction originated from unusual country"
REASON_NEW_DEVICE = "New device detected"
REASON_SPENDING_ANOMALY = "Transaction amount significantly exceeds user history"


@dataclass(frozen=True)
class BehavioralTransactionInput:
    """Transaction fields required for behavioral fraud evaluation."""

    amount: float
    country: str
    device_id: str


def evaluate_behavioral_rules(
    transaction: BehavioralTransactionInput,
    context: UserBehaviorContext,
) -> FraudEvaluationResult:
    """
    Evaluate behavioral fraud rules using PostgreSQL transaction history.

    Rules:
      1. Velocity burst in short/long windows
      2. Country change vs historical user countries
      3. Device never seen before for this user
      4. Amount significantly above user spending average
    """
    risk_score = 0
    reasons: list[str] = []

    velocity_score = _evaluate_velocity(context)
    if velocity_score > 0:
        risk_score += velocity_score
        reasons.append(REASON_VELOCITY)

    country_score = _evaluate_country_change(transaction.country, context)
    if country_score > 0:
        risk_score += country_score
        reasons.append(REASON_UNUSUAL_COUNTRY)

    device_score = _evaluate_new_device(transaction.device_id, context)
    if device_score > 0:
        risk_score += device_score
        reasons.append(REASON_NEW_DEVICE)

    spending_score = _evaluate_spending_anomaly(transaction.amount, context)
    if spending_score > 0:
        risk_score += spending_score
        reasons.append(REASON_SPENDING_ANOMALY)

    return FraudEvaluationResult(
        risk_score=risk_score,
        status="",  # Status is assigned after aggregation with static rules.
        reasons=reasons,
    )


def _evaluate_velocity(context: UserBehaviorContext) -> int:
    """Detect transaction bursts within configured time windows."""
    score = 0

    if (
        context.recent_short_window_count
        >= settings.VELOCITY_SHORT_WINDOW_MAX_COUNT
    ):
        score += settings.VELOCITY_SHORT_WINDOW_SCORE

    if context.recent_long_window_count >= settings.VELOCITY_LONG_WINDOW_MAX_COUNT:
        score += settings.VELOCITY_LONG_WINDOW_SCORE

    return score


def _evaluate_country_change(
    country: str,
    context: UserBehaviorContext,
) -> int:
    """Flag transactions from countries not seen in the user's history."""
    if context.prior_transaction_count == 0:
        return 0

    normalized_country = normalize_country(country)
    if normalized_country in context.historical_countries:
        return 0

    return settings.COUNTRY_CHANGE_SCORE


def _evaluate_new_device(device_id: str, context: UserBehaviorContext) -> int:
    """Flag devices that have never been used by this user before."""
    if context.prior_transaction_count == 0:
        return 0

    normalized_device_id = device_id.strip()
    if normalized_device_id in context.known_device_ids:
        return 0

    return settings.NEW_DEVICE_SCORE


def _evaluate_spending_anomaly(
    amount: float,
    context: UserBehaviorContext,
) -> int:
    """Flag amounts that significantly exceed the user's historical average."""
    if context.prior_transaction_count < settings.SPENDING_ANOMALY_MIN_PRIOR_TRANSACTIONS:
        return 0

    if context.average_amount is None or context.average_amount <= 0:
        return 0

    threshold = context.average_amount * settings.SPENDING_ANOMALY_MULTIPLIER
    if amount <= threshold:
        return 0

    return settings.SPENDING_ANOMALY_SCORE
