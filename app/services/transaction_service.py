"""Transaction persistence and orchestration service."""

import math
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, col, func, select

from app.core.config import settings
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCheckRequest, TransactionCheckResponse
from app.services.behavioral_fraud import (
    BehavioralTransactionInput,
    evaluate_behavioral_rules,
)
from app.services.fraud_engine import (
    aggregate_fraud_evaluations,
    apply_ml_boost,
    evaluate_transaction,
)
from app.services.user_history_service import UserHistoryService
from app.utils.logging import logger

SortField = Literal["created_at", "amount", "risk_score"]
SortOrder = Literal["asc", "desc"]

SORT_COLUMNS: dict[SortField, object] = {
    "created_at": Transaction.created_at,
    "amount": Transaction.amount,
    "risk_score": Transaction.risk_score,
}


@dataclass(frozen=True)
class PaginatedTransactions:
    """Paginated transaction query result."""

    items: list[Transaction]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        """Return the total number of pages for the current page size."""
        if self.total == 0:
            return 0
        return math.ceil(self.total / self.page_size)


class TransactionService:
    """Coordinates fraud evaluation and transaction persistence."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def check_transaction(
        self,
        payload: TransactionCheckRequest,
    ) -> TransactionCheckResponse:
        """Evaluate fraud rules and persist the transaction."""
        logger.info(
            "Evaluating transaction for user_id=%s merchant=%s country=%s",
            payload.user_id,
            payload.merchant,
            payload.country,
        )

        user_history = UserHistoryService(self.session)
        behavior_context = user_history.build_context(payload.user_id)

        static_evaluation = evaluate_transaction(
            amount=payload.amount,
            country=payload.country,
            device_id=payload.device_id,
        )
        behavioral_evaluation = evaluate_behavioral_rules(
            BehavioralTransactionInput(
                amount=payload.amount,
                country=payload.country,
                device_id=payload.device_id,
            ),
            behavior_context,
        )
        evaluation = aggregate_fraud_evaluations(
            static_evaluation,
            behavioral_evaluation,
        )

        # --- ML prediction (Phase 3) --------------------------------------
        fraud_probability: float | None = None
        model_version: str | None = None

        if settings.ML_ENABLED:
            from app.ml.feature_engineering import extract_features
            from app.ml.prediction_service import get_predictor

            # Determine behavioral flags for feature extraction.
            country_anomaly = any(
                r == "Transaction originated from unusual country"
                for r in behavioral_evaluation.reasons
            )
            spending_anomaly = any(
                r == "Transaction amount significantly exceeds user history"
                for r in behavioral_evaluation.reasons
            )

            feature_vector = extract_features(
                amount=payload.amount,
                country=payload.country,
                device_id=payload.device_id,
                merchant=payload.merchant,
                velocity_short=behavior_context.recent_short_window_count,
                velocity_long=behavior_context.recent_long_window_count,
                country_anomaly=country_anomaly,
                spending_anomaly=spending_anomaly,
                rule_score=evaluation.risk_score,
            )

            predictor = get_predictor()
            ml_result = predictor.predict(feature_vector)
            fraud_probability = ml_result.fraud_probability
            model_version = ml_result.model_version

            evaluation = apply_ml_boost(
                evaluation,
                ml_probability=fraud_probability,
                ml_weight=settings.ML_WEIGHT,
            )

        logger.info(
            "Fraud evaluation complete: user_id=%s risk_score=%d status=%s "
            "fraud_probability=%s reasons=%s",
            payload.user_id,
            evaluation.risk_score,
            evaluation.status,
            fraud_probability,
            evaluation.reasons,
        )

        transaction = Transaction(
            user_id=payload.user_id,
            amount=payload.amount,
            merchant=payload.merchant,
            country=payload.country,
            device_id=payload.device_id,
            risk_score=evaluation.risk_score,
            status=evaluation.status,
            reasons=evaluation.reasons,
            fraud_probability=fraud_probability,
            model_version=model_version,
        )

        self.session.add(transaction)
        try:
            self.session.commit()
            self.session.refresh(transaction)
        except SQLAlchemyError:
            self.session.rollback()
            logger.exception("Database error while persisting transaction")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to persist transaction",
            ) from None

        logger.info(
            "Transaction checked: transaction_id=%s risk_score=%d status=%s",
            transaction.id,
            transaction.risk_score,
            transaction.status,
        )

        return TransactionCheckResponse(
            transaction_id=transaction.id,
            risk_score=transaction.risk_score,
            status=transaction.status,
            reasons=transaction.reasons_as_list(),
            fraud_probability=fraud_probability,
            model_version=model_version,
        )

    def list_transactions(
        self,
        *,
        page: int = 1,
        page_size: int = 10,
        status: str | None = None,
        user_id: str | None = None,
        country: str | None = None,
        merchant: str | None = None,
        sort_by: SortField = "created_at",
        sort_order: SortOrder = "desc",
    ) -> PaginatedTransactions:
        """Return a paginated, filtered, and sorted list of transactions."""
        filters = self._build_filters(
            status=status,
            user_id=user_id,
            country=country,
            merchant=merchant,
        )

        count_statement = select(func.count()).select_from(Transaction)
        for condition in filters:
            count_statement = count_statement.where(condition)
        total = self.session.exec(count_statement).one()

        statement = select(Transaction)
        for condition in filters:
            statement = statement.where(condition)

        sort_column = SORT_COLUMNS[sort_by]
        if sort_order == "desc":
            statement = statement.order_by(col(sort_column).desc())
        else:
            statement = statement.order_by(col(sort_column).asc())

        offset = (page - 1) * page_size
        statement = statement.offset(offset).limit(page_size)
        items = list(self.session.exec(statement).all())

        logger.debug(
            "Listed transactions: page=%d page_size=%d total=%d filters=%s sort_by=%s sort_order=%s",
            page,
            page_size,
            total,
            {
                "status": status,
                "user_id": user_id,
                "country": country,
                "merchant": merchant,
            },
            sort_by,
            sort_order,
        )

        return PaginatedTransactions(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_transaction(self, transaction_id: UUID) -> Transaction:
        """Return a single transaction or raise 404."""
        transaction = self.session.get(Transaction, transaction_id)
        if transaction is None:
            logger.info("Transaction not found: transaction_id=%s", transaction_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction {transaction_id} not found",
            )
        return transaction

    @staticmethod
    def _build_filters(
        *,
        status: str | None,
        user_id: str | None,
        country: str | None,
        merchant: str | None,
    ) -> list[object]:
        """Build optional SQLModel filter conditions."""
        filters: list[object] = []
        if status is not None:
            filters.append(Transaction.status == status)
        if user_id is not None:
            filters.append(Transaction.user_id == user_id)
        if country is not None:
            filters.append(Transaction.country == country)
        if merchant is not None:
            filters.append(Transaction.merchant == merchant)
        return filters
