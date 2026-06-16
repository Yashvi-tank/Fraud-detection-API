"""Initial transactions table

Revision ID: 001_initial
Revises:
Create Date: 2026-06-15 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("merchant", sa.String(), nullable=False),
        sa.Column("country", sa.String(), nullable=False),
        sa.Column("device_id", sa.String(), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_transactions_amount_positive"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_transactions_created_at"),
        "transactions",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_transactions_status"),
        "transactions",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_transactions_user_id"),
        "transactions",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_transactions_user_id"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_status"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_created_at"), table_name="transactions")
    op.drop_table("transactions")
