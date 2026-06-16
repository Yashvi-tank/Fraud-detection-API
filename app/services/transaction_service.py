"""Transaction persistence and orchestration service."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCheckRequest, TransactionCheckResponse
from app.services.fraud_engine import evaluate_transaction


class TransactionService:
    """Coordinates fraud evaluation and transaction persistence."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def check_transaction(
        self,
        payload: TransactionCheckRequest,
    ) -> TransactionCheckResponse:
        """Evaluate fraud rules and persist the transaction."""
        evaluation = evaluate_transaction(
            amount=payload.amount,
            country=payload.country,
            device_id=payload.device_id,
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
        )

        self.session.add(transaction)
        try:
            self.session.commit()
            self.session.refresh(transaction)
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to persist transaction",
            ) from exc

        return TransactionCheckResponse(
            transaction_id=transaction.id,
            risk_score=transaction.risk_score,
            status=transaction.status,
            reasons=transaction.reasons_as_list(),
        )

    def list_transactions(self) -> list[Transaction]:
        """Return all stored transactions ordered by creation time."""
        statement = select(Transaction).order_by(Transaction.created_at.desc())
        return list(self.session.exec(statement).all())

    def get_transaction(self, transaction_id: UUID) -> Transaction:
        """Return a single transaction or raise 404."""
        transaction = self.session.get(Transaction, transaction_id)
        if transaction is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction {transaction_id} not found",
            )
        return transaction
