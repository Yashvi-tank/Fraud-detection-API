"""Transaction API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.schemas.transaction import (
    TransactionCheckRequest,
    TransactionCheckResponse,
    TransactionResponse,
)
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])


def get_transaction_service(
    session: Session = Depends(get_session),
) -> TransactionService:
    """Provide a request-scoped transaction service."""
    return TransactionService(session)


@router.post(
    "/check",
    response_model=TransactionCheckResponse,
    summary="Check a transaction for fraud",
    description=(
        "Evaluate the transaction against fraud rules, persist the result, "
        "and return the risk assessment."
    ),
)
def check_transaction(
    payload: TransactionCheckRequest,
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionCheckResponse:
    """Evaluate fraud rules and store the transaction."""
    return service.check_transaction(payload)


@router.get(
    "",
    response_model=list[TransactionResponse],
    summary="List all transactions",
    description="Return every stored transaction ordered by most recent first.",
)
def list_transactions(
    service: TransactionService = Depends(get_transaction_service),
) -> list[TransactionResponse]:
    """Return all stored transactions."""
    transactions = service.list_transactions()
    return [
        TransactionResponse(
            id=transaction.id,
            user_id=transaction.user_id,
            amount=transaction.amount,
            merchant=transaction.merchant,
            country=transaction.country,
            device_id=transaction.device_id,
            risk_score=transaction.risk_score,
            status=transaction.status,
            reasons=transaction.reasons_as_list(),
            created_at=transaction.created_at,
        )
        for transaction in transactions
    ]


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Get a transaction by ID",
    description="Return a single transaction record by its UUID.",
)
def get_transaction(
    transaction_id: UUID,
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponse:
    """Return one transaction by identifier."""
    transaction = service.get_transaction(transaction_id)
    return TransactionResponse(
        id=transaction.id,
        user_id=transaction.user_id,
        amount=transaction.amount,
        merchant=transaction.merchant,
        country=transaction.country,
        device_id=transaction.device_id,
        risk_score=transaction.risk_score,
        status=transaction.status,
        reasons=transaction.reasons_as_list(),
        created_at=transaction.created_at,
    )
