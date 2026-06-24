"""Transaction API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.schemas.transaction import (
    TransactionCheckRequest,
    TransactionCheckResponse,
    TransactionListQuery,
    TransactionListResponse,
    TransactionResponse,
    to_transaction_response,
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
    response_model=TransactionListResponse,
    summary="List transactions",
    description=(
        "Return a paginated list of transactions with optional filters and sorting. "
        "Defaults to sorting by created_at descending."
    ),
)
def list_transactions(
    query: TransactionListQuery = Depends(),
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionListResponse:
    """Return paginated, filterable transaction results."""
    result = service.list_transactions(
        page=query.page,
        page_size=query.page_size,
        status=query.status,
        user_id=query.user_id,
        country=query.country,
        merchant=query.merchant,
        sort_by=query.sort_by,
        sort_order=query.sort_order,
    )
    return TransactionListResponse(
        items=[to_transaction_response(transaction) for transaction in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


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
    return to_transaction_response(transaction)
