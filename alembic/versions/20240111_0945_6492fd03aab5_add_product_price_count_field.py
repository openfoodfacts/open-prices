"""add product.price_count field

Revision ID: 6492fd03aab5
Revises: a8ad2f078f3f
Create Date: 2024-01-11 09:45:53.633475

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6492fd03aab5"
down_revision: Union[str, None] = "a8ad2f078f3f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "products",
        sa.Column("price_count", sa.Integer(), server_default="0", nullable=False),
    )
    # Set the price_count to the number of prices for each product
    op.execute(
        """
        UPDATE products
        SET price_count = (
            SELECT COUNT(*)
            FROM prices
            WHERE prices.product_id = products.id
        )
        """
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("products", "price_count")
    # ### end Alembic commands ###