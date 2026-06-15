"""Transaction API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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
    created_at: datetime
