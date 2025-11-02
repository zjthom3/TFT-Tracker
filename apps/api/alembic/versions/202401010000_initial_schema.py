"""Initial schema

Revision ID: 202401010000
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "202401010000"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "assets",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ticker", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("type", sa.String(length=16), nullable=False, server_default="stock"),
        sa.Column("exchange", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("ticker", "type", name="uq_assets_ticker_type"),
    )

    op.create_table(
        "market_snapshot",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "asset_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("price", sa.Float, nullable=True),
        sa.Column("price_change_pct", sa.Float, nullable=True),
        sa.Column("volume", sa.Float, nullable=True),
        sa.Column("vwap", sa.Float, nullable=True),
        sa.Column("volatility_1d", sa.Float, nullable=True),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("asset_id", "as_of", name="uq_market_snapshot_asset_time"),
    )
    op.create_index(
        "ix_market_snapshot_asset_time",
        "market_snapshot",
        ["asset_id", "as_of"],
        unique=False,
    )

    op.create_table(
        "indicator_snapshot",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "asset_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "market_snapshot_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("market_snapshot.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("rsi_14", sa.Numeric(10, 4), nullable=True),
        sa.Column("macd", sa.Numeric(10, 4), nullable=True),
        sa.Column("macd_signal", sa.Numeric(10, 4), nullable=True),
        sa.Column("atr_14", sa.Numeric(10, 4), nullable=True),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("asset_id", "as_of", name="uq_indicator_snapshot_asset_time"),
    )
    op.create_index(
        "ix_indicator_snapshot_asset_time",
        "indicator_snapshot",
        ["asset_id", "as_of"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_indicator_snapshot_asset_time", table_name="indicator_snapshot")
    op.drop_table("indicator_snapshot")
    op.drop_index("ix_market_snapshot_asset_time", table_name="market_snapshot")
    op.drop_table("market_snapshot")
    op.drop_table("assets")
