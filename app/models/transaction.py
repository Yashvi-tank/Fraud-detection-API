"""Transaction database model."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, JSON
from sqlmodel import Field, SQLModel


class Transaction(SQLModel, table=True):
    """Persisted financial transaction with fraud evaluation results."""

    __tablename__ = "transactions"

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    user_id: str = Field(index=True, nullable=False)
    amount: float = Field(nullable=False)
    merchant: str = Field(nullable=False)
    country: str = Field(nullable=False)
    device_id: str = Field(nullable=False)
    risk_score: int = Field(nullable=False)
    status: str = Field(nullable=False, index=True)
    reasons: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )

    def reasons_as_list(self) -> list[str]:
        """Return reasons as a typed list regardless of storage format."""
        if isinstance(self.reasons, list):
            return [str(reason) for reason in self.reasons]
        return []
