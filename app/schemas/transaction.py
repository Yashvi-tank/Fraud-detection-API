"""Transaction API schemas."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field

from app.models.transaction import Transaction


class TransactionCheckRequest(BaseModel):
    """Incoming transaction payload for fraud evaluation."""

    user_id: str = Field(..., min_length=1, description="Unique user identifier")
    amount: float = Field(..., gt=0, description="Transaction amount (must be positive)")
    merchant: str = Field(..., min_length=1, description="Merchant name")
    country: str = Field(..., min_length=1, description="Transaction country")
    device_id: str = Field(..., min_length=1, description="Device identifier")


class TransactionCheckResponse(BaseModel):
    """Fraud evaluation result returned after checking a transaction."""

    transaction_id: UUID
    risk_score: int
    status: str
    reasons: list[str]
    fraud_probability: float | None = None
    model_version: str | None = None


class TransactionResponse(BaseModel):
    """Full transaction record returned by read endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: str
    amount: float
    merchant: str
    country: str
    device_id: str
    risk_score: int
    status: str
    reasons: list[str]
    fraud_probability: float | None = None
    model_version: str | None = None
    created_at: datetime


class TransactionListResponse(BaseModel):
    """Paginated list of transactions."""

    items: list[TransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TransactionListQuery:
    """Query parameters for listing transactions with pagination and filters."""

    def __init__(
        self,
        page: Annotated[int, Query(ge=1, description="Page number (1-based)")] = 1,
        page_size: Annotated[
            int, Query(ge=1, le=100, description="Number of items per page")
        ] = 10,
        status: Annotated[
            str | None, Query(description="Filter by transaction status")
        ] = None,
        user_id: Annotated[
            str | None, Query(description="Filter by user identifier")
        ] = None,
        country: Annotated[
            str | None, Query(description="Filter by country")
        ] = None,
        merchant: Annotated[
            str | None, Query(description="Filter by merchant name")
        ] = None,
        sort_by: Annotated[
            Literal["created_at", "amount", "risk_score"],
            Query(description="Field to sort by"),
        ] = "created_at",
        sort_order: Annotated[
            Literal["asc", "desc"], Query(description="Sort direction")
        ] = "desc",
    ) -> None:
        self.page = page
        self.page_size = page_size
        self.status = status
        self.user_id = user_id
        self.country = country
        self.merchant = merchant
        self.sort_by = sort_by
        self.sort_order = sort_order


def to_transaction_response(transaction: Transaction) -> TransactionResponse:
    """Map a persisted transaction to an API response."""
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
        fraud_probability=transaction.fraud_probability,
        model_version=transaction.model_version,
        created_at=transaction.created_at,
    )
