"""create stock_movements ledger

Revision ID: 0002_create_stock_movements
Revises: 0001_create_products
Create Date: 2026-10-16
"""

import sqlalchemy as sa

from alembic import op

revision = "0002_create_stock_movements"
down_revision = "0001_create_products"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stock_movements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=20), nullable=False),
        sa.Column("note", sa.String(length=240), nullable=False, server_default=""),
        sa.Column("quantity_after", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_stock_movements_product_id", "stock_movements", ["product_id"])
    op.create_index("ix_stock_movements_created_at", "stock_movements", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_stock_movements_created_at", table_name="stock_movements")
    op.drop_index("ix_stock_movements_product_id", table_name="stock_movements")
    op.drop_table("stock_movements")
