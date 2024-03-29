"""add price_price_without_discount field

Revision ID: fffca9fb2990
Revises: 6492fd03aab5
Create Date: 2024-01-11 10:31:00.992969

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fffca9fb2990"
down_revision: Union[str, None] = "6492fd03aab5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "prices",
        sa.Column(
            "price_without_discount", sa.Numeric(precision=10, scale=2), nullable=True
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("prices", "price_without_discount")
    # ### end Alembic commands ###
