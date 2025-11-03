"""Add display_ticker column

Revision ID: 202511031142
Revises: 202511030740
Create Date: 2025-11-03 11:42:00
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "202511031142"
down_revision: Union[str, None] = "202511030740"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("assets", sa.Column("display_ticker", sa.String(length=64), nullable=True))
    op.execute("UPDATE assets SET display_ticker = ticker WHERE display_ticker IS NULL")
    op.create_index("ix_assets_display_ticker", "assets", ["display_ticker"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_assets_display_ticker", table_name="assets")
    op.drop_column("assets", "display_ticker")
