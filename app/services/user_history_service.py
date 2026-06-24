"""User transaction history analysis for behavioral fraud detection."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlmodel import Session, func, select

from app.core.config import settings
from app.models.transaction import Transaction


def normalize_country(country: str) -> str:
    """Normalize a country value for consistent comparison."""
    return country.strip().casefold()


@dataclass(frozen=True)
class UserBehaviorContext:
    """Historical behavior signals derived from prior user transactions."""

    user_id: str
    prior_transaction_count: int
    recent_short_window_count: int
    recent_long_window_count: int
    historical_countries: frozenset[str]
    known_device_ids: frozenset[str]
    average_amount: float | None


class UserHistoryService:
    """Loads user transaction history from PostgreSQL for fraud evaluation."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def build_context(self, user_id: str) -> UserBehaviorContext:
        """Build behavioral context from a user's stored transaction history."""
        now = datetime.now(UTC)
        short_cutoff = now - timedelta(minutes=settings.VELOCITY_SHORT_WINDOW_MINUTES)
        long_cutoff = now - timedelta(minutes=settings.VELOCITY_LONG_WINDOW_MINUTES)

        short_count = self._count_transactions_since(user_id, short_cutoff)
        long_count = self._count_transactions_since(user_id, long_cutoff)

        prior_transactions = self._get_prior_transactions(user_id)
        prior_count = len(prior_transactions)

        historical_countries = frozenset(
            normalize_country(transaction.country)
            for transaction in prior_transactions
        )
        known_device_ids = frozenset(
            transaction.device_id.strip() for transaction in prior_transactions
        )
        average_amount = self._calculate_average_amount(prior_transactions)

        return UserBehaviorContext(
            user_id=user_id,
            prior_transaction_count=prior_count,
            recent_short_window_count=short_count,
            recent_long_window_count=long_count,
            historical_countries=historical_countries,
            known_device_ids=known_device_ids,
            average_amount=average_amount,
        )

    def _count_transactions_since(self, user_id: str, since: datetime) -> int:
        """Count prior transactions for a user within a time window."""
        statement = (
            select(func.count())
            .select_from(Transaction)
            .where(Transaction.user_id == user_id)
            .where(Transaction.created_at >= since)
        )
        return self.session.exec(statement).one()

    def _get_prior_transactions(self, user_id: str) -> list[Transaction]:
        """Return all prior transactions for a user ordered by creation time."""
        statement = (
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.created_at.asc())
        )
        return list(self.session.exec(statement).all())

    @staticmethod
    def _calculate_average_amount(transactions: list[Transaction]) -> float | None:
        """Return the average transaction amount or None when no history exists."""
        if not transactions:
            return None
        return sum(transaction.amount for transaction in transactions) / len(
            transactions
        )
