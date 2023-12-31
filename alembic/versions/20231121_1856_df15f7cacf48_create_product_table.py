"""Create Product table

Revision ID: aead2a83cfa8
Revises: 1c8431a64d3a
Create Date: 2023-11-21 18:56:39.786743

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "df15f7cacf48"
down_revision: Union[str, None] = "1c8431a64d3a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("product_name", sa.String(), nullable=True),
        sa.Column("product_quantity", sa.Integer(), nullable=True),
        sa.Column("image_url", sa.String(), nullable=True),
        sa.Column(
            "created",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_products_id"), "products", ["id"], unique=False)
    op.create_index(op.f("ix_products_code"), "products", ["code"], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_products_code"), table_name="products")
    op.drop_index(op.f("ix_products_id"), table_name="products")
    op.drop_table("products")
    # ### end Alembic commands ###
