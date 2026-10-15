"""create products table

Revision ID: 0001_create_products
Revises:
Create Date: 2026-10-16
"""

import sqlalchemy as sa

from alembic import op

revision = "0001_create_products"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sku", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("category", sa.String(length=60), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reorder_level", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("location", sa.String(length=40), nullable=False, server_default=""),
        sa.Column("supplier", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("quantity >= 0", name="ck_products_quantity_non_negative"),
        sa.CheckConstraint("reorder_level >= 0", name="ck_products_reorder_non_negative"),
    )
    op.create_index("ix_products_sku", "products", ["sku"], unique=True)
    op.create_index("ix_products_category", "products", ["category"])


def downgrade() -> None:
    op.drop_index("ix_products_category", table_name="products")
    op.drop_index("ix_products_sku", table_name="products")
    op.drop_table("products")
